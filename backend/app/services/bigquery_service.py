import os
from pathlib import Path
from typing import Optional, Dict

# -------------------------
# CONFIG
# -------------------------
def _is_mock_enabled() -> bool:
    value = os.getenv("USE_MOCK_DATA")

    # Fallback to backend/.env when python-dotenv is not installed.
    if value is None:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, raw = stripped.split("=", 1)
                if key.strip() == "USE_MOCK_DATA":
                    value = raw.strip().strip('"').strip("'")
                    break

    # Default to BigQuery mode unless mock is explicitly enabled.
    value = (value or "false").strip().lower()
    return value in {"1", "true", "yes", "on"}

PROJECT_ID = "equityguard-492819"
DATASET = "bias_stats"
TABLE = "intersectional_slices"

TABLE_ID = f"{PROJECT_ID}.{DATASET}.{TABLE}"

# Initialize BigQuery client once (efficient)
bq_client = None

# -------------------------
# MAIN ROUTER
# -------------------------
def get_intersectional_slice(domain: str, sex: str, race: str, age_group: str) -> Dict:
    if _is_mock_enabled():
        print("Using MOCK data")
        return get_mock_slice(domain, sex, race, age_group)
    else:
        print("Using BIGQUERY data")
        print("CREDENTIAL PATH:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        result = get_bigquery_slice(domain, sex, race, age_group)

        # Fallback if no data found
        if result is None:
            return {
                "domain": domain,
                "sex": sex,
                "race": race,
                "age_group": age_group,
                "approval_rate": None,
                "sample_size": 0,
                "disparity_ratio": None,
                "fourfifths_breach": False,
                "reference_approval_rate": None,
                "remediation_priority": "none",
                "remediation_note": "No data available for this group"
            }

        return result

# -------------------------
# MOCK DATA
# -------------------------
def get_mock_slice(domain: str, sex: str, race: str, age_group: str) -> Dict:
    mock_db = {
        ("hiring", "Female", "Black", "45-54"): {
            "domain": "hiring",
            "sex": "Female",
            "race": "Black",
            "age_group": "45-54",
            "approval_rate": 0.09,
            "sample_size": 120,
            "disparity_ratio": 4.6,
            "fourfifths_breach": True,
            "reference_approval_rate": 0.41,
            "remediation_priority": "high",
            "remediation_note": "Review standard tenure criteria which has historic demographic skew."
        }
    }

    key = (domain.lower(), sex, race, age_group)

    return mock_db.get(
        key,
        {
            "domain": domain,
            "sex": sex,
            "race": race,
            "age_group": age_group,
            "approval_rate": 0.20,
            "sample_size": 50,
            "disparity_ratio": 1.1,
            "fourfifths_breach": False,
            "reference_approval_rate": 0.22,
            "remediation_priority": "none",
            "remediation_note": ""
        }
    )

# -------------------------
# BIGQUERY FETCH
# -------------------------
def get_bigquery_slice(domain: str, sex: str, race: str, age_group: str) -> Optional[Dict]:
    global bq_client

    try:
        from google.cloud import bigquery

        if bq_client is None:
            bq_client = bigquery.Client()

        query = f"""
            SELECT *
            FROM `{TABLE_ID}`
            WHERE domain = @domain
              AND sex = @sex
              AND race = @race
              AND age_group = @age_group
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain", "STRING", domain),
                bigquery.ScalarQueryParameter("sex", "STRING", sex),
                bigquery.ScalarQueryParameter("race", "STRING", race),
                bigquery.ScalarQueryParameter("age_group", "STRING", age_group),
            ]
        )

        query_job = bq_client.query(query, job_config=job_config)
        results = query_job.result()

        for row in results:
            print("BQ data found")
            return dict(row)

        print("No matching data found in BQ")
        return None

    except Exception as e:
        print(f"[BigQuery ERROR]: {e}")
        return None