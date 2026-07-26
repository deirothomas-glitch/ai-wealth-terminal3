"""Page Streamlit des actualités filtrées et dédupliquées."""
from datetime import datetime, timedelta, timezone
import streamlit as st
from services.news_aggregator import agreger_actualites
from services.news_cache import charger_cache_actualites,sauvegarder_cache_actualites
from services.news_sources import YahooNewsSource
from ui.news_card import afficher_actualites_normalisees
from ui.news_sentiment_card import afficher_sentiment_actualites

def afficher_page_actualites():
    st.header("📰 Actualités de marché");c=st.columns(2);symbole=c[0].text_input("Symbole","AAPL",key="news_symbol").upper().strip();recherche=c[1].text_input("Recherche",key="news_search").casefold().strip()
    if st.button("🔄 Rafraîchir les actualités",key="news_refresh"):
        articles,errors=agreger_actualites([YahooNewsSource()],symbole,limite=20);st.session_state.actualites_marche=articles
        try:sauvegarder_cache_actualites(articles)
        except OSError:st.warning("Le cache local des actualités n’a pas pu être mis à jour.")
        for error in errors:st.warning(error)
    if "actualites_marche" not in st.session_state:
        cache,error=charger_cache_actualites();st.session_state.actualites_marche=cache.get("donnees",[]) if isinstance(cache,dict) else []
        if error:st.warning(error)
    articles=st.session_state.actualites_marche;c=st.columns(5);source=c[0].selectbox("Source",["Toutes"]+sorted({x.get("source","") for x in articles if isinstance(x,dict) and x.get("source")}));categorie=c[1].selectbox("Catégorie",["Toutes"]+sorted({cat for x in articles if isinstance(x,dict) for cat in x.get("categories",[]) if isinstance(cat,str)}));pertinence=c[2].selectbox("Pertinence",["Toutes","forte","moyenne","faible"]);periode=c[3].selectbox("Date",["Toutes","7 jours","30 jours"]);tri=c[4].selectbox("Tri",["Pertinence","Plus récent"])
    def date_dans_periode(article):
        if periode=="Toutes":return True
        try:publication=datetime.fromisoformat(str(article.get("date_publication")).replace("Z","+00:00"));publication=publication if publication.tzinfo else publication.replace(tzinfo=timezone.utc)
        except (TypeError,ValueError):return False
        jours=7 if periode=="7 jours" else 30
        return publication>=datetime.now(timezone.utc)-timedelta(days=jours)
    filtres=[x for x in articles if isinstance(x,dict) and (source=="Toutes" or x.get("source")==source) and (categorie=="Toutes" or categorie in x.get("categories",[])) and (pertinence=="Toutes" or (x.get("pertinence") or {}).get("niveau")==pertinence) and date_dans_periode(x) and (not recherche or recherche in (str(x.get("titre",""))+" "+str(x.get("resume",""))).casefold())]
    filtres.sort(key=(lambda x:str(x.get("date_publication") or "")) if tri=="Plus récent" else (lambda x:(x.get("pertinence") or {}).get("score_pertinence",0)),reverse=True)
    if filtres:afficher_sentiment_actualites(filtres[0].get("sentiment",{}))
    afficher_actualites_normalisees(filtres)
