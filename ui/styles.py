"""CSS injection for the Streamlit app."""

from pathlib import Path

import streamlit as st

_STYLES_PATH = Path(__file__).with_name("styles.css")


def inject_css() -> None:
    """Inject the application stylesheet exactly once per session.

    Streamlit re-runs the entire script on every interaction, so we
    guard with a session-state flag to avoid emitting the <style> tag
    repeatedly.
    """
    css = _STYLES_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
