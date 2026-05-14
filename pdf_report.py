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
from xml.sax.saxutils import escape as _xml_escape

from gtin_core import Severity


# =============================================================================
# Constants
# =============================================================================

# Brand palette
DARK = colors.HexColor("#1a1a2e")
ACCENT = colors.HexColor("#e94560")
GRAY = colors.HexColor("#6c757d")
LIGHT_GRAY = colors.HexColor("#f8f9fa")
GREEN = colors.HexColor("#28a745")
YELLOW = colors.HexColor("#ffc107")
RED = colors.HexColor("#dc3545")
INFO_BLUE = colors.HexColor("#17a2b8")
WHITE = colors.white
BORDER = colors.HexColor("#dee2e6")
TOTAL_ROW_BG = colors.HexColor("#fff3cd")

# Page geometry — letter is 792pt tall, with 0.75in margins top+bottom and a
# 40pt safety buffer this leaves ~644pt of usable vertical space we use to
# decide whether a flowable group fits on one page or needs continuation.
PAGE_MARGIN = 0.75 * inch
PAGE_CONTENT_HEIGHT = 792 - (PAGE_MARGIN * 2) - 40  # ~644pt usable

# Layout heuristics for the item-detail pagination decisions. These are
# rough estimates of rendered flowable height in points; they only need to
# be in the right ballpark for KeepTogether vs explicit continuation.
ITEM_HEADER_PT = 18
ISSUE_BLOCK_PT = 30  # message + fix line
GROUP_HEADER_PT = 40  # heading + recommendation
MULTI_GROUP_HEADER_PT = 30
FAILING_ROW_PT = 14
FAILING_HEADER_PT = 20

# Issue-code → human-readable group label, used when grouping items in
# the per-severity sections of the item detail page.
_CRITICAL_LABELS = {
    "EMPTY": "Empty or Blank GTINs",
    "NON_NUMERIC": "Non-Numeric Characters in GTIN",
    "INVALID_LENGTH": "Invalid GTIN Length",
    "BAD_CHECK_DIGIT": "Incorrect Check Digit",
    "ALL_ZEROS": "Placeholder GTINs (All Zeros)",
}
_WARNING_LABELS = {
    "DUPLICATE": "Duplicate GTINs",
    "PREFIX_MISMATCH": "Company Prefix Mismatch",
    "ORPHAN_CASE_GTIN": "Orphan Case GTINs (no matching unit)",
    "INDICATOR_NINE": "Variable Measure Indicator Digit",
    "UPC_NOT_GTIN13": "UPC-A Format (GTIN-13 may be required)",
    "NO_CASE_GTIN": "Missing Case-Level GTIN-14",
}
_INFO_LABELS = {
    "INDICATOR_ZERO": "GTIN-14 with Indicator 0 (base unit in 14-digit format)",
    "CASE_LEVEL": "Case/Inner Pack Level GTIN-14",
}


# =============================================================================
# Helpers
# =============================================================================

def _escape(value) -> str:
    """Escape user-supplied text before embedding in a ReportLab Paragraph.

    ReportLab parses inline XML/HTML-style markup in Paragraph strings,
    so any `<`, `>`, or `&` from user input would corrupt rendering or
    inject unintended markup.
    """
    return _xml_escape("" if value is None else str(value))


def severity_color(severity):
    """Map a Severity enum to its brand colour."""
    if severity == Severity.CRITICAL:
        return RED
    elif severity == Severity.WARNING:
        return YELLOW
    return INFO_BLUE


def _build_styles() -> dict:
    """Build the named ParagraphStyle objects used throughout the report."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"], fontSize=22,
            textColor=DARK, spaceAfter=6, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle", parent=base["Normal"], fontSize=11,
            textColor=GRAY, spaceAfter=20,
        ),
        "heading": ParagraphStyle(
            "SectionHeading", parent=base["Heading2"], fontSize=14,
            textColor=DARK, spaceBefore=20, spaceAfter=10, borderWidth=0,
        ),
        "body": ParagraphStyle(
            "BodyText", parent=base["Normal"], fontSize=10,
            textColor=DARK, spaceAfter=6, leading=14,
        ),
        "small": ParagraphStyle(
            "SmallText", parent=base["Normal"], fontSize=8,
            textColor=GRAY, spaceAfter=4,
        ),
        "score": ParagraphStyle(
            "ScoreText", parent=base["Normal"], fontSize=36,
            textColor=DARK, alignment=TA_CENTER, spaceAfter=4, leading=44,
        ),
        "grade": ParagraphStyle(
            "GradeText", parent=base["Normal"], fontSize=16,
            textColor=GRAY, alignment=TA_CENTER,
            spaceBefore=16, spaceAfter=16,
        ),
        "company_name": ParagraphStyle(
            "CompanyName", parent=base["Normal"], fontSize=12,
            textColor=ACCENT, spaceAfter=4,
        ),
    }


# =============================================================================
# Builder
# =============================================================================

class PDFReportBuilder:
    """Assemble the validation PDF.

    Each `_render_*` method appends flowables to `self.elements`. The public
    `build()` method composes them in order and returns a populated BytesIO.
    """

    def __init__(self, validation_data: dict, company_name: str = ""):
        self.data = validation_data
        self.company_name = company_name
        self.styles = _build_styles()
        self.elements: list = []
        self.results = validation_data["results"]
        self.summary = validation_data["summary"]
        self.score = validation_data["score"]
        self.cost = validation_data["cost_estimate"]
        self.retailer_checklists = validation_data["retailer_checklists"]

    # -- public entrypoint -------------------------------------------------

    def build(self) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=PAGE_MARGIN,
            bottomMargin=PAGE_MARGIN,
            leftMargin=PAGE_MARGIN,
            rightMargin=PAGE_MARGIN,
        )

        self._render_title()
        self._render_score()
        self._render_summary()
        self._render_cost()
        self._render_retailer_checklists()
        self._render_item_detail()
        self._render_footer()

        doc.build(self.elements)
        buffer.seek(0)
        return buffer

    # -- sections ----------------------------------------------------------

    def _render_title(self):
        if self.company_name:
            self.elements.append(Paragraph(
                _escape(self.company_name), self.styles["company_name"],
            ))
        self.elements.append(Paragraph(
            "Product Data Validation Report", self.styles["title"],
        ))
        self.elements.append(Paragraph(
            f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles["subtitle"],
        ))
        self.elements.append(HRFlowable(
            width="100%", thickness=1, color=BORDER, spaceAfter=20,
        ))

    def _render_score(self):
        score = self.score
        self.elements.append(Paragraph(
            "Submission Readiness Score", self.styles["heading"],
        ))
        score_color = (
            GREEN if score["score"] >= 75
            else YELLOW if score["score"] >= 50
            else RED
        )
        self.elements.append(Paragraph(
            f'<font color="{score_color.hexval()}">{score["score"]}</font>'
            f'<font color="{GRAY.hexval()}"> / 100</font>',
            self.styles["score"],
        ))
        self.elements.append(Spacer(1, 20))
        self.elements.append(Paragraph(
            f'Grade: {score["grade"]}', self.styles["grade"],
        ))
        self.elements.append(Paragraph(
            score["interpretation"], self.styles["body"],
        ))
        self.elements.append(Spacer(1, 12))

    def _render_summary(self):
        s = self.summary
        self.elements.append(Paragraph("Summary", self.styles["heading"]))
        rows = [
            ["Metric", "Value"],
            ["Total GTINs Analyzed", str(s["total_gtins"])],
            ["Valid GTINs", str(s["valid"])],
            ["Critical Issues", str(s["critical_issues"])],
            ["Warnings", str(s["warnings"])],
            ["Clean (No Issues)", str(s["clean"])],
            ["Duplicate Groups", str(s["duplicate_groups"])],
            ["Unique Company Prefixes", str(s["unique_prefixes"])],
        ]
        table = Table(rows, colWidths=[3.5 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ]))
        self.elements.append(table)
        self.elements.append(Spacer(1, 12))

    def _render_cost(self):
        cost = self.cost
        if not cost:
            return
        self.elements.append(PageBreak())
        self.elements.append(Paragraph(
            "Estimated Cost of Inaction", self.styles["heading"],
        ))
        self.elements.append(Paragraph(
            "These estimates are based on industry averages for specialty food brands "
            "at similar scale. Actual costs vary by retailer mix and volume.",
            self.styles["small"],
        ))
        rows = [
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
        table = Table(rows, colWidths=[3.5 * inch, 2.5 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), TOTAL_ROW_BG),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, LIGHT_GRAY]),
        ]))
        self.elements.append(table)
        if cost.get("growth_note"):
            self.elements.append(Spacer(1, 6))
            self.elements.append(Paragraph(
                f"<i>{_escape(cost['growth_note'])}</i>", self.styles["small"],
            ))

    def _render_retailer_checklists(self):
        total_gtins = self.summary["total_gtins"]
        for idx, (retailer_name, checklist) in enumerate(self.retailer_checklists.items()):
            self.elements.append(PageBreak())
            if idx == 0:
                self.elements.append(Paragraph(
                    "Retailer Readiness Checklists", self.styles["heading"],
                ))
                self.elements.append(Spacer(1, 12))

            if checklist["ready"]:
                status = "ALL CHECKS PASSED"
            else:
                status = (
                    f"{checklist['passed']} of {checklist['total']} GTIN validation checks passed "
                    f"(across all {total_gtins} GTINs submitted)"
                )
            status_color = GREEN if checklist["ready"] else RED

            self.elements.append(Paragraph(
                f'<font color="{status_color.hexval()}">●</font> '
                f'<b>{retailer_name}</b>',
                ParagraphStyle("RetailerName", parent=self.styles["body"],
                               fontSize=14, spaceBefore=12),
            ))
            self.elements.append(Paragraph(
                checklist["profile"]["description"], self.styles["small"],
            ))
            self.elements.append(Paragraph(
                f'<b>{status}</b>',
                ParagraphStyle("RetailerStatus", parent=self.styles["body"],
                               fontSize=10, textColor=status_color, spaceAfter=8),
            ))

            for check in checklist["checks"]:
                icon = "✓" if check["passed"] else "✗"
                icon_color = GREEN if check["passed"] else RED
                self.elements.append(Paragraph(
                    f'<font color="{icon_color.hexval()}">{icon}</font>  '
                    f'{check["check"]} — <i>{check["detail"]}</i>',
                    ParagraphStyle("CheckItem", parent=self.styles["body"],
                                   fontSize=9, leftIndent=20),
                ))

            self._render_failing_gtins_for_retailer(checklist)

    def _render_failing_gtins_for_retailer(self, checklist):
        failed_checks = [
            c for c in checklist["checks"]
            if not c["passed"] and c.get("failing_gtins")
        ]
        if not failed_checks:
            return

        self.elements.append(Spacer(1, 12))
        self.elements.append(Paragraph(
            '<b>Failing GTINs by Issue</b>',
            ParagraphStyle("FailingHeader", parent=self.styles["body"],
                           fontSize=11, spaceBefore=8),
        ))

        for check in failed_checks:
            failing = check["failing_gtins"]
            if not failing:
                continue

            block = [Paragraph(
                f'<font color="{RED.hexval()}">✗</font> <b>{check["check"]}</b> — '
                f'{len(failing)} GTIN(s)',
                ParagraphStyle("FailGroup", parent=self.styles["body"],
                               fontSize=10, spaceBefore=10, leftIndent=20),
            )]
            for row_num, raw_input in failing:
                block.append(Paragraph(
                    f'Row {row_num}: {_escape(raw_input)}',
                    ParagraphStyle("FailItem", parent=self.styles["small"],
                                   fontSize=8, leftIndent=40),
                ))

            est_height = FAILING_HEADER_PT + len(failing) * FAILING_ROW_PT
            if est_height <= PAGE_CONTENT_HEIGHT:
                self.elements.append(KeepTogether(block))
            else:
                # Too tall — chunk with continued headers
                self.elements.append(block[0])
                running = FAILING_HEADER_PT
                for j, item_para in enumerate(block[1:]):
                    if running + FAILING_ROW_PT > PAGE_CONTENT_HEIGHT and j > 0:
                        self.elements.append(PageBreak())
                        self.elements.append(Paragraph(
                            f'<font color="{RED.hexval()}">✗</font> '
                            f'<b>{check["check"]} — continued</b>',
                            ParagraphStyle("FailGroupCont", parent=self.styles["body"],
                                           fontSize=10, spaceBefore=10, leftIndent=20),
                        ))
                        running = FAILING_HEADER_PT
                    self.elements.append(item_para)
                    running += FAILING_ROW_PT

    def _render_item_detail(self):
        self.elements.append(PageBreak())
        self.elements.append(Paragraph(
            "Item-Level Detail", self.styles["heading"],
        ))
        self.elements.append(Paragraph(
            "Each GTIN analyzed, with issues and recommendations.",
            self.styles["small"],
        ))

        sorted_results = sorted(
            self.results,
            key=lambda r: (
                0 if r.has_critical else (1 if r.has_warning else 2),
                r.row_number,
            ),
        )

        critical_items = [r for r in sorted_results if r.has_critical]
        warning_items = [
            r for r in sorted_results
            if r.has_warning and not r.has_critical
        ]
        info_items = [
            r for r in sorted_results
            if r.issues and not r.has_critical and not r.has_warning
        ]

        self._render_critical_section(critical_items)
        self._render_warning_section(warning_items)
        self._render_info_section(info_items)
        self._render_clean_summary()

    def _render_critical_section(self, critical_items):
        if not critical_items:
            return
        self.elements.append(Paragraph(
            f'<font color="{RED.hexval()}">●</font> '
            f'<b>Critical Issues — These GTINs will be rejected</b>',
            ParagraphStyle("SeverityHeader", parent=self.styles["heading"], fontSize=14),
        ))
        self.elements.append(Spacer(1, 8))

        single_critical = [
            r for r in critical_items
            if sum(1 for i in r.issues if i.severity == Severity.CRITICAL) == 1
        ]
        multi_critical = [
            r for r in critical_items
            if sum(1 for i in r.issues if i.severity == Severity.CRITICAL) > 1
        ]

        if single_critical:
            groups: dict[str, list] = defaultdict(list)
            for r in single_critical:
                crit_issue = next(
                    i for i in r.issues if i.severity == Severity.CRITICAL
                )
                groups[crit_issue.code].append(r)
            for code, items in groups.items():
                label = _CRITICAL_LABELS.get(code, code)
                sample_issue = next(i for i in items[0].issues if i.code == code)
                self._render_group_with_continuation(
                    label, sample_issue.recommendation, items, RED,
                )

        if multi_critical:
            multi_critical.sort(
                key=lambda r: sum(1 for i in r.issues if i.severity == Severity.CRITICAL),
                reverse=True,
            )
            self._render_multi_issue_group(
                "Items with Multiple Critical Issues", multi_critical, RED,
            )

    def _render_warning_section(self, warning_items):
        if not warning_items:
            return
        self.elements.append(PageBreak())
        self.elements.append(Paragraph(
            f'<font color="{YELLOW.hexval()}">●</font> '
            f'<b>Warnings — These GTINs may cause problems</b>',
            ParagraphStyle("SeverityHeader", parent=self.styles["heading"], fontSize=14),
        ))
        self.elements.append(Spacer(1, 8))

        single = [
            r for r in warning_items
            if sum(1 for i in r.issues if i.severity == Severity.WARNING) == 1
        ]
        multi = [
            r for r in warning_items
            if sum(1 for i in r.issues if i.severity == Severity.WARNING) > 1
        ]

        if single:
            groups: dict[str, list] = defaultdict(list)
            for r in single:
                warning_issue = next(
                    i for i in r.issues if i.severity == Severity.WARNING
                )
                groups[warning_issue.code].append(r)
            for code, items in groups.items():
                label = _WARNING_LABELS.get(code, code)
                sample_issue = next(i for i in items[0].issues if i.code == code)
                self._render_group_with_continuation(
                    label, sample_issue.recommendation, items, YELLOW,
                )

        if multi:
            multi.sort(
                key=lambda r: sum(1 for i in r.issues if i.severity == Severity.WARNING),
                reverse=True,
            )
            self._render_multi_issue_group(
                "Items with Multiple Warnings", multi, YELLOW,
            )

    def _render_info_section(self, info_items):
        if not info_items:
            return
        self.elements.append(PageBreak())
        self.elements.append(Paragraph(
            f'<font color="{INFO_BLUE.hexval()}">●</font> '
            f'<b>Info — Best practice notes</b>',
            ParagraphStyle("SeverityHeader", parent=self.styles["heading"], fontSize=14),
        ))
        self.elements.append(Spacer(1, 8))

        groups: dict[str, list] = defaultdict(list)
        for r in info_items:
            info_issue = next(
                (i for i in r.issues if i.severity == Severity.INFO),
                r.issues[0],
            )
            groups[info_issue.code].append(r)

        for code, items in groups.items():
            label = _INFO_LABELS.get(code, code)
            sample_issue = next(
                (i for i in items[0].issues if i.code == code),
                items[0].issues[0],
            )
            self._render_group_with_continuation(
                label, sample_issue.recommendation, items, INFO_BLUE,
            )

    def _render_clean_summary(self):
        clean_items = [r for r in self.results if not r.issues]
        if not clean_items:
            return
        self.elements.append(Spacer(1, 12))
        self.elements.append(Paragraph(
            f"{len(clean_items)} GTIN(s) passed all checks with no issues.",
            ParagraphStyle("CleanSummary", parent=self.styles["body"], textColor=GREEN),
        ))

    def _render_footer(self):
        self.elements.append(Spacer(1, 30))
        self.elements.append(HRFlowable(
            width="100%", thickness=0.5, color=BORDER, spaceAfter=10,
        ))
        self.elements.append(Paragraph(
            "This report was generated by the GTIN Product Data Validator. "
            "Estimates are directional based on industry averages and should be "
            "validated against your specific retailer relationships and volume. "
            "For a comprehensive Product Data Health Audit, contact the author.",
            ParagraphStyle("Footer", parent=self.styles["small"], alignment=TA_CENTER),
        ))

    # -- per-item rendering helpers ---------------------------------------

    def _render_item_flowables(self, r, label_color):
        """Return a list of flowables for one row (NOT wrapped in KeepTogether)."""
        block = [Paragraph(
            f'<font color="{label_color.hexval()}">●</font> '
            f'Row {r.row_number}: <b>{_escape(r.raw_input)}</b> '
            f'({_escape(r.gtin_type.value) if r.gtin_type.value != "Unknown" else "Unknown format"})',
            ParagraphStyle("ItemHeader", parent=self.styles["body"],
                           fontSize=10, spaceBefore=10),
        )]
        for issue in r.issues:
            block.append(Paragraph(
                f'<b>[{issue.severity.value}]</b> {_escape(issue.message)}',
                ParagraphStyle("IssueMsg", parent=self.styles["body"],
                               fontSize=9, leftIndent=20),
            ))
            block.append(Paragraph(
                f'<i>Fix: {_escape(issue.recommendation)}</i>',
                ParagraphStyle("IssueFix", parent=self.styles["small"], leftIndent=20),
            ))
        return block

    def _render_item_block(self, r, label_color):
        return KeepTogether(self._render_item_flowables(r, label_color))

    @staticmethod
    def _estimate_item_height(r):
        return ITEM_HEADER_PT + len(r.issues) * ISSUE_BLOCK_PT

    def _render_group_with_continuation(
        self, group_label, recommendation_text, items, label_color,
    ):
        """Render a group of items. Try KeepTogether; fall back to chunked."""
        def make_header(continued: bool):
            suffix = " — continued" if continued else ""
            parts = [Paragraph(
                f'<b>{group_label}{suffix}</b> — {len(items)} item(s)',
                ParagraphStyle("GroupHeader", parent=self.styles["body"],
                               fontSize=11, spaceBefore=16, spaceAfter=4,
                               textColor=DARK),
            )]
            if recommendation_text and not continued:
                parts.append(Paragraph(
                    f'<i>{_escape(recommendation_text)}</i>',
                    ParagraphStyle("GroupRec", parent=self.styles["small"],
                                   leftIndent=20, spaceAfter=8),
                ))
            return parts

        item_heights = [self._estimate_item_height(r) for r in items]
        total_height = GROUP_HEADER_PT + sum(item_heights)

        if total_height <= PAGE_CONTENT_HEIGHT:
            block = make_header(continued=False)
            for r in items:
                block.extend(self._render_item_flowables(r, label_color))
            self.elements.append(KeepTogether(block))
            return

        # Too tall for one page — chunk with continued headers
        self.elements.extend(make_header(continued=False))
        running = GROUP_HEADER_PT
        for i, r in enumerate(items):
            h = item_heights[i]
            if running + h > PAGE_CONTENT_HEIGHT and i > 0:
                self.elements.append(PageBreak())
                self.elements.extend(make_header(continued=True))
                running = GROUP_HEADER_PT
            self.elements.append(self._render_item_block(r, label_color))
            running += h

    def _render_multi_issue_group(self, group_label, items, label_color):
        """Render an item group whose entries each have multiple issues."""
        def make_header(continued: bool):
            suffix = " — continued" if continued else ""
            return [Paragraph(
                f'<b>{group_label}{suffix}</b> — {len(items)} item(s)',
                ParagraphStyle("MultiGroupHeader", parent=self.styles["body"],
                               fontSize=11, spaceBefore=16, spaceAfter=8,
                               textColor=DARK),
            )]

        item_heights = [self._estimate_item_height(r) for r in items]
        total_height = MULTI_GROUP_HEADER_PT + sum(item_heights)

        if total_height <= PAGE_CONTENT_HEIGHT:
            block = make_header(continued=False)
            for r in items:
                block.extend(self._render_item_flowables(r, label_color))
            self.elements.append(KeepTogether(block))
            return

        self.elements.extend(make_header(continued=False))
        running = MULTI_GROUP_HEADER_PT
        for i, r in enumerate(items):
            h = item_heights[i]
            if running + h > PAGE_CONTENT_HEIGHT and i > 0:
                self.elements.append(PageBreak())
                self.elements.extend(make_header(continued=True))
                running = MULTI_GROUP_HEADER_PT
            self.elements.append(self._render_item_block(r, label_color))
            running += h


# =============================================================================
# Public API
# =============================================================================

def generate_pdf_report(validation_data: dict, company_name: str = "") -> BytesIO:
    """Generate a branded PDF report and return it as BytesIO.

    This is the stable entry point — the construction is delegated to
    PDFReportBuilder, which is internal.
    """
    return PDFReportBuilder(validation_data, company_name).build()
