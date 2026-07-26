"""Composants Streamlit du Cockpit Investisseur."""

from html import escape
import math

from ui.portfolio_intelligence_card import afficher_intelligence_portefeuille


def _nombre(valeur, suffixe=""):
    if not isinstance(valeur, (int, float)) or isinstance(valeur, bool) or not math.isfinite(valeur):
        return "Indisponible"
    return f"{valeur:,.2f}{suffixe}".replace(",", " ")


def _badge(texte, niveau=""):
    classe = "awt-badge"
    if niveau == "bon":
        classe += " awt-badge--good"
    elif niveau == "attention":
        classe += " awt-badge--bad"
    elif niveau == "partiel":
        classe += " awt-badge--warn"
    return f'<span class="{classe}">{escape(str(texte))}</span>'


def afficher_cockpit(st, cockpit, analyse_ia=None):
    donnees = cockpit if isinstance(cockpit, dict) else {}
    bandeau = donnees.get("bandeau", {})
    qualite = bandeau.get("qualite", "Indisponible")
    sources = donnees.get("sources", {}) if isinstance(donnees.get("sources"), dict) else {}
    yahoo = sources.get("Yahoo Finance", {})
    openai = sources.get("OpenAI", {})
    stockage = sources.get("Stockage local", {})
    badges = [
        _badge(f"Mise à jour · {bandeau.get('mise_a_jour', 'Indisponible')}"),
        _badge(f"Yahoo · {yahoo.get('etat', 'Non vérifié')}", "bon" if yahoo.get("etat") == "Données reçues" else "partiel"),
        _badge(f"OpenAI · {openai.get('etat', 'Non vérifié')}", "bon" if openai.get("etat") == "Configuré" else "partiel"),
        _badge(f"Stockage · {stockage.get('etat', 'Non vérifié')}", "bon" if stockage.get("etat") == "Chargé" else "partiel"),
        _badge(f"Qualité · {qualite}", "bon" if qualite == "Bonne" else ("attention" if qualite == "Faible" else "partiel")),
    ]
    st.markdown('<div class="awt-card">' + "".join(badges) + "</div>", unsafe_allow_html=True)
    st.caption(bandeau.get("justification_qualite", "Qualité non évaluée."))

    marche = donnees.get("marche", {})
    portefeuille = donnees.get("portefeuille", {})
    gauche, droite = st.columns(2)
    with gauche:
        st.subheader("🌍 Résumé Marché")
        cartes = st.columns(3)
        cartes[0].metric("Tendance", marche.get("tendance", "Indisponible"))
        cartes[1].metric("Sentiment", marche.get("sentiment", "Indisponible"))
        cartes[2].metric("Volatilité globale", marche.get("volatilite", "Indisponible"))
        st.caption(
            f"Actifs surveillés : {marche.get('actifs_surveilles', 0)} · "
            f"Opportunités : {marche.get('opportunites', 0)} · "
            f"Risque global : {marche.get('risque_global', 'Non évalué')}"
        )
    with droite:
        st.subheader("💼 Résumé Portefeuille")
        cartes = st.columns(3)
        cartes[0].metric("Valeur totale", _nombre(portefeuille.get("valeur_totale"), " €"))
        cartes[1].metric("Variation", _nombre(portefeuille.get("variation"), " %"))
        cartes[2].metric("Exposition", _nombre(portefeuille.get("exposition"), " €"))
        st.caption(
            f"Ouvertes : {portefeuille.get('positions_ouvertes', 'Indisponible')} · "
            f"Clôturées : {portefeuille.get('positions_cloturees', 'Indisponible')} · "
            f"Gains réalisés : {_nombre(portefeuille.get('gains'), ' €')} · "
            f"Pertes réalisées : {_nombre(portefeuille.get('pertes'), ' €')}"
        )

    afficher_intelligence_portefeuille(
        st,
        donnees.get("intelligence_portefeuille", {}),
        compact=True,
    )
    st.subheader("🎯 Point de départ du parcours")
    st.caption("Choisissez une opportunité déjà calculée, ou lancez le Scanner pour commencer.")
    opportunites = donnees.get("opportunites", [])
    def ouvrir_scanner(symbole=None):
        if not hasattr(st, "session_state"):
            return
        if isinstance(symbole, str) and symbole:
            st.session_state.selected_asset = symbole
            st.session_state.scanner_actif_selectionne = symbole
        st.session_state.navigation = "🔎 Scanner"

    if not opportunites:
        st.info("Aucun classement n’est encore disponible dans cette session.")
        st.button("🔎 Lancer le Scanner", key="cockpit_open_scanner", on_click=ouvrir_scanner)
    for opportunite in opportunites[:5]:
        score = "—" if opportunite.get("score") is None else f"{opportunite['score']:.1f}/100"
        st.markdown(
            '<div class="awt-card">'
            f'<div class="awt-card-title">{escape(opportunite.get("symbole", "—"))} · {escape(score)}</div>'
            f'{_badge("Risque · " + opportunite.get("risque", "Indisponible"), "partiel" if opportunite.get("risque") != "Disponible" else "bon")}'
            f'{_badge("Qualité · " + opportunite.get("qualite", "Indisponible"))}'
            f'{_badge("Stratégie · " + opportunite.get("strategie", "Indisponible"))}'
            f'<div class="awt-meta">{escape(opportunite.get("resume", "Résumé indisponible"))}</div></div>',
            unsafe_allow_html=True,
        )
        symbole = opportunite.get("symbole", "")
        st.button(
            f"Approfondir {symbole}",
            key=f"cockpit_opportunite_{symbole}",
            on_click=ouvrir_scanner,
            args=(symbole,),
        )

    st.subheader("🚨 Alertes prioritaires")
    alertes = donnees.get("alertes", [])
    if not alertes:
        st.success("Aucune alerte prioritaire disponible dans les données chargées.")
    for alerte in alertes:
        message = f"**{alerte.get('symbole', 'Actif')} — {alerte.get('titre', 'Alerte')}**\n\n{alerte.get('message', '')}"
        (st.error if alerte.get("niveau") == "attention" else st.warning)(message)

    briefing = donnees.get("briefing", {})
    st.subheader("🤖 Briefing IA")
    st.caption("Synthèse déterministe disponible immédiatement · IA générative uniquement à la demande.")
    if briefing.get("donnees_partielles"):
        st.warning("Ce briefing repose sur des données partielles. Les éléments indisponibles ne sont pas estimés.")
    st.markdown(f"**Marché** — {briefing.get('resume_marche', 'Indisponible')}")
    st.markdown(f"**Portefeuille** — {briefing.get('resume_portefeuille', 'Indisponible')}")
    st.caption(briefing.get("contexte", "Contexte indisponible"))
    for titre, cle in (("Points positifs", "points_positifs"), ("Points de vigilance", "points_vigilance")):
        valeurs = briefing.get(cle, [])
        st.markdown(f"**{titre}**")
        if valeurs:
            for valeur in valeurs:
                st.write(f"• {valeur}")
        else:
            st.caption("Aucun élément fiable disponible.")
    demande_ia = st.button("🤖 Générer le briefing IA", key="cockpit_briefing_generate")
    if isinstance(analyse_ia, dict):
        st.markdown("**Synthèse IA générée à la demande**")
        st.write(analyse_ia.get("resume", "Analyse IA indisponible."))
        st.caption(f"Confiance déclarée : {analyse_ia.get('niveau_confiance', 'faible')}.")

    agenda = donnees.get("agenda", {})
    st.subheader("🗓️ Évènements de marché")
    evenements = agenda.get("evenements", [])
    if not evenements:
        st.info(agenda.get("message", "Aucun événement disponible."))
    else:
        for evenement in evenements:
            if not isinstance(evenement, dict):
                continue
            titre = evenement.get("titre", "Événement")
            details = " · ".join(x for x in (evenement.get("date"), evenement.get("source")) if isinstance(x, str) and x)
            st.markdown(f"**{titre}**" + (f" — {details}" if details else ""))
    st.caption("Les informations présentées ne constituent ni une garantie de gain ni un ordre automatique.")
    return demande_ia
