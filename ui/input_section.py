"""Input collection: paste, CSV upload, or sample data."""

from __future__ import annotations

from io import StringIO
from typing import Optional

import pandas as pd
import streamlit as st

from sample_data import SAMPLE_DATA, SAMPLE_DESCRIPTION
from ui.state import MAX_GTINS_PER_BATCH


def render_input_section() -> tuple[list[str], Optional[pd.DataFrame]]:
    """Render the input controls and return the parsed (gtins, dataframe).

    The dataframe is None unless the user uploaded a CSV or chose the
    sample data path — it's used by the data-completeness section.
    """
    input_method = st.radio(
        "Choose input method:",
        ["Paste GTINs", "Upload CSV", "Try sample data"],
        horizontal=True,
    )

    if input_method == "Paste GTINs":
        return _paste_input(), None
    if input_method == "Upload CSV":
        return _csv_upload_input()
    return _sample_data_input()


# -- paste -------------------------------------------------------------------

def _paste_input() -> list[str]:
    gtin_input = st.text_area(
        "Paste your GTINs (one per line):",
        height=200,
        placeholder="614141000012\n614141000029\n614141000036\n...",
    )
    if not gtin_input.strip():
        return []

    parsed_lines = [
        line.strip()
        for line in gtin_input.strip().split("\n")
        if line.strip()
    ]
    if len(parsed_lines) > MAX_GTINS_PER_BATCH:
        st.error(
            f"Too many GTINs ({len(parsed_lines):,}). The current limit "
            f"is {MAX_GTINS_PER_BATCH:,} per batch — please split your "
            "list and validate it in chunks."
        )
        return []
    return parsed_lines


# -- CSV upload --------------------------------------------------------------

def _csv_upload_input() -> tuple[list[str], Optional[pd.DataFrame]]:
    uploaded_file = st.file_uploader(
        "Upload a CSV file with a GTIN column:",
        type=["csv"],
        help="Your CSV should have a column containing GTINs. We'll auto-detect it.",
    )
    if not uploaded_file:
        return [], None

    try:
        df = pd.read_csv(uploaded_file, dtype=str)
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as e:
        st.error(f"Error reading CSV: {e}")
        return [], None
    except Exception as e:  # noqa: BLE001 — surface to UI without crashing
        st.error(f"Unexpected error reading CSV: {e}")
        return [], None

    gtin_col = _detect_gtin_column(df)
    if gtin_col is None:
        gtin_col = st.selectbox(
            "Which column contains GTINs?", df.columns.tolist(),
        )
    else:
        st.info(f"Auto-detected GTIN column: **{gtin_col}**")

    parsed_lines = df[gtin_col].dropna().tolist()
    if len(parsed_lines) > MAX_GTINS_PER_BATCH:
        st.error(
            f"Too many GTINs ({len(parsed_lines):,}). The current "
            f"limit is {MAX_GTINS_PER_BATCH:,} per batch — please "
            "split your file and validate it in chunks."
        )
        return [], df

    st.success(f"Loaded {len(parsed_lines)} GTINs from '{gtin_col}'")
    return parsed_lines, df


_GTIN_COL_HINTS = ("gtin", "upc", "ean", "barcode", "code")


def _detect_gtin_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if any(hint in col.lower() for hint in _GTIN_COL_HINTS):
            return col
    return None


# -- sample data -------------------------------------------------------------

def _sample_data_input() -> tuple[list[str], pd.DataFrame]:
    st.markdown(SAMPLE_DESCRIPTION)
    sample_df = pd.read_csv(StringIO(SAMPLE_DATA.strip()), dtype=str)
    st.dataframe(sample_df, use_container_width=True, height=300)
    gtins = sample_df["GTIN"].dropna().tolist()
    st.info(f"Loaded {len(gtins)} sample GTINs")
    return gtins, sample_df
