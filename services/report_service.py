import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from services.timeline_service import get_timeline_data


async def build_report_data():
    # ✅ Fix 5: No await — get_timeline_data() is sync
    timeline_data = get_timeline_data()

    if not timeline_data:
        return {
            "organisation": "EquityGuard Client",
            "date": datetime.utcnow().isoformat(),
            "fairness_score": 1.0,
            "severity": "No Data",
            "flagged_groups": [],
            "compliance": {
                "Four-Fifths Rule": "N/A",
                "Demographic Parity": "N/A",
                "EU AI Act Readiness": "Pending"
            },
            "remediation": ["Upload a dataset to begin analysis"]
        }

    flagged_groups = []

    for row in timeline_data:
        group_name = f"{row['sex']}-{row['race']}-{row['age_group']}"
        flagged_groups.append({
            "group": group_name,
            "approval_rate": round(row["approval_rate"], 2),
            "disparity_ratio": round(row["disparity_ratio"], 2),
            "severity": "Critical" if row["disparity_ratio"] < 0.8 else "Normal"
        })

    # ✅ Fix 6: Use min disparity so Critical groups aren't averaged away
    min_score = min(g["disparity_ratio"] for g in flagged_groups)
    overall_severity = (
        "Critical" if any(g["disparity_ratio"] < 0.8 for g in flagged_groups)
        else "Stable"
    )

    return {
        "organisation": "EquityGuard Client",
        "date": datetime.utcnow().isoformat(),
        "fairness_score": round(min_score, 2),
        "severity": overall_severity,
        "flagged_groups": flagged_groups,
        "compliance": {
            "Four-Fifths Rule": "Fail" if any(g["disparity_ratio"] < 0.8 for g in flagged_groups) else "Pass",
            "Demographic Parity": "Calculated",
            "EU AI Act Readiness": "Pending"
        },
        "remediation": [
            "Rebalance training dataset",
            "Introduce fairness constraints",
            "Audit model features for proxy bias"
        ]
    }


def generate_pdf(data, file_path=None):
    # ✅ Fix 7: Save PDF relative to this file, not wherever uvicorn runs from
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "report.pdf")

    doc = SimpleDocTemplate(file_path, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    # ── COVER ────────────────────────────────────────────────
    elements.append(Paragraph("EquityGuard Audit Report", styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Organisation: {data['organisation']}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {data['date']}", styles["Normal"]))
    elements.append(Paragraph(f"Fairness Score: {data['fairness_score']}", styles["Normal"]))
    elements.append(Paragraph(f"Severity: {data['severity']}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # ── EXECUTIVE SUMMARY ────────────────────────────────────
    elements.append(Paragraph("Executive Summary", styles["Heading2"]))
    elements.append(Paragraph(
        "This audit evaluates fairness across demographic groups. "
        "Disparities below acceptable thresholds indicate potential bias requiring remediation.",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 20))

    # ── FLAGGED GROUPS TABLE ─────────────────────────────────
    elements.append(Paragraph("Flagged Groups", styles["Heading2"]))

    if data["flagged_groups"]:
        table_data = [["Group", "Approval Rate", "Disparity Ratio", "Severity"]]
        for g in data["flagged_groups"]:
            table_data.append([
                g["group"],
                str(g["approval_rate"]),
                str(g["disparity_ratio"]),
                g["severity"]
            ])

        table = Table(table_data, colWidths=[2.5 * inch, 1.2 * inch, 1.5 * inch, 1 * inch])
        # ✅ Fix 8: Color Critical rows red for visibility
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]
        for i, g in enumerate(data["flagged_groups"], start=1):
            if g["severity"] == "Critical":
                style.append(("BACKGROUND", (0, i), (-1, i), colors.lightcoral))

        table.setStyle(TableStyle(style))
        elements.append(table)
    else:
        elements.append(Paragraph("No flagged groups found.", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # ── COMPLIANCE ───────────────────────────────────────────
    elements.append(Paragraph("Compliance", styles["Heading2"]))
    for k, v in data["compliance"].items():
        elements.append(Paragraph(f"• {k}: {v}", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # ── REMEDIATION ──────────────────────────────────────────
    elements.append(Paragraph("Remediation Roadmap", styles["Heading2"]))
    for item in data["remediation"]:
        elements.append(Paragraph(f"• {item}", styles["Normal"]))

    doc.build(elements)
    return file_path