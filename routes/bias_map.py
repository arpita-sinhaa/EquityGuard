from fastapi import APIRouter
from pydantic import BaseModel
from google.cloud import bigquery
from typing import Literal
from datetime import datetime

router = APIRouter(prefix="/map", tags=["map"])

TABLE = "equityguard-492819.bias_stats.bias_map_contributions"


# ✅ create client dynamically (IMPORTANT FIX)
def get_client():
    return bigquery.Client()


class MapContribution(BaseModel):
    city: str
    sector: Literal["hiring", "lending"]
    disparity_ratio: float
    consent: bool


@router.post("/contribute")
def contribute(data: MapContribution):

    if not data.consent:
        return {"stored": False}

    client = get_client()

    rows = [{
        "city": data.city.strip().title(),
        "sector": data.sector,
        "disparity_ratio": float(data.disparity_ratio),
        "case_count": 1,
        "last_updated": datetime.utcnow().isoformat()  # ✅ FIX
    }]

    # ❗ use load job (free tier compatible)
    job = client.load_table_from_json(rows, TABLE)
    job.result()

    return {"stored": True}


@router.get("/data")
def get_map_data(sector: str = "hiring"):

    client = get_client()

    query = f"""
        SELECT
          city,
          sector,
          COUNT(*) AS case_count,
          AVG(disparity_ratio) AS avg_disparity,
          MAX(last_updated) AS last_updated
        FROM `{TABLE}`
        WHERE sector = @sector
        GROUP BY city, sector
        HAVING COUNT(*) >= 10
        ORDER BY avg_disparity DESC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("sector", "STRING", sector)
        ]
    )

    rows = client.query(query, job_config=job_config).result()

    return [dict(row) for row in rows]