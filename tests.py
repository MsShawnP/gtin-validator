"""
Tests for the GTIN Validator core engine.

Run with: python -m pytest tests.py -v
"""

import pandas as pd
import pytest
from gtin_core import (
    calculate_check_digit,
    identify_gtin_type,
    validate_single_gtin,
    validate_batch,
    analyze_hierarchy,
    calculate_readiness_score,
    check_data_completeness,
    estimate_cost_of_inaction,
    generate_before_after,
    generate_executive_summary,
    generate_fix_roadmap,
    generate_gtin14_suggestions,
    generate_retailer_checklists,
    GTINType,
    RETAILER_PROFILES,
    Severity,
)
from csv_report import generate_csv_report
from pdf_report import generate_pdf_report


# =========================================================================
# Check digit calculation
# =========================================================================

class TestCheckDigit:
    """GS1 mod-10 check digit algorithm per General Specifications §7.9."""

    def test_gtin12_check_digit(self):
        # GS1 example: 61414100001 → check digit 2
        assert calculate_check_digit("61414100001") == 2

    def test_gtin13_check_digit(self):
        # EAN-13: 590123412345 → check digit 7
        assert calculate_check_digit("590123412345") == 7

    def test_gtin14_check_digit(self):
        # GTIN-14: 1061414100001 → check digit 9
        assert calculate_check_digit("1061414100001") == 9

    def test_gtin8_check_digit(self):
        # GTIN-8: 9638507 → check digit 4
        assert calculate_check_digit("9638507") == 4

    def test_all_zeros(self):
        assert calculate_check_digit("00000000000") == 0


# =========================================================================
# GTIN type identification
# =========================================================================

class TestGTINType:
    def test_gtin8(self):
        assert identify_gtin_type(8) == GTINType.GTIN_8

    def test_gtin12(self):
        assert identify_gtin_type(12) == GTINType.GTIN_12

    def test_gtin13(self):
        assert identify_gtin_type(13) == GTINType.GTIN_13

    def test_gtin14(self):
        assert identify_gtin_type(14) == GTINType.GTIN_14

    def test_unknown_lengths(self):
        for length in [0, 1, 5, 9, 10, 11, 15, 20]:
            assert identify_gtin_type(length) == GTINType.UNKNOWN


# =========================================================================
# Single GTIN validation
# =========================================================================

class TestSingleValidation:
    def test_valid_gtin12(self):
        result = validate_single_gtin("614141000012", row_number=1)
        assert result.gtin_type == GTINType.GTIN_12
        # Note: will have UPC_NOT_GTIN13 warning, but no critical issues
        assert not result.has_critical

    def test_empty_gtin(self):
        result = validate_single_gtin("", row_number=1)
        assert not result.is_valid
        assert result.has_critical
        assert result.issues[0].code == "EMPTY"

    def test_non_numeric(self):
        result = validate_single_gtin("6141410003A5", row_number=1)
        assert not result.is_valid
        assert result.issues[0].code == "NON_NUMERIC"

    def test_invalid_length(self):
        result = validate_single_gtin("61414100010", row_number=1)  # 11 digits
        assert not result.is_valid
        assert result.issues[0].code == "INVALID_LENGTH"

    def test_bad_check_digit(self):
        result = validate_single_gtin("614141000356", row_number=1)
        assert not result.is_valid
        assert any(i.code == "BAD_CHECK_DIGIT" for i in result.issues)
        assert result.corrected_value == "614141000357"

    def test_all_zeros(self):
        result = validate_single_gtin("000000000000", row_number=1)
        assert not result.is_valid
        assert any(i.code == "ALL_ZEROS" for i in result.issues)

    def test_gtin14_case_level(self):
        result = validate_single_gtin("10614141000019", row_number=1)
        assert result.gtin_type == GTINType.GTIN_14
        assert result.indicator_digit == "1"
        assert any(i.code == "CASE_LEVEL" for i in result.issues)

    def test_gtin14_indicator_nine(self):
        result = validate_single_gtin("90614141000016", row_number=1)
        assert any(i.code == "INDICATOR_NINE" for i in result.issues)

    def test_strips_whitespace_and_dashes(self):
        result = validate_single_gtin(" 614-141-000012 ", row_number=1)
        assert result.cleaned == "614141000012"
        assert not result.has_critical

    def test_upc_gtin13_warning(self):
        result = validate_single_gtin("614141000012", row_number=1)
        assert any(i.code == "UPC_NOT_GTIN13" for i in result.issues)

    def test_company_prefix_extracted_gtin12(self):
        # GTIN-12 is normalized onto the GTIN-13 frame (leading zero) before
        # the prefix slice is taken, so it matches a paired GTIN-14.
        result = validate_single_gtin("614141000012", row_number=1)
        assert result.company_prefix == "0614141"

    def test_company_prefix_extracted_gtin14(self):
        result = validate_single_gtin("10614141000019", row_number=1)
        assert result.company_prefix == "0614141"


# =========================================================================
# Batch validation
# =========================================================================

class TestBatchValidation:
    def test_duplicate_detection(self):
        data = validate_batch(["614141000012", "614141000012"])
        assert data["summary"]["duplicate_groups"] == 1
        for r in data["results"]:
            assert any(i.code == "DUPLICATE" for i in r.issues)

    def test_prefix_mismatch_detection(self):
        data = validate_batch([
            "614141000012",
            "614141000029",
            "732141000013",  # different prefix
        ])
        mismatched = [r for r in data["results"] if any(
            i.code == "PREFIX_MISMATCH" for i in r.issues
        )]
        assert len(mismatched) == 1
        assert mismatched[0].company_prefix == "0732141"

    def test_summary_counts(self):
        data = validate_batch([
            "614141000012",   # valid (with UPC warning)
            "61414100010",    # critical: invalid length
            "000000000000",   # critical: all zeros
        ])
        assert data["summary"]["total_gtins"] == 3
        assert data["summary"]["critical_issues"] == 2

    def test_score_returned(self):
        data = validate_batch(["614141000012"])
        assert "score" in data["score"]
        assert "grade" in data["score"]
        assert 0 <= data["score"]["score"] <= 100

    def test_cost_estimate_returned(self):
        data = validate_batch(["61414100010"])  # will have critical issue
        cost = data["cost_estimate"]
        assert cost["chargeback_range"][0] <= cost["chargeback_range"][1]
        assert cost["annual_estimate_low"] <= cost["annual_estimate_high"]

    def test_empty_batch(self):
        data = validate_batch([])
        assert data["summary"]["total_gtins"] == 0
        assert data["score"]["score"] == 0


# =========================================================================
# Hierarchy analysis
# =========================================================================

class TestHierarchy:
    def test_matched_pair(self):
        data = validate_batch([
            "614141000012",    # unit GTIN-12
            "10614141000019",  # case GTIN-14 (indicator 1)
        ])
        assert len(data["hierarchy"]["matched_pairs"]) == 1
        assert data["hierarchy"]["has_hierarchy"] is True

    def test_orphan_case(self):
        data = validate_batch([
            "10999999999993",  # case GTIN-14 with no matching unit
        ])
        assert len(data["hierarchy"]["orphan_cases"]) == 1

    def test_no_hierarchy(self):
        data = validate_batch(["614141000012"])
        assert data["hierarchy"]["has_hierarchy"] is False


# =========================================================================
# Before/after corrections
# =========================================================================

class TestBeforeAfter:
    def test_correction_generated(self):
        data = validate_batch(["614141000356"])  # bad check digit
        pairs = generate_before_after(data["results"])
        assert len(pairs) == 1
        assert pairs[0]["after"] == "614141000357"

    def test_no_corrections_when_valid(self):
        data = validate_batch(["614141000012"])
        pairs = generate_before_after(data["results"])
        assert len(pairs) == 0


# =========================================================================
# Executive summary
# =========================================================================

class TestExecutiveSummary:
    def test_returns_string(self):
        data = validate_batch(["614141000012", "61414100010"])
        summary = generate_executive_summary(data)
        assert isinstance(summary, str)
        assert len(summary) > 50

    def test_mentions_score(self):
        data = validate_batch(["614141000012"])
        summary = generate_executive_summary(data)
        assert "/100" in summary


# =========================================================================
# Fix roadmap
# =========================================================================

class TestFixRoadmap:
    def test_roadmap_sorted_by_priority(self):
        data = validate_batch([
            "614141000012",   # UPC warning + no case GTIN
            "61414100010",    # invalid length (critical)
            "614141000356",   # bad check digit (critical)
        ])
        roadmap = generate_fix_roadmap(data["results"], data["hierarchy"])
        priorities = [item["priority"] for item in roadmap]
        assert priorities == sorted(priorities)

    def test_info_items_excluded(self):
        data = validate_batch(["10614141000019"])  # GTIN-14, info only
        roadmap = generate_fix_roadmap(data["results"], data["hierarchy"])
        # Should not include CASE_LEVEL info item
        codes = [item["code"] for item in roadmap]
        assert "CASE_LEVEL" not in codes


# =========================================================================
# GTIN-14 suggestions
# =========================================================================

class TestGTIN14Suggestions:
    def test_suggestion_generated(self):
        data = validate_batch(["614141000012"])
        suggestions = generate_gtin14_suggestions(
            data["results"], data["hierarchy"]
        )
        assert len(suggestions) == 1
        assert len(suggestions[0]["indicators"]) == 8

    def test_check_digit_correct_on_suggestions(self):
        data = validate_batch(["614141000012"])
        suggestions = generate_gtin14_suggestions(
            data["results"], data["hierarchy"]
        )
        for ind, info in suggestions[0]["indicators"].items():
            gtin14 = info["gtin14"]
            assert len(gtin14) == 14
            # Verify check digit
            payload = gtin14[:-1]
            expected = calculate_check_digit(payload)
            assert int(gtin14[-1]) == expected

    def test_no_suggestion_for_invalid_gtin(self):
        data = validate_batch(["61414100010"])  # invalid length
        suggestions = generate_gtin14_suggestions(
            data["results"], data["hierarchy"]
        )
        assert len(suggestions) == 0


# =========================================================================
# Single-GTIN edge cases not covered above
# =========================================================================

class TestSingleValidationEdgeCases:
    def test_valid_gtin8(self):
        # 96385074 is a canonical valid GTIN-8 (check digit 4)
        result = validate_single_gtin("96385074", row_number=1)
        assert result.gtin_type == GTINType.GTIN_8
        assert result.is_valid
        assert not result.has_critical
        assert result.company_prefix == "9638"

    def test_gtin14_indicator_zero(self):
        # Indicator 0 => base unit in 14-digit form. Check digit: 1061414100002 -> 8
        # We construct a valid GTIN-14 with indicator 0:
        from gtin_core import calculate_check_digit
        payload = "0061414100001"
        check = calculate_check_digit(payload)
        gtin14 = payload + str(check)
        result = validate_single_gtin(gtin14, row_number=1)
        assert result.indicator_digit == "0"
        assert any(i.code == "INDICATOR_ZERO" for i in result.issues)
        # INDICATOR_ZERO is informational only
        assert not result.has_critical

    def test_none_input_handled_gracefully(self):
        result = validate_single_gtin(None, row_number=1)
        assert not result.is_valid
        assert result.issues[0].code == "EMPTY"

    def test_nan_input_handled_gracefully(self):
        result = validate_single_gtin(float("nan"), row_number=1)
        assert not result.is_valid
        assert result.issues[0].code == "EMPTY"

    def test_numeric_input_handled_gracefully(self):
        # int / float values are coerced — they should validate normally,
        # not crash on .strip()
        result = validate_single_gtin(614141000012, row_number=1)
        assert result.gtin_type == GTINType.GTIN_12
        assert not result.has_critical

    def test_duplicate_lists_all_sibling_rows(self):
        data = validate_batch([
            "614141000012",
            "614141000012",
            "614141000012",
        ])
        # Each duplicate should list the other two row numbers in its message
        for r in data["results"]:
            dup_issues = [i for i in r.issues if i.code == "DUPLICATE"]
            assert len(dup_issues) == 1
            sibling_rows = [
                str(n) for n in (1, 2, 3) if n != r.row_number
            ]
            for sr in sibling_rows:
                assert sr in dup_issues[0].message


# =========================================================================
# Readiness scoring (grade thresholds + bonuses/penalties)
# =========================================================================

class TestReadinessScore:
    def test_empty_returns_zero(self):
        score = calculate_readiness_score([], {"has_hierarchy": False, "hierarchy_complete": False})
        assert score["score"] == 0
        assert score["grade"] == "N/A"

    def test_grade_landscape_with_warnings(self):
        # GTIN-12 inputs all carry a UPC_NOT_GTIN13 warning. With a complete
        # hierarchy bonus the score lands in the C/B band — and crucially
        # never in F since there are no critical issues.
        data = validate_batch([
            "614141000012", "614141000029", "614141000036",
            "10614141000019", "10614141000026", "10614141000033",
        ])
        assert data["score"]["grade"] in {"A", "B", "C"}
        assert data["summary"]["critical_issues"] == 0

    def test_grade_f_on_all_critical(self):
        data = validate_batch([
            "61414100010",  # invalid length
            "6141410003A5",  # non-numeric
            "000000000000",  # all zeros
        ])
        assert data["score"]["grade"] == "F"
        assert data["score"]["score"] < 40

    def test_hierarchy_bonus_applied(self):
        no_hierarchy = validate_batch(["614141000012"])
        with_hierarchy = validate_batch(["614141000012", "10614141000019"])
        # With a matched unit/case pair the score should be at least as
        # high as without (and typically higher because of the bonus)
        assert with_hierarchy["score"]["score"] >= no_hierarchy["score"]["score"]


# =========================================================================
# Cost-of-inaction
# =========================================================================

class TestCostEstimate:
    def test_empty_returns_empty_dict(self):
        assert estimate_cost_of_inaction([]) == {}

    def test_low_sku_count_growth_note(self):
        # 1 critical, < 20 total: should use the "compound" growth note
        data = validate_batch(["61414100010"])
        cost = data["cost_estimate"]
        assert "compound" in cost["growth_note"].lower()

    def test_high_sku_count_growth_note(self):
        # 20+ inputs: should use the explicit "2x" growth note
        gtins = ["614141000012"] * 20
        data = validate_batch(gtins)
        cost = data["cost_estimate"]
        assert "2x" in cost["growth_note"]

    def test_rework_cost_matches_rework_hours(self):
        data = validate_batch(["61414100010", "614141000012"])
        cost = data["cost_estimate"]
        assert cost["rework_cost"] == cost["rework_hours"] * 50

    def test_low_le_high_across_all_ranges(self):
        data = validate_batch(["61414100010", "000000000000"])
        cost = data["cost_estimate"]
        assert cost["chargeback_range"][0] <= cost["chargeback_range"][1]
        assert cost["delayed_launch_range"][0] <= cost["delayed_launch_range"][1]
        assert cost["annual_estimate_low"] <= cost["annual_estimate_high"]


# =========================================================================
# Retailer checklists
# =========================================================================

class TestRetailerChecklists:
    def test_all_profiles_included(self):
        data = validate_batch(["614141000012"])
        checklists = data["retailer_checklists"]
        for retailer in RETAILER_PROFILES.keys():
            assert retailer in checklists
            assert "checks" in checklists[retailer]
            assert "ready" in checklists[retailer]

    def test_check_digit_failure_reflected_per_retailer(self):
        data = validate_batch(["614141000356"])  # bad check digit
        for retailer, cl in data["retailer_checklists"].items():
            cd_check = next(c for c in cl["checks"] if "check digit" in c["check"].lower())
            assert cd_check["passed"] is False
            assert cd_check["failing_gtins"]

    def test_clean_data_with_hierarchy_passes_walmart(self):
        data = validate_batch([
            "614141000012",     # unit
            "10614141000019",   # matching case
        ])
        walmart = data["retailer_checklists"]["Walmart"]
        # All check-digit / duplicate / case-present / hierarchy / prefix
        # checks pass; UPC types accepted by Walmart
        assert walmart["passed"] == walmart["total"]

    def test_hierarchy_check_only_for_retailers_that_require_it(self):
        data = validate_batch(["614141000012"])
        for retailer, cl in data["retailer_checklists"].items():
            has_hierarchy_check = any(
                "hierarchy" in c["check"].lower() for c in cl["checks"]
            )
            profile_requires = cl["profile"]["requires_hierarchy"]
            assert has_hierarchy_check == profile_requires


# =========================================================================
# Data completeness
# =========================================================================

class TestDataCompleteness:
    def test_empty_dataframe(self):
        df = pd.DataFrame({"GTIN": []})
        result = check_data_completeness(df)
        assert result["field_analysis"] == {}
        assert result["overall_completeness"] == 0

    def test_pattern_matching_picks_up_columns(self):
        df = pd.DataFrame({
            "GTIN": ["614141000012"],
            "Product Name": ["Marinara"],
            "Brand Name": ["Acme"],
            "Net Weight": ["12oz"],
        })
        result = check_data_completeness(df)
        assert "product_name" in result["field_analysis"]
        assert "brand" in result["field_analysis"]
        assert "weight" in result["field_analysis"]

    def test_completeness_pct_calculated(self):
        df = pd.DataFrame({
            "Product Name": ["A", "B", "", None],
        })
        result = check_data_completeness(df)
        # 2 of 4 rows populated for product_name => 50%
        assert result["field_analysis"]["product_name"]["completeness_pct"] == 50.0

    def test_retailer_gap_analysis_flags_missing(self):
        df = pd.DataFrame({"GTIN": ["614141000012"]})
        result = check_data_completeness(df)
        # No retailer can be ready with only a GTIN column
        for retailer, gaps in result["retailer_data_gaps"].items():
            assert gaps["ready"] is False
            assert gaps["missing_fields"]


# =========================================================================
# Report generators (smoke tests)
# =========================================================================

class TestCSVReport:
    def test_csv_has_header_and_rows(self):
        data = validate_batch(["614141000012", "61414100010"])
        csv_text = generate_csv_report(data)
        lines = csv_text.strip().splitlines()
        assert lines[0].startswith("Row,GTIN (Original),GTIN (Cleaned),")
        assert len(lines) == 3  # header + 2 rows

    def test_csv_escapes_formula_injection(self):
        # Simulate a malicious paste — leading '=' must be neutralized
        data = validate_batch(["=cmd|'/c calc'!A1"])
        csv_text = generate_csv_report(data)
        # The cell containing the malicious payload must be prefixed with '
        # so that Excel/Sheets treats it as literal text, not a formula
        assert "\"'=cmd" in csv_text or "'=cmd" in csv_text
        # And the bare formula prefix should never appear as a value
        assert ",=cmd" not in csv_text

    def test_csv_handles_clean_input(self):
        data = validate_batch(["614141000012"])
        csv_text = generate_csv_report(data)
        # Row's status column should reflect a clean-ish result
        assert "614141000012" in csv_text


class TestPDFReport:
    def test_pdf_generates_for_typical_batch(self):
        data = validate_batch([
            "614141000012",
            "61414100010",
            "000000000000",
            "10614141000019",
        ])
        buf = generate_pdf_report(data, company_name="Test Co.")
        content = buf.getvalue()
        assert content.startswith(b"%PDF-")
        assert len(content) > 1000  # non-trivial document

    def test_pdf_handles_no_company_name(self):
        data = validate_batch(["614141000012"])
        buf = generate_pdf_report(data, company_name="")
        assert buf.getvalue().startswith(b"%PDF-")

    def test_pdf_escapes_markup_in_company_name(self):
        # ReportLab parses inline markup; an unescaped '<' would corrupt
        # or fail to render. The escape helper should prevent that.
        data = validate_batch(["614141000012"])
        buf = generate_pdf_report(data, company_name="Bob & <Co>")
        assert buf.getvalue().startswith(b"%PDF-")


# =========================================================================
# Sample data regression guard
# =========================================================================

class TestSampleData:
    def test_sample_data_parses_and_validates(self):
        from io import StringIO
        from sample_data import SAMPLE_DATA
        df = pd.read_csv(StringIO(SAMPLE_DATA.strip()), dtype=str)
        gtins = df["GTIN"].dropna().tolist()
        data = validate_batch(gtins)
        assert data["summary"]["total_gtins"] == len(gtins)
        # The sample is intentionally messy — there should be some critical
        # issues and at least one duplicate
        assert data["summary"]["critical_issues"] > 0
        assert data["summary"]["duplicate_groups"] >= 1
