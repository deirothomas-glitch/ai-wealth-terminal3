"""Thème visuel partagé par toutes les pages Streamlit."""

import streamlit as st


COLORS = {
    "background": "#08111F",
    "surface": "#101C2F",
    "card": "#142238",
    "card_hover": "#182A45",
    "border": "#263A57",
    "primary": "#5B8CFF",
    "primary_soft": "#1A315A",
    "success": "#2DD4A8",
    "warning": "#F6B84A",
    "danger": "#F87171",
    "text": "#F4F7FB",
    "secondary_text": "#A6B5CA",
}


def apply_theme():
    """Applique une identité visuelle cohérente sans modifier le métier."""
    st.markdown(
        f"""
        <style>
        :root {{
            --awt-bg: {COLORS['background']};
            --awt-surface: {COLORS['surface']};
            --awt-card: {COLORS['card']};
            --awt-border: {COLORS['border']};
            --awt-primary: {COLORS['primary']};
            --awt-text: {COLORS['text']};
            --awt-muted: {COLORS['secondary_text']};
        }}
        .stApp {{ background: radial-gradient(circle at 85% 0%, #102445 0, var(--awt-bg) 34%); }}
        .block-container {{ max-width: 1480px; padding-top: 2rem; padding-bottom: 4rem; }}
        [data-testid="stSidebar"] {{ background: #0B1627; border-right: 1px solid var(--awt-border); }}
        [data-testid="stSidebar"] .block-container {{ padding-top: 1.5rem; }}
        h1 {{ font-size: clamp(1.75rem, 3vw, 2.35rem) !important; letter-spacing: -0.035em; margin-bottom: .25rem !important; }}
        h2 {{ font-size: 1.45rem !important; letter-spacing: -0.02em; margin-top: 1.75rem !important; }}
        h3 {{ font-size: 1.08rem !important; margin-top: 1.1rem !important; }}
        h1, h2, h3, h4, label {{ color: var(--awt-text) !important; }}
        p, [data-testid="stCaptionContainer"] {{ color: var(--awt-muted); }}
        div[data-testid="stMetric"] {{
            min-height: 112px; padding: 1rem 1.1rem; border-radius: 16px;
            border: 1px solid var(--awt-border); background: linear-gradient(145deg, var(--awt-card), #101C30);
            box-shadow: 0 10px 30px rgba(0, 0, 0, .14);
        }}
        div[data-testid="stMetric"] label {{ color: var(--awt-muted) !important; font-size: .82rem !important; }}
        div[data-testid="stMetricValue"] {{ color: var(--awt-text); font-weight: 700; letter-spacing: -.02em; }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: var(--awt-border) !important; border-radius: 16px !important;
            background: rgba(20, 34, 56, .72); box-shadow: 0 10px 28px rgba(0, 0, 0, .12);
        }}
        .stButton > button, .stDownloadButton > button {{
            min-height: 2.7rem; border-radius: 10px; border: 1px solid #36527A;
            font-weight: 650; transition: transform .15s ease, border-color .15s ease, background .15s ease;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-1px); border-color: var(--awt-primary); color: white;
        }}
        .stButton > button[kind="primary"] {{ background: var(--awt-primary); border-color: var(--awt-primary); }}
        [data-testid="stDataFrame"] {{ border: 1px solid var(--awt-border); border-radius: 14px; overflow: hidden; }}
        [data-baseweb="input"], [data-baseweb="select"] > div, textarea {{ border-radius: 10px !important; }}
        [data-testid="stAlert"] {{ border-radius: 12px; border: 1px solid var(--awt-border); }}
        hr {{ border-color: var(--awt-border) !important; margin: 1.8rem 0 !important; }}
        .awt-card {{
            padding: 1rem 1.1rem; margin: .55rem 0 1rem; border-radius: 14px;
            border: 1px solid var(--awt-border); background: rgba(20, 34, 56, .82);
        }}
        .awt-card:hover {{ background: {COLORS['card_hover']}; }}
        .awt-card-title {{ color: var(--awt-text); font-size: 1rem; font-weight: 700; margin-bottom: .45rem; }}
        .awt-meta {{ color: var(--awt-muted); font-size: .8rem; line-height: 1.55; }}
        .awt-badge {{
            display: inline-block; padding: .2rem .55rem; margin: 0 .3rem .3rem 0;
            border-radius: 999px; border: 1px solid var(--awt-border); background: #172944;
            color: #DCE7F7; font-size: .72rem; font-weight: 700; letter-spacing: .01em;
        }}
        .awt-badge--good {{ color: #91F2D6; border-color: #256D60; background: #123B36; }}
        .awt-badge--warn {{ color: #FFD58A; border-color: #765721; background: #3C2D13; }}
        .awt-badge--bad {{ color: #FFB0B0; border-color: #7C343B; background: #401D25; }}
        .awt-link a {{ color: #8FB2FF !important; font-weight: 700; text-decoration: none; }}
        .awt-link a:hover {{ text-decoration: underline; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
