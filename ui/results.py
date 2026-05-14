"""Validation results: score card, summary stats, downloads, results tabs."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from csv_report import generate_csv_report
from gtin_core import Severity, generate_before_after
from pdf_report import generate_pdf_report
from ui.state import (
    KEY_CSV_CACHE, KEY_PDF_CACHE, KEY_PDF_COMPANY, KEY_PDF_ERROR,
)


# -- score + summary ---------------------------------------------------------

def render_score_card(score: dict) -> None:
    score_color = (
        "#28a745" if score["score"] >= 75
        else "#ffc107" if score["score"] >= 50
        else "#dc3545"
    )
    st.markdown(
        f"""
        <div class="score-card">
            <div class="score-number" style="color: {score_color};">{score["score"]}</div>
            <div class="score-grade">Grade: {score["grade"]}</div>
            <div class="score-interp">{score["interpretation"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_stats(summary: dict) -> None:
    cols = st.columns(4)
    cards = [
        ("stat-card", summary["total_gtins"], "Total GTINs"),
        ("stat-card stat-critical", summary["critical_issues"], "Critical Issues"),
        ("stat-card stat-warning", summary["warnings"], "Warnings"),
        ("stat-card stat-clean", summary["clean"], "Clean"),
    ]
    for col, (cls, value, label) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="{cls}">
                    <div class="stat-number">{value}</div>
                    <div class="stat-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# -- downloads ---------------------------------------------------------------

def render_download_buttons(validation_data: dict, company_name: str) -> None:
    st.markdown("### 📥 Download Validation Reports")
    col_csv, col_pdf = st.columns(2)
    filename_base = company_name.replace(" ", "_") if company_name else "gtin_validation"

    with col_csv:
        _render_csv_download(validation_data, filename_base)
    with col_pdf:
        _render_pdf_download(validation_data, company_name, filename_base)


def _render_csv_download(validation_data: dict, filename_base: str) -> None:
    st.markdown("**📄 CSV Report — Raw Data**")
    st.markdown(
        '<p style="font-size:0.85rem; color:var(--text-muted);">'
        'Row-by-row validation results in spreadsheet format. '
        'Includes each GTIN, its status, issue codes, and corrected values. '
        'Best for importing into Excel or your own systems for further analysis.'
        '</p>',
        unsafe_allow_html=True,
    )
    if KEY_CSV_CACHE not in st.session_state:
        st.session_state[KEY_CSV_CACHE] = generate_csv_report(validation_data)
    st.download_button(
        label="📄 Download CSV Report",
        data=st.session_state[KEY_CSV_CACHE],
        file_name=f"{filename_base}_report.csv",
        mime="text/csv",
        use_container_width=True,
    )


def _render_pdf_download(
    validation_data: dict, company_name: str, filename_base: str,
) -> None:
    st.markdown("**📑 PDF Report — Full Diagnostic**")
    st.markdown(
        '<p style="font-size:0.85rem; color:var(--text-muted);">'
        'Branded, professional report with readiness score, retailer-specific '
        'checklists, cost-of-inaction estimates, and prioritized issue detail. '
        'Designed to hand directly to your operations team, broker, or trading partner coordinator.'
        '</p>',
        unsafe_allow_html=True,
    )

    pdf_cache_stale = (
        KEY_PDF_CACHE not in st.session_state
        or st.session_state.get(KEY_PDF_COMPANY) != company_name
    )
    if pdf_cache_stale:
        try:
            st.session_state[KEY_PDF_CACHE] = generate_pdf_report(
                validation_data, company_name,
            )
            st.session_state[KEY_PDF_COMPANY] = company_name
            st.session_state.pop(KEY_PDF_ERROR, None)
        except Exception as e:  # noqa: BLE001
            st.session_state[KEY_PDF_CACHE] = None
            st.session_state[KEY_PDF_ERROR] = str(e)

    if st.session_state.get(KEY_PDF_ERROR):
        st.error(f"PDF generation error: {st.session_state[KEY_PDF_ERROR]}")
        return

    st.download_button(
        label="📑 Download PDF Report",
        data=st.session_state[KEY_PDF_CACHE],
        file_name=f"{filename_base}_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# -- results tabs ------------------------------------------------------------

def render_results_tabs(validation_data: dict) -> None:
    """Render the four validation-result tabs."""
    results = validation_data["results"]
    hierarchy = validation_data["hierarchy"]

    tab_issues, tab_detail, tab_check_digit_fixes, tab_item_detail = st.tabs([
        "📋 Issues by Severity",
        "🔍 Full Item Detail",
        "✏️ Check Digit Corrections",
        "📦 Packaging Hierarchy",
    ])
    with tab_issues:
        _render_issues_by_severity(results)
    with tab_detail:
        _render_full_item_detail(results)
    with tab_check_digit_fixes:
        _render_check_digit_fixes(results)
    with tab_item_detail:
        _render_packaging_hierarchy(hierarchy)


def _render_issues_by_severity(results) -> None:
    st.markdown("### Issues by Severity")
    critical_items = [r for r in results if r.has_critical]
    warning_items = [
        r for r in results if r.has_warning and not r.has_critical
    ]
    info_items = [
        r for r in results
        if r.issues and not r.has_critical and not r.has_warning
    ]

    if critical_items:
        st.markdown(
            '<span class="badge-critical">CRITICAL</span> — '
            'These GTINs will be **rejected** by retailers.',
            unsafe_allow_html=True,
        )
        for r in critical_items:
            with st.expander(f"Row {r.row_number}: {r.raw_input}"):
                for issue in r.issues:
                    if issue.severity == Severity.CRITICAL:
                        st.error(f"**{issue.message}**")
                        st.markdown(f"**Fix:** {issue.recommendation}")
                        st.markdown(f"**Retailer impact:** {issue.retailer_impact}")
                        st.markdown("---")

    if warning_items:
        st.markdown(
            '<span class="badge-warning">WARNING</span> — '
            'These GTINs may cause problems.',
            unsafe_allow_html=True,
        )
        for r in warning_items:
            with st.expander(f"Row {r.row_number}: {r.raw_input}"):
                for issue in r.issues:
                    st.warning(f"**{issue.message}**")
                    st.markdown(f"**Fix:** {issue.recommendation}")
                    st.markdown(f"**Retailer impact:** {issue.retailer_impact}")

    if info_items:
        st.markdown(
            '<span class="badge-info">INFO</span> — Best practice notes.',
            unsafe_allow_html=True,
        )
        for r in info_items:
            with st.expander(f"Row {r.row_number}: {r.raw_input}"):
                for issue in r.issues:
                    st.info(f"{issue.message}")

    if not critical_items and not warning_items and not info_items:
        st.success("🎉 All GTINs passed validation with no issues!")


def _render_full_item_detail(results) -> None:
    st.markdown("### Full Item Detail")
    detail_rows = []
    for r in results:
        status = (
            "✅ Clean" if not r.issues
            else "❌ Critical" if r.has_critical
            else "⚠️ Warning" if r.has_warning
            else "ℹ️ Info"
        )
        detail_rows.append({
            "Row": r.row_number,
            "GTIN": r.raw_input,
            "Type": r.gtin_type.value,
            "Status": status,
            "Issues": len(r.issues),
            "Corrected": r.corrected_value or "",
        })
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)


def _render_check_digit_fixes(results) -> None:
    st.markdown("### Check Digit Corrections")
    st.markdown(
        "These GTINs have incorrect check digits. The corrected values are shown below. "
        "**Important:** always verify corrections against your original barcode or GS1 "
        "registration before updating your product master."
    )
    before_after = generate_before_after(results)
    if before_after:
        ba_df = pd.DataFrame(before_after)
        ba_df.columns = ["Row", "Current (Before)", "Corrected (After)", "Issue"]
        st.dataframe(ba_df, use_container_width=True, hide_index=True)
    else:
        st.success("No check digit corrections needed — all check digits are valid.")


def _render_packaging_hierarchy(hierarchy: dict) -> None:
    st.markdown("### Packaging Hierarchy Analysis")
    st.markdown(
        "Retailers like Walmart require GTINs at every packaging level — "
        "each, inner pack, case, and pallet. This analysis checks whether "
        "your case-level GTIN-14s match up with unit-level GTINs."
    )

    if hierarchy["matched_pairs"]:
        st.markdown("#### ✅ Matched unit → case pairs")
        pairs_df = pd.DataFrame(hierarchy["matched_pairs"])
        pairs_df.columns = ["Case GTIN", "Case Row", "Unit GTIN", "Unit Row", "Indicator"]
        st.dataframe(pairs_df, use_container_width=True, hide_index=True)

    if hierarchy["orphan_cases"]:
        st.markdown("#### ⚠️ Case GTINs without matching unit GTINs")
        for r in hierarchy["orphan_cases"]:
            st.warning(f"Row {r.row_number}: **{r.cleaned}** — no matching unit GTIN found")

    if hierarchy["units_without_cases"]:
        st.markdown("#### 📦 Unit GTINs without case-level GTINs")
        st.caption(
            "These items don't have a corresponding GTIN-14 for case/shipping identification. "
            "If you ship these to retailers in cases, you'll need case GTINs."
        )
        for r in hierarchy["units_without_cases"]:
            st.info(f"Row {r.row_number}: **{r.cleaned}** ({r.gtin_type.value})")

    if not hierarchy["matched_pairs"] and not hierarchy["orphan_cases"]:
        st.info(
            "No GTIN-14 case-level codes found in your data. "
            "If you ship to Walmart or Costco, you'll likely need case GTINs (GTIN-14 with indicator digits 1-8)."
        )
