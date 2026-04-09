from typing import List, Dict
from app.models.request_models import OrganizationDecision
from app.services.bigquery_service import get_intersectional_slice

def process_audit_decisions(domain: str, decisions: List[OrganizationDecision]) -> dict:
    slice_counts = {}
    for d in decisions:
        key = (d.sex, d.race, d.age_group)
        if key not in slice_counts:
            slice_counts[key] = {'count': 0, 'outcomes': []}
        slice_counts[key]['count'] += 1
        slice_counts[key]['outcomes'].append(d.outcome)

    total_records = len(decisions)
    flagged_slices = []
    
    for (sex, race, age_group), data in slice_counts.items():
        slice_stats = get_intersectional_slice(domain, sex, race, age_group)
        
        if not slice_stats or slice_stats.get("sample_size", 0) < 100:
            continue

        is_flagged = False
        priority = "low"
        
        if domain.lower() == "hiring":
            if slice_stats.get("fourfifths_breach", False):
                is_flagged = True
        elif domain.lower() == "lending":
            if slice_stats.get("disparity_ratio", 1.0) > 1.5:
                is_flagged = True
        else:
            if slice_stats.get("disparity_ratio", 1.0) > 1.5:
                is_flagged = True
                
        if is_flagged:
            dr = slice_stats.get("disparity_ratio", 1.0)
            if dr >= 3.0:
                priority = "high"
            elif dr >= 1.5:
                priority = "medium"
                
            flagged_slices.append({
                "sex": sex,
                "race": race,
                "age_group": age_group,
                "disparity_ratio": dr,
                "priority": priority,
                "remediation_note": slice_stats.get("remediation_note", "")
            })
            
    flagged_slices = sorted(flagged_slices, key=lambda x: x["disparity_ratio"], reverse=True)
    
    return {
        "bias_summary": {
            "total_records": total_records,
            "flagged_count": len(flagged_slices)
        },
        "flagged_slices": flagged_slices
    }
