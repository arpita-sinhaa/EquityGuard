import os
import json
import importlib
from pathlib import Path
from typing import Optional, Dict

# -------------------------
# CONFIG
# -------------------------
PROJECT_ID = "equityguard-492819"
DATASET = "bias_stats"

bq_client = None


def _build_bq_client():
    from google.cloud import bigquery
    service_account = importlib.import_module("google.oauth2.service_account")

    raw = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS_JSON is not set")

    try:
        info = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"Invalid GOOGLE_APPLICATION_CREDENTIALS_JSON: {exc}") from exc

    credentials = service_account.Credentials.from_service_account_info(info)
    project = info.get("project_id") or PROJECT_ID
    return bigquery.Client(project=project, credentials=credentials)

# -------------------------
# ENV CHECK
# -------------------------
def _is_mock_enabled() -> bool:
    value = os.getenv("USE_MOCK_DATA")

    if value is None:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "=" in line:
                    key, val = line.split("=", 1)
                    if key.strip() == "USE_MOCK_DATA":
                        value = val.strip()
                        break

    return str(value).lower() in {"1", "true", "yes"}

# -------------------------
# TABLE SELECTOR
# -------------------------
def get_table_id(domain: str) -> str:
    if domain.lower() == "lending":
        return f"{PROJECT_ID}.{DATASET}.lending_bias_data"
    return f"{PROJECT_ID}.{DATASET}.intersectional_slices"

# -------------------------
# MAIN ROUTER
# -------------------------
def get_intersectional_slice(domain: str, **kwargs) -> Dict:
    if _is_mock_enabled():
        return get_mock_slice(domain, **kwargs)

    result = get_bigquery_slice(domain, **kwargs)

    if result is None:
        return {
            "domain": domain,
            "approval_rate": None,
            "sample_size": 0,
            "disparity_ratio": None,
            "fourfifths_breach": False,
            "reference_approval_rate": None,
            "remediation_priority": "none",
            "remediation_note": "No data available"
        }

    return result

# -------------------------
# MOCK DATA (OPTIONAL)
# -------------------------
def get_mock_slice(domain: str, **kwargs) -> Dict:
    if domain.lower() == "lending":
        return {
            "domain": domain,
            "Gender": kwargs.get("gender"),
            "Education": kwargs.get("education"),
            "income_group": kwargs.get("income_group"),
            "approval_rate": 0.62,
            "sample_size": 60,
            "disparity_ratio": 1.1,
            "fourfifths_breach": False,
            "reference_approval_rate": 0.59,
            "remediation_priority": "low",
            "remediation_note": "Mock fallback lending data",
        }

    return {
        "domain": domain,
        "approval_rate": 0.25,
        "sample_size": 120,
        "disparity_ratio": 1.2,
        "fourfifths_breach": False,
        "reference_approval_rate": 0.30,
        "remediation_priority": "low",
        "remediation_note": "Mock fallback data"
    }

# -------------------------
# BIGQUERY FETCH
# -------------------------
def get_bigquery_slice(domain: str, **kwargs) -> Optional[Dict]:
    global bq_client

    try:
        from google.cloud import bigquery

        if bq_client is None:
            bq_client = _build_bq_client()

        table_id = get_table_id(domain)

        if domain.lower() == "lending":
            required_keys = ["gender", "education", "income_group"]
        else:
            required_keys = ["sex", "race", "age_group"]

        # Validate inputs
        missing = [k for k in required_keys if k not in kwargs]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        if domain.lower() == "lending":
            query = f"""
                SELECT *
                FROM `{table_id}`
                                WHERE LOWER(Gender) = LOWER(@gender)
                                    AND LOWER(Education) = LOWER(@education)
                                    AND LOWER(income_group) = LOWER(@income_group)
                LIMIT 1
            """

            params = [
                bigquery.ScalarQueryParameter("gender", "STRING", kwargs["gender"]),
                bigquery.ScalarQueryParameter("education", "STRING", kwargs["education"]),
                bigquery.ScalarQueryParameter("income_group", "STRING", kwargs["income_group"]),
            ]

        else:
            query = f"""
                SELECT *
                FROM `{table_id}`
                WHERE sex = @sex
                  AND race = @race
                  AND age_group = @age_group
                LIMIT 1
            """

            params = [
                bigquery.ScalarQueryParameter("sex", "STRING", kwargs["sex"]),
                bigquery.ScalarQueryParameter("race", "STRING", kwargs["race"]),
                bigquery.ScalarQueryParameter("age_group", "STRING", kwargs["age_group"]),
            ]

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = bq_client.query(query, job_config=job_config).result()

        for row in results:
            return dict(row)

        return None

    except Exception as e:
        print(f"[BigQuery ERROR]: {e}")
        return None