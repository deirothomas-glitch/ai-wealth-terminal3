"""Cockpit d’accueil et point de départ du parcours investisseur."""

from datetime import datetime

import streamlit as st

from config import APP_NAME, APP_VERSION
from core.analysis_context import construire_contexte_analyse
from core.cockpit import construire_cockpit
from market_data import recuperer_cryptos, recuperer_indices
from services.ai_client import obtenir_cle_api
from services.ai_market_analysis import analyser_contexte_marche
from ui.investor_cockpit import afficher_cockpit


def _cartes_marche(titre, elements):
    st.subheader(titre)
    if not elements:
        st.info("Données indisponibles.")
        return
    for colonne, element in zip(st.columns(min(len(elements), 4)), elements[:4]):
        colonne.metric(
            element["nom"], f"{element['prix']:,.2f}", f"{element['variation']:+.2f}%"
        )


def _preparer_cockpit(indices_marche, cryptos_marche):
    """Prépare le Cockpit avec les données déjà chargées ou mises en cache."""
    session = st.session_state
    try:
        openai_disponible = obtenir_cle_api(getattr(st, "secrets", None)) is not None
    except Exception:
        openai_disponible = False
    return construire_cockpit(
        indices=indices_marche,
        cryptos=cryptos_marche,
        opportunites=session.get("opportunites_classees", []),
        positions=session.get("portfolio", []),
        prix_portefeuille=session.get("portfolio_prix", {}),
        journal=session.get("trading_journal", []),
        alertes=session.get("alertes_positions", []),
        actualites=session.get("actualites_marche", []),
        evenements=session.get("evenements_marche", []),
        portefeuille_charge="portfolio" in session,
        openai_disponible=openai_disponible,
        yahoo_interroge=True,
        mise_a_jour=datetime.now().astimezone().strftime("%d/%m/%Y %H:%M"),
    )


def afficher_dashboard():
    """Affiche uniquement le Cockpit ; l’analyse détaillée vit dans le Scanner."""
    st.title(APP_NAME)
    st.caption(f"Version {APP_VERSION} · Votre point de départ pour investir méthodiquement")
    indices_marche = recuperer_indices()
    cryptos_marche = recuperer_cryptos()
    try:
        cockpit = _preparer_cockpit(indices_marche, cryptos_marche)
        analyse_cockpit = st.session_state.get("cockpit_briefing_ia")
        demande_briefing_ia = afficher_cockpit(st, cockpit, analyse_cockpit)
        if demande_briefing_ia:
            with st.spinner("Synthèse du briefing en cours..."):
                contexte = construire_contexte_analyse(
                    marche={"cockpit": cockpit.get("marche", {})},
                    portefeuille=cockpit.get("portefeuille", {}),
                    actualites=st.session_state.get("actualites_marche", []),
                    limites=[
                        "Briefing construit à partir des données déjà disponibles.",
                        "Certaines données peuvent être partielles ou différées.",
                    ],
                )
                st.session_state.cockpit_briefing_ia = analyser_contexte_marche(
                    contexte,
                    "Résume le marché, le portefeuille, les points positifs et les vigilances.",
                )
            st.rerun()
    except Exception:
        st.warning(
            "Le Cockpit est temporairement partiel. Vous pouvez continuer depuis le Scanner."
        )
        _cartes_marche("🌍 Marchés mondiaux", indices_marche)
        _cartes_marche("🪙 Cryptomonnaies", cryptos_marche)
