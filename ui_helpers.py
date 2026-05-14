"""UI helper functions for the GTIN Validator Streamlit app."""

from pathlib import Path
import streamlit as st


def load_css():
    """Load external CSS from styles/app.css and inject into the page."""
    css_path = Path(__file__).parent / "styles" / "app.css"
    css = css_path.read_text()
    st.html(f"<style>{css}</style>")
