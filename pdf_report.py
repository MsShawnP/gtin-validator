"""
PDF Report Generator for GTIN Validator.
Produces a branded, professional PDF report using reportlab.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
from collections import defaultdict
from gtin_core import Severity


# Colors
DARK = colors.HexColor("#1a1a2e")
ACCENT = colors.HexColor("#e94560")
GRAY = colors.HexColor("#6c757d")
LIGHT_GRAY = colors.HexColor("#f8f9fa")
GREEN = colors.HexColor("#28a745")
YELLOW = colors.HexColor("#ffc107")
RED = colors.HexColor("#dc3545")
WHITE = colors.white

# Approximate page height available for content (letter = 792pt, minus margins and buffer)
PAGE_CONTENT_HEIGHT = 792 - (0.75 * 72 * 2) - 40  # ~600pt usable


def severity_color(severity):
    if severity == Severity.CRITICAL:
        return RED
    elif severity == Severity.WARNING:
        return YELLOW
    return colors.HexColor("#17a2b8")


def generate_pdf_report(validation_data: dict, company_name: str = "") -> BytesIO:
    """Generate a branded PDF report and return as BytesIO."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=DARK,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=GRAY,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=DARK,
        spaceBefore=20,
        spaceAfter=10,
        borderWidth=0,
    )
    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontSize=10,
        textColor=DARK,
        spaceAfter=6,
        leading=14,
    )
    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontSize=8,
        textColor=GRAY,
        spaceAfter=4,
    )
    score_style = ParagraphStyle(
        "ScoreText",
        parent=styles["Normal"],
        fontSize=36,
        textColor=DARK,
        alignment=TA_CENTER,
        spaceAfter=4,
        leading=44,
    )
    grade_style = ParagraphStyle(
        "GradeText",
        parent=styles["Normal"],
        fontSize=16,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceBefore=16,
        spaceAfter=16,
    )

    elements = []
    summary = validation_data["summary"]
    score = validation_data["score"]
    cost = validation_data["cost_estimate"]
    results = validation_data["results"]

    # --- Title page content ---
    report_title = "Product Data Validation Report"
    if company_name:
        report_title = f"Product Data Validation Report"
        elements.append(Paragraph(company_name, ParagraphStyle(
            "CompanyName", parent=styles["Normal"],
            fontSize=12, textColor=ACCENT, spaceAfter=4,
        )))

    elements.append(Paragraph(report_title, title_style))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        subtitle_style,
    ))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor("#dee2e6"),
        spaceAfter=20,
    ))

    # --- Readiness Score ---
    elements.append(Paragraph("Submission Readiness Score", heading_style))

    score_color = GREEN if score["score"] >= 75 else (YELLOW if score["score"] >= 50 else RED)
    elements.append(Paragraph(
        f'<font color="{score_color.hexval()}">{score["score"]}</font>'
        f'<font color="{GRAY.hexval()}"> / 100</font>',
        score_style,
    ))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f'Grade: {score["grade"]}', grade_style))
    elements.append(Paragraph(score["interpretation"], body_style))
    elements.append(Spacer(1, 12))

    # --- Summary table ---
    elements.append(Paragraph("Summary", heading_style))
    summary_data = [
        ["Metric", "Value"],
        ["Total GTINs Analyzed", str(summary["total_gtins"])],
        ["Valid GTINs", str(summary["valid"])],
        ["Critical Issues", str(summary["critical_issues"])],
        ["Warnings", str(summary["warnings"])],
        ["Clean (No Issues)", str(summary["clean"])],
        ["Duplicate Groups", str(summary["duplicate_groups"])],
        ["Unique Company Prefixes", str(summary["unique_prefixes"])],
    ]
    summary_table = Table(summary_data, colWidths=[3.5 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 12))

    # --- Cost of Inaction ---
    if cost:
        elements.append(PageBreak())
        elements.append(Paragraph("Estimated Cost of Inaction", heading_style))
        elements.append(Paragraph(
            "These estimates are based on industry averages for specialty food brands "
            "at similar scale. Actual costs vary by retailer mix and volume.",
            small_style,
        ))

        cost_data = [
            ["Cost Category", "Estimated Annual Range"],
            [
                "Chargebacks from invalid GTINs",
                f"${cost['chargeback_range'][0]:,} – ${cost['chargeback_range'][1]:,}",
            ],
            [
                f"Delayed retailer launches ({cost['delayed_skus']} SKUs)",
                f"${cost['delayed_launch_range'][0]:,} – ${cost['delayed_launch_range'][1]:,}",
            ],
            [
                f"Manual rework ({cost['rework_hours']} hours/year)",
                f"${cost['rework_cost']:,}",
            ],
            [
                "Total Estimated Annual Cost",
                f"${cost['annual_estimate_low']:,} – ${cost['annual_estimate_high']:,}",
            ],
        ]
        cost_table = Table(cost_data, colWidths=[3.5 * inch, 2.5 * inch])
        cost_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff3cd")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, LIGHT_GRAY]),
        ]))
        elements.append(cost_table)

        if cost.get("growth_note"):
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"<i>{cost['growth_note']}</i>", small_style))

    # --- Retailer Checklists ---
    retailer_checklists = validation_data["retailer_checklists"]
    total_gtins = validation_data["summary"]["total_gtins"]
    for idx, (retailer_name, checklist) in enumerate(retailer_checklists.items()):
        elements.append(PageBreak())
        if idx == 0:
            elements.append(Paragraph("Retailer Readiness Checklists", heading_style))
            elements.append(Spacer(1, 12))

        if checklist["ready"]:
            status = "ALL CHECKS PASSED"
        else:
            status = (
                f"{checklist['passed']} of {checklist['total']} GTIN validation checks passed "
                f"(across all {total_gtins} GTINs submitted)"
            )
        status_color = GREEN if checklist["ready"] else RED

        elements.append(Paragraph(
            f'<font color="{status_color.hexval()}">●</font> '
            f'<b>{retailer_name}</b>',
            ParagraphStyle("RetailerName", parent=body_style, fontSize=14, spaceBefore=12),
        ))
        elements.append(Paragraph(
            checklist["profile"]["description"],
            small_style,
        ))
        elements.append(Paragraph(
            f'<b>{status}</b>',
            ParagraphStyle("RetailerStatus", parent=body_style, fontSize=10,
                           textColor=status_color, spaceAfter=8),
        ))

        # List each check
        for check in checklist["checks"]:
            icon = "✓" if check["passed"] else "✗"
            icon_color = GREEN if check["passed"] else RED
            elements.append(Paragraph(
                f'<font color="{icon_color.hexval()}">{icon}</font>  '
                f'{check["check"]} — <i>{check["detail"]}</i>',
                ParagraphStyle("CheckItem", parent=body_style, fontSize=9, leftIndent=20),
            ))

        # Group failing GTINs by check (issue type)
        failed_checks = [c for c in checklist["checks"] if not c["passed"] and c.get("failing_gtins")]
        if failed_checks:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(
                '<b>Failing GTINs by Issue</b>',
                ParagraphStyle("FailingHeader", parent=body_style, fontSize=11, spaceBefore=8),
            ))

            for check in failed_checks:
                failing = check["failing_gtins"]
                if not failing:
                    continue

                # Try to keep the whole group together
                block = []
                block.append(Paragraph(
                    f'<font color="{RED.hexval()}">✗</font> <b>{check["check"]}</b> — '
                    f'{len(failing)} GTIN(s)',
                    ParagraphStyle("FailGroup", parent=body_style, fontSize=10,
                                   spaceBefore=10, leftIndent=20),
                ))
                for row_num, raw_input in failing:
                    block.append(Paragraph(
                        f'Row {row_num}: {raw_input}',
                        ParagraphStyle("FailItem", parent=small_style, fontSize=8,
                                       leftIndent=40),
                    ))

                # Estimate height: header ~20pt + each row ~14pt
                est_height = 20 + len(failing) * 14
                if est_height <= PAGE_CONTENT_HEIGHT:
                    elements.append(KeepTogether(block))
                else:
                    # Too tall — chunk with continued headers
                    elements.append(block[0])  # header
                    running = 20
                    for j, item_para in enumerate(block[1:]):
                        if running + 14 > PAGE_CONTENT_HEIGHT and j > 0:
                            elements.append(PageBreak())
                            elements.append(Paragraph(
                                f'<font color="{RED.hexval()}">✗</font> '
                                f'<b>{check["check"]} — continued</b>',
                                ParagraphStyle("FailGroupCont", parent=body_style,
                                               fontSize=10, spaceBefore=10, leftIndent=20),
                            ))
                            running = 20
                        elements.append(item_para)
                        running += 14

    # --- Item Detail ---
    elements.append(PageBreak())
    elements.append(Paragraph("Item-Level Detail", heading_style))
    elements.append(Paragraph(
        "Each GTIN analyzed, with issues and recommendations.",
        small_style,
    ))

    # Sort: critical first, then warnings, then clean
    sorted_results = sorted(
        results,
        key=lambda r: (
            0 if r.has_critical else (1 if r.has_warning else 2),
            r.row_number,
        ),
    )

    # Split results by severity
    critical_items = [r for r in sorted_results if r.has_critical]
    warning_items = [r for r in sorted_results if r.has_warning and not r.has_critical]
    info_items = [r for r in sorted_results if r.issues and not r.has_critical and not r.has_warning]

    def render_item_flowables(r, label_color, body_style, small_style):
        """Return a list of flowables for one row (NOT wrapped in KeepTogether)."""
        block = []
        block.append(Paragraph(
            f'<font color="{label_color.hexval()}">●</font> '
            f'Row {r.row_number}: <b>{r.raw_input}</b> '
            f'({r.gtin_type.value if r.gtin_type.value != "Unknown" else "Unknown format"})',
            ParagraphStyle("ItemHeader", parent=body_style, fontSize=10, spaceBefore=10),
        ))
        for issue in r.issues:
            block.append(Paragraph(
                f'<b>[{issue.severity.value}]</b> {issue.message}',
                ParagraphStyle("IssueMsg", parent=body_style, fontSize=9, leftIndent=20),
            ))
            block.append(Paragraph(
                f'<i>Fix: {issue.recommendation}</i>',
                ParagraphStyle("IssueFix", parent=small_style, leftIndent=20),
            ))
        return block

    def render_item_block(r, label_color, body_style, small_style):
        """Return a KeepTogether block for one row."""
        return KeepTogether(render_item_flowables(r, label_color, body_style, small_style))

    def estimate_item_height(r):
        """Rough estimate of how tall one item block will be in points."""
        # Header line ~18pt + each issue ~30pt (message + fix)
        return 18 + len(r.issues) * 30

    def render_group_with_continuation(group_label, recommendation_text, items,
                                       label_color, body_style, small_style, elements):
        """
        Render a group of items. Try to keep header + all items together.
        If too tall, chunk into pages with 'continued' headers.
        """
        # Build the header flowables
        def make_header(continued=False):
            suffix = " — continued" if continued else ""
            header_parts = []
            header_parts.append(Paragraph(
                f'<b>{group_label}{suffix}</b> — {len(items)} item(s)',
                ParagraphStyle("GroupHeader", parent=body_style, fontSize=11,
                               spaceBefore=16, spaceAfter=4, textColor=DARK),
            ))
            if recommendation_text and not continued:
                header_parts.append(Paragraph(
                    f'<i>{recommendation_text}</i>',
                    ParagraphStyle("GroupRec", parent=small_style, leftIndent=20, spaceAfter=8),
                ))
            return header_parts

        # Calculate total height
        total_height = 40  # header + recommendation
        item_heights = []
        for r in items:
            h = estimate_item_height(r)
            item_heights.append(h)
            total_height += h

        # If everything fits on one page, wrap it all in KeepTogether
        if total_height <= PAGE_CONTENT_HEIGHT:
            group_block = make_header(continued=False)
            for r in items:
                group_block.extend(render_item_flowables(r, label_color, body_style, small_style))
            elements.append(KeepTogether(group_block))
        else:
            # Too tall for one page — chunk with continued headers
            elements.extend(make_header(continued=False))

            running_height = 40  # header already placed
            for i, r in enumerate(items):
                h = item_heights[i]
                if running_height + h > PAGE_CONTENT_HEIGHT and i > 0:
                    # Start new page with continued header
                    elements.append(PageBreak())
                    elements.extend(make_header(continued=True))
                    running_height = 40
                elements.append(render_item_block(r, label_color, body_style, small_style))
                running_height += h

    def render_multi_issue_group(group_label, items, label_color, body_style, small_style, elements):
        """Render a multi-issue group with continuation support."""
        def make_header(continued=False):
            suffix = " — continued" if continued else ""
            return [Paragraph(
                f'<b>{group_label}{suffix}</b> — {len(items)} item(s)',
                ParagraphStyle("MultiGroupHeader", parent=body_style, fontSize=11,
                               spaceBefore=16, spaceAfter=8, textColor=DARK),
            )]

        total_height = 30
        item_heights = [estimate_item_height(r) for r in items]
        total_height += sum(item_heights)

        if total_height <= PAGE_CONTENT_HEIGHT:
            group_block = make_header(continued=False)
            for r in items:
                group_block.extend(render_item_flowables(r, label_color, body_style, small_style))
            elements.append(KeepTogether(group_block))
        else:
            elements.extend(make_header(continued=False))
            running_height = 30
            for i, r in enumerate(items):
                h = item_heights[i]
                if running_height + h > PAGE_CONTENT_HEIGHT and i > 0:
                    elements.append(PageBreak())
                    elements.extend(make_header(continued=True))
                    running_height = 30
                elements.append(render_item_block(r, label_color, body_style, small_style))
                running_height += h

    # --- Critical Issues — grouped by issue type ---
    if critical_items:
        elements.append(Paragraph(
            f'<font color="{RED.hexval()}">●</font> '
            f'<b>Critical Issues — These GTINs will be rejected</b>',
            ParagraphStyle("SeverityHeader", parent=heading_style, fontSize=14),
        ))
        elements.append(Spacer(1, 8))

        single_critical = [r for r in critical_items if len([i for i in r.issues if i.severity == Severity.CRITICAL]) == 1]
        multi_critical = [r for r in critical_items if len([i for i in r.issues if i.severity == Severity.CRITICAL]) > 1]

        if single_critical:
            crit_groups = defaultdict(list)
            for r in single_critical:
                crit_issue = next(i for i in r.issues if i.severity == Severity.CRITICAL)
                crit_groups[crit_issue.code].append(r)

            crit_code_labels = {
                "EMPTY": "Empty or Blank GTINs",
                "NON_NUMERIC": "Non-Numeric Characters in GTIN",
                "INVALID_LENGTH": "Invalid GTIN Length",
                "BAD_CHECK_DIGIT": "Incorrect Check Digit",
                "ALL_ZEROS": "Placeholder GTINs (All Zeros)",
            }

            for code, items in crit_groups.items():
                group_label = crit_code_labels.get(code, code)
                sample_issue = next(i for i in items[0].issues if i.code == code)
                render_group_with_continuation(
                    group_label, sample_issue.recommendation, items,
                    RED, body_style, small_style, elements,
                )

        if multi_critical:
            multi_critical.sort(key=lambda r: len([i for i in r.issues if i.severity == Severity.CRITICAL]), reverse=True)
            render_multi_issue_group(
                "Items with Multiple Critical Issues", multi_critical,
                RED, body_style, small_style, elements,
            )

    # --- Warnings — grouped by issue type ---
    if warning_items:
        elements.append(PageBreak())
        elements.append(Paragraph(
            f'<font color="{YELLOW.hexval()}">●</font> '
            f'<b>Warnings — These GTINs may cause problems</b>',
            ParagraphStyle("SeverityHeader", parent=heading_style, fontSize=14),
        ))
        elements.append(Spacer(1, 8))

        single_issue = [r for r in warning_items if len([i for i in r.issues if i.severity == Severity.WARNING]) == 1]
        multi_issue = [r for r in warning_items if len([i for i in r.issues if i.severity == Severity.WARNING]) > 1]

        if single_issue:
            issue_groups = defaultdict(list)
            for r in single_issue:
                warning_issue = next(i for i in r.issues if i.severity == Severity.WARNING)
                issue_groups[warning_issue.code].append(r)

            code_labels = {
                "DUPLICATE": "Duplicate GTINs",
                "PREFIX_MISMATCH": "Company Prefix Mismatch",
                "ORPHAN_CASE_GTIN": "Orphan Case GTINs (no matching unit)",
                "INDICATOR_NINE": "Variable Measure Indicator Digit",
                "UPC_NOT_GTIN13": "UPC-A Format (GTIN-13 may be required)",
                "NO_CASE_GTIN": "Missing Case-Level GTIN-14",
            }

            for code, items in issue_groups.items():
                group_label = code_labels.get(code, code)
                sample_issue = next(i for i in items[0].issues if i.code == code)
                render_group_with_continuation(
                    group_label, sample_issue.recommendation, items,
                    YELLOW, body_style, small_style, elements,
                )

        if multi_issue:
            multi_issue.sort(key=lambda r: len([i for i in r.issues if i.severity == Severity.WARNING]), reverse=True)
            render_multi_issue_group(
                "Items with Multiple Warnings", multi_issue,
                YELLOW, body_style, small_style, elements,
            )

    # --- Info ---
    if info_items:
        elements.append(PageBreak())
        elements.append(Paragraph(
            f'<font color="{colors.HexColor("#17a2b8").hexval()}">●</font> '
            f'<b>Info — Best practice notes</b>',
            ParagraphStyle("SeverityHeader", parent=heading_style, fontSize=14),
        ))
        elements.append(Spacer(1, 8))

        # Group info items by code too
        info_groups = defaultdict(list)
        for r in info_items:
            # Use first info issue code for grouping
            info_issue = next((i for i in r.issues if i.severity == Severity.INFO), r.issues[0])
            info_groups[info_issue.code].append(r)

        info_code_labels = {
            "INDICATOR_ZERO": "GTIN-14 with Indicator 0 (base unit in 14-digit format)",
            "CASE_LEVEL": "Case/Inner Pack Level GTIN-14",
        }

        for code, items in info_groups.items():
            group_label = info_code_labels.get(code, code)
            sample_issue = next((i for i in items[0].issues if i.code == code), items[0].issues[0])
            render_group_with_continuation(
                group_label, sample_issue.recommendation, items,
                colors.HexColor("#17a2b8"), body_style, small_style, elements,
            )

    # --- Clean items summary ---
    clean_items = [r for r in results if not r.issues]
    if clean_items:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            f"{len(clean_items)} GTIN(s) passed all checks with no issues.",
            ParagraphStyle("CleanSummary", parent=body_style, textColor=GREEN),
        ))

    # --- Footer ---
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#dee2e6"),
        spaceAfter=10,
    ))
    elements.append(Paragraph(
        "This report was generated by the GTIN Product Data Validator. "
        "Estimates are directional based on industry averages and should be "
        "validated against your specific retailer relationships and volume. "
        "For a comprehensive Product Data Health Audit, contact the author.",
        ParagraphStyle("Footer", parent=small_style, alignment=TA_CENTER),
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
