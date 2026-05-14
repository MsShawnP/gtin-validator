"""Deep-analysis tabs: exec summary, fix plan, retailer readiness,
cost of inaction, GTIN-14 generator, data completeness."""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from gtin_core import (
    check_data_completeness,
    generate_executive_summary,
    generate_fix_roadmap,
    generate_gtin14_suggestions,
)


def render_deep_analysis(
    validation_data: dict,
    selected_retailer: str,
    uploaded_df: Optional[pd.DataFrame],
) -> None:
    st.markdown("---")
    st.markdown("## 🔬 Deep Analysis")
    st.markdown(
        "Go beyond basic validation — understand what to fix first, "
        "check retailer readiness, estimate costs, and track your progress."
    )

    tabs = st.tabs([
        "📝 Executive Summary",
        "🗺️ Prioritized Fix Plan",
        "🏪 Retailer Readiness",
        "💰 Cost of Inaction",
        "🔧 Case GTIN Generator",
        "📊 Product Data Completeness",
    ])
    tab_summary, tab_roadmap, tab_retailer, tab_cost, tab_gtin14, tab_completeness = tabs

    with tab_summary:
        _render_executive_summary(validation_data)
    with tab_roadmap:
        _render_fix_roadmap(validation_data)
    with tab_retailer:
        _render_retailer_readiness(validation_data, selected_retailer)
    with tab_cost:
        _render_cost_of_inaction(validation_data)
    with tab_gtin14:
        _render_gtin14_generator(validation_data)
    with tab_completeness:
        _render_data_completeness(uploaded_df)


def _render_executive_summary(validation_data: dict) -> None:
    st.markdown("### Executive Summary")
    st.markdown(
        "Copy this summary and send it to your team. "
        "It's written in plain language — no jargon."
    )
    exec_summary = generate_executive_summary(validation_data)
    st.markdown(
        f'<div class="security-box" style="border-color:var(--border-color);">'
        f'{exec_summary.replace(chr(10) + chr(10), "<br><br>")}'
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


def _render_fix_roadmap(validation_data: dict) -> None:
    st.markdown("### Prioritized Fix Plan")
    st.markdown(
        "Issues ranked by **impact × effort**. Start at the top — "
        "these are your fastest wins with the biggest payoff."
    )
    roadmap = generate_fix_roadmap(
        validation_data["results"], validation_data["hierarchy"],
    )
    if not roadmap:
        st.success("No issues to fix — your data is clean!")
        return

    effort_colors = {"Low": "#28a745", "Medium": "#ffc107", "High": "#dc3545"}
    impact_colors = {"High": "#dc3545", "Medium": "#ffc107", "Low": "#28a745"}

    for idx, item in enumerate(roadmap, 1):
        effort_color = effort_colors.get(item["effort"], "#6c757d")
        impact_color = impact_colors.get(item["impact"], "#6c757d")

        action_preview = item["action"][:80]
        if len(item["action"]) > 80:
            action_preview += "..."
        plural = "s" if item["count"] != 1 else ""

        with st.expander(
            f"Priority {idx}: {action_preview} ({item['count']} item{plural})"
        ):
            col_e, col_i, col_t = st.columns(3)
            with col_e:
                st.markdown(
                    f"**Effort:** <span style='color:{effort_color}'>{item['effort']}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(item["effort_detail"])
            with col_i:
                st.markdown(
                    f"**Impact:** <span style='color:{impact_color}'>{item['impact']}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(item["impact_detail"])
            with col_t:
                st.markdown("**Time estimate:**")
                st.caption(item["time_estimate"])

            st.markdown(f"**Full recommendation:** {item['action']}")


def _render_retailer_readiness(
    validation_data: dict, selected_retailer: str,
) -> None:
    st.markdown("### Retailer Submission Readiness")
    st.markdown(
        "Each retailer has specific GTIN requirements. "
        "Here's how your data stacks up."
    )
    checklists = validation_data["retailer_checklists"]
    retailers_to_show = (
        {selected_retailer: checklists[selected_retailer]}
        if selected_retailer != "All Retailers"
        else checklists
    )

    for retailer_name, checklist in retailers_to_show.items():
        ready_class = "retailer-ready" if checklist["ready"] else "retailer-not-ready"
        status_text = (
            "✅ READY" if checklist["ready"]
            else f"❌ {checklist['passed']}/{checklist['total']} checks passed"
        )
        st.markdown(
            f"""
            <div class="retailer-card {ready_class}">
                <strong>{retailer_name}</strong> — {status_text}<br>
                <small style="color:#6c757d;">{checklist['profile']['description']}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for check in checklist["checks"]:
            icon = "✅" if check["passed"] else "❌"
            st.markdown(
                f"&nbsp;&nbsp;&nbsp;&nbsp;{icon} {check['check']} — *{check['detail']}*"
            )
        if checklist["profile"].get("notes"):
            st.caption(checklist["profile"]["notes"])
        st.markdown("")


def _render_cost_of_inaction(validation_data: dict) -> None:
    st.markdown("### Estimated Cost of Inaction")
    st.markdown(
        "These estimates are based on industry averages for specialty food brands "
        "at similar scale. They're directional — meant to quantify the risk, not "
        "predict exact costs."
    )
    cost = validation_data["cost_estimate"]
    if not cost:
        st.info("No cost estimates available — no issues detected.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
            <div class="cost-card">
                <div class="cost-number">
                    ${cost['annual_estimate_low']:,} – ${cost['annual_estimate_high']:,}
                </div>
                <div>Estimated annual cost of unresolved GTIN issues</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f"""
            <div class="cost-card">
                <div class="cost-number">{cost['rework_hours']} hours/year</div>
                <div>Manual rework from GTIN problems</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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


def _render_gtin14_generator(validation_data: dict) -> None:
    st.markdown("### Case GTIN-14 Generator")
    st.markdown(
        "These are your unit-level GTINs that don't have a corresponding "
        "case-level GTIN-14 in your file. Below are the GTIN-14s you'd need "
        "to create for each packaging level."
    )
    suggestions = generate_gtin14_suggestions(
        validation_data["results"], validation_data["hierarchy"],
    )
    if not suggestions:
        st.success(
            "All unit GTINs have matching case-level GTIN-14s, "
            "or no valid unit GTINs were found to generate suggestions for."
        )
        return

    st.markdown(f"**{len(suggestions)} unit GTIN(s)** need case-level GTIN-14s.")
    for s in suggestions:
        with st.expander(f"Row {s['row']}: {s['unit_gtin']} ({s['unit_type']})"):
            rows = [
                {
                    "Indicator": str(ind),
                    "GTIN-14": info["gtin14"],
                    "Packaging Level": info["label"],
                }
                for ind, info in s["indicators"].items()
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(
                "Most commonly, indicator 1 = case. Copy the GTIN-14 you need "
                "and add it to your product master."
            )


def _render_data_completeness(uploaded_df: Optional[pd.DataFrame]) -> None:
    st.markdown("### Product Data Completeness")
    if uploaded_df is None or len(uploaded_df.columns) <= 1:
        st.info(
            "Data completeness analysis is available when you upload a CSV file "
            "with multiple columns (beyond just GTINs). Upload a product master "
            "spreadsheet to see which fields are missing or incomplete."
        )
        return

    st.markdown(
        "Beyond GTINs, retailers require dozens of product attributes. "
        "Here's what we found in your file."
    )
    completeness = check_data_completeness(uploaded_df)

    if not completeness["field_analysis"]:
        st.info(
            "No standard product data fields detected beyond GTINs. "
            "Upload a CSV with columns like Product Name, Brand, Weight, "
            "Height, Width, Depth, etc. for a completeness analysis."
        )
        return

    overall = completeness["overall_completeness"]
    overall_color = (
        "#28a745" if overall >= 80
        else "#ffc107" if overall >= 50
        else "#dc3545"
    )
    st.markdown(
        f'<div class="stat-card" style="text-align:center;">'
        f'<div class="stat-number" style="color:{overall_color} !important;">'
        f'{overall}%</div>'
        f'<div class="stat-label">Overall Data Completeness</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### Fields Found in Your File")
    field_rows = [
        {
            "Field": field_name.replace("_", " ").title(),
            "Column": data["column_name"],
            "Populated": f"{data['populated']}/{data['total_rows']}",
            "% Rows Populated": f"{data['completeness_pct']}%",
        }
        for field_name, data in completeness["field_analysis"].items()
    ]
    st.dataframe(pd.DataFrame(field_rows), use_container_width=True, hide_index=True)

    if completeness["missing_important_fields"]:
        st.markdown("#### Missing Important Fields")
        st.warning(
            "The following fields were not found in your file: **"
            + ", ".join(
                f.replace("_", " ").title()
                for f in completeness["missing_important_fields"]
            )
            + "**. Most retailers require these for item setup."
        )

    st.markdown("#### Retailer Data Readiness")
    for retailer, gaps in completeness["retailer_data_gaps"].items():
        status = (
            "✅ READY" if gaps["ready"]
            else f"❌ {gaps['present']}/{gaps['required']} fields present"
        )
        with st.expander(f"{retailer} — {status}"):
            if gaps["missing_fields"]:
                st.markdown(
                    "**Missing:** "
                    + ", ".join(
                        f.replace("_", " ").title()
                        for f in gaps["missing_fields"]
                    )
                )
            if gaps["incomplete_fields"]:
                st.markdown(
                    "**Incomplete (not all rows filled):** "
                    + ", ".join(
                        f.replace("_", " ").title()
                        for f in gaps["incomplete_fields"]
                    )
                )
            if gaps["ready"]:
                st.success("All required fields present and complete.")
