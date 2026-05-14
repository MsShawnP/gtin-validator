"""
GTIN Product Data Validator
A diagnostic tool for specialty food brands preparing product data
for retailer submission (Walmart, Costco, UNFI, 1WorldSync, and more).

Built for operations people, not developers.

This file is the Streamlit entry point — it wires together page config,
the sidebar, and the rendering modules under ui/. The substantive UI
lives there.
"""

import streamlit as st

from gtin_core import RETAILER_PROFILES, validate_batch
from ui.deep_analysis import render_deep_analysis
from ui.input_section import render_input_section
from ui.results import (
    render_download_buttons,
    render_results_tabs,
    render_score_card,
    render_summary_stats,
)
from ui.state import (
    KEY_DF, KEY_GTINS, KEY_VALIDATED, KEY_VALIDATION_CACHE,
    invalidate_report_caches, reset_session,
)
from ui.styles import inject_css


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="GTIN Product Data Validator",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


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

    company_name = st.text_input(
        "Your company name (optional)",
        placeholder="e.g., Cedar Hollow Provisions",
        help="Used to brand your PDF report.",
    )

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

gtins_to_validate, uploaded_df = render_input_section()

if gtins_to_validate:
    # Persist parsed input so it survives Streamlit reruns triggered by
    # unrelated widget interactions.
    st.session_state[KEY_GTINS] = gtins_to_validate
    if uploaded_df is not None:
        st.session_state[KEY_DF] = uploaded_df

# Recover the parsed input from session state when the current rerun lost it.
if (
    not gtins_to_validate
    and st.session_state.get(KEY_VALIDATED)
    and st.session_state.get(KEY_GTINS)
):
    gtins_to_validate = st.session_state[KEY_GTINS]
    uploaded_df = st.session_state.get(KEY_DF, uploaded_df)


# ---------------------------------------------------------------------------
# Validation flow
# ---------------------------------------------------------------------------

def _no_data_explainer() -> None:
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
        "Streamlit's infrastructure processes the request but does not persist application data between sessions. "
        'For details, see <a href="https://streamlit.io/privacy-policy">Streamlit\'s privacy policy</a>.</small>'
        '</div>',
        unsafe_allow_html=True,
    )


def _share_and_security_footer() -> None:
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


if not gtins_to_validate:
    _no_data_explainer()
else:
    btn_col1, btn_col2 = st.columns([3, 1])
    with btn_col1:
        validate_btn = st.button(
            "🔍 Validate GTINs", type="primary", use_container_width=True,
        )
    with btn_col2:
        reset_btn = st.button("🔄 Reset", use_container_width=True)

    if reset_btn:
        reset_session()
        st.rerun()

    if validate_btn or st.session_state.get(KEY_VALIDATED):
        st.session_state[KEY_VALIDATED] = True

        # Use cached validation data when nothing has changed; on a fresh
        # validate run, also drop the derived report caches.
        if validate_btn or KEY_VALIDATION_CACHE not in st.session_state:
            with st.spinner("Validating your GTINs against GS1 standards..."):
                validation_data = validate_batch(gtins_to_validate)
                st.session_state[KEY_VALIDATION_CACHE] = validation_data
                invalidate_report_caches()
        else:
            validation_data = st.session_state[KEY_VALIDATION_CACHE]

        st.markdown("---")
        render_score_card(validation_data["score"])
        render_summary_stats(validation_data["summary"])
        render_download_buttons(validation_data, company_name)

        st.markdown("---")
        st.markdown("### Validation Results")
        render_results_tabs(validation_data)

        render_deep_analysis(validation_data, selected_retailer, uploaded_df)
        _share_and_security_footer()
