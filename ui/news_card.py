"""Cartes Streamlit d'actualités normalisées."""
import streamlit as st
def afficher_actualites_normalisees(actualites,limite=10):
    valides=[x for x in actualites if isinstance(x,dict)] if isinstance(actualites,list) else []
    if not valides:st.info("Aucune actualité pertinente disponible.");return
    for article in valides[:limite]:
        titre=article.get("titre") or "Titre indisponible";st.markdown(f"**{titre}**")
        source=article.get("source") or "Source non renseignée";date=article.get("date_publication") or "Date non renseignée";pertinence=(article.get("pertinence") or {}).get("niveau","indéterminée");qualite=(article.get("qualite") or {}).get("niveau","indéterminée");sentiment=article.get("sentiment") or {};st.caption(f"{source} · {date} · Pertinence {pertinence} · Qualité {qualite} · Sentiment {sentiment.get('sentiment','indetermine')} ({sentiment.get('confiance','faible')})")
        resume=article.get("resume")
        if isinstance(resume,str) and resume.strip():st.write(resume[:600])
        url=article.get("url")
        if isinstance(url,str) and url.startswith(("https://","http://")):st.markdown(f"[Ouvrir la source originale]({url})")
