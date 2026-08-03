"""Client-mode tests for gtin-validator: intake, preflight, provenance report.

Adversarial fixtures per checklist §6: missing GTIN column (blocked path),
BOM+semicolon, Excel-mangled GTIN read as text, and a clean file.
Skipped if lailara_engagement isn't installed.
"""

import pytest

pytest.importorskip("lailara_engagement")

import client_mode  # noqa: E402

_CONFIG = """
client: {name: Meridian Farms}
engagement: {id: MER-2026-08}
as_of_date: 2026-07-31
demo: true
columns: {gtin: "UPC / Barcode"}
"""


@pytest.fixture
def cfg(tmp_path):
    p = tmp_path / "engagement.demo.yml"
    p.write_text(_CONFIG, encoding="utf-8")
    return str(p)


def _write(tmp_path, name, text, encoding="utf-8"):
    p = tmp_path / name
    p.write_bytes(text.encode(encoding) if isinstance(text, str) else text)
    return str(p)


def test_clean_file_scores_and_reports(cfg, tmp_path):
    src = _write(tmp_path, "items.csv",
                 "UPC / Barcode\n614141000012\n614141000029\n614141000036\n")
    out = str(tmp_path / "client-output")
    result = client_mode.run(cfg, src, out)
    assert result["status"] == "ok"
    assert result["grade"] == "A"          # all valid UPCs -> Grade A (INFO not counted)
    assert result["clean"] == 3
    html = open(result["report"], encoding="utf-8").read()
    assert "Meridian Farms" in html
    assert "#f5f3ee" in html               # branded canvas
    assert "SHA-256" in html               # provenance footer
    assert "DRAFT" in html


def test_missing_gtin_column_is_blocked(cfg, tmp_path):
    # No column maps to gtin -> Data Readiness Report, no results.
    src = _write(tmp_path, "bad.csv", "product,price\nA,1\nB,2\n")
    out = str(tmp_path / "out")
    result = client_mode.run(cfg, src, out)
    assert result["status"] == "blocked"
    html = open(result["readiness_report"], encoding="utf-8").read()
    assert "gtin" in html.lower()


def test_bom_semicolon_and_gtin_as_text(cfg, tmp_path):
    body = "﻿UPC / Barcode;name\n0614141000012;A\n614141000029;B\n"
    src = _write(tmp_path, "bom.csv", body)
    out = str(tmp_path / "out")
    result = client_mode.run(cfg, src, out)
    assert result["status"] == "ok"
    # leading-zero GTIN preserved as text through the CSV report
    csv_text = open(result["csv"], encoding="utf-8").read()
    assert "0614141000012" in csv_text


def test_final_flag_drops_watermark(cfg, tmp_path):
    src = _write(tmp_path, "items.csv", "UPC / Barcode\n614141000012\n")
    out = str(tmp_path / "out")
    result = client_mode.run(cfg, src, out, final=True)
    html = open(result["report"], encoding="utf-8").read()
    assert "ll-draft" not in html
