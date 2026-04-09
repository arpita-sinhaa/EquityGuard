from fastapi import APIRouter, HTTPException
from app.models.request_models import CitizenBiasRequest
from app.models.response_models import CitizenBiasResponse, BiasData
from app.services.bigquery_service import get_intersectional_slice
from app.services.gemini_service import generate_citizen_explanation

router = APIRouter()

@router.post("/check-bias", response_model=CitizenBiasResponse)
async def check_bias(request: CitizenBiasRequest):
    # Lookup in BigQuery / Mock
    slice_stats = get_intersectional_slice(
        request.domain,
        request.sex,
        request.race,
        request.age_group
    )
    
    if not slice_stats or slice_stats.get("sample_size", 0) < 100:
        return CitizenBiasResponse(
            status="INSUFFICIENT_DATA",
            message="Not enough historical data to generate a reliable statistical indication."
        )
        
    data = BiasData(
        approval_rate=slice_stats.get("approval_rate", 0.0),
        disparity_ratio=slice_stats.get("disparity_ratio", 1.0),
        fourfifths_breach=slice_stats.get("fourfifths_breach", False),
        sample_size=slice_stats.get("sample_size", 0)
    )
    
    # Check if a flag triggers explanation
    explanation = None
    is_flagged = False
    
    if request.domain.lower() == "hiring" and data.fourfifths_breach:
        is_flagged = True
    elif request.domain.lower() == "lending" and data.disparity_ratio > 1.5:
        is_flagged = True
    elif data.disparity_ratio > 1.5:
        is_flagged = True
        
    if is_flagged:
        explanation = generate_citizen_explanation(
            request.domain, 
            data.disparity_ratio, 
            data.sample_size
        )
    else:
        explanation = "Data indicates approval rates for this group are comparable to the reference groups. No statistical indication of bias was flagged."

    return CitizenBiasResponse(
        status="OK",
        data=data,
        explanation=explanation
    )
