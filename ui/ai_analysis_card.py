"""Affichage professionnel d'une analyse IA structurée et validée."""

import streamlit as st


def afficher_analyse_ia(analyse):
    donnees = analyse if isinstance(analyse, dict) else {}
    st.subheader("🤖 Synthèse IA structurée")
    if not donnees or donnees.get("resume") == "Analyse IA indisponible.":
        st.warning("Analyse IA indisponible.")
    confiance = donnees.get("niveau_confiance", "faible")
    limites = donnees.get("limites")
    st.metric("Confiance déclarée", str(confiance).capitalize())
    st.metric(
        "Couverture des données",
        "Partielle" if isinstance(limites, list) and limites else "Disponible",
    )
    if isinstance(limites, list) and limites:
        st.warning("Cette réponse repose sur des données partielles ou comporte des limites explicites.")
    for label, key in (
        ("Résumé", "resume"),
        ("Contexte de marché", "contexte_marche"),
        ("Lecture technique", "lecture_technique"),
        ("Lecture des actualités", "lecture_actualites"),
        ("Scénario favorable", "scenario_favorable"),
        ("Scénario défavorable", "scenario_defavorable"),
    ):
        valeur = donnees.get(key)
        if isinstance(valeur, str) and valeur:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.write(valeur)
    for label, key in (
        ("Confirmations", "conditions_confirmation"),
        ("Invalidations", "conditions_invalidation"),
        ("Risques principaux", "risques_principaux"),
        ("À surveiller", "points_a_surveiller"),
        ("Limites", "limites"),
    ):
        valeurs = donnees.get(key)
        if isinstance(valeurs, list) and valeurs:
            st.markdown(f"**{label}**")
            for valeur in valeurs[:8]:
                if isinstance(valeur, str):
                    st.write(f"• {valeur}")
    st.caption(
        f"Confiance déclarée : {confiance}. La décision finale appartient à l’utilisateur."
    )
