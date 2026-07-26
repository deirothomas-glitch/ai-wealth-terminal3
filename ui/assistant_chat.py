"""Composants de conversation bornée en session Streamlit."""

import streamlit as st


def afficher_historique_conversation(messages):
    """Affiche uniquement les messages valides, dans leur ordre d'origine."""
    valides = messages if isinstance(messages, list) else []
    if not valides:
        st.caption("La conversation est conservée uniquement pendant cette session.")
        return
    st.subheader("Historique de conversation")
    for message in valides:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        contenu = message.get("content")
        if role in ("user", "assistant") and isinstance(contenu, str):
            with st.chat_message(role):
                st.markdown(contenu)


def resumer_reponse_pour_historique(analyse):
    """Produit un texte lisible à partir du contrat IA validé."""
    if not isinstance(analyse, dict):
        return "Analyse IA indisponible."
    parties = [str(analyse.get("resume") or "Analyse IA indisponible.")]
    risques = analyse.get("risques_principaux")
    if isinstance(risques, list) and risques:
        parties.append("**Risques principaux**\n" + "\n".join(
            f"- {risque}" for risque in risques[:3] if isinstance(risque, str)
        ))
    confiance = analyse.get("niveau_confiance")
    if isinstance(confiance, str) and confiance:
        parties.append(f"*Niveau de confiance déclaré : {confiance}.*")
    limites = analyse.get("limites")
    if isinstance(limites, list) and limites:
        parties.append("*Réponse fondée sur des données partielles ou comportant des limites.*")
    return "\n\n".join(parties)


def questions_suggerees():
    return [
        "Quels sont les principaux risques ?",
        "Quelles conditions confirmeraient le scénario ?",
        "Quelles informations pourraient invalider l’analyse ?",
        "Comment interpréter le plan de risque ?",
        "Cette actualité change-t-elle réellement le contexte ?",
        "Que dois-je surveiller aujourd’hui ?",
    ]
