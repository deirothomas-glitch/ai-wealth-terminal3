"""Composant de conversation bornée en session Streamlit."""
import streamlit as st
def afficher_historique_conversation(messages):
    for message in messages if isinstance(messages,list) else []:
        if not isinstance(message,dict):continue
        role=message.get("role");content=message.get("content")
        if role in ("user","assistant") and isinstance(content,str):
            with st.chat_message(role):st.markdown(content)
def questions_suggerees():
    return ["Quels sont les principaux risques ?","Quelles conditions confirmeraient le scénario ?","Quelles informations pourraient invalider l’analyse ?","Comment interpréter le plan de risque ?","Cette actualité change-t-elle réellement le contexte ?","Que dois-je surveiller aujourd’hui ?"]
