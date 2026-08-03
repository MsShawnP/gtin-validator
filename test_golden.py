"""Demo golden-file lock + P1 regression tests for gtin-validator.

The golden test pins the shipped sample dataset's batch summary so the deployed
demo experience cannot drift during the client-mode conversion. The regression
tests lock the two 07-31 audit P1s:
  1. A UPC-A and its case-level GTIN-14 share a company prefix (no false
     PREFIX_MISMATCH on textbook unit/case pairs — sample rows 37-39).
  2. INFO advisories (UPC_NOT_GTIN13) do not zero the clean count.
"""

import csv
import io

from gtin_core import validate_batch, validate_single_gtin
from sample_data import SAMPLE_DATA


def _sample_gtins():
    rows = list(csv.reader(io.StringIO(SAMPLE_DATA.strip())))[1:]
    return [r[0] for r in rows]


class TestDemoGolden:
    """Locks the deployed demo output. If this changes, the live site changes."""

    def test_sample_summary_is_locked(self):
        batch = validate_batch(_sample_gtins())
        assert batch["summary"] == {
            "total_gtins": 46,
            "valid": 40,
            "critical_issues": 6,
            "warnings": 4,
            "clean": 36,
            "duplicate_groups": 2,
            "unique_prefixes": 3,
        }

    def test_sample_score_is_locked(self):
        batch = validate_batch(_sample_gtins())
        assert batch["score"]["score"] == 82
        assert batch["score"]["grade"] == "B"


class TestPrefixParityRegression:
    """07-31 P1: unit UPC and its case GTIN-14 must share a company prefix."""

    def test_sample_case_rows_37_39_no_false_prefix_mismatch(self):
        batch = validate_batch(_sample_gtins())
        for r in batch["results"]:
            if r.row_number in (37, 38, 39):  # the GTIN-14 case rows
                assert not any(i.code == "PREFIX_MISMATCH" for i in r.issues), (
                    f"row {r.row_number} ({r.cleaned}) false-failed PREFIX_MISMATCH"
                )

    def test_upc_and_case_gtin14_share_prefix(self):
        unit = validate_single_gtin("614141000012", 1)
        case = validate_single_gtin("10614141000019", 2)
        assert unit.company_prefix == case.company_prefix == "0614141"


class TestCleanCountRegression:
    """07-31 P1: INFO advisories must not zero the clean count / grade."""

    def test_all_upc_file_counts_as_clean(self):
        # Every valid UPC-A gets an INFO UPC_NOT_GTIN13 advisory; the file must
        # still read as clean and score Grade A, not "0 passed with no issues".
        valid_upcs = ["614141000012", "614141000029", "614141000036", "614141000043"]
        batch = validate_batch(valid_upcs)
        assert batch["summary"]["clean"] == 4
        assert batch["summary"]["total_gtins"] == 4
        assert batch["score"]["grade"] == "A"

    def test_info_only_row_is_clean(self):
        batch = validate_batch(["614141000012"])  # one valid UPC-A -> INFO only
        r = batch["results"][0]
        assert r.issues  # it does carry the INFO advisory
        assert all(i.severity.value == "Info" for i in r.issues)
        assert batch["summary"]["clean"] == 1
