"""Présentation Streamlit d'un plan de risque indicatif."""

import streamlit as st


TITRE = "🛡️ Plan de risque indicatif"
AVERTISSEMENT = (
    "Scénario haussier hypothétique basé sur la volatilité historique. "
    "Ce plan ne constitue pas une recommandation d’achat."
)
PLAN_INDISPONIBLE = (
    "Le plan de risque est temporairement indisponible. L’analyse technique "
    "et la décision prudente restent accessibles."
)
TAILLE_INDISPONIBLE = (
    "La taille de position n’est pas calculée tant qu’un capital de référence "
    "et un risque maximal valides ne sont pas fournis."
)


def _format_nombre(valeur, decimales=8):
    texte = f"{valeur:.{decimales}f}"
    return texte.rstrip("0").rstrip(".")


def _afficher_risques_et_decision(plan):
    st.markdown("**Risques et limites**")
    for risque in plan.get("risques", []):
        st.write(f"• {risque}")
    st.caption(plan.get("decision_finale_utilisateur", ""))


def afficher_plan_risque(plan: dict) -> None:
    """Affiche sans calcul les valeurs déjà produites par le moteur de risque."""
    st.subheader(TITRE)
    st.caption(AVERTISSEMENT)

    if plan.get("statut") == "indisponible":
        st.warning(PLAN_INDISPONIBLE)
        _afficher_risques_et_decision(plan)
        return

    metriques = (
        ("Prix d’entrée de référence", plan.get("prix_entree"), 8, ""),
        ("ATR", plan.get("atr"), 8, ""),
        ("Stop-loss indicatif", plan.get("stop_loss"), 8, ""),
        ("Objectif indicatif", plan.get("objectif"), 8, ""),
        ("Risque par unité", plan.get("risque_par_unite"), 8, ""),
        ("Ratio risque/rendement", plan.get("ratio_risque_rendement"), 4, "ratio"),
    )
    for colonne, (label, valeur, decimales, suffixe) in zip(
        st.columns(3) + st.columns(3), metriques
    ):
        if valeur is not None:
            texte = _format_nombre(valeur, decimales)
            colonne.metric(label, f"1 : {texte}" if suffixe == "ratio" else texte)

    if plan.get("taille_position") is not None:
        taille = (
            ("Capital de référence", plan.get("capital_reference"), 2, " €"),
            ("Risque maximal", plan.get("risque_max_pct"), 4, " %"),
            ("Risque en euros", plan.get("risque_capital"), 2, " €"),
            ("Taille de position indicative", plan.get("taille_position"), 8, ""),
        )
        for colonne, (label, valeur, decimales, suffixe) in zip(
            st.columns(4), taille
        ):
            if valeur is not None:
                texte = (
                    f"{valeur:.2f}"
                    if suffixe == " €"
                    else _format_nombre(valeur, decimales)
                )
                colonne.metric(label, f"{texte}{suffixe}")
    else:
        st.info(TAILLE_INDISPONIBLE)

    _afficher_risques_et_decision(plan)
