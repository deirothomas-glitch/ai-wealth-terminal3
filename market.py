"""Page d'analyse technique détaillée."""

import plotly.graph_objects as go
import streamlit as st

from charts import create_candlestick_chart
from config import AVAILABLE_PERIODS
from core.alerts import construire_alertes
from core.decision import construire_decision
from core.risk import calculer_atr, construire_plan_risque
from indicators import bollinger_bands, ema, macd, rsi
from market_data import charger_donnees, dernier_prix, dernier_volume, variation_journaliere
from scoring import calculer_score
from ui.alert_card import afficher_alertes
from ui.decision_card import afficher_decision_prudente
from ui.risk_card import afficher_plan_risque


def afficher_marche():
    st.header("📈 Marchés")
    col1, col2 = st.columns(2)
    symbole = col1.text_input(
        "Symbole", "AAPL", key="market_symbole").upper().strip()
    periode = col2.selectbox("Période", AVAILABLE_PERIODS,
                             index=AVAILABLE_PERIODS.index("1y"), key="market_periode")
    historique = charger_donnees(symbole, periode)
    if historique is None:
        st.error("Impossible de récupérer les données.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cours", f"{dernier_prix(historique):.2f}")
    col2.metric("Variation", f"{variation_journaliere(historique):+.2f}%")
    col3.metric("Plus haut", f"{historique['High'].max():.2f}")
    col4.metric("Volume", f"{dernier_volume(historique):,}")

    figure = create_candlestick_chart(historique, symbole)
    for periode_ema, nom in [(20, "EMA 20"), (50, "EMA 50"), (200, "EMA 200")]:
        figure.add_scatter(x=historique.index, y=ema(
            historique, periode_ema), name=nom)
    bandes = bollinger_bands(historique)
    figure.add_scatter(
        x=historique.index, y=bandes["upper"], name="Bollinger haut", line=dict(dash="dot"))
    figure.add_scatter(
        x=historique.index, y=bandes["lower"], name="Bollinger bas", line=dict(dash="dot"))
    st.plotly_chart(figure, use_container_width=True)

    col1, col2 = st.columns(2)
    rsi_data = rsi(historique)
    figure_rsi = go.Figure(go.Scatter(
        x=historique.index, y=rsi_data, name="RSI"))
    figure_rsi.add_hline(y=70, line_dash="dot")
    figure_rsi.add_hline(y=30, line_dash="dot")
    figure_rsi.update_layout(template="plotly_dark", height=280, title="RSI")
    col1.plotly_chart(figure_rsi, use_container_width=True)
    macd_data = macd(historique)
    figure_macd = go.Figure()
    figure_macd.add_scatter(
        x=historique.index, y=macd_data["macd"], name="MACD")
    figure_macd.add_scatter(
        x=historique.index, y=macd_data["signal"], name="Signal")
    figure_macd.add_bar(x=historique.index,
                        y=macd_data["histogram"], name="Histogramme")
    figure_macd.update_layout(template="plotly_dark", height=280, title="MACD")
    col2.plotly_chart(figure_macd, use_container_width=True)

    resultat_score = calculer_score({}, historique)
    st.subheader("🧠 Synthèse technique")
    col1, col2 = st.columns(2)
    col1.metric("Score technique", f"{resultat_score['score']}/100")
    col2.metric("Signal technique", resultat_score["signal"])
    for raison in resultat_score["raisons"]:
        st.write(f"• {raison}")

    st.caption(
        "Le signal technique résume les indicateurs. La recommandation "
        "prudente tient compte de la couverture et de la cohérence des "
        "preuves disponibles."
    )
    decision = None
    try:
        decision = construire_decision(resultat_score)
        afficher_decision_prudente(decision)
        if (
            resultat_score["signal"] == "VENTE"
            and decision["recommandation"] == "Éviter"
        ):
            st.info(
                "« Éviter » signifie ne pas initier une position sur la base "
                "des données actuelles. Cela ne suppose pas que vous détenez "
                "l'actif."
            )
    except Exception:
        st.warning(
            "La recommandation prudente est indisponible. Le score et le "
            "signal techniques restent consultables."
        )

    plan_risque = None
    try:
        colonnes_atr = {"High", "Low", "Close"}
        if colonnes_atr.issubset(historique.columns):
            atr_actuel = calculer_atr(
                [float(valeur) for valeur in historique["High"].tolist()],
                [float(valeur) for valeur in historique["Low"].tolist()],
                [float(valeur) for valeur in historique["Close"].tolist()],
            )
            prix_entree_risque = float(historique["Close"].iloc[-1])
        else:
            atr_actuel = None
            prix_entree_risque = None
        plan_risque = construire_plan_risque(
            prix_entree=prix_entree_risque,
            atr=atr_actuel,
            capital_reference=None,
            risque_max_pct=None,
        )
        afficher_plan_risque(plan_risque)
    except Exception:
        st.warning(
            "Le plan de risque est temporairement indisponible. L’analyse "
            "technique et la décision prudente restent accessibles."
        )

    try:
        alertes = construire_alertes(resultat_score, decision, plan_risque)
        afficher_alertes(alertes)
    except Exception:
        st.warning(
            "Les alertes d’analyse sont temporairement indisponibles. Les "
            "autres fonctions restent accessibles."
        )
