"""Présentation Streamlit des alertes d'analyse."""

import streamlit as st


TITRE = "🚨 Alertes d’analyse"
AUCUNE_ALERTE = "Aucune alerte particulière détectée pour cette analyse."
RAPPEL_DECISION = "La décision finale appartient à l’utilisateur."


def afficher_alertes(alertes: list[dict]) -> None:
    """Affiche les alertes valides dans leur ordre d'entrée, sans mutation."""
    st.subheader(TITRE)
    if not isinstance(alertes, list) or not alertes:
        st.caption(AUCUNE_ALERTE)
        return

    affichee = False
    for alerte in alertes:
        if not isinstance(alerte, dict):
            continue
        titre = alerte.get("titre")
        message = alerte.get("message")
        niveau = alerte.get("niveau")
        categorie = alerte.get("categorie")
        if not isinstance(titre, str) or not isinstance(message, str):
            continue
        contenu = f"**{titre}** — {message}"
        if niveau == "information":
            st.info(contenu)
        elif niveau == "attention" and categorie in ("donnees", "risque"):
            st.error(contenu)
        else:
            st.warning(contenu)
        facteurs = alerte.get("facteurs")
        if isinstance(facteurs, list):
            for facteur in facteurs[:3]:
                if isinstance(facteur, str) and facteur.strip():
                    st.write(f"• {facteur.strip()}")
        action = alerte.get("action_suggeree")
        if isinstance(action, str) and action.strip():
            st.caption(f"Action suggérée : {action.strip()}")
        if alerte.get("decision_finale_utilisateur") is True:
            st.caption(RAPPEL_DECISION)
        affichee = True
    if not affichee:
        st.caption(AUCUNE_ALERTE)
