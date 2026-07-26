"""Assistant conversationnel fondé sur un contexte d'analyse borné."""
import streamlit as st
from config import MAX_AI_MESSAGES,MAX_AI_QUESTION_LENGTH
from core.analysis_context import construire_contexte_analyse
from core.decision import construire_decision
from core.risk import calculer_atr,construire_plan_risque
from market_data import charger_donnees,dernier_prix,recuperer_infos
from scoring import calculer_score
from services.ai_market_analysis import analyser_contexte_marche
from services.news_aggregator import agreger_actualites
from services.news_sources import YahooNewsSource
from ui.ai_analysis_card import afficher_analyse_ia
from ui.assistant_chat import afficher_historique_conversation,questions_suggerees

def afficher_assistant():
    st.header("🤖 Assistant IA");st.caption("Les données déterministes restent disponibles sans clé OpenAI.");c=st.columns(2);symbole=c[0].text_input("Actif","AAPL",key="assistant_symbol").upper().strip();profil=c[1].selectbox("Profil",["Court terme","Swing","Tendance"],key="assistant_profile")
    st.selectbox("Question suggérée",["Question libre"]+questions_suggerees(),key="assistant_suggestion");question=st.text_area("Votre question",max_chars=MAX_AI_QUESTION_LENGTH,key="assistant_question")
    st.session_state.setdefault("assistant_messages",[]);afficher_historique_conversation(st.session_state.assistant_messages)
    if st.button("Analyser et répondre",key="assistant_submit"):
        with st.spinner("Construction du contexte..."):
            hist=charger_donnees(symbole,"1y");info=recuperer_infos(symbole) if hist is not None else {};score=calculer_score(info,hist) if hist is not None else {};decision=construire_decision(score)
            if hist is not None and {"High","Low","Close"}.issubset(hist.columns):atr=calculer_atr([float(x) for x in hist["High"].tolist()],[float(x) for x in hist["Low"].tolist()],[float(x) for x in hist["Close"].tolist()]);prix=float(hist["Close"].iloc[-1])
            else:atr=prix=None
            risk=construire_plan_risque(prix,atr);news,_=agreger_actualites([YahooNewsSource()],symbole,info.get("longName",symbole),limite=5);position=next((p for p in st.session_state.get("portfolio",[]) if p.get("symbole")==symbole),None)
            context=construire_contexte_analyse(actif={"symbole":symbole,"nom":info.get("longName",symbole),"prix":prix},technique=score,strategie={"profil":profil},decision=decision,risque=risk,actualites=news,sentiment_actualites=news[0].get("sentiment",{}) if news else {},portefeuille=position,limites=["Données de marché potentiellement différées."])
            answer=analyser_contexte_marche(context,question or st.session_state.assistant_suggestion)
        st.session_state.assistant_messages=(st.session_state.assistant_messages+[{"role":"user","content":question or st.session_state.assistant_suggestion},{"role":"assistant","content":answer["resume"]}])[-MAX_AI_MESSAGES:];afficher_analyse_ia(answer)
