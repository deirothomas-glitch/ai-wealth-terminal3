"""Cartes lisibles d'actualités normalisées."""

from datetime import datetime, timezone
from html import escape

import streamlit as st


def _fraicheur(date_publication):
    try:
        publication = datetime.fromisoformat(str(date_publication).replace("Z", "+00:00"))
        if publication.tzinfo is None:
            publication = publication.replace(tzinfo=timezone.utc)
        heures = max(0, int((datetime.now(timezone.utc) - publication).total_seconds() // 3600))
    except (TypeError, ValueError, OverflowError):
        return "Fraîcheur inconnue"
    if heures < 1:
        return "À l’instant"
    if heures < 24:
        return f"Il y a {heures} h"
    jours = heures // 24
    return f"Il y a {jours} j"


def _classe_badge(valeur):
    texte = str(valeur).casefold()
    if texte in {"positif", "forte", "bon", "élevée", "elevee"}:
        return "awt-badge--good"
    if texte in {"negatif", "faible", "insuffisant"}:
        return "awt-badge--bad"
    return "awt-badge--warn"


def afficher_actualites_normalisees(actualites, limite=10):
    valides = [x for x in actualites if isinstance(x, dict)] if isinstance(actualites, list) else []
    if not valides:
        st.info("Aucune actualité pertinente disponible.")
        return
    for article in valides[:limite]:
        titre = str(article.get("titre") or "Titre indisponible")
        source = str(article.get("source") or "Source non renseignée")
        date = article.get("date_publication") or "Date non renseignée"
        pertinence = (article.get("pertinence") or {}).get("niveau", "indéterminée")
        qualite = (article.get("qualite") or {}).get("niveau", "indéterminée")
        sentiment = article.get("sentiment") or {}
        humeur = sentiment.get("sentiment", "indetermine")
        confiance = sentiment.get("confiance", "faible")
        badges = (
            f'<span class="awt-badge {_classe_badge(humeur)}">Sentiment · {escape(str(humeur))}</span>'
            f'<span class="awt-badge {_classe_badge(pertinence)}">Importance · {escape(str(pertinence))}</span>'
            f'<span class="awt-badge {_classe_badge(qualite)}">Qualité · {escape(str(qualite))}</span>'
            f'<span class="awt-badge">{escape(_fraicheur(date))}</span>'
        )
        st.markdown(
            f'<div class="awt-card"><div class="awt-card-title">{escape(titre)}</div>'
            f'{badges}<div class="awt-meta">{escape(source)} · {escape(str(date))} · '
            f'Confiance lexicale {escape(str(confiance))}</div></div>',
            unsafe_allow_html=True,
        )
        resume = article.get("resume")
        if isinstance(resume, str) and resume.strip():
            st.write(resume[:600])
        url = article.get("url")
        if isinstance(url, str) and url.startswith(("https://", "http://")):
            st.markdown(f'<div class="awt-link"><a href="{escape(url, quote=True)}" target="_blank">Lire la source originale →</a></div>', unsafe_allow_html=True)
