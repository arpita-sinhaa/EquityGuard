from fastapi import APIRouter
from app.models.request_models import CitizenBiasRequest
from app.models.response_models import CitizenBiasResponse, BiasData
from app.services.bigquery_service import get_intersectional_slice
from app.services.gemini_service import generate_citizen_explanation

router = APIRouter()


def get_legal_rights(country: str) -> str:
    if not country:
        return "Under DPDP Act 2023, you have the right to grievance redressal."

    country = country.strip().lower()

    mapping = {
        "india": "Under DPDP Act 2023, you have the right to grievance redressal.",
        "eu": "Under EU AI Act Article 22, you have the right to explanation.",
        "us": "Under EEOC guidelines, discrimination is prohibited.",
        "uk": "Under UK GDPR Article 22, you can request human review.",
    }

    return mapping.get(country, "You have the right to question automated decisions and seek human review.")


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
    
    # Remediation simulator
    remediation = None
    if data.disparity_ratio < 0.8:
        reference_approval_rate = 1.0  # assume for now
        required_rate = 0.8 * reference_approval_rate
        increase_needed = required_rate - data.approval_rate
        extra_per_100 = increase_needed * 100
        remediation = {
            "required_rate": required_rate,
            "increase_needed": increase_needed,
            "extra_per_100": extra_per_100
        }
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

    country = (request.country or "India").strip()
    legal_rights = get_legal_rights(country)

    return CitizenBiasResponse(
        status="OK",
        data=data,
        explanation=explanation,
        legal_rights=legal_rights,
        counterfactuals=counterfactuals if counterfactuals else None,
        remediation=remediation
    )
