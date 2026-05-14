"""
CSV Report Generator for GTIN Validator.
Exports validation results as a flat CSV file.
"""

import csv
from io import StringIO
from gtin_core import Severity


# Characters that trigger formula evaluation when a CSV is opened in
# Excel, LibreOffice Calc, or Google Sheets. Prefixing cells that start
# with one of these with a leading apostrophe neutralizes the formula.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_cell(value):
    """Neutralize CSV/spreadsheet formula injection on user-controlled cells."""
    if isinstance(value, str) and value and value[0] in _FORMULA_PREFIXES:
        return "'" + value
    return value


def generate_csv_report(validation_data: dict) -> str:
    """Generate a CSV report string from validation results."""
    output = StringIO()
    writer = csv.writer(output)

    results = validation_data["results"]

    # Header
    writer.writerow([
        "Row",
        "GTIN (Original)",
        "GTIN (Cleaned)",
        "Valid",
        "GTIN Type",
        "Highest Severity",
        "Issue Count",
        "Issues",
        "Recommendations",
        "Retailer Impact",
        "Corrected GTIN",
        "Company Prefix",
        "Indicator Digit",
    ])

    for r in results:
        highest_severity = ""
        if r.has_critical:
            highest_severity = "Critical"
        elif r.has_warning:
            highest_severity = "Warning"
        elif r.issues:
            highest_severity = "Info"
        else:
            highest_severity = "Clean"

        issues_text = " | ".join(
            f"[{i.severity.value}] {i.message}" for i in r.issues
        ) if r.issues else "No issues"

        recommendations_text = " | ".join(
            i.recommendation for i in r.issues
        ) if r.issues else ""

        impact_text = " | ".join(
            i.retailer_impact for i in r.issues
        ) if r.issues else ""

        writer.writerow([
            r.row_number,
            _sanitize_cell(r.raw_input),
            _sanitize_cell(r.cleaned),
            "Yes" if r.is_valid else "No",
            r.gtin_type.value,
            highest_severity,
            len(r.issues),
            _sanitize_cell(issues_text),
            _sanitize_cell(recommendations_text),
            _sanitize_cell(impact_text),
            _sanitize_cell(r.corrected_value or ""),
            _sanitize_cell(r.company_prefix or ""),
            _sanitize_cell(r.indicator_digit or ""),
        ])

    return output.getvalue()
