from typing import List, Dict
from app.models.request_models import OrganizationDecision
from app.services.bigquery_service import get_intersectional_slice


def process_audit_decisions(domain: str, decisions: List[OrganizationDecision]) -> dict:
    slice_counts = {}

    # -------------------------
    # GROUP DECISIONS
    # -------------------------
    for d in decisions:
        if domain.lower() == "lending":
            key = (d.gender, d.education, d.income_group)
        else:
            key = (d.sex, d.race, d.age_group)

        if key not in slice_counts:
            slice_counts[key] = {"count": 0, "outcomes": []}

        slice_counts[key]["count"] += 1
        slice_counts[key]["outcomes"].append(d.outcome)

    total_records = len(decisions)
    flagged_slices = []

    # -------------------------
    # ANALYZE EACH SLICE
    # -------------------------
    for key, data in slice_counts.items():

        if domain.lower() == "lending":
            slice_stats = get_intersectional_slice(
                domain,
                gender=key[0],
                education=key[1],
                income_group=key[2]
            )
        else:
            slice_stats = get_intersectional_slice(
                domain,
                sex=key[0],
                race=key[1],
                age_group=key[2]
            )

        # Skip insufficient data
        if not slice_stats or slice_stats.get("sample_size", 0) < 50:
            continue

        # -------------------------
        # FLAGGING LOGIC
        # -------------------------
        dr = slice_stats.get("disparity_ratio")

        if dr is None:
            continue  # skip invalid ratios

        if domain.lower() == "hiring":
            is_flagged = slice_stats.get("fourfifths_breach", False)
        else:
            is_flagged = dr > 1.5

        if not is_flagged:
            continue

        # -------------------------
        # PRIORITY
        # -------------------------
        if dr >= 3:
            priority = "high"
        elif dr >= 1.5:
            priority = "medium"
        else:
            priority = "low"

        # -------------------------
        # RESULT FORMAT
        # -------------------------
        if domain.lower() == "lending":
            result = {
                "gender": key[0],
                "education": key[1],
                "income_group": key[2],
            }
        else:
            result = {
                "sex": key[0],
                "race": key[1],
                "age_group": key[2],
            }

        result.update({
            "disparity_ratio": dr,
            "priority": priority,
            "remediation_note": slice_stats.get("remediation_note", "")
        })

        flagged_slices.append(result)

    # -------------------------
    # SORT RESULTS
    # -------------------------
    flagged_slices.sort(key=lambda x: x["disparity_ratio"], reverse=True)

    return {
        "bias_summary": {
            "total_records": total_records,
            "flagged_count": len(flagged_slices)
        },
        "flagged_slices": flagged_slices
    }