import streamlit as st
import yfinance as yf

from portfolio import afficher_portefeuille
from data import get_stock_history, get_stock_info
from indicators import moving_average, ema
from charts import create_candlestick
from ai_analysis import analyse_marche
from dashboard import afficher_dashboard

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="AI Wealth Terminal",
    page_icon="📈",
    layout="wide"
)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Choisissez une section",
    [
        "🏠 Accueil",
        "📈 Marchés",
        "📊 Actions",
        "₿ Cryptomonnaies",
        "💼 Portefeuille",
        "🤖 Assistant IA"
    ]
)


# =====================================================
# ACCUEIL
# =====================================================

if menu == "🏠 Accueil":
    afficher_dashboard()

# =====================================================
# MARCHÉS
# =====================================================

elif menu == "📈 Marchés":

    st.header("📈 Les marchés financiers")

    watchlist = [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "META",
        "GOOGL",
        "TSLA",
        "BTC-USD",
        "ETH-USD"
    ]

    symbole = st.sidebar.selectbox(
        "📋 Watchlist",
        watchlist
    )

    historique = get_stock_history(symbole)

    if historique.empty:
        st.error("Aucune donnée disponible.")
    else:

        # ============================
        # Statistiques
        # ============================

        dernier_prix = historique["Close"].iloc[-1]
        variation = historique["Close"].pct_change().iloc[-1] * 100
        plus_haut = historique["High"].max()
        plus_bas = historique["Low"].min()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "💲 Cours",
            f"{dernier_prix:.2f}"
        )

        col2.metric(
            "📈 Variation",
            f"{variation:.2f}%"
        )

        col3.metric(
            "⬆ Plus haut",
            f"{plus_haut:.2f}"
        )

        col4.metric(
            "⬇ Plus bas",
            f"{plus_bas:.2f}"
        )

        st.divider()

        # ============================
        # Graphique
        # ============================

        fig = create_candlestick(
            historique,
            symbole
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
# =====================================================
# ACTIONS
# =====================================================

elif menu == "📊 Actions":

    st.header("📊 Analyse d'une action")

    symbole = st.text_input(
        "Symbole de l'action",
        value="MSFT"
    )

    try:

        info = get_stock_info(symbole)

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Entreprise",
                info.get("longName", "Inconnue")
            )

            st.metric(
                "Cours actuel",
                info.get("currentPrice", "N/A")
            )

            st.metric(
                "Capitalisation",
                info.get("marketCap", "N/A")
            )

        with col2:
            st.metric(
                "Secteur",
                info.get("sector", "N/A")
            )

            st.metric(
                "Industrie",
                info.get("industry", "N/A")
            )

            st.metric(
                "Pays",
                info.get("country", "N/A")
            )

        st.divider()

        if st.button("🤖 Analyser avec l'IA"):

            prix = info.get("currentPrice", "N/A")

            with st.spinner("Analyse en cours..."):

                resultat = analyse_marche(
                    symbole,
                    prix
                )

            st.success("Analyse terminée")

            st.markdown(resultat)

    except Exception as e:

        st.error(e)
# =====================================================
# CRYPTOMONNAIES
# =====================================================

elif menu == "₿ Cryptomonnaies":

    st.header("₿ Marché des cryptomonnaies")

    crypto = st.selectbox(
        "Choisissez une cryptomonnaie",
        [
            "BTC-USD",
            "ETH-USD",
            "SOL-USD",
            "BNB-USD",
            "XRP-USD"
        ]
    )

    historique = get_stock_history(crypto)

    if historique.empty:
        st.error("Impossible de récupérer les données.")
    else:
        fig = create_candlestick(
            historique,
            crypto
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# =====================================================
# ASSISTANT IA
# =====================================================

elif menu == "🤖 Assistant IA":

    st.header("🤖 Assistant IA")

    symbole = st.text_input(
        "Symbole à analyser",
        value="AAPL"
    )

    if st.button("Lancer l'analyse"):

        try:

            info = get_stock_info(symbole)

            prix = info.get(
                "currentPrice",
                "N/A"
            )

            with st.spinner(
                "Analyse en cours..."
            ):

                resultat = analyse_marche(
                    symbole,
                    prix
                )

            st.success("Analyse terminée")

            st.markdown(resultat)

        except Exception as e:

            st.error(str(e))
            
elif menu == "💼 Portefeuille":

    afficher_portefeuille()
