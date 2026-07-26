"""Scanner de la watchlist, déclenché manuellement pour limiter les appels marché."""

import pandas as pd
import streamlit as st

from ai_analysis import analyser_actif
from core.alerts import construire_alertes
from core.decision import construire_decision
from core.risk import construire_plan_risque
from core.strategy_profiles import obtenir_profils
from market_data import charger_donnees
from scanner_core import analyser_watchlist, generer_csv
from services.scanner_opportunities import classer_resultats_scanner
from ui.opportunity_table import afficher_table_opportunites
from scoring import calculer_score
from ui.alert_card import afficher_alertes
from ui.decision_card import afficher_decision_prudente
from ui.technical_summary import afficher_resume_technique
from watchlist import charger_watchlist


def scanner_marche(progress_callback=None, error_callback=None):
    """Orchestre les dépendances du moteur et retourne un DataFrame."""
    resultats = analyser_watchlist(
        charger_watchlist(),
        charger_donnees,
        calculer_score,
        progress_callback=progress_callback,
        error_callback=error_callback,
    )
    return pd.DataFrame(resultats)


def afficher_scanner():
    st.header("🔎 Scanner IA")
    profils = obtenir_profils()
    profil = st.selectbox("Profil de stratégie", profils, format_func=lambda p: p["nom"], key="scanner_profil")
    if st.button("🚀 Lancer le scanner", use_container_width=True):
        progression = st.progress(0)
        erreurs = []

        def mettre_a_jour_progression(traites, total):
            progression.progress(traites / max(total, 1))

        def noter_erreur(categorie, symbole):
            erreurs.append((categorie, symbole))

        with st.spinner("Analyse de la watchlist..."):
            st.session_state.scanner_resultats = scanner_marche(
                progress_callback=mettre_a_jour_progression,
                error_callback=noter_erreur,
            )
        progression.empty()
        st.session_state.scanner_nombre_erreurs = len(erreurs)
        st.session_state.scanner_opportunites = classer_resultats_scanner(st.session_state.scanner_resultats.to_dict(orient="records"), profil)
        st.session_state.opportunites_classees = st.session_state.scanner_opportunites
    resultat = st.session_state.get("scanner_resultats")
    if resultat is None:
        st.info("Cliquez sur « Lancer le scanner ».")
        return
    nombre_erreurs = st.session_state.get("scanner_nombre_erreurs", 0)
    if nombre_erreurs:
        st.warning(f"{nombre_erreurs} actif(s) n'ont pas pu être analysé(s).")
    if resultat.empty:
        st.warning("Aucun actif n'a pu être analysé.")
        return

    opportunites = st.session_state.get("scanner_opportunites", [])
    if opportunites:
        c1, c2, c3, c4 = st.columns(4)
        confiance = c1.selectbox("Niveau de confiance", ["Toutes", "elevee", "moderee", "faible"], key="filtre_confiance")
        qualite = c2.selectbox("Qualité", ["Toutes", "bon", "partiel", "insuffisant"], key="filtre_qualite")
        decision_filtre = c3.selectbox("Recommandation prudente", ["Toutes"] + sorted({x["decision"] for x in opportunites}), key="filtre_decision")
        maximum = c4.number_input("Résultats maximum", min_value=1, max_value=100, value=min(20, len(opportunites)))
        classement = [x for x in opportunites if (confiance == "Toutes" or x["confiance"] == confiance) and (qualite == "Toutes" or x["qualite_donnees"] == qualite) and (decision_filtre == "Toutes" or x["decision"] == decision_filtre)][:int(maximum)]
        st.subheader("Classement des opportunités")
        afficher_table_opportunites(st, classement)
    col1, col2 = st.columns(2)
    minimum = col1.slider("Score minimum", 0, 100, 60, 5)
    recherche = col2.text_input("Recherche").upper().strip()
    filtre = resultat[resultat["Score"] >= minimum]
    if recherche:
        filtre = filtre[filtre["Actif"].str.contains(
            recherche, case=False, na=False)]
    if filtre.empty:
        st.info("Aucun actif ne correspond à ces filtres.")
        return
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Actifs", len(filtre))
    col2.metric("📈 Score moyen", round(filtre["Score"].mean(), 1))
    meilleur = filtre.iloc[0]
    col3.metric("🥇 Meilleur", meilleur["Actif"])
    col4.metric("⭐ Score", meilleur["Score"])

    colonnes_masquees = ["Raisons", "Historique", "Ventilation"]
    st.dataframe(
        filtre.drop(columns=[
            colonne for colonne in colonnes_masquees if colonne in filtre.columns
        ]),
        use_container_width=True,
    )
    meilleur = filtre.iloc[0]
    resultat_score_selectionne = {
        "score": int(meilleur["Score"]),
        "signal": str(meilleur["Signal"]),
        "raisons": list(meilleur["Raisons"]),
        "ventilation": list(meilleur["Ventilation"]),
    }
    st.subheader(
        f"🔎 Actif en tête du classement technique : {meilleur['Actif']}"
    )
    afficher_resume_technique(resultat_score_selectionne)
    st.caption(
        "Le signal technique résume les indicateurs. La recommandation "
        "prudente tient compte de la couverture et de la cohérence des "
        "preuves disponibles."
    )
    decision = None
    try:
        decision = construire_decision(resultat_score_selectionne)
        afficher_decision_prudente(decision)
        if (resultat_score_selectionne["signal"] == "VENTE"
                and decision["recommandation"] == "Éviter"):
            st.info(
                "« Éviter » signifie ne pas initier une position sur la base "
                "des données actuelles. Cela ne suppose pas que vous détenez "
                "l’actif."
            )
    except Exception:
        st.warning(
            "La recommandation prudente est temporairement indisponible. Le "
            "classement technique, l’analyse IA et l’export restent "
            "accessibles."
        )

    try:
        plan_risque = construire_plan_risque(None, None, None, None)
        alertes = construire_alertes(
            resultat_score_selectionne, decision, plan_risque
        )
        afficher_alertes(alertes)
    except Exception:
        st.warning(
            "Les alertes d’analyse sont temporairement indisponibles. Les "
            "autres fonctions restent accessibles."
        )

    st.subheader("🤖 Analyse complémentaire par l’IA")
    st.caption(
        "L’analyse IA apporte un commentaire complémentaire. Elle ne remplace "
        "pas la recommandation déterministe ni votre décision."
    )
    if st.button("🤖 Analyser la sélection", key="scanner_ia"):
        with st.spinner("Analyse IA en cours..."):
            st.markdown(analyser_actif(
                meilleur["Actif"], meilleur["Actif"], meilleur["Prix"],
                meilleur["Score"], meilleur["RSI"], meilleur["Signal"],
            ))
    csv = generer_csv(filtre.to_dict(orient="records"))
    st.download_button(
        "📥 Télécharger les résultats (CSV)", csv,
        "scanner_ai_wealth_terminal.csv", "text/csv",
    )
