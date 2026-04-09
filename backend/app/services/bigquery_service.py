import os

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

def get_intersectional_slice(domain: str, sex: str, race: str, age_group: str) -> dict:
    if USE_MOCK_DATA:
        return get_mock_slice(domain, sex, race, age_group)
    else:
        return get_bigquery_slice(domain, sex, race, age_group)

def get_mock_slice(domain: str, sex: str, race: str, age_group: str) -> dict:
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
        },
        ("hiring", "Male", "White", "25-34"): {
            "domain": "hiring",
            "sex": "Male",
            "race": "White",
            "age_group": "25-34",
            "approval_rate": 0.45,
            "sample_size": 500,
            "disparity_ratio": 1.0,
            "fourfifths_breach": False,
            "reference_approval_rate": 0.45,
            "remediation_priority": "none",
            "remediation_note": ""
        },
       ("lending", "Male", "Hispanic", "35-44"): {
            "domain": "lending",
            "sex": "Male",
            "race": "Hispanic",
            "age_group": "35-44",
            "approval_rate": 0.15,
            "sample_size": 300,
            "disparity_ratio": 1.8,
            "fourfifths_breach": True,
            "reference_approval_rate": 0.27,
            "remediation_priority": "medium",
            "remediation_note": "Evaluate automated credit rejection rules."
        }
    }
    
    key = (domain.lower(), sex, race, age_group)
    result = mock_db.get(key)
    if result:
        return result
    
    # Generic low data mock
    return {
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

def get_bigquery_slice(domain: str, sex: str, race: str, age_group: str) -> dict:
    from google.cloud import bigquery
    client = bigquery.Client()
    
    query = """
        SELECT *
        FROM `equityguard.bias_stats.intersectional_slices`
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
    
    try:
        results = client.query(query, job_config=job_config).result()
        for row in results:
            return dict(row)
        return None
    except Exception as e:
        print(f"BQ Error: {e}")
        return None
