"""Présentation prudente du sentiment d'actualités."""
import streamlit as st
def afficher_sentiment_actualites(sentiment):
    data=sentiment if isinstance(sentiment,dict) else {};value=data.get("sentiment","indetermine");confidence=data.get("confiance","faible");st.metric("Sentiment des actualités",value.capitalize());st.caption(f"Confiance lexicale : {confidence}. Ce sentiment ne constitue pas une prévision du prix.")
    for limit in data.get("limites",[])[:2] if isinstance(data.get("limites"),list) else []:st.caption(limit)
