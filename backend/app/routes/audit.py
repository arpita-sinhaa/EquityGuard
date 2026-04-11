from fastapi import APIRouter
from app.models.request_models import OrganizationAuditRequest
from app.models.response_models import OrganizationAuditResponse, RemediationPriority
from app.services.audit_engine import process_audit_decisions
from app.services.gemini_service import generate_org_recommendation

router = APIRouter()


def _slice_label(domain: str, slice_data: dict) -> str:
    if domain.lower() == "lending":
        return f"{slice_data.get('gender', 'Unknown')} | {slice_data.get('education', 'Unknown')} | {slice_data.get('income_group', 'Unknown')}"
    return f"{slice_data.get('race', 'Unknown')} | {slice_data.get('sex', 'Unknown')} | {slice_data.get('age_group', 'Unknown')}"


@router.post("/audit", response_model=OrganizationAuditResponse)
async def audit_organization(request: OrganizationAuditRequest):

    audit_results = process_audit_decisions(request.domain, request.decisions)

    flagged_slices = audit_results.get("flagged_slices", [])
    bias_summary = audit_results.get("bias_summary", {})

    # FALLBACK: if no slices found → create manually
    if not flagged_slices and request.domain.lower() == "hiring":
        slices_dict = {}

        for decision in request.decisions:
            key = (decision.race, decision.sex, decision.age_group)

            if key not in slices_dict:
                slices_dict[key] = {"approved": 0, "total": 0}

            slices_dict[key]["total"] += 1

            if decision.outcome == 1:
                slices_dict[key]["approved"] += 1

        for (race, sex, age_group), stats in slices_dict.items():
            approval_rate = stats["approved"] / stats["total"] if stats["total"] > 0 else 0

            flagged_slices.append({
                "race": race,
                "sex": sex,
                "age_group": age_group,
                "approval_rate": approval_rate,
                "disparity_ratio": round(1 / (approval_rate + 0.01), 2),
                "priority": "high",
                "sample_size": stats["total"]
            })

    #  REMEDIATION LOGIC HERE
    for s in flagged_slices:
        if "approval_rate" in s:
            current = s["approval_rate"]
            required = 0.8
            increase = max(0, required - current)

            s["remediation"] = {
                "required_rate": round(required, 2),
                "increase_needed": round(increase, 2),
                "extra_per_100": int(increase * 100)
            }

    # Generate Gemini Report
    gemini_report = generate_org_recommendation(request.domain, flagged_slices)

    # Map priorities
    remediation_priorities = []
    for s in flagged_slices[:3]:
        slice_name = _slice_label(request.domain, s)

        remediation_priorities.append(
            RemediationPriority(
                slice=slice_name,
                priority=s['priority'],
                recommendation=gemini_report
            )
        )

    return OrganizationAuditResponse(
        bias_summary=bias_summary,
        flagged_slices=flagged_slices,
        remediation_priorities=remediation_priorities,
        gemini_report=gemini_report
    )
