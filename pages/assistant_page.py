"""Assistant conversationnel fondé sur un contexte d'analyse borné."""

import streamlit as st

from config import MAX_AI_MESSAGES, MAX_AI_QUESTION_LENGTH
from core.analysis_context import construire_contexte_analyse
from core.decision import construire_decision
from core.risk import calculer_atr, construire_plan_risque
from core.scenario_engine import construire_scenarios_depuis_contrats, enrichir_redaction_scenarios
from market_data import charger_donnees, recuperer_infos
from scoring import calculer_score
from services.ai_market_analysis import analyser_contexte_marche
from services.news_aggregator import agreger_actualites
from services.news_sources import YahooNewsSource
from ui.ai_analysis_card import afficher_analyse_ia
from ui.scenario_card import afficher_scenarios
from ui.assistant_chat import (
    afficher_historique_conversation,
    questions_suggerees,
    resumer_reponse_pour_historique,
)


def afficher_assistant():
    st.header("🤖 Assistant IA")
    st.caption(
        "Posez une question sur un actif. Les faits, limites et risques restent "
        "distingués des interprétations de l’IA."
    )
    controles = st.columns(2)
    symbole = controles[0].text_input(
        "Actif", "AAPL", key="assistant_symbol"
    ).upper().strip()
    profil = controles[1].selectbox(
        "Profil", ["Court terme", "Swing", "Tendance"], key="assistant_profile"
    )
    suggestion = st.selectbox(
        "Suggestion de question",
        ["Question libre"] + questions_suggerees(),
        key="assistant_suggestion",
    )
    question = st.text_area(
        "Votre question",
        placeholder="Décrivez ce que vous souhaitez comprendre…",
        max_chars=MAX_AI_QUESTION_LENGTH,
        key="assistant_question",
    )
    question_effective = question.strip() or (
        suggestion if suggestion != "Question libre" else "Que dois-je surveiller aujourd’hui ?"
    )

    st.session_state.setdefault("assistant_messages", [])
    actions = st.columns([3, 1])
    envoyer = actions[0].button(
        "Analyser et répondre", key="assistant_submit", use_container_width=True
    )
    if actions[1].button(
        "Effacer l’historique", key="assistant_clear", use_container_width=True
    ):
        st.session_state.assistant_messages = []
        st.success("Historique effacé pour cette session.")

    if envoyer:
        try:
            with st.spinner("Construction du contexte et analyse…"):
                historique = charger_donnees(symbole, "1y")
                infos = recuperer_infos(symbole) if historique is not None else {}
                score = calculer_score(infos, historique) if historique is not None else {}
                decision = construire_decision(score)
                if historique is not None and {"High", "Low", "Close"}.issubset(historique.columns):
                    atr = calculer_atr(
                        [float(x) for x in historique["High"].tolist()],
                        [float(x) for x in historique["Low"].tolist()],
                        [float(x) for x in historique["Close"].tolist()],
                    )
                    prix = float(historique["Close"].iloc[-1])
                else:
                    atr = prix = None
                risque = construire_plan_risque(prix, atr)
                actualites, erreurs_actualites = agreger_actualites(
                    [YahooNewsSource()], symbole, infos.get("longName", symbole), limite=5
                )
                position = next((
                    p for p in st.session_state.get("portfolio", [])
                    if isinstance(p, dict) and str(p.get("symbole", "")).upper() == symbole
                ), None)
                limites = ["Données de marché potentiellement différées."]
                if historique is None:
                    limites.append("Historique de marché indisponible.")
                if not actualites:
                    limites.append("Actualités absentes ou indisponibles.")
                limites.extend(str(erreur) for erreur in erreurs_actualites[:2])
                contexte = construire_contexte_analyse(
                    actif={"symbole": symbole, "nom": infos.get("longName", symbole), "prix": prix},
                    technique=score,
                    strategie={"profil": profil},
                    decision=decision,
                    risque=risque,
                    actualites=actualites,
                    sentiment_actualites=actualites[0].get("sentiment", {}) if actualites else {},
                    portefeuille=position,
                    limites=limites,
                )
                reponse = analyser_contexte_marche(contexte, question_effective)
                scenarios = construire_scenarios_depuis_contrats(
                    decision, risque, horizon=profil
                )
                scenarios = enrichir_redaction_scenarios(scenarios, {
                    "haussier": reponse.get("scenario_favorable"),
                    "neutre": reponse.get("resume"),
                    "baissier": reponse.get("scenario_defavorable"),
                })
            st.session_state.assistant_messages = (
                st.session_state.assistant_messages
                + [
                    {"role": "user", "content": question_effective},
                    {"role": "assistant", "content": resumer_reponse_pour_historique(reponse)},
                ]
            )[-MAX_AI_MESSAGES:]
            afficher_analyse_ia(reponse)
            afficher_scenarios(scenarios)
        except Exception:
            st.warning(
                "La réponse IA est temporairement indisponible. Vérifiez le symbole, "
                "la connexion et la configuration OpenAI, puis réessayez."
            )

    afficher_historique_conversation(st.session_state.assistant_messages)
