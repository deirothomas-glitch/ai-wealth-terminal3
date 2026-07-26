"""Compatibilité UI autour du pipeline d'actualités normalisées."""
import streamlit as st
from config import MAX_NEWS,NEWS_CACHE_TTL
from services.news_aggregator import agreger_actualites
from services.news_sources import YahooNewsSource
from ui.news_card import afficher_actualites_normalisees

@st.cache_data(ttl=NEWS_CACHE_TTL,show_spinner=False)
def recuperer_actualites(symbole="AAPL",limite=MAX_NEWS):
    articles,_=agreger_actualites([YahooNewsSource()],symbole,limite=limite)
    return [{**a,"lien":a.get("url","")} for a in articles]

def afficher_actualites(symbole="AAPL"):
    afficher_actualites_normalisees(recuperer_actualites(symbole))
