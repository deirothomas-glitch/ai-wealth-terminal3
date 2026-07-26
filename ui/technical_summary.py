"""Présentation Streamlit des faits techniques d'un score."""
import math
import streamlit as st


def construire_modele_resume_technique(score_data: dict) -> dict:
    """Construit un modèle JSON natif sans interpréter ni modifier le score."""
    donnees = score_data if isinstance(score_data, dict) else {}
    score = donnees.get("score")
    if (isinstance(score, (int, float)) and not isinstance(score, bool)
            and 0 <= score <= 100 and math.isfinite(score)):
        score_affiche = f"{score}/100"
    else:
        score_affiche = "Indisponible"
    signal = donnees.get("signal")
    signal_affiche = signal.strip() if isinstance(signal, str) and signal.strip() else "INDISPONIBLE"
    source = donnees.get("raisons")
    raisons = ([raison.strip() for raison in source
                if isinstance(raison, str) and raison.strip()]
               if isinstance(source, list) else [])
    return {
        "score_label": "Score technique",
        "score": score_affiche,
        "signal_label": "Signal technique",
        "signal": signal_affiche,
        "raisons_titre": "Raisons techniques",
        "raisons": raisons,
    }


def afficher_resume_technique(score_data: dict, *, afficher_raisons: bool = True) -> None:
    """Affiche le score, le signal et, sur demande, leurs raisons techniques."""
    modele = construire_modele_resume_technique(score_data)
    col1, col2 = st.columns(2)
    col1.metric(modele["score_label"], modele["score"])
    col2.metric(modele["signal_label"], modele["signal"])
    if afficher_raisons:
        st.markdown(f"**{modele['raisons_titre']}**")
        if modele["raisons"]:
            for raison in modele["raisons"]:
                st.write(f"• {raison}")
        else:
            st.write("Aucune raison technique exploitable.")
