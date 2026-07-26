"""Point d'entrée de l'AI Wealth Terminal."""

import streamlit as st

from ai_analysis import analyser_actif
from charts import create_candlestick_chart
from config import APP_NAME
from core.alerts import construire_alertes
from core.decision import construire_decision
from core.risk import calculer_atr, construire_plan_risque
from core.scenario_engine import construire_scenarios_depuis_contrats
from core.analysis_context import construire_contexte_analyse
from dashboard import afficher_dashboard
from pages.assistant_page import afficher_assistant
from pages.news_page import afficher_page_actualites
from indicators import rsi
from market import afficher_marche
from market_data import charger_donnees, dernier_prix, recuperer_infos
from portfolio import afficher_portefeuille
from pages.strategies import afficher_strategies
from scanner import afficher_scanner
from scoring import calculer_score
from ui.alert_card import afficher_alertes
from ui.decision_card import afficher_decision_prudente
from ui.risk_card import afficher_plan_risque
from ui.technical_summary import afficher_resume_technique
from ui.scenario_card import afficher_scenarios
from services.news_aggregator import agreger_actualites
from services.news_sources import YahooNewsSource
from ui.news_card import afficher_actualites_normalisees
from ui.news_sentiment_card import afficher_sentiment_actualites
from ui.theme import apply_theme


st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide")
apply_theme()


def _afficher_scenarios_actif(decision, plan_risque):
    """Affiche les scénarios déterministes sans fragiliser l'analyse principale."""
    try:
        scenarios = construire_scenarios_depuis_contrats(
            decision, plan_risque, horizon="swing"
        )
        afficher_scenarios(scenarios)
    except Exception:
        st.warning(
            "L’analyse multi-scénarios est temporairement indisponible. "
            "Les autres éléments restent accessibles."
        )


def afficher_analyse_actif(titre, valeur_defaut):
    st.header(titre)
    cle_symbole = f"analyse_{valeur_defaut}"
    session_disponible = hasattr(st, "session_state")
    session = st.session_state if session_disponible else {}
    selection_parcours = session.get("selected_asset")
    marqueur = f"{cle_symbole}_selection_parcours"
    if isinstance(selection_parcours, str) and selection_parcours and session.get(marqueur) != selection_parcours:
        session[cle_symbole] = selection_parcours
        session[marqueur] = selection_parcours
    if session_disponible:
        session.setdefault(cle_symbole, valeur_defaut)
        symbole = st.text_input("Symbole", key=cle_symbole).upper().strip()
    else:
        symbole = st.text_input("Symbole", valeur_defaut, key=cle_symbole).upper().strip()
    historique = charger_donnees(symbole, "1y")
    if historique is None:
        st.warning("Aucune donnée disponible pour ce symbole.")
        return
    info = recuperer_infos(symbole)
    resultat_score = calculer_score(info, historique)
    col1, col2 = st.columns(2)
    col1.metric("Actif", info.get("longName", symbole))
    col2.metric("Cours actuel", f"{dernier_prix(historique):.2f}")
    st.plotly_chart(create_candlestick_chart(historique, info.get(
        "longName", symbole)), use_container_width=True)
    afficher_resume_technique(resultat_score)
    st.caption(
        "Le signal technique résume les indicateurs. La recommandation "
        "prudente tient compte de la couverture et de la cohérence des "
        "preuves disponibles."
    )
    decision = None
    try:
        decision = construire_decision(resultat_score)
        afficher_decision_prudente(decision)
        if (resultat_score["signal"] == "VENTE"
                and decision["recommandation"] == "Éviter"):
            st.info(
                "« Éviter » signifie ne pas initier une position sur la base "
                "des données actuelles. Cela ne suppose pas que vous détenez "
                "l’actif."
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

    if "_afficher_scenarios_actif" in globals():
        _afficher_scenarios_actif(decision, plan_risque)

    cle_news = f"actualites_{valeur_defaut}_{symbole}"
    if session_disponible and st.button(
        "📰 Actualiser les actualités", key=f"news_{valeur_defaut}"
    ):
        st.session_state[cle_news], erreurs_news = agreger_actualites(
            [YahooNewsSource()], symbole, info.get("longName", symbole), limite=5
        )
        for erreur_news in erreurs_news:
            st.warning(erreur_news)
    actualites_actif = st.session_state.get(cle_news, []) if session_disponible else []
    if actualites_actif:
        st.subheader("📰 Actualités pertinentes")
        afficher_sentiment_actualites(actualites_actif[0].get("sentiment", {}))
        afficher_actualites_normalisees(actualites_actif, limite=5)

    st.subheader("🤖 Analyse complémentaire par l’IA")
    st.caption(
        "L’analyse IA apporte un commentaire complémentaire. Elle ne remplace "
        "pas la recommandation déterministe ni votre décision."
    )
    if st.button("🤖 Analyser avec GPT", key=f"ia_{valeur_defaut}"):
        rsi_actuel = float(
            rsi(historique).iloc[-1]) if len(historique) >= 14 else 50.0
        with st.spinner("Analyse IA en cours..."):
            analyse_kwargs = {}
            if session_disponible:
                contexte_ia = construire_contexte_analyse(
                    actif={"nom": info.get("longName", symbole), "symbole": symbole,
                           "prix": dernier_prix(historique)},
                    technique=resultat_score, decision=decision, risque=plan_risque,
                    actualites=actualites_actif,
                    sentiment_actualites=(actualites_actif[0].get("sentiment", {})
                                           if actualites_actif else {}),
                    limites=["Données de marché potentiellement différées."],
                )
                analyse_kwargs["contexte"] = contexte_ia
            st.markdown(analyser_actif(
                info.get("longName", symbole), symbole, dernier_prix(historique),
                resultat_score["score"], rsi_actuel, resultat_score["signal"],
                **analyse_kwargs,
            ))


st.sidebar.title("Navigation")
menu = st.sidebar.radio("Choisissez une section", [
    "🏠 Accueil", "📈 Marchés", "📊 Actions", "₿ Cryptomonnaies",
    "💼 Portefeuille", "🔎 Scanner", "🧭 Stratégies", "📰 Actualités",
    "🤖 Assistant IA",
], key="navigation")

if menu == "🏠 Accueil":
    afficher_dashboard()
elif menu == "📈 Marchés":
    afficher_marche()
elif menu == "📊 Actions":
    afficher_analyse_actif("📊 Analyse d'une action", "AAPL")
elif menu == "₿ Cryptomonnaies":
    afficher_analyse_actif("₿ Analyse d'une cryptomonnaie", "BTC-USD")
elif menu == "💼 Portefeuille":
    afficher_portefeuille()
elif menu == "🔎 Scanner":
    afficher_scanner()
elif menu == "🧭 Stratégies":
    afficher_strategies()
elif menu == "📰 Actualités":
    afficher_page_actualites()
elif menu == "🤖 Assistant IA":
    afficher_assistant()
