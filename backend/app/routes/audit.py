from fastapi import APIRouter
from app.models.request_models import OrganizationAuditRequest
from app.models.response_models import OrganizationAuditResponse, RemediationPriority
from app.services.audit_engine import process_audit_decisions
from app.services.gemini_service import generate_org_recommendation

router = APIRouter()

@router.post("/audit", response_model=OrganizationAuditResponse)
async def audit_organization(request: OrganizationAuditRequest):
    # Process decisions to find flagged slices via audit engine
    audit_results = process_audit_decisions(request.domain, request.decisions)
    
    flagged_slices = audit_results.get("flagged_slices", [])
    bias_summary = audit_results.get("bias_summary", {})
    
    # Generate Gemini Report (Recommendation)
    gemini_report = generate_org_recommendation(request.domain, flagged_slices)
    
    # Map prioritized slices
    remediation_priorities = []
    for s in flagged_slices[:3]: # top 3
        slice_name = f"{s['race']} {s['sex']} {s['age_group']}"
        remediation_priorities.append(
            RemediationPriority(
                slice=slice_name,
                priority=s['priority'],
                recommendation=gemini_report # For simplicity, we apply the overall gemini context or we could generate per slice
            )
        )
        
    return OrganizationAuditResponse(
        bias_summary=bias_summary,
        flagged_slices=flagged_slices,
        remediation_priorities=remediation_priorities,
        gemini_report=gemini_report
    )
