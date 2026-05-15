"""
CSV Report Generator for GTIN Validator.
Exports validation results as a flat CSV file.
"""

from __future__ import annotations

import csv
from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gtin_core import BatchResult

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_cell(value: str) -> str:
    """Prefix formula-trigger characters so spreadsheet apps don't execute them."""
    if isinstance(value, str) and value and value[0] in _FORMULA_PREFIXES:
        return "'" + value
    return value


def generate_csv_report(validation_data: BatchResult) -> str:
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
            r.corrected_value or "",
            r.company_prefix or "",
            r.indicator_digit or "",
        ])

    return output.getvalue()


def generate_corrected_csv(validation_data: BatchResult) -> str:
    """Generate a CSV with corrected GTINs ready for re-import.

    Each row gets the best available GTIN: corrected check digit if fixable,
    cleaned value if already valid, or the original with a status flag if
    unfixable. Designed for users to paste directly into their product master.
    """
    output = StringIO()
    writer = csv.writer(output)

    results = validation_data["results"]

    writer.writerow(["Row", "Original GTIN", "Corrected GTIN", "Status", "Action Taken"])

    for r in results:
        if r.corrected_value:
            corrected = r.corrected_value
            status = "Fixed"
            action = "Check digit corrected"
        elif r.is_valid and not r.has_critical:
            corrected = r.cleaned
            if r.cleaned != r.raw_input.strip():
                status = "Cleaned"
                action = "Whitespace/formatting removed"
            else:
                status = "OK"
                action = "No changes needed"
        else:
            corrected = ""
            unfixable_codes = [i.code for i in r.issues if i.severity.value == "Critical"]
            status = "Needs manual fix"
            action = ", ".join(unfixable_codes) if unfixable_codes else "Review required"

        writer.writerow([
            r.row_number,
            _sanitize_cell(r.raw_input),
            _sanitize_cell(corrected),
            status,
            action,
        ])

    return output.getvalue()
