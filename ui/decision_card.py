"""Présentation Streamlit d'une recommandation prudente expliquée."""

import streamlit as st


QUALITE_LABEL = "Couverture et cohérence techniques"
QUALITE_EXPLICATION = (
    "Mesure la complétude et la cohérence des critères analysés, "
    "pas une probabilité de gain."
)
FACTEURS_FAVORABLES_VIDES = (
    "Aucun facteur favorable identifié dans les critères analysés."
)
FACTEURS_DEFAVORABLES_VIDES = (
    "Aucun facteur défavorable identifié dans les critères analysés."
)
DECISION_FINALE = "Décision finale : elle vous appartient."


def construire_modele_affichage(decision: dict) -> dict:
    """Construit sans effet de bord le modèle JSON natif de la carte."""
    facteurs_favorables = list(decision.get("facteurs_favorables", []))
    facteurs_defavorables = list(decision.get("facteurs_defavorables", []))
    facteurs_neutres = list(decision.get("facteurs_neutres", []))
    risques = list(decision.get("risques", []))
    donnees_manquantes = list(decision.get("donnees_manquantes", []))

    if not facteurs_favorables:
        facteurs_favorables = [FACTEURS_FAVORABLES_VIDES]
    if not facteurs_defavorables:
        facteurs_defavorables = [FACTEURS_DEFAVORABLES_VIDES]

    return {
        "titre": "🧭 Recommandation prudente",
        "recommandation_label": "Recommandation prudente",
        "recommandation": str(decision.get("recommandation", "")),
        "qualite_label": QUALITE_LABEL,
        "qualite": f"{decision.get('confiance', 0)}/100",
        "qualite_explication": QUALITE_EXPLICATION,
        "resume": str(decision.get("resume", "")),
        "facteurs_favorables_titre": "Facteurs favorables",
        "facteurs_favorables": facteurs_favorables,
        "facteurs_defavorables_titre": "Facteurs défavorables",
        "facteurs_defavorables": facteurs_defavorables,
        "facteurs_neutres_titre": "Facteurs neutres",
        "facteurs_neutres": facteurs_neutres,
        "risques_titre": "Risques et limites",
        "risques": risques,
        "donnees_manquantes_titre": "Données manquantes",
        "donnees_manquantes": donnees_manquantes,
        "action_titre": "Action suggérée",
        "action_suggeree": str(decision.get("action_suggeree", "")),
        "decision_finale": DECISION_FINALE,
    }


def _afficher_liste(elements):
    for element in elements:
        st.write(f"• {element}")


def afficher_decision_prudente(decision: dict) -> None:
    """Affiche toutes les dimensions de la recommandation sans en masquer les risques."""
    modele = construire_modele_affichage(decision)

    st.subheader(modele["titre"])
    col1, col2 = st.columns(2)
    col1.metric(modele["recommandation_label"], modele["recommandation"])
    col2.metric(modele["qualite_label"], modele["qualite"])
    st.caption(modele["qualite_explication"])
    st.write(modele["resume"])

    st.markdown(f"**{modele['facteurs_favorables_titre']}**")
    _afficher_liste(modele["facteurs_favorables"])

    st.markdown(f"**{modele['facteurs_defavorables_titre']}**")
    _afficher_liste(modele["facteurs_defavorables"])

    if modele["facteurs_neutres"]:
        st.markdown(f"**{modele['facteurs_neutres_titre']}**")
        _afficher_liste(modele["facteurs_neutres"])

    st.markdown(f"**{modele['risques_titre']}**")
    _afficher_liste(modele["risques"])

    if modele["donnees_manquantes"]:
        st.markdown(f"**{modele['donnees_manquantes_titre']}**")
        _afficher_liste(modele["donnees_manquantes"])

    st.markdown(f"**{modele['action_titre']}**")
    st.write(modele["action_suggeree"])
    st.caption(modele["decision_finale"])
