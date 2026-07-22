import streamlit as st


COLORS = {
    "background": "#0B1220",
    "card": "#172033",
    "primary": "#3B82F6",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text": "#F8FAFC",
    "secondary_text": "#94A3B8"
}


def apply_theme():
    """Applique le thème graphique AI Wealth Terminal."""

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-color: {COLORS["background"]};
        }}

        div[data-testid="stMetric"] {{
            background-color: {COLORS["card"]};
            padding: 15px;
            border-radius: 12px;
            border: 1px solid #2A3955;
        }}

        h1, h2, h3, h4 {{
            color: {COLORS["text"]};
        }}

        p {{
            color: {COLORS["secondary_text"]};
        }}

        </style>
        """,
        unsafe_allow_html=True
    )
