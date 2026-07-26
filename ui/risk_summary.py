"""Résumé Streamlit léger d'un plan de risque indicatif."""

import math

import streamlit as st


TITRE = "🛡️ Résumé du risque"
AVERTISSEMENT = (
    "Scénario haussier hypothétique basé sur la volatilité historique. "
    "Les niveaux présentés sont indicatifs."
)
RAPPEL_PRUDENCE = (
    "Le stop-loss et l’objectif ne garantissent aucun résultat et peuvent "
    "être dépassés lors de gaps ou de mouvements rapides."
)
RESUME_INDISPONIBLE = (
    "Le résumé du risque est temporairement indisponible. Le Dashboard, "
    "les actualités et l’analyse IA restent accessibles."
)


def _format_nombre(valeur):
    if type(valeur) not in (int, float) or not math.isfinite(valeur):
        return None
    return f"{valeur:.8f}".rstrip("0").rstrip(".")


def afficher_resume_risque(plan: dict) -> None:
    """Affiche un résumé sans calculer ni modifier le plan reçu."""
    st.subheader(TITRE)
    st.caption(AVERTISSEMENT)

    if not isinstance(plan, dict) or plan.get("statut") == "indisponible":
        st.warning(RESUME_INDISPONIBLE)
        if isinstance(plan, dict):
            st.caption(plan.get("decision_finale_utilisateur", ""))
        return

    metriques = (
        ("ATR", plan.get("atr"), False),
        ("Stop-loss indicatif", plan.get("stop_loss"), False),
        ("Objectif indicatif", plan.get("objectif"), False),
        ("Ratio risque/rendement", plan.get("ratio_risque_rendement"), True),
    )
    for colonne, (label, valeur, est_ratio) in zip(st.columns(4), metriques):
        texte = _format_nombre(valeur)
        if texte is not None:
            colonne.metric(label, f"1 : {texte}" if est_ratio else texte)

    st.caption(RAPPEL_PRUDENCE)
    st.caption(plan.get("decision_finale_utilisateur", ""))
