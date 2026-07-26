"""Façade historique de l'analyse IA structurée et validée."""
import os
import streamlit as st
from core.analysis_context import construire_contexte_analyse
from news import recuperer_actualites
from services.ai_market_analysis import analyser_contexte_marche

def _api_key():
    try:key=st.secrets.get("OPENAI_API_KEY")
    except Exception:key=None
    return key or os.getenv("OPENAI_API_KEY")

def _markdown(analyse):
    sections=[]
    for titre,cle in (("Résumé","resume"),("Contexte de marché","contexte_marche"),("Lecture technique","lecture_technique"),("Lecture des actualités","lecture_actualites"),("Scénario favorable","scenario_favorable"),("Scénario défavorable","scenario_defavorable")):
        value=analyse.get(cle)
        if value:sections.append(f"### {titre}\n{value}")
    for titre,cle in (("Risques principaux","risques_principaux"),("Points à surveiller","points_a_surveiller"),("Limites","limites")):
        values=analyse.get(cle,[])
        if values:sections.append(f"### {titre}\n"+"\n".join(f"- {x}" for x in values))
    sections.append("*La décision finale appartient à l’utilisateur.*")
    return "\n\n".join(sections)

def analyser_actif(nom,symbole,prix,score,rsi,tendance,contexte=None,question=None):
    cle=_api_key()
    if not cle:return "⚠️ Configurez `OPENAI_API_KEY` dans `.streamlit/secrets.toml` ou dans les variables d'environnement."
    if not isinstance(contexte,dict):
        actualites=recuperer_actualites(symbole)
        contexte=construire_contexte_analyse(actif={"nom":nom,"symbole":symbole,"prix":prix},technique={"score":score,"rsi":rsi,"signal":tendance},actualites=actualites,sentiment_actualites=actualites[0].get("sentiment",{}) if actualites else {},limites=["Contexte limité fourni par l’interface historique."])
    return _markdown(analyser_contexte_marche(contexte,question,api_key=cle))
