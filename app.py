"""
GTIN Product Data Validator
A diagnostic tool for specialty food brands preparing product data
for retailer submission (Walmart, Costco, UNFI, 1WorldSync, and more).

Built for operations people, not developers.
"""

import streamlit as st
import pandas as pd
from io import StringIO
from gtin_core import (
    validate_batch, Severity, generate_before_after,
    RETAILER_PROFILES, GTINType,
    generate_executive_summary, generate_fix_roadmap,
    generate_gtin14_suggestions, check_data_completeness,
)
from csv_report import generate_csv_report
from pdf_report import generate_pdf_report
from sample_data import SAMPLE_DATA, SAMPLE_DESCRIPTION
from ui_helpers import load_css


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="GTIN Product Data Validator",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

load_css()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown("# 📦 GTIN Product Data Validator")
st.markdown(
    "Validate your product GTINs against GS1 standards and retailer requirements. "
    "Built for operations teams at specialty food brands preparing for national retail."
)

# ---------------------------------------------------------------------------
# Sidebar — input + settings
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### How to use")
    st.markdown(
        "1. Paste GTINs or upload a CSV file\n"
        "2. Review your readiness score\n"
        "3. Check retailer-specific requirements\n"
        "4. Download your report"
    )

    st.markdown("---")

    # Company name for branding
    company_name = st.text_input(
        "Your company name (optional)",
        placeholder="e.g., Cedar Hollow Provisions",
        help="Used to brand your PDF report.",
    )

    # Retailer filter
    st.markdown("### Filter by retailer")
    selected_retailer = st.selectbox(
        "Show requirements for:",
        ["All Retailers"] + list(RETAILER_PROFILES.keys()),
        help="Filter the checklist to show requirements for a specific retailer.",
    )

    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.8rem; color:#6c757d; text-align:center;">'
        'Built for specialty food brands.<br>'
        'Not affiliated with GS1, Walmart, or any retailer.'
        '</p>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------

st.markdown("---")

input_method = st.radio(
    "Choose input method:",
    ["Paste GTINs", "Upload CSV", "Try sample data"],
    horizontal=True,
)

gtins_to_validate = []
uploaded_df = None  # Store full DataFrame for data completeness check

if input_method == "Paste GTINs":
    gtin_input = st.text_area(
        "Paste your GTINs (one per line):",
        height=200,
        placeholder="614141000012\n614141000029\n614141000036\n...",
    )
    if gtin_input.strip():
        gtins_to_validate = [
            line.strip() for line in gtin_input.strip().split("\n")
            if line.strip()
        ]

elif input_method == "Upload CSV":
    uploaded_file = st.file_uploader(
        "Upload a CSV file with a GTIN column:",
        type=["csv"],
        help="Your CSV should have a column containing GTINs. We'll auto-detect it.",
    )
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, dtype=str)
            uploaded_df = df  # Save for data completeness
            # Auto-detect GTIN column
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

elif input_method == "Try sample data":
    st.markdown(SAMPLE_DESCRIPTION)
    sample_df = pd.read_csv(StringIO(SAMPLE_DATA.strip()), dtype=str)
    uploaded_df = sample_df  # Save for data completeness
    st.dataframe(sample_df, use_container_width=True, height=300)
    gtins_to_validate = sample_df["GTIN"].dropna().tolist()
    st.info(f"Loaded {len(gtins_to_validate)} sample GTINs")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

if gtins_to_validate:
    # Store GTINs in session state so dark mode toggle doesn't lose them
    st.session_state["gtins_to_validate"] = gtins_to_validate
    if uploaded_df is not None:
        st.session_state["uploaded_df"] = uploaded_df

# Recover from session state if input was lost (e.g., after dark mode toggle)
if not gtins_to_validate and st.session_state.get("validated") and st.session_state.get("gtins_to_validate"):
    gtins_to_validate = st.session_state["gtins_to_validate"]
    uploaded_df = st.session_state.get("uploaded_df", uploaded_df)

if gtins_to_validate:
    btn_col1, btn_col2 = st.columns([3, 1])
    with btn_col1:
        validate_btn = st.button("🔍 Validate GTINs", type="primary", use_container_width=True)
    with btn_col2:
        reset_btn = st.button("🔄 Reset", use_container_width=True)

    if reset_btn:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if validate_btn or st.session_state.get("validated"):
        st.session_state["validated"] = True

        # Use cached validation data if available, otherwise validate
        if validate_btn or "validation_data_cache" not in st.session_state:
            with st.spinner("Validating your GTINs against GS1 standards..."):
                validation_data = validate_batch(gtins_to_validate)
                st.session_state["validation_data_cache"] = validation_data
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
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{summary["total_gtins"]}</div>
                <div class="stat-label">Total GTINs</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card stat-critical">
                <div class="stat-number">{summary["critical_issues"]}</div>
                <div class="stat-label">Critical Issues</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card stat-warning">
                <div class="stat-number">{summary["warnings"]}</div>
                <div class="stat-label">Warnings</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="stat-card stat-clean">
                <div class="stat-number">{summary["clean"]}</div>
                <div class="stat-label">Clean</div>
            </div>
            """, unsafe_allow_html=True)

        # === DOWNLOAD VALIDATION REPORTS (above results) ===
        st.markdown("### 📥 Download Validation Reports")

        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            st.markdown("**📄 CSV Report — Raw Data**")
            st.markdown(
                '<p style="font-size:0.85rem; color:var(--text-muted);">'
                'Row-by-row validation results in spreadsheet format. '
                'Includes each GTIN, its status, issue codes, and corrected values. '
                'Best for importing into Excel or your own systems for further analysis.'
                '</p>',
                unsafe_allow_html=True,
            )
            csv_data = generate_csv_report(validation_data)
            filename_base = company_name.replace(" ", "_") if company_name else "gtin_validation"
            st.download_button(
                label="📄 Download CSV Report",
                data=csv_data,
                file_name=f"{filename_base}_report.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with dl_col2:
            st.markdown("**📑 PDF Report — Full Diagnostic**")
            st.markdown(
                '<p style="font-size:0.85rem; color:var(--text-muted);">'
                'Branded, professional report with readiness score, retailer-specific '
                'checklists, cost-of-inaction estimates, and prioritized issue detail. '
                'Designed to hand directly to your operations team, broker, or trading partner coordinator.'
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
                st.markdown(f'<span class="badge-critical">CRITICAL</span> — '
                           f'These GTINs will be **rejected** by retailers.',
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
                st.markdown(f'<span class="badge-warning">WARNING</span> — '
                           f'These GTINs may cause problems.',
                           unsafe_allow_html=True)
                for r in warning_items:
                    with st.expander(f"Row {r.row_number}: {r.raw_input}"):
                        for issue in r.issues:
                            st.warning(f"**{issue.message}**")
                            st.markdown(f"**Fix:** {issue.recommendation}")
                            st.markdown(f"**Retailer impact:** {issue.retailer_impact}")

            if info_items:
                st.markdown(f'<span class="badge-info">INFO</span> — '
                           f'Best practice notes.',
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
                f'<div class="security-box" style="border-color:var(--border-color);">'
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
                            st.markdown(f"**Time estimate:**")
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
                status_text = "✅ READY" if checklist["ready"] else f"❌ {checklist['passed']}/{checklist['total']} checks passed"

                st.markdown(f"""
                <div class="retailer-card {ready_class}">
                    <strong>{retailer_name}</strong> — {status_text}<br>
                    <small style="color:#6c757d;">{checklist['profile']['description']}</small>
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
                        f'<div class="stat-card" style="text-align:center;">'
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

        # === SHARE & SECURITY ===
        st.markdown("---")
        st.markdown("### 🔗 Share Results")
        st.info(
            "To share these results, download the PDF report and send it to your team. "
            "The branded report is designed to be forwarded to your operations team, broker, or "
            "trading partner coordinator."
        )

        st.markdown(
            '<div class="security-box-compact">'
            '<strong>🔒 Your Data Stays Yours</strong> — '
            'No product data is stored, logged, or transmitted to third parties. '
            'Everything is processed in-session and discarded when you close this page.'
            '</div>',
            unsafe_allow_html=True,
        )

else:
    # No data loaded yet — show explainer
    st.markdown("---")
    st.markdown("### What this tool checks")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("#### 🔢 Format & Structure")
        st.markdown(
            "Valid GTIN lengths (8, 12, 13, 14 digits), numeric-only, "
            "correct check digits using GS1's mod-10 algorithm."
        )

    with col_b:
        st.markdown("#### 🏪 Retailer Requirements")
        st.markdown(
            "Walmart Item 360, Costco, UNFI, KeHE, Whole Foods, "
            "1WorldSync — each has specific GTIN format and hierarchy requirements."
        )

    with col_c:
        st.markdown("#### 📦 Packaging Hierarchy")
        st.markdown(
            "Detects unit-to-case GTIN relationships, orphan case codes, "
            "and missing packaging levels that will block retail setup."
        )

    st.markdown("---")
    st.markdown(
        '<div class="security-box">'
        '<strong>🔒 Your Data Stays Yours</strong><br><br>'
        'This tool processes your GTINs entirely within your browser session. '
        'No product data is stored, logged, transmitted to third parties, or retained after you close this page. '
        'There is no database behind this tool — nothing is saved, period.<br><br>'
        'Your data is never used for training, analytics, or any purpose beyond generating '
        'your validation results in this session. When you close the tab, your data is gone.<br><br>'
        '<small style="color:var(--text-muted);">This tool runs on Streamlit Community Cloud. '
        'Streamlit\'s infrastructure processes the request but does not persist application data between sessions. '
        'For details, see <a href="https://streamlit.io/privacy-policy">Streamlit\'s privacy policy</a>.</small>'
        '</div>',
        unsafe_allow_html=True,
    )
