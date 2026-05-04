"""
PDF Report Export Module

Generates a one-page PDF summary report of Basel III capital ratios
for a given bank and period, including breach flags and trend data.
"""

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from ratios import CBN_THRESHOLDS


def _get_status_color(value: float, threshold: float):
    """Return green if compliant, red if breached."""
    return colors.HexColor("#059669") if value >= threshold else colors.HexColor("#DC2626")


def _build_styles():
    """Build custom paragraph styles for the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#0A0F1E"),
    ))

    styles.add(ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=12,
        textColor=colors.HexColor("#6B7280"),
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#0A0F1E"),
    ))

    return styles


def generate_pdf_report(processed_df, bank_name: str = "Bank") -> bytes:
    """
    Generate a PDF report from processed ratio data.

    Args:
        processed_df: DataFrame with computed ratios and breach flags
        bank_name: Name of the bank for the report header

    Returns:
        PDF content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = _build_styles()
    elements = []

    # Title
    elements.append(Paragraph(
        f"Basel III Capital Adequacy Report",
        styles["ReportTitle"]
    ))
    elements.append(Paragraph(
        f"{bank_name} — Generated {datetime.now().strftime('%d %B %Y')}",
        styles["ReportSubtitle"]
    ))
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#E5E7EB"),
        spaceAfter=12
    ))

    # Latest ratios summary
    latest = processed_df.iloc[-1]
    latest_period = latest.get("period", "Latest")

    elements.append(Paragraph(
        f"Current Position — {latest_period}",
        styles["SectionHeader"]
    ))

    ratio_data = [["Ratio", "Value", "CBN Minimum", "Status"]]
    for ratio_name, threshold in CBN_THRESHOLDS.items():
        value = latest[ratio_name]
        status = "✓ Compliant" if value >= threshold else "✗ BREACH"
        ratio_data.append([
            ratio_name,
            f"{value:.2f}%",
            f"{threshold:.1f}%",
            status,
        ])

    ratio_table = Table(ratio_data, colWidths=[180, 80, 90, 100])
    ratio_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A0F1E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white, colors.HexColor("#F9FAFB")
        ]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    # Color the status column based on compliance
    for i, (ratio_name, threshold) in enumerate(CBN_THRESHOLDS.items(), start=1):
        value = latest[ratio_name]
        color = _get_status_color(value, threshold)
        ratio_table.setStyle(TableStyle([
            ("TEXTCOLOR", (3, i), (3, i), color),
            ("FONTNAME", (3, i), (3, i), "Helvetica-Bold"),
        ]))

    elements.append(ratio_table)
    elements.append(Spacer(1, 16))

    # Historical trend table
    elements.append(Paragraph("Historical Trend", styles["SectionHeader"]))

    trend_headers = ["Period"] + list(CBN_THRESHOLDS.keys())
    trend_data = [trend_headers]

    for _, row in processed_df.iterrows():
        trend_row = [row.get("period", "—")]
        for ratio_name in CBN_THRESHOLDS.keys():
            trend_row.append(f"{row[ratio_name]:.2f}%")
        trend_data.append(trend_row)

    trend_table = Table(trend_data, colWidths=[90, 120, 130, 150])
    trend_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A0F1E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white, colors.HexColor("#F9FAFB")
        ]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(trend_table)
    elements.append(Spacer(1, 20))

    # Footer
    elements.append(HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#E5E7EB"),
        spaceAfter=8
    ))
    elements.append(Paragraph(
        "Report generated by Basel III Capital Ratio Dashboard — "
        "github.com/JimiR3d/basel3-dashboard",
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#9CA3AF"),
        )
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
