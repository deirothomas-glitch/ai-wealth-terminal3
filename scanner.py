"""Scanner de la watchlist, déclenché manuellement pour limiter les appels marché."""

import math

import pandas as pd
import streamlit as st

from ai_analysis import analyser_actif
from core.decision import construire_decision
from core.risk import construire_plan_risque
from core.opportunity_sheet import construire_fiche_opportunite
from core.scenario_engine import construire_scenarios_depuis_contrats
from core.strategy_profiles import obtenir_profils
from market_data import charger_donnees
from scanner_core import analyser_watchlist, generer_csv
from services.scanner_opportunities import classer_resultats_scanner
from ui.opportunity_table import afficher_table_opportunites
from ui.opportunity_sheet import afficher_fiche_opportunite
from scoring import calculer_score
from ui.scenario_card import afficher_scenarios
from ui.risk_card import afficher_plan_risque
from ui.news_card import afficher_actualites_normalisees
from watchlist import ajouter_actif, charger_watchlist


def _valeur_numerique_session(valeur, maximum=None):
    """Retourne une valeur de widget sûre sans fabriquer de donnée métier."""
    if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
        return 0.0
    nombre = float(valeur)
    if not math.isfinite(nombre) or nombre < 0:
        return 0.0
    if maximum is not None and nombre > maximum:
        return 0.0
    return nombre


def _champs_fiables_position(symbole, plan_risque):
    """Prépare uniquement les valeurs validées par le moteur de risque."""
    plan = plan_risque if isinstance(plan_risque, dict) else {}
    resultat = {"symbole": symbole}
    for source, destination in (
        ("prix_entree", "prix_entree"),
        ("stop_loss", "stop_loss"),
        ("objectif", "objectif"),
        ("taille_position", "taille_position"),
    ):
        valeur = plan.get(source)
        if isinstance(valeur, (int, float)) and not isinstance(valeur, bool) and math.isfinite(valeur) and valeur > 0:
            resultat[destination] = float(valeur)
    return resultat


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
    if not opportunites:
        st.warning("Aucune opportunité exploitable n’est disponible dans ce scan.")
        return

    c1, c2, c3, c4 = st.columns(4)
    confiance = c1.selectbox("Niveau de confiance", ["Toutes", "elevee", "moderee", "faible"], key="filtre_confiance")
    qualite = c2.selectbox("Qualité", ["Toutes", "bon", "partiel", "insuffisant"], key="filtre_qualite")
    decision_filtre = c3.selectbox("Recommandation prudente", ["Toutes"] + sorted({x["decision"] for x in opportunites}), key="filtre_decision")
    maximum = c4.number_input("Résultats maximum", min_value=1, max_value=100, value=min(20, len(opportunites)))
    classement = [
        x for x in opportunites
        if (confiance == "Toutes" or x["confiance"] == confiance)
        and (qualite == "Toutes" or x["qualite_donnees"] == qualite)
        and (decision_filtre == "Toutes" or x["decision"] == decision_filtre)
    ][:int(maximum)]
    st.subheader("Classement des opportunités")
    afficher_table_opportunites(st, classement)
    if not classement:
        st.info("Aucun actif ne correspond à ces filtres.")
        return

    identifiants = [
        f"{x.get('rang', index + 1)}|{x.get('categorie', '')}|{x.get('symbole', '')}"
        for index, x in enumerate(classement)
    ]
    selection_precedente = st.session_state.get("selected_asset")
    index_selection = next(
        (index for index, x in enumerate(classement) if x.get("symbole") == selection_precedente),
        0,
    )
    if st.session_state.get("scanner_actif_selectionne") not in identifiants:
        st.session_state.scanner_actif_selectionne = identifiants[index_selection]
    identifiant_selectionne = st.selectbox(
        "Actif à approfondir",
        identifiants,
        format_func=lambda identifiant: (
            f"#{classement[identifiants.index(identifiant)].get('rang', '—')} · "
            f"{classement[identifiants.index(identifiant)].get('symbole', '—')} — "
            f"{classement[identifiants.index(identifiant)].get('categorie', 'Indisponible')}"
        ),
        key="scanner_actif_selectionne",
    )
    index_actif = identifiants.index(identifiant_selectionne)
    opportunite_selectionnee = classement[index_actif]
    symbole_selectionne = opportunite_selectionnee.get("symbole", "")
    st.session_state.selected_asset = symbole_selectionne
    lignes_scanner = resultat.to_dict(orient="records")
    correspondances = [
        x for x in lignes_scanner
        if x.get("Actif") == symbole_selectionne
        and str(x.get("Catégorie", "")) == str(opportunite_selectionnee.get("categorie", ""))
    ]
    ligne_selectionnee = correspondances[0] if correspondances else next(
        (x for x in lignes_scanner if x.get("Actif") == symbole_selectionne),
        {},
    )
    score_selectionne = {
        "score": ligne_selectionnee.get("Score"),
        "signal": ligne_selectionnee.get("Signal"),
        "raisons": list(ligne_selectionnee.get("Raisons", [])),
        "ventilation": list(ligne_selectionnee.get("Ventilation", [])),
    }
    decision = construire_decision(score_selectionne)
    capital = st.session_state.get("parcours_capital_reference")
    risque_pct = st.session_state.get("parcours_risque_max_pct")
    plan_risque = construire_plan_risque(
        ligne_selectionnee.get("Prix"),
        ligne_selectionnee.get("ATR"),
        capital,
        risque_pct,
    )
    scenarios = construire_scenarios_depuis_contrats(
        decision,
        plan_risque,
        {"qualite_donnees": opportunite_selectionnee.get("qualite_donnees")},
        horizon=profil.get("nom", "swing"),
    )
    actualites_par_actif = st.session_state.setdefault("actualites_par_actif", {})
    actualites_selectionnees = actualites_par_actif.get(symbole_selectionne, []) if isinstance(actualites_par_actif, dict) else []
    fiche = construire_fiche_opportunite(
        ligne_selectionnee,
        opportunite_selectionnee,
        decision,
        plan_risque,
        scenarios,
        actualites_selectionnees,
    )
    afficher_fiche_opportunite(
        st,
        fiche,
        afficher_scenarios_fn=afficher_scenarios,
        afficher_actualites_fn=afficher_actualites_normalisees,
    )
    st.subheader("9. Analyse IA uniquement sur demande")
    cle_ia = f"fiche_ia_{symbole_selectionne}"
    if cle_ia in st.session_state:
        st.markdown(st.session_state[cle_ia])
    if st.button("🤖 Analyser cette fiche avec l’IA", key="fiche_ia"):
        try:
            with st.spinner("Analyse IA en cours..."):
                st.session_state[cle_ia] = analyser_actif(
                    symbole_selectionne,
                    symbole_selectionne,
                    ligne_selectionnee.get("Prix"),
                    ligne_selectionnee.get("Score"),
                    ligne_selectionnee.get("RSI"),
                    ligne_selectionnee.get("Signal"),
                )
            st.rerun()
        except Exception:
            st.warning(
                "L’analyse IA est temporairement indisponible. La fiche "
                "déterministe et le plan de risque restent accessibles."
            )

    st.subheader("10. Plan de risque")
    st.caption("Ces paramètres personnels restent dans la session et ne déclenchent aucun ordre.")
    c1, c2 = st.columns(2)
    st.session_state.parcours_capital_reference = _valeur_numerique_session(
        st.session_state.get("parcours_capital_reference")
    )
    st.session_state.parcours_risque_max_pct = _valeur_numerique_session(
        st.session_state.get("parcours_risque_max_pct"), maximum=100.0
    )
    capital_saisi = c1.number_input(
        "Capital de référence",
        min_value=0.0,
        key="parcours_capital_reference",
    )
    risque_saisi = c2.number_input(
        "Risque maximal par position (%)",
        min_value=0.0,
        max_value=100.0,
        key="parcours_risque_max_pct",
    )
    plan_risque = construire_plan_risque(
        ligne_selectionnee.get("Prix"),
        ligne_selectionnee.get("ATR"),
        capital_saisi or None,
        risque_saisi or None,
    )
    afficher_plan_risque(plan_risque)

    st.subheader("11. Décision et prochaines actions")
    st.caption("Aucune action ne passe d’ordre. Vous pouvez aussi décider de ne rien faire.")
    actions = st.columns(4)
    if actions[0].button("👁️ Surveiller", key="fiche_surveiller", use_container_width=True):
        try:
            categorie = str(ligne_selectionnee.get("Catégorie", "Autre"))
            ajouter_actif(categorie, symbole_selectionne)
            st.success("Actif ajouté à la watchlist.")
        except Exception:
            st.warning("La watchlist n’a pas pu être mise à jour.")
    if actions[1].button("🧮 Préparer une position", key="fiche_preparer", use_container_width=True):
        st.session_state.position_preparee = _champs_fiables_position(
            symbole_selectionne, plan_risque
        )
        st.success("Plan préparé dans cette session. Vérifiez chaque valeur avant de poursuivre.")

    def ouvrir_portefeuille():
        st.session_state.portfolio_prefill = {
            **_champs_fiables_position(symbole_selectionne, plan_risque),
            "nom": symbole_selectionne,
            "type_actif": (
                "crypto" if "crypto" in str(ligne_selectionnee.get("Catégorie", "")).casefold()
                else ("ETF" if "etf" in str(ligne_selectionnee.get("Catégorie", "")).casefold() else "action")
            ),
        }
        st.session_state.navigation = "💼 Portefeuille"

    actions[2].button(
        "➕ Ajouter au portefeuille",
        key="fiche_portefeuille",
        use_container_width=True,
        on_click=ouvrir_portefeuille,
        disabled=plan_risque.get("prix_entree") is None,
        help=(
            "Un prix valide est nécessaire pour préremplir le portefeuille."
            if plan_risque.get("prix_entree") is None else None
        ),
    )
    documenter = actions[3].button("📝 Documenter", key="fiche_documenter", use_container_width=True)
    if documenter or st.session_state.get("fiche_documentation_ouverte"):
        st.session_state.fiche_documentation_ouverte = True
        with st.form("fiche_note_decision"):
            note = st.text_area(
                "Note de décision",
                placeholder="Pourquoi agir, attendre ou ne rien faire ? Qu’est-ce qui invaliderait votre analyse ?",
            )
            enregistrer_note = st.form_submit_button("Conserver dans cette session")
        if enregistrer_note:
            notes = st.session_state.setdefault("decision_notes", [])
            notes.append({
                "symbole": symbole_selectionne,
                "decision": decision.get("recommandation"),
                "note": note.strip(),
                "date_donnees": ligne_selectionnee.get("Date données"),
            })
            st.success("Décision documentée dans cette session.")

    with st.expander("Résultats techniques et export"):
        colonnes_masquees = ["Raisons", "Historique", "Ventilation", "ATR"]
        st.dataframe(
            resultat.drop(columns=[x for x in colonnes_masquees if x in resultat.columns]),
            use_container_width=True,
            hide_index=True,
        )
        csv = generer_csv(resultat.to_dict(orient="records"))
        st.download_button(
            "📥 Télécharger les résultats (CSV)",
            csv,
            "scanner_ai_wealth_terminal.csv",
            "text/csv",
        )
