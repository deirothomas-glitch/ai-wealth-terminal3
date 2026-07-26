"""Affichage d'une analyse IA structurée et validée."""
import streamlit as st
def afficher_analyse_ia(analyse):
    d=analyse if isinstance(analyse,dict) else {};st.subheader("🤖 Synthèse IA structurée")
    if not d or d.get("resume")=="Analyse IA indisponible.":st.warning("Analyse IA indisponible.")
    for label,key in (("Résumé","resume"),("Contexte de marché","contexte_marche"),("Lecture technique","lecture_technique"),("Lecture des actualités","lecture_actualites"),("Scénario favorable","scenario_favorable"),("Scénario défavorable","scenario_defavorable")):
        value=d.get(key)
        if isinstance(value,str) and value:st.markdown(f"**{label}**");st.write(value)
    for label,key in (("Confirmations","conditions_confirmation"),("Invalidations","conditions_invalidation"),("Risques principaux","risques_principaux"),("À surveiller","points_a_surveiller"),("Limites","limites")):
        values=d.get(key);
        if isinstance(values,list) and values:st.markdown(f"**{label}**");[st.write(f"• {x}") for x in values[:8] if isinstance(x,str)]
    st.caption(f"Confiance déclarée : {d.get('niveau_confiance','faible')}. La décision finale appartient à l’utilisateur.")
