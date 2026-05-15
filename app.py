"""
GTIN Product Data Validator
A diagnostic tool for specialty food brands preparing product data
for retailer submission (Walmart, Costco, UNFI, 1WorldSync, and more).

Built for operations people, not developers.
"""

from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

from csv_report import generate_corrected_csv, generate_csv_report
from gtin_core import (
    RETAILER_PROFILES,
    Severity,
    check_data_completeness,
    generate_before_after,
    generate_executive_summary,
    generate_fix_roadmap,
    generate_gtin14_suggestions,
    validate_batch,
)
from pdf_report import generate_pdf_report
from sample_data import SAMPLE_DATA, SAMPLE_DESCRIPTION

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="GTIN Product Data Validator",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

_css = (Path(__file__).parent / "styles" / "app.css").read_text()
st.html(f"<style>{_css}</style>")


# ---------------------------------------------------------------------------
# Sidebar — settings
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Settings")

    st.markdown("### Filter by retailer")
    selected_retailer = st.selectbox(
        "Show requirements for:",
        ["All Retailers"] + list(RETAILER_PROFILES.keys()),
        help="Filter the checklist to show requirements for a specific retailer.",
    )

    st.markdown("---")

    st.markdown("#### How it works")
    st.markdown(
        "1. Upload your GTINs or try sample data\n"
        "2. Review your readiness score\n"
        "3. Check retailer-specific requirements\n"
        "4. Download your branded report"
    )

    st.markdown("---")
    st.markdown(
        '<p class="text-xs-muted">'
        'Built for specialty food brands.<br>'
        'Not affiliated with GS1, Walmart, or any retailer.'
        '</p>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Hero section
# ---------------------------------------------------------------------------

if not st.session_state.get("validated"):
    st.markdown(
        '<div class="hero">'
        '<h1>Validate your product GTINs in seconds</h1>'
        '<p class="subtitle">'
        'Find data quality issues before retailers do. Check your GTINs against '
        'GS1 format standards and retailer requirement rules &mdash; get a readiness '
        'score, prioritized fix plan, and branded PDF report.'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-checks">'
        '<div class="hero-check">'
        '<strong>What this checks</strong>'
        '<p>GS1 format standards (check digits, lengths, structure), '
        'retailer submission rules (Walmart, Costco, UNFI format needs), '
        'packaging hierarchy, and duplicate detection.</p>'
        '</div>'
        '<div class="hero-check">'
        '<strong>What this does NOT do</strong>'
        '<p>This does not look up GTINs in retailer databases or verify '
        'product assignments. It validates your data format and structure '
        '&mdash; a pre-flight check before you submit.</p>'
        '</div>'
        '<div class="hero-check">'
        '<strong>What you\'ll need</strong>'
        '<p>A list of GTINs &mdash; upload a CSV file or paste them directly. '
        'No account needed, no data stored.</p>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown("# GTIN Product Data Validator")


# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------

if "input_method" not in st.session_state:
    st.session_state["input_method"] = None

st.markdown("---")

col_upload, col_sample = st.columns(2)
with col_upload:
    if st.button("Upload your GTINs", type="primary", use_container_width=True):
        st.session_state["input_method"] = "upload"
        st.session_state.pop("validation_data_cache", None)
with col_sample:
    if st.button("Try with sample data", use_container_width=True):
        st.session_state["input_method"] = "sample"
        st.session_state.pop("validation_data_cache", None)

gtins_to_validate = []
uploaded_df = None

input_method = st.session_state.get("input_method")

if input_method == "upload":
    uploaded_file = st.file_uploader(
        "Upload a CSV file with a GTIN column:",
        type=["csv"],
        help="Your CSV should have a column containing GTINs. We'll auto-detect it.",
    )
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, dtype=str)
            uploaded_df = df
            gtin_col = None
            for col in df.columns:
                if any(term in col.lower() for term in ["gtin", "upc", "ean", "barcode", "code"]):
                    gtin_col = col
                    break
            if gtin_col is None:
                gtin_col = st.selectbox(
                    "Which column contains GTINs?",
                    df.columns.tolist(),
                )
            else:
                st.info(f"Auto-detected GTIN column: **{gtin_col}**")

            gtins_to_validate = df[gtin_col].dropna().tolist()
            st.success(f"Loaded {len(gtins_to_validate)} GTINs from '{gtin_col}'")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    with st.expander("Or paste GTINs manually"):
        with st.form("gtin_paste_form"):
            gtin_input = st.text_area(
                "Paste your GTINs (one per line):",
                height=150,
                placeholder="614141000012\n614141000029\n614141000036\n...",
            )
            paste_submitted = st.form_submit_button(
                "Validate GTINs", type="primary", use_container_width=True,
            )
        if paste_submitted and gtin_input.strip():
            raw_lines = [
                line.strip() for line in gtin_input.strip().split("\n")
                if line.strip()
            ]
            if len(raw_lines) > 10_000:
                st.warning(
                    f"You pasted {len(raw_lines):,} GTINs — maximum is 10,000. "
                    f"Only the first 10,000 will be validated."
                )
                raw_lines = raw_lines[:10_000]
            gtins_to_validate = raw_lines
            uploaded_df = None
            st.session_state.pop("validation_data_cache", None)
            st.session_state.pop("uploaded_df", None)

elif input_method == "sample":
    st.markdown(
        '<div class="sample-banner">'
        'You\'re viewing <strong>sample data</strong> &mdash; '
        'upload your own file to validate your GTINs.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(SAMPLE_DESCRIPTION)
    sample_df = pd.read_csv(StringIO(SAMPLE_DATA.strip()), dtype=str)
    uploaded_df = sample_df
    st.dataframe(sample_df, use_container_width=True, height=300)
    gtins_to_validate = sample_df["GTIN"].dropna().tolist()

else:
    st.caption("Choose an option above to get started.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

if gtins_to_validate:
    st.session_state["gtins_to_validate"] = gtins_to_validate
    if uploaded_df is not None:
        st.session_state["uploaded_df"] = uploaded_df

# Recover from session state if input was lost on rerun
if not gtins_to_validate and st.session_state.get("validated") and st.session_state.get("gtins_to_validate"):
    gtins_to_validate = st.session_state["gtins_to_validate"]
    uploaded_df = st.session_state.get("uploaded_df", uploaded_df)

if gtins_to_validate:
    if st.button("Start over", use_container_width=False):
        st.session_state.clear()
        st.rerun()

    st.session_state["validated"] = True

    cached_gtins = st.session_state.get("_cached_gtins")
    if "validation_data_cache" not in st.session_state or cached_gtins != gtins_to_validate:
        with st.spinner("Validating your GTINs against GS1 standards..."):
            validation_data = validate_batch(gtins_to_validate)
            st.session_state["validation_data_cache"] = validation_data
            st.session_state["_cached_gtins"] = gtins_to_validate
    else:
        validation_data = st.session_state["validation_data_cache"]

    summary = validation_data["summary"]
    score = validation_data["score"]
    cost = validation_data["cost_estimate"]
    results = validation_data["results"]
    hierarchy = validation_data["hierarchy"]
    retailer_checklists = validation_data["retailer_checklists"]

    st.markdown("---")

    # === READINESS SCORE ===
    score_color = "#28a745" if score["score"] >= 75 else ("#ffc107" if score["score"] >= 50 else "#dc3545")
    st.markdown(f"""
    <div class="score-card">
        <div class="score-number" style="color: {score_color};">{score["score"]}</div>
        <div class="score-grade">Grade: {score["grade"]}</div>
        <div class="score-interp">{score["interpretation"]}</div>
    </div>
    """, unsafe_allow_html=True)

    # === SUMMARY STATS ===
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-number">{summary["total_gtins"]}</div>
            <div class="stat-label">Total GTINs</div>
        </div>
        <div class="stat-card stat-critical">
            <div class="stat-number">{summary["critical_issues"]}</div>
            <div class="stat-label">Critical Issues</div>
        </div>
        <div class="stat-card stat-warning">
            <div class="stat-number">{summary["warnings"]}</div>
            <div class="stat-label">Warnings</div>
        </div>
        <div class="stat-card stat-clean">
            <div class="stat-number">{summary["clean"]}</div>
            <div class="stat-label">Clean</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # === DOWNLOAD VALIDATION REPORTS (above results) ===
    st.markdown("### 📥 Download Validation Reports")

    company_name = st.text_input(
        "Company name (optional)",
        value=st.session_state.get("company_name", ""),
        placeholder="e.g., Cedar Hollow Provisions",
        help="Brands your PDF report and file names.",
        key="company_name_input",
    )
    st.session_state["company_name"] = company_name

    filename_base = company_name.replace(" ", "_") if company_name else "gtin_validation"

    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        st.markdown("**✅ Corrected GTINs**")
        st.markdown(
            '<p class="text-sm-muted">'
            'Clean CSV with corrected check digits and formatting fixes applied. '
            'Paste directly into your product master or retailer portal.'
            '</p>',
            unsafe_allow_html=True,
        )
        corrected_data = generate_corrected_csv(validation_data)
        st.download_button(
            label="✅ Download Corrected GTINs",
            data=corrected_data,
            file_name=f"{filename_base}_corrected.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl_col2:
        st.markdown("**📄 CSV Report — Raw Data**")
        st.markdown(
            '<p class="text-sm-muted">'
            'Row-by-row validation results with issue codes, recommendations, '
            'and retailer impact. Best for Excel analysis.'
            '</p>',
            unsafe_allow_html=True,
        )
        csv_data = generate_csv_report(validation_data)
        st.download_button(
            label="📄 Download CSV Report",
            data=csv_data,
            file_name=f"{filename_base}_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl_col3:
        st.markdown("**📑 PDF Report — Full Diagnostic**")
        st.markdown(
            '<p class="text-sm-muted">'
            'Branded report with readiness score, retailer checklists, '
            'and cost-of-inaction estimates. Hand to your COO or broker.'
            '</p>',
            unsafe_allow_html=True,
        )
        try:
            pdf_buffer = generate_pdf_report(validation_data, company_name)
            st.download_button(
                label="📑 Download PDF Report",
                data=pdf_buffer,
                file_name=f"{filename_base}_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

    # === VALIDATION RESULTS TABS ===
    st.markdown("---")
    st.markdown("### Validation Results")

    tab_issues, tab_detail, tab_check_digit_fixes, tab_item_detail = st.tabs([
        "📋 Issues by Severity",
        "🔍 Full Item Detail",
        "✏️ Check Digit Corrections",
        "📦 Packaging Hierarchy",
    ])

    # --- Issues by Severity ---
    with tab_issues:
        st.markdown("### Issues by Severity")

        critical_items = [r for r in results if r.has_critical]
        warning_items = [r for r in results if r.has_warning and not r.has_critical]
        info_items = [r for r in results if r.issues and not r.has_critical and not r.has_warning]

        if critical_items:
            st.markdown('<span class="badge-critical">CRITICAL</span> — '
                       'These GTINs will be **rejected** by retailers.',
                       unsafe_allow_html=True)
            for r in critical_items:
                with st.expander(f"Row {r.row_number}: {r.raw_input}"):
                    for issue in r.issues:
                        if issue.severity == Severity.CRITICAL:
                            st.error(f"**{issue.message}**")
                            st.markdown(f"**Fix:** {issue.recommendation}")
                            st.markdown(f"**Retailer impact:** {issue.retailer_impact}")
                            st.markdown("---")

        if warning_items:
            st.markdown('<span class="badge-warning">WARNING</span> — '
                       'These GTINs may cause problems.',
                       unsafe_allow_html=True)
            for r in warning_items:
                with st.expander(f"Row {r.row_number}: {r.raw_input}"):
                    for issue in r.issues:
                        st.warning(f"**{issue.message}**")
                        st.markdown(f"**Fix:** {issue.recommendation}")
                        st.markdown(f"**Retailer impact:** {issue.retailer_impact}")

        if info_items:
            st.markdown('<span class="badge-info">INFO</span> — '
                       'Best practice notes.',
                       unsafe_allow_html=True)
            for r in info_items:
                with st.expander(f"Row {r.row_number}: {r.raw_input}"):
                    for issue in r.issues:
                        st.info(f"{issue.message}")

        if not critical_items and not warning_items and not info_items:
            st.success("🎉 All GTINs passed validation with no issues!")

    # --- Check Digit Corrections ---
    with tab_check_digit_fixes:
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

    # --- Packaging Hierarchy ---
    with tab_item_detail:
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

    # --- Full Item Detail ---
    with tab_detail:
        st.markdown("### Full Item Detail")

        detail_rows = []
        for r in results:
            status = "✅ Clean" if not r.issues else (
                "❌ Critical" if r.has_critical else (
                    "⚠️ Warning" if r.has_warning else "ℹ️ Info"
                )
            )
            detail_rows.append({
                "Row": r.row_number,
                "GTIN": r.raw_input,
                "Type": r.gtin_type.value,
                "Status": status,
                "Issues": len(r.issues),
                "Corrected": r.corrected_value or "",
            })

        detail_df = pd.DataFrame(detail_rows)
        st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # =================================================================
    # DEEP ANALYSIS SECTION
    # =================================================================
    st.markdown("---")
    st.markdown("## 🔬 Deep Analysis")
    st.markdown(
        "Go beyond basic validation — understand what to fix first, "
        "check retailer readiness, estimate costs, and track your progress."
    )

    tab_summary, tab_roadmap, tab_retailer, tab_cost, tab_gtin14, tab_completeness = st.tabs([
        "📝 Executive Summary",
        "🗺️ Prioritized Fix Plan",
        "🏪 Retailer Readiness",
        "💰 Cost of Inaction",
        "🔧 Case GTIN Generator",
        "📊 Product Data Completeness",
    ])

    # --- Executive Summary ---
    with tab_summary:
        st.markdown("### Executive Summary")
        st.markdown(
            "Copy this summary and send it to your team. "
            "It's written in plain language — no jargon."
        )

        exec_summary = generate_executive_summary(validation_data)
        st.markdown(
            f'<div class="security-box">'
            f'{exec_summary.replace(chr(10)+chr(10), "<br><br>")}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            label="📋 Copy Summary as Text",
            data=exec_summary,
            file_name="gtin_executive_summary.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # --- Prioritized Fix Plan ---
    with tab_roadmap:
        st.markdown("### Prioritized Fix Plan")
        st.markdown(
            "Issues ranked by **impact × effort**. Start at the top — "
            "these are your fastest wins with the biggest payoff."
        )

        roadmap = generate_fix_roadmap(results, hierarchy)
        if roadmap:
            for idx, item in enumerate(roadmap, 1):
                effort_color = {"Low": "#28a745", "Medium": "#ffc107", "High": "#dc3545"}.get(item["effort"], "#6c757d")
                impact_color = {"High": "#dc3545", "Medium": "#ffc107", "Low": "#28a745"}.get(item["impact"], "#6c757d")

                with st.expander(
                    f"Priority {idx}: {item['action'][:80]}{'...' if len(item['action']) > 80 else ''} "
                    f"({item['count']} item{'s' if item['count'] != 1 else ''})"
                ):
                    col_e, col_i, col_t = st.columns(3)
                    with col_e:
                        st.markdown(f"**Effort:** <span style='color:{effort_color}'>{item['effort']}</span>",
                                   unsafe_allow_html=True)
                        st.caption(item["effort_detail"])
                    with col_i:
                        st.markdown(f"**Impact:** <span style='color:{impact_color}'>{item['impact']}</span>",
                                   unsafe_allow_html=True)
                        st.caption(item["impact_detail"])
                    with col_t:
                        st.markdown("**Time estimate:**")
                        st.caption(item["time_estimate"])

                    st.markdown(f"**Full recommendation:** {item['action']}")
        else:
            st.success("No issues to fix — your data is clean!")

    # --- Retailer Readiness ---
    with tab_retailer:
        st.markdown("### Retailer Submission Readiness")
        st.markdown(
            "Each retailer has specific GTIN requirements. "
            "Here's how your data stacks up."
        )

        retailers_to_show = (
            {selected_retailer: retailer_checklists[selected_retailer]}
            if selected_retailer != "All Retailers"
            else retailer_checklists
        )

        for retailer_name, checklist in retailers_to_show.items():
            ready_class = "retailer-ready" if checklist["ready"] else "retailer-not-ready"
            if checklist["ready"]:
                status_text = "✅ READY"
            else:
                status_text = f"❌ {checklist['passed']}/{checklist['total']} checks passed"

            st.markdown(f"""
            <div class="retailer-card {ready_class}">
                <strong>{retailer_name}</strong> — {status_text}<br>
                <small class="text-sm-muted">{checklist['profile']['description']}</small>
            </div>
            """, unsafe_allow_html=True)

            for check in checklist["checks"]:
                icon = "✅" if check["passed"] else "❌"
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{icon} {check['check']} — *{check['detail']}*")

            if checklist["profile"].get("notes"):
                st.caption(checklist["profile"]["notes"])

            st.markdown("")

    # --- Cost of Inaction ---
    with tab_cost:
        st.markdown("### Estimated Cost of Inaction")
        st.markdown(
            "These estimates are based on industry averages for specialty food brands "
            "at similar scale. They're directional — meant to quantify the risk, not "
            "predict exact costs."
        )

        if cost:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div class="cost-card">
                    <div class="cost-number">
                        ${cost['annual_estimate_low']:,} – ${cost['annual_estimate_high']:,}
                    </div>
                    <div>Estimated annual cost of unresolved GTIN issues</div>
                </div>
                """, unsafe_allow_html=True)

            with col_b:
                st.markdown(f"""
                <div class="cost-card">
                    <div class="cost-number">{cost['rework_hours']} hours/year</div>
                    <div>Manual rework from GTIN problems</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("#### Breakdown")
            cost_df = pd.DataFrame([
                {
                    "Category": "Chargebacks from invalid GTINs",
                    "Low Estimate": f"${cost['chargeback_range'][0]:,}",
                    "High Estimate": f"${cost['chargeback_range'][1]:,}",
                },
                {
                    "Category": f"Delayed launches ({cost['delayed_skus']} SKUs)",
                    "Low Estimate": f"${cost['delayed_launch_range'][0]:,}",
                    "High Estimate": f"${cost['delayed_launch_range'][1]:,}",
                },
                {
                    "Category": f"Manual rework ({cost['rework_hours']} hrs)",
                    "Low Estimate": f"${cost['rework_cost']:,}",
                    "High Estimate": f"${cost['rework_cost']:,}",
                },
            ])
            st.dataframe(cost_df, use_container_width=True, hide_index=True)

            if cost.get("growth_note"):
                st.warning(f"📈 **Growth multiplier:** {cost['growth_note']}")
        else:
            st.info("No cost estimates available — no issues detected.")

    # --- Case GTIN Generator ---
    with tab_gtin14:
        st.markdown("### Case GTIN-14 Generator")
        st.markdown(
            "These are your unit-level GTINs that don't have a corresponding "
            "case-level GTIN-14 in your file. Below are the GTIN-14s you'd need "
            "to create for each packaging level."
        )

        suggestions = generate_gtin14_suggestions(results, hierarchy)
        if suggestions:
            st.markdown(
                f"**{len(suggestions)} unit GTIN(s)** need case-level GTIN-14s."
            )

            for s in suggestions:
                with st.expander(f"Row {s['row']}: {s['unit_gtin']} ({s['unit_type']})"):
                    gtin14_rows = []
                    for ind, info in s["indicators"].items():
                        gtin14_rows.append({
                            "Indicator": str(ind),
                            "GTIN-14": info["gtin14"],
                            "Packaging Level": info["label"],
                        })
                    st.dataframe(
                        pd.DataFrame(gtin14_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.caption(
                        "Most commonly, indicator 1 = case. Copy the GTIN-14 you need "
                        "and add it to your product master."
                    )
        else:
            st.success(
                "All unit GTINs have matching case-level GTIN-14s, "
                "or no valid unit GTINs were found to generate suggestions for."
            )

    # --- Product Data Completeness ---
    with tab_completeness:
        st.markdown("### Product Data Completeness")

        if uploaded_df is not None and len(uploaded_df.columns) > 1:
            st.markdown(
                "Beyond GTINs, retailers require dozens of product attributes. "
                "Here's what we found in your file."
            )

            completeness = check_data_completeness(uploaded_df)

            if completeness["field_analysis"]:
                overall = completeness["overall_completeness"]
                overall_color = "#28a745" if overall >= 80 else ("#ffc107" if overall >= 50 else "#dc3545")
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-number" style="color:{overall_color} !important;">'
                    f'{overall}%</div>'
                    f'<div class="stat-label">Overall Data Completeness</div></div>',
                    unsafe_allow_html=True,
                )

                st.markdown("#### Fields Found in Your File")
                field_rows = []
                for field_name, data in completeness["field_analysis"].items():
                    field_rows.append({
                        "Field": field_name.replace("_", " ").title(),
                        "Column": data["column_name"],
                        "Populated": f"{data['populated']}/{data['total_rows']}",
                        "% Rows Populated": f"{data['completeness_pct']}%",
                    })
                st.dataframe(pd.DataFrame(field_rows), use_container_width=True, hide_index=True)

                if completeness["missing_important_fields"]:
                    st.markdown("#### Missing Important Fields")
                    st.warning(
                        "The following fields were not found in your file: **" +
                        ", ".join(f.replace("_", " ").title() for f in completeness["missing_important_fields"]) +
                        "**. Most retailers require these for item setup."
                    )

                st.markdown("#### Retailer Data Readiness")
                for retailer, gaps in completeness["retailer_data_gaps"].items():
                    status = "✅ READY" if gaps["ready"] else f"❌ {gaps['present']}/{gaps['required']} fields present"
                    with st.expander(f"{retailer} — {status}"):
                        if gaps["missing_fields"]:
                            st.markdown(
                                "**Missing:** " +
                                ", ".join(f.replace("_", " ").title() for f in gaps["missing_fields"])
                            )
                        if gaps["incomplete_fields"]:
                            st.markdown(
                                "**Incomplete (not all rows filled):** " +
                                ", ".join(f.replace("_", " ").title() for f in gaps["incomplete_fields"])
                            )
                        if gaps["ready"]:
                            st.success("All required fields present and complete.")
            else:
                st.info(
                    "No standard product data fields detected beyond GTINs. "
                    "Upload a CSV with columns like Product Name, Brand, Weight, "
                    "Height, Width, Depth, etc. for a completeness analysis."
                )
        else:
            st.info(
                "Data completeness analysis is available when you upload a CSV file "
                "with multiple columns (beyond just GTINs). Upload a product master "
                "spreadsheet to see which fields are missing or incomplete."
            )

# ---------------------------------------------------------------------------
# Footer — security & privacy
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    '<div class="security-box">'
    '<strong>Your Data Stays Yours</strong><br><br>'
    'This tool processes your GTINs entirely within your browser session. '
    'No product data is stored, logged, transmitted to third parties, or retained after you close this page. '
    'There is no database behind this tool &mdash; nothing is saved, period.<br><br>'
    'Your data is never used for training, analytics, or any purpose beyond generating '
    'your validation results in this session. When you close the tab, your data is gone.<br><br>'
    '<small class="text-sm-muted">This tool runs on Streamlit Community Cloud. '
    "Streamlit's infrastructure processes the request but does not persist application data between sessions. "
    'For details, see <a href="https://streamlit.io/privacy-policy">Streamlit\'s privacy policy</a>.</small>'
    '</div>',
    unsafe_allow_html=True,
)
