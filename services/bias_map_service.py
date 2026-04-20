from config import FULL_TABLE

def get_bias_map_data():
    query = f"""
    SELECT 
        city,
        sector,
        AVG(disparity_ratio) AS intensity,
        COUNT(*) AS cases
    FROM `{FULL_TABLE}`
    GROUP BY city, sector
    HAVING cases >= 10
    ORDER BY intensity DESC
    """

    df = bq_client.run_query(query)
    return df.to_dict(orient="records")