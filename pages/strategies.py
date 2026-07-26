"""Page Streamlit Stratégies et Backtest, exécutée uniquement à la demande."""
import pandas as pd
import streamlit as st
from ai_analysis import analyser_actif
from core.analysis_context import construire_contexte_analyse
from core.data_quality import evaluer_qualite_donnees
from core.decision import construire_decision
from core.strategy_engine import evaluer_strategie
from core.strategy_profiles import obtenir_profils
from market_data import charger_donnees
from scoring import calculer_score
from services.backtest_runner import lancer_backtest
from services.news_aggregator import agreger_actualites
from services.news_sources import YahooNewsSource
from ui.backtest_summary import afficher_resume_backtest
from ui.data_quality_card import afficher_qualite_donnees
from ui.strategy_card import afficher_carte_strategie

def _qualite(historique,score,minimum):
    colonnes=set(historique.columns); close=historique["Close"]; return evaluer_qualite_donnees({"nombre_points":len(historique),"minimum_requis":minimum,"prix":float(close.iloc[-1]),"valeurs_manquantes":int(historique.isna().sum().sum()),"volume_disponible":"Volume" in colonnes,"volatilite_disponible":{"High","Low","Close"}.issubset(colonnes) and len(historique)>=15,"indicateurs_essentiels":{"score":score.get("score") is not None,"rsi":score.get("rsi") is not None,"ema20":score.get("ema20") is not None}})
def afficher_strategies():
    st.header("🧭 Stratégies et backtest"); st.write("Comparez un signal actuel à un profil, puis testez sa logique sur l’historique.")
    profils=obtenir_profils(); c=st.columns(2); symbole=c[0].text_input("Symbole","AAPL",key="strategie_symbole").upper().strip(); profil=c[1].selectbox("Mode",profils,format_func=lambda p:p["nom"],key="strategie_profil")
    with st.expander("Paramètres du backtest"):
        c=st.columns(4); capital=c[0].number_input("Capital initial",min_value=100.0,value=10000.0); taille=c[1].number_input("Capital engagé (%)",min_value=1.0,max_value=100.0,value=100.0); frais=c[2].number_input("Frais (%)",min_value=0.0,value=0.0,step=0.01); slippage=c[3].number_input("Slippage (%)",min_value=0.0,value=0.0,step=0.01)
    lancer=st.button("▶️ Lancer le backtest",key="lancer_backtest")
    if lancer:
        historique=charger_donnees(symbole,profil["periode_donnees"]);
        if historique is None: st.error("Données indisponibles pour ce symbole.")
        else:
            score=calculer_score({},historique); decision=construire_decision(score); qualite=_qualite(historique,score,profil["regles"]["historique_minimum"]); strategie=evaluer_strategie(score,score,decision,profil,qualite); resultat=lancer_backtest(symbole,profil,charger_donnees,capital_initial=capital,taille_position_pct=taille,frais_pct=frais,slippage_pct=slippage); st.session_state.strategie_resultat={"symbole":symbole,"profil":profil,"strategie":strategie,"qualite":qualite,"backtest":resultat,"prix":float(historique["Close"].iloc[-1]),"score":score,"decision":decision}
    donnees=st.session_state.get("strategie_resultat")
    if not donnees: st.info("Le backtest ne démarre qu’après un clic sur le bouton."); return
    afficher_carte_strategie(st,donnees["strategie"]); afficher_qualite_donnees(st,donnees["qualite"]); st.subheader("Résultat historique"); afficher_resume_backtest(st,donnees["backtest"]); operations=donnees["backtest"]["operations"]; st.dataframe(pd.DataFrame(operations),use_container_width=True,hide_index=True) if operations else st.info("Aucune opération sur la période."); courbe=donnees["backtest"]["courbe_capital"];
    if courbe: st.line_chart(pd.DataFrame(courbe).set_index("date")["capital"])
    for a in donnees["backtest"]["avertissements"]: st.warning(a)
    st.warning("Les performances passées ne garantissent pas les performances futures. Le backtest simplifie les conditions réelles : frais, liquidité, slippage et écarts de prix peuvent modifier les résultats. Un faible nombre d’opérations rend les statistiques peu fiables. Aucun signal ne constitue une certitude.")
    if st.button("Préremplir le formulaire Portefeuille",key="strategie_prefill"): st.session_state.portfolio_prefill={"symbole":donnees["symbole"],"nom":donnees["symbole"],"prix_entree":donnees["prix"],"stop_loss":None,"objectif":None,"type_actif":"autre"}; st.success("Préremplissage préparé. Ouvrez le Portefeuille pour confirmer l’ajout.")
    if st.button("🤖 Analyser la stratégie avec les actualités",key="strategie_ia"):
        actualites,_=agreger_actualites([YahooNewsSource()],donnees["symbole"],limite=5)
        contexte=construire_contexte_analyse(
            actif={"symbole":donnees["symbole"],"prix":donnees["prix"]},
            technique=donnees.get("score",{}),strategie=donnees["strategie"],
            decision=donnees.get("decision",{}),qualite_donnees=donnees["qualite"],
            actualites=actualites,
            sentiment_actualites=actualites[0].get("sentiment",{}) if actualites else {},
            limites=["Le backtest décrit le passé et ne prédit pas les performances futures."],
        )
        st.markdown(analyser_actif(donnees["symbole"],donnees["symbole"],donnees["prix"],donnees.get("score",{}).get("score",0),donnees.get("score",{}).get("rsi",50),donnees["strategie"].get("signal","indisponible"),contexte=contexte))
