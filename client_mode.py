"""Client-mode CLI for the GTIN validator.

Wraps the existing validation engine (`gtin_core`) with the shared
``lailara_engagement`` scaffold so a client's product-master export can be
validated locally: tolerant CSV/XLSX intake (GTIN read as text), a preflight
that names the GTIN column via ``engagement.yml`` (Data Readiness Report if it's
missing), and a branded, provenance-footed, draft-watermarked readiness summary
plus the standard CSV report — all written to ``client-output/`` only.

Usage:
    python client_mode.py --config engagement.yml --input client-data/items.csv \
        --out client-output [--final]
"""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

from lailara_engagement import (
    ColumnSpec,
    PreflightSpec,
    build_provenance,
    load_config,
    read_table,
    render_html,
    run_preflight,
    validation_status_label,
    write_report,
)
from lailara_engagement import palette as P
from lailara_engagement.provenance import Provenance

from csv_report import generate_csv_report
from gtin_core import validate_batch

TOOL = "gtin-validator"
TOOL_VERSION = "1.0"


def _gtin_spec() -> PreflightSpec:
    return PreflightSpec(
        tool=TOOL,
        version=TOOL_VERSION,
        columns=[
            ColumnSpec(
                name="gtin",
                dtype="identifier",
                required=True,
                description="the product GTIN/UPC/barcode to validate",
                spec_ref="INPUT-SPEC §1",
            )
        ],
    )


def _summary_html(config, batch, provenance: Provenance, *, draft: bool) -> str:
    esc = html.escape
    s = batch["summary"]
    score = batch["score"]
    draft_class = " ll-draft" if draft else ""
    # top issue types (non-INFO), by count
    from collections import Counter
    codes = Counter(
        i.code for r in batch["results"] for i in r.issues if i.severity.value != "Info"
    )
    issue_rows = "".join(
        f"<tr><td class=mono>{esc(code)}</td><td class=num>{n}</td></tr>"
        for code, n in codes.most_common(10)
    ) or "<tr><td colspan=2>No critical or warning issues.</td></tr>"

    grade_fill = P.LL_HK_SURFACE if score["grade"] in ("A", "B") else P.LL_SG_SURFACE
    grade_text = P.LL_HK_DARK if score["grade"] in ("A", "B") else P.LL_SG_DARK

    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>GTIN Readiness — {esc(config.client_name)}</title>
<style>{_css(draft)}</style></head>
<body class="{draft_class.strip()}"><main class=ll-page>
<header class=ll-header>
  <div class=ll-eyebrow>Lailara LLC · GTIN Validation</div>
  <h1 class=ll-title>GTIN Readiness Summary</h1>
  <div class=ll-client>
    <div><span class=ll-k>Client</span> {esc(config.client_name)}</div>
    <div><span class=ll-k>Engagement</span> {esc(config.engagement_id)}</div>
    <div><span class=ll-k>As of</span> {esc(config.as_of_date.isoformat())}</div>
  </div>
</header>
<section class=ll-banner style="background:{grade_fill};color:{grade_text}">
  <div class=ll-score>Score {score['score']}/100 · Grade {esc(score['grade'])}</div>
  <div>{esc(score['interpretation'])}</div>
</section>
<section class=ll-section>
  <h2 class=ll-h2>Batch summary</h2>
  <table class=ll-table>
    <tr><td>Total GTINs</td><td class=num>{s['total_gtins']:,}</td></tr>
    <tr><td>Clean (no critical/warning)</td><td class=num>{s['clean']:,}</td></tr>
    <tr><td>Critical issues</td><td class=num>{s['critical_issues']:,}</td></tr>
    <tr><td>Warnings</td><td class=num>{s['warnings']:,}</td></tr>
    <tr><td>Duplicate groups</td><td class=num>{s['duplicate_groups']:,}</td></tr>
  </table>
</section>
<section class=ll-section>
  <h2 class=ll-h2>Issues by type</h2>
  <table class=ll-table><thead><tr><th>Code</th><th>Count</th></tr></thead>
  <tbody>{issue_rows}</tbody></table>
</section>
{provenance.to_html()}
</main></body></html>"""


def _css(draft: bool) -> str:
    draft_css = (
        ".ll-draft::before{content:'DRAFT';position:fixed;top:50%;left:50%;"
        "transform:translate(-50%,-50%) rotate(-32deg);font-family:var(--s);"
        "font-size:22vw;font-weight:700;color:rgba(204,16,10,.06);z-index:0;"
        "pointer-events:none;white-space:nowrap}" if draft else ""
    )
    return f"""
:root{{--s:{P.LL_SERIF};--f:{P.LL_SANS}}}
*{{box-sizing:border-box}}
body{{margin:0;background:{P.LL_CANVAS};color:{P.LL_TEXT};font-family:var(--f);line-height:1.6}}
.ll-page{{position:relative;z-index:1;max-width:{P.LL_MAX_WIDTH};margin:0 auto;padding:48px 24px}}
.ll-header{{border-bottom:1px solid {P.LL_GRIDLINE};padding-bottom:24px;margin-bottom:24px}}
.ll-eyebrow{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:{P.LL_RED};font-weight:600}}
.ll-title{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:34px;margin:8px 0 16px}}
.ll-client{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 24px;font-size:14px}}
.ll-k{{display:block;color:{P.LL_TEXT_SEC};font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.ll-banner{{border-radius:2px;padding:16px 20px;margin-bottom:32px}}
.ll-score{{font-family:var(--s);font-weight:700;font-size:22px}}
.ll-h2{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:22px;margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-table{{width:100%;border-collapse:collapse;font-size:14px}}
.ll-table th{{text-align:left;background:{P.LL_CHICAGO};color:#fff;padding:8px 12px}}
.ll-table td{{padding:8px 12px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.mono{{font-family:ui-monospace,Consolas,monospace;font-size:12px}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.ll-provenance{{margin-top:40px;background:{P.LL_CARD_BG};color:{P.LL_CARD_TEXT};padding:20px 24px;border-radius:2px;font-size:13px}}
.ll-prov-title{{font-family:var(--s);font-weight:700;font-size:16px;margin-bottom:8px}}
.ll-provenance div{{margin-bottom:4px;color:{P.LL_CARD_SUBTITLE}}}
.ll-provenance strong{{color:{P.LL_CARD_TEXT}}}
.ll-prov-inputs{{width:100%;border-collapse:collapse;margin-top:8px}}
.ll-prov-inputs th{{text-align:left;border-bottom:1px solid rgba(255,255,255,.12);padding:4px 8px;color:{P.LL_CARD_MUTED}}}
.ll-prov-inputs td{{padding:4px 8px;border-bottom:1px solid rgba(255,255,255,.08);color:{P.LL_CARD_SUBTITLE}}}
.ll-prov-brand{{margin-top:12px;font-family:var(--s);color:{P.LL_CARD_MUTED}}}
{draft_css}
@media print{{body{{background:#fff}}}}
"""


def run(config_path: str, input_path: str, out_dir: str, *, final: bool = False) -> dict:
    config = load_config(config_path)
    read = read_table(input_path)
    spec = _gtin_spec()
    report = run_preflight(read, spec, config)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    provenance = build_provenance(
        tool=TOOL, tool_version=TOOL_VERSION, inputs=[read], config=config,
        validation_status=validation_status_label(report.status, report.n_warnings),
    )

    # Preflight gate: no GTIN column -> Data Readiness Report, no results.
    if not report.passed:
        paths = write_report(report, config, str(out), provenance=provenance,
                             draft=not final, basename="data-readiness-report",
                             title="GTIN Data Readiness Report")
        return {"status": "blocked", "readiness_report": paths["html"], "report": paths["html"]}

    gtin_col = report.column_mapping["gtin"]
    gtins = [v for v in read.frame[gtin_col].astype(str)]
    batch = validate_batch(gtins)

    # CSV report (reuse the existing generator)
    csv_path = out / "gtin-validation.csv"
    csv_path.write_text(generate_csv_report(batch), encoding="utf-8")

    # Branded, provenance-footed readiness summary
    summary_path = out / "gtin-readiness-summary.html"
    summary_path.write_text(_summary_html(config, batch, provenance, draft=not final),
                            encoding="utf-8")

    return {
        "status": "ok",
        "score": batch["score"]["score"],
        "grade": batch["score"]["grade"],
        "clean": batch["summary"]["clean"],
        "total": batch["summary"]["total_gtins"],
        "csv": str(csv_path),
        "report": str(summary_path),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gtin client mode",
                                 description="Validate a client GTIN file in engagement mode.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="client-output")
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)
    result = run(args.config, args.input, args.out, final=args.final)
    if result["status"] == "blocked":
        print(f"BLOCKED — data not ready. See {result['readiness_report']}")
        return 3
    print(f"scored {result['score']}/100 (Grade {result['grade']}); "
          f"{result['clean']}/{result['total']} clean")
    print(f"report -> {result['report']}\ncsv    -> {result['csv']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
