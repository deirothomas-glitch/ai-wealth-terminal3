import streamlit as st
import yfinance as yf


def afficher_actualites(symbole="AAPL"):

    st.subheader("📰 Dernières actualités")

    try:

        ticker = yf.Ticker(symbole)

        actualites = ticker.news

        if not actualites:
            st.info("Aucune actualité disponible.")
            return

        for article in actualites[:5]:

            content = article.get("content", {})

            titre = content.get("title", "Sans titre")

            lien = content.get("canonicalUrl", {}).get("url", "#")

            source = content.get("provider", {}).get("displayName", "Source inconnue")

            st.markdown(f"### {titre}")
            st.caption(source)
            st.markdown(f"[Lire l'article]({lien})")
            st.divider()

    except Exception as e:

        st.error(f"Erreur : {e}")
        
def recuperer_actualites(symbole="AAPL", limite=5):
    try:
        ticker = yf.Ticker(symbole)
        actualites = ticker.news

        resultat = []

        for article in actualites[:limite]:
            content = article.get("content", {})

            resultat.append({
                "titre": content.get("title", ""),
                "source": content.get("provider", {}).get("displayName", ""),
                "resume": content.get("summary", ""),
            })

        return resultat

    except Exception:
        return []