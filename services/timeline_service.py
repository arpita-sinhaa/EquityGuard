import json
from datetime import datetime

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

TABLE = "equityguard-492819.bias_stats.audit_timeline"

# ✅ Fix 1: Explicit credentials from key.json
with open("key.json") as f:
    key_data = json.load(f)

credentials = service_account.Credentials.from_service_account_file("key.json")
client = bigquery.Client(project=key_data["project_id"], credentials=credentials)


async def process_and_store(file):
    df = pd.read_csv(file.file)

    # ✅ Fix 2: Validate 'approved' column exists and has valid values
    if "approved" not in df.columns:
        raise ValueError("CSV must contain an 'approved' column")

    df["approved"] = pd.to_numeric(df["approved"], errors="coerce").fillna(0)

    rows = []
    grouped = df.groupby(["sex", "race", "age_group"])

    for (sex, race, age), group in grouped:
        approval_rate = group["approved"].mean()
        # ✅ Fix 3: Avoid division by zero in disparity ratio
        reference_rate = 0.5
        disparity_ratio = approval_rate / reference_rate if reference_rate > 0 else 0.0

        rows.append({
            "sex": sex,
            "race": race,
            "age_group": age,
            "approval_rate": float(approval_rate),
            "disparity_ratio": float(disparity_ratio),
            "sample_size": len(group),
            "time_period": datetime.utcnow().isoformat()
        })

    job = client.load_table_from_json(rows, TABLE)
    job.result()

    return len(rows)


def detect_drift(values):
    threshold = 1.0
    cum_sum = 0
    results = []

    for v in values:
        cum_sum += (v - 1)
        if cum_sum > threshold:
            results.append("drifting")
        elif v > 2:
            results.append("breach")
        else:
            results.append("stable")

    return results


def get_timeline_data():
    # ✅ Fix 4: Query deduplicates rows using GROUP BY and fetches all needed fields
    query = f"""
    SELECT 
        sex,
        race,
        age_group,
        AVG(approval_rate)   AS approval_rate,
        AVG(disparity_ratio) AS disparity_ratio,
        MAX(time_period)     AS time_period
    FROM `{TABLE}`
    GROUP BY sex, race, age_group
    ORDER BY time_period
    """

    df = client.query(query).to_dataframe()

    if df.empty:
        return []

    values = df["disparity_ratio"].tolist()
    df["status"] = detect_drift(values)

    return df.to_dict(orient="records")