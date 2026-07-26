"""Page d'accueil du terminal."""

from datetime import date

import streamlit as st

from ai_analysis import analyser_actif
from charts import create_candlestick_chart
from config import APP_NAME, APP_VERSION, AVAILABLE_PERIODS
from core.alerts import construire_alertes
from core.analysis_context import construire_contexte_analyse
from core.daily_briefing import construire_briefing
from core.decision import construire_decision
from core.risk import calculer_atr, construire_plan_risque
from indicators import macd, rsi
from news import afficher_actualites
from market_data import charger_donnees, dernier_prix, dernier_volume, recuperer_cryptos, recuperer_indices, variation_journaliere
from scoring import calculer_score
from ui.alert_card import afficher_alertes
from ui.decision_card import afficher_decision_prudente
from ui.risk_summary import afficher_resume_risque
from ui.technical_summary import afficher_resume_technique
from ui.ai_analysis_card import afficher_analyse_ia
from ui.daily_briefing_card import afficher_briefing
from ui.news_card import afficher_actualites_normalisees
from services.ai_market_analysis import analyser_contexte_marche


def _cartes_marche(titre, elements):
    st.subheader(titre)
    if not elements:
        st.info("Données indisponibles.")
        return
    for colonne, element in zip(st.columns(min(len(elements), 4)), elements[:4]):
        colonne.metric(
            element["nom"], f"{element['prix']:,.2f}", f"{element['variation']:+.2f}%")


def afficher_dashboard():
    st.title(APP_NAME)
    st.caption(f"Version {APP_VERSION} · Tableau de bord de marché")
    if hasattr(st, "session_state"):
        positions_session = st.session_state.get("portfolio", [])
        opportunites_session = st.session_state.get("opportunites_classees", [])
        alertes_session = st.session_state.get("alertes_positions", [])
        actualites_session = st.session_state.get("actualites_marche", [])
        st.subheader("Vue d’ensemble")
        cartes = st.columns(4)
        cartes[0].metric("Positions suivies", len(positions_session) if isinstance(positions_session, list) else 0)
        cartes[1].metric("Opportunités", len(opportunites_session) if isinstance(opportunites_session, list) else 0)
        cartes[2].metric("Alertes importantes", len(alertes_session) if isinstance(alertes_session, list) else 0)
        cartes[3].metric("Actualités disponibles", len(actualites_session) if isinstance(actualites_session, list) else 0)
        st.caption("Synthèse construite à partir des données déjà chargées dans la session.")
    indices_marche = recuperer_indices()
    cryptos_marche = recuperer_cryptos()
    _cartes_marche("🌍 Marchés mondiaux", indices_marche)
    _cartes_marche("🪙 Cryptomonnaies", cryptos_marche)
    st.divider()
    if hasattr(st, "subheader"):
        st.subheader("🎯 Opportunités à surveiller")
        opportunites = st.session_state.get("opportunites_classees", [])
        if not opportunites:
            st.info("Lancez le Sca" "nner pour afficher les opportunités du dernier classement.")
        else:
            for opportunite in opportunites[:5]:
                raison = next(iter(opportunite.get("raisons_principales", [])), "Aucune raison disponible")
                vigilance = next(iter(opportunite.get("points_vigilance", [])), "Aucun point de vigilance majeur")
                score_global = opportunite.get("score_global")
                score_texte = "—" if score_global is None else f"{score_global:.1f}"
                st.markdown(f"**{opportunite['symbole']} · {opportunite['strategie']} · {score_texte}/100 · {opportunite['confiance']} · {opportunite['decision']}**  \n{raison}  \n_Vigilance : {vigilance}_")
    actualites_briefing = []
    if hasattr(st, "session_state"):
        actualites_briefing = st.session_state.get("actualites_marche", [])
        positions_briefing = st.session_state.get("alertes_positions", [])
        briefing = construire_briefing(
            indices=indices_marche + cryptos_marche,
            opportunites=st.session_state.get("opportunites_classees", []),
            positions=positions_briefing,
            actualites=actualites_briefing,
            qualite={"niveau": "partiel" if not actualites_briefing else "bon"},
            date_generation=date.today().isoformat(),
        )
        briefing_affichage = {**briefing, "opportunites_a_surveiller": []}
        afficher_briefing(briefing_affichage)
        if st.button("🤖 Générer la synthèse IA du briefing", key="briefing_ia"):
            with st.spinner("Synthèse du briefing en cours..."):
                contexte_briefing = construire_contexte_analyse(
                    marche={"briefing": briefing},
                    actualites=actualites_briefing,
                    limites=["Briefing construit à partir des données déjà disponibles."],
                )
                afficher_analyse_ia(analyser_contexte_marche(
                    contexte_briefing, "Résume les priorités du briefing du marché."
                ))
    st.divider()

    col1, col2 = st.columns(2)
    symbole = col1.text_input("Actif à suivre", "AAPL",
                              key="dashboard_symbole").upper().strip()
    periode = col2.selectbox("Période", AVAILABLE_PERIODS, index=AVAILABLE_PERIODS.index(
        "1y"), key="dashboard_periode")
    historique = charger_donnees(symbole, periode)
    if historique is None:
        st.warning("Aucune donnée disponible pour cet actif.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Dernier prix", f"{dernier_prix(historique):.2f}")
    col2.metric("Variation", f"{variation_journaliere(historique):+.2f}%")
    col3.metric("Volume", f"{dernier_volume(historique):,}")
    st.plotly_chart(create_candlestick_chart(
        historique, symbole), use_container_width=True)

    resultat_score = calculer_score({}, historique)
    rsi_actuel = float(
        rsi(historique).iloc[-1]) if len(historique) >= 14 else 50.0
    macd_data = macd(historique)
    afficher_resume_technique(resultat_score, afficher_raisons=False)
    st.metric("RSI", f"{rsi_actuel:.1f}")
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
        if not historique.empty and colonnes_atr.issubset(historique.columns):
            plus_hauts = [
                float(valeur) for valeur in historique["High"].tolist()
            ]
            plus_bas = [
                float(valeur) for valeur in historique["Low"].tolist()
            ]
            clotures = [
                float(valeur) for valeur in historique["Close"].tolist()
            ]
            prix_entree_risque = float(historique["Close"].iloc[-1])
            atr_actuel = calculer_atr(plus_hauts, plus_bas, clotures)
        else:
            prix_entree_risque = None
            atr_actuel = None
        plan_risque = construire_plan_risque(
            prix_entree=prix_entree_risque,
            atr=atr_actuel,
            capital_reference=None,
            risque_max_pct=None,
        )
        afficher_resume_risque(plan_risque)
    except Exception:
        st.warning(
            "Le résumé du risque est temporairement indisponible. Le "
            "Dashboard, les actualités et l’analyse IA restent accessibles."
        )


    try:
        alertes = construire_alertes(resultat_score, decision, plan_risque)
        afficher_alertes(alertes)
    except Exception:
        st.warning(
            "Les alertes d’analyse sont temporairement indisponibles. Les "
            "autres fonctions restent accessibles."
        )

    with st.expander("📰 Actualités", expanded=False):
        if hasattr(st, "session_state"):
            afficher_actualites_normalisees(actualites_briefing, limite=5)
        else:
            afficher_actualites(symbole)
    with st.expander("🤖 Analyse complémentaire par l’IA", expanded=False):
        st.caption(
            "L’analyse IA apporte un commentaire complémentaire. Elle ne "
            "remplace pas la recommandation déterministe ni votre décision."
        )
        if st.button("Générer l'analyse", key="dashboard_ia"):
            with st.spinner("Analyse en cours..."):
                st.markdown(analyser_actif(symbole, symbole, dernier_prix(
                    historique), resultat_score["score"], rsi_actuel,
                    resultat_score["signal"]))
