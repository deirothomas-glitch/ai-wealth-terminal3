"""Composants Streamlit du Cockpit Investisseur."""

from html import escape
import math


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
    badges = [
        _badge(f"Mise à jour · {bandeau.get('mise_a_jour', 'Indisponible')}"),
        _badge(f"Connexion · {bandeau.get('connexion', 'Indisponible')}", "bon" if bandeau.get("connexion") == "Connectée" else "partiel"),
        _badge(f"OpenAI · {bandeau.get('openai', 'Indisponible')}", "bon" if bandeau.get("openai") == "Configuré" else "partiel"),
        _badge(f"Yahoo · {bandeau.get('yahoo', 'Indisponible')}", "bon" if bandeau.get("yahoo") == "Disponible" else "attention"),
        _badge(f"Qualité · {qualite}", "bon" if qualite == "Bonne" else "partiel"),
    ]
    st.markdown('<div class="awt-card">' + "".join(badges) + "</div>", unsafe_allow_html=True)

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

    st.subheader("🎯 Top opportunités")
    opportunites = donnees.get("opportunites", [])
    if not opportunites:
        st.info("Lancez le Scanner pour alimenter le classement du Cockpit.")
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
        st.info(agenda.get("message", "Aucun évènement fiable disponible."))
    else:
        for evenement in evenements:
            st.write(f"• {evenement}")
    st.caption("Les informations présentées ne constituent ni une garantie de gain ni un ordre automatique.")
    return demande_ia
