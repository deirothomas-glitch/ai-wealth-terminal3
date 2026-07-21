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

            titre = article.get("title", "Sans titre")

            lien = article.get("link", "#")

            source = article.get("publisher", "Source inconnue")

            st.markdown(f"### {titre}")
            st.caption(source)
            st.markdown(f"[Lire l'article]({lien})")
            st.divider()

    except Exception as e:

        st.error(f"Erreur : {e}")
