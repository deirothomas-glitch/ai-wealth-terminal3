"""Cartes Streamlit des scénarios conditionnels."""

import streamlit as st

TITRES = {
    "haussier": "📈 Scénario haussier",
    "neutre": "⏸️ Scénario neutre",
    "baissier": "📉 Scénario baissier",
}


def _classe_confiance(niveau):
    return {
        "Élevée": "awt-badge--good",
        "Modérée": "awt-badge--warn",
        "Faible": "awt-badge--bad",
    }.get(niveau, "awt-badge--bad")


def _afficher_liste(ui, titre, valeurs, repli):
    ui.markdown(f"**{titre}**")
    if isinstance(valeurs, list) and valeurs:
        for valeur in valeurs:
            if isinstance(valeur, str):
                ui.write(f"• {valeur}")
    else:
        ui.caption(repli)


def _afficher_scenario(ui, scenario):
    donnees = scenario if isinstance(scenario, dict) else {}
    nom = donnees.get("type", "neutre")
    confiance = donnees.get("niveau_confiance", "Faible")
    ui.markdown(f"### {TITRES.get(nom, TITRES['neutre'])}")
    ui.markdown(
        f'<span class="awt-badge {_classe_confiance(confiance)}">Confiance · {confiance}</span>'
        f'<span class="awt-badge">Horizon · {donnees.get("horizon", "swing")}</span>',
        unsafe_allow_html=True,
    )
    ui.write(donnees.get("resume", "Résumé indisponible."))
    _afficher_liste(ui, "Facteurs favorables", donnees.get("facteurs_favorables"), "Aucun facteur favorable documenté.")
    _afficher_liste(ui, "Points de vigilance", donnees.get("facteurs_defavorables"), "Aucun facteur défavorable documenté.")
    _afficher_liste(ui, "Risques identifiés", donnees.get("risques_identifies"), "Aucun risque spécifique documenté.")
    _afficher_liste(ui, "Données manquantes", donnees.get("elements_manquants"), "Aucune donnée manquante signalée.")
    _afficher_liste(ui, "Conditions d’invalidation", donnees.get("conditions_invalidation"), "Conditions d’invalidation non documentées.")


def afficher_scenarios(resultat, interface=None):
    """Affiche les trois scénarios sans déclencher de calcul ni d'appel IA."""
    ui = interface or st
    donnees = resultat if isinstance(resultat, dict) else {}
    ui.subheader("🧭 Analyse multi-scénarios")
    if donnees.get("donnees_partielles"):
        ui.warning("Les scénarios reposent sur des données partielles ; aucun élément absent n’a été estimé.")
    onglets = ui.tabs([TITRES["haussier"], TITRES["neutre"], TITRES["baissier"]])
    for onglet, nom in zip(onglets, ("haussier", "neutre", "baissier")):
        with onglet:
            _afficher_scenario(ui, donnees.get(f"scenario_{nom}", {"type": nom}))
    ui.caption(donnees.get("rappel_prudence", "Ces scénarios ne constituent pas une certitude."))


def afficher_scenario_principal(resultat, interface=None):
    """Affiche uniquement le scénario principal pour une synthèse compacte."""
    ui = interface or st
    donnees = resultat if isinstance(resultat, dict) else {}
    principal = donnees.get("scenario_principal", "neutre")
    ui.subheader("🧭 Scénario principal")
    if donnees.get("donnees_partielles"):
        ui.warning("Scénario fondé sur des données partielles.")
    with ui.container(border=True):
        scenario = donnees.get(f"scenario_{principal}", {"type": principal})
        scenario = scenario if isinstance(scenario, dict) else {"type": principal}
        nom = scenario.get("type", "neutre")
        confiance = scenario.get("niveau_confiance", "Faible")
        ui.markdown(f"### {TITRES.get(nom, TITRES['neutre'])}")
        ui.markdown(
            f'<span class="awt-badge {_classe_confiance(confiance)}">Confiance · {confiance}</span>'
            f'<span class="awt-badge">Horizon · {scenario.get("horizon", "swing")}</span>',
            unsafe_allow_html=True,
        )
        ui.write(scenario.get("resume", "Résumé indisponible."))
        favorables = scenario.get("facteurs_favorables")
        vigilances = scenario.get("facteurs_defavorables")
        risques = scenario.get("risques_identifies")
        manquantes = scenario.get("elements_manquants")
        invalidations = scenario.get("conditions_invalidation")
        if isinstance(favorables, list) and favorables:
            ui.caption(f"Facteur favorable principal · {favorables[0]}")
        if isinstance(vigilances, list) and vigilances:
            ui.caption(f"Vigilance principale · {vigilances[0]}")
        elif isinstance(risques, list) and risques:
            ui.caption(f"Vigilance principale · {risques[0]}")
        if isinstance(manquantes, list) and manquantes:
            ui.caption(f"Données manquantes · {', '.join(manquantes)}")
        if isinstance(invalidations, list) and invalidations:
            ui.caption(f"Condition d’invalidation · {invalidations[0]}")
    ui.caption(donnees.get("rappel_prudence", "Ce scénario ne constitue pas une certitude."))
