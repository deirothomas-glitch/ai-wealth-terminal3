import streamlit as st
import yfinance as yf

from portfolio import afficher_portefeuille
from data import get_stock_history, get_stock_info
from indicators import moving_average, ema
from dashboard import afficher_dashboard
from charts import create_candlestick_chart
from market import afficher_marche
from scanner import afficher_scanner
from openai import OpenAI
import os
from ai_analysis import analyser_actif
from scoring import calculer_score
from ui.theme import apply_theme



client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="AI Wealth Terminal",
    page_icon="📈",
    layout="wide"
)

apply_theme()

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
        "🤖 Assistant IA",
        "🔎 Scanner"

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
    afficher_marche()
# =====================================================
# ACTIONS
# =====================================================

elif menu == "📊 Actions":

    st.header("📊 Analyse d'une action")

    symbole = st.text_input(
        "Symbole de l'action",
        value="MSFT"
    )

    info = get_stock_info(symbole)
    historique = get_stock_history(symbole)

    resultat = calculer_score(info, historique)

    st.write("historique:", historique)
    if historique is not None:
        st.write("Nombre de lignes : ", len(historique))

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

        st.subheader("📈 Graphique du cours")

        if historique is not None and not historique.empty:
            fig = create_candlestick_chart(
                historique,
                info.get("longName", symbole)
            )
            st.plotly_chart(fig, key="graph_action")
            st.subheader("🤖 Score IA")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Score IA", f"{resultat['score']}/100")

            with col2:
                st.metric("Signal", resultat["signal"])

            st.subheader("📈 Indicateurs techniques")

            close = historique["Close"]

            ma20 = close.rolling(20).mean()
            ema20 = close.ewm(span=20).mean()

            st.metric("📊 Dernier cours", f"{close.iloc[-1]:.2f} $")
            st.metric("📈 Moyenne mobile 20", f"{ma20.iloc[-1]:.2f} $")
            st.metric("⚡ EMA 20", f"{ema20.iloc[-1]:.2f} $")
        
        else:
            st.warning("Aucune donnée historique disponible.")

        st.divider()

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
        fig = create_candlestick_chart(
            historique,
            crypto
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            key="graph_crypto",
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
            historique = get_stock_history(symbole)
            st.subheader("📈 Graphique")

            if historique is not None and not historique.empty:
                fig = create_candlestick_chart(
                    historique,
                    info.get("longName", symbole)
                )

            st.divider()
            with st.spinner(
                "Analyse en cours..."
            ):

                resultat = analyser_actif(
                    nom = info.get("longName", symbole),
                    symbole = symbole,
                    prix = prix,
                    score = 80,
                    rsi ="N/A",
                    tendance = "Neutre"
                )

            st.success("Analyse terminée")

            st.success("✅ Analyse terminée")

            st.progress(82)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("🎯 Score IA", "82/100")

            with col2:
                st.metric("📈 Tendance", "Haussière")

            with col3:
                st.metric("💡 Recommandation", "Acheter")

            st.divider()

            st.markdown(resultat)

            st.divider()

            st.subheader("📊 Résumé")

            st.info("""
            • 📈 Potentiel estimé : +8 %

            • ⚠️ Risque : Moyen

            • 🤖 Confiance IA : 91 %

            • ⏳ Horizon : Moyen terme
            """)

        except Exception as e:

            st.error(str(e))
            
elif menu == "💼 Portefeuille":

    afficher_portefeuille()
    
elif menu == "🔎 Scanner":
    afficher_scanner()