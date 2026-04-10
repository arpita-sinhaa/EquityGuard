from fastapi import APIRouter
from app.models.request_models import CitizenBiasRequest
from app.models.response_models import CitizenBiasResponse, BiasData
from app.services.bigquery_service import get_intersectional_slice
from app.services.gemini_service import generate_citizen_explanation

router = APIRouter()

@router.post("/check-bias", response_model=CitizenBiasResponse)
async def check_bias(request: CitizenBiasRequest):
    # Lookup in BigQuery / Mock
    domain = request.domain.lower()

    if domain == "lending":
        slice_stats = get_intersectional_slice(
            request.domain,
            gender=request.gender,
            education=request.education,
            income_group=request.income_group
        )
    else:
        slice_stats = get_intersectional_slice(
            request.domain,
            sex=request.sex,
            race=request.race,
            age_group=request.age_group
        )
    
    min_sample_size = 50 if domain == "lending" else 100
    if not slice_stats or slice_stats.get("sample_size", 0) < min_sample_size:
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
    
    # Generate counterfactuals
    counterfactuals = []
    if domain == "lending":
        current_attrs = {
            'gender': request.gender,
            'education': request.education,
            'income_group': request.income_group
        }
        references = {
            'gender': 'Male',
            'education': 'Graduate',
            'income_group': 'high'
        }
    else:
        current_attrs = {
            'sex': request.sex,
            'race': request.race,
            'age_group': request.age_group
        }
        references = {
            'sex': 'Male',
            'race': 'White',
            'age_group': '25-34'
        }
    
    for attr, ref_val in references.items():
        if current_attrs[attr] != ref_val:
            new_attrs = current_attrs.copy()
            new_attrs[attr] = ref_val
            new_slice = get_intersectional_slice(request.domain, **new_attrs)
            if new_slice and new_slice.get("sample_size", 0) >= min_sample_size:
                counterfactuals.append({
                    "changed_attribute": attr,
                    "new_value": ref_val,
                    "approval_rate": new_slice.get("approval_rate", 0.0)
                })
    
    # Check if a flag triggers explanation
    explanation = None
    is_flagged = False
    
    if domain == "hiring" and data.fourfifths_breach:
        is_flagged = True
    elif domain == "lending" and data.disparity_ratio > 1.5:
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
        explanation=explanation,
        counterfactuals=counterfactuals if counterfactuals else None
    )
