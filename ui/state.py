"""Session-state key constants and helpers.

Centralizing these here means the rest of the UI never deals with raw
string keys, and reset_session() can no longer accidentally wipe
unrelated keys.
"""

from __future__ import annotations

import streamlit as st


# Hard cap on rows we will validate from any input source. Keeps Streamlit
# responsive when someone pastes (or uploads) a huge list by accident.
MAX_GTINS_PER_BATCH = 50_000


# -- session_state keys ------------------------------------------------------

KEY_GTINS = "gtins_to_validate"
KEY_DF = "uploaded_df"
KEY_VALIDATED = "validated"
KEY_VALIDATION_CACHE = "validation_data_cache"
KEY_CSV_CACHE = "csv_report_cache"
KEY_PDF_CACHE = "pdf_report_cache"
KEY_PDF_COMPANY = "pdf_report_company_name"
KEY_PDF_ERROR = "pdf_report_error"

# Keys this UI owns. reset_session() only clears these — anything else
# (e.g. Streamlit-internal widget state) is left alone.
_OWNED_KEYS = (
    KEY_GTINS,
    KEY_DF,
    KEY_VALIDATED,
    KEY_VALIDATION_CACHE,
    KEY_CSV_CACHE,
    KEY_PDF_CACHE,
    KEY_PDF_COMPANY,
    KEY_PDF_ERROR,
)


# -- helpers -----------------------------------------------------------------

def reset_session() -> None:
    """Clear every key this UI owns. Used by the Reset button."""
    for key in _OWNED_KEYS:
        st.session_state.pop(key, None)


def invalidate_report_caches() -> None:
    """Drop the derived CSV / PDF caches so they regenerate on next use.

    Called whenever validate_batch is re-run with fresh input.
    """
    st.session_state.pop(KEY_CSV_CACHE, None)
    st.session_state.pop(KEY_PDF_CACHE, None)
    st.session_state.pop(KEY_PDF_COMPANY, None)
    st.session_state.pop(KEY_PDF_ERROR, None)
