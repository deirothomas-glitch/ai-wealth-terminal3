"""Présentation compacte de la fiche d’opportunité du parcours investisseur."""

from html import escape
import math


def _format_nombre(valeur, suffixe=""):
    if not isinstance(valeur, (int, float)) or isinstance(valeur, bool) or not math.isfinite(valeur):
        return "Indisponible"
    return f"{valeur:,.2f}{suffixe}".replace(",", " ")


def _liste(ui, titre, elements, repli):
    ui.markdown(f"**{titre}**")
    valides = [x for x in elements if isinstance(x, str) and x.strip()] if isinstance(elements, list) else []
    if not valides:
        ui.caption(repli)
    for element in valides:
        ui.write(f"• {element}")


def afficher_fiche_opportunite(ui, fiche, afficher_scenarios_fn=None, afficher_actualites_fn=None):
    """Affiche les huit premières sections sans calcul ni appel externe."""
    donnees = fiche if isinstance(fiche, dict) else {}
    symbole = str(donnees.get("symbole", "—"))
    recommandation = str(donnees.get("recommandation", "Attendre"))
    ui.header(f"🎯 Fiche d’opportunité — {symbole}")
    ui.caption("Parcours : conclusion → compréhension → risque → décision documentée")

    ui.subheader("1. Conclusion")
    classe = "awt-badge--good" if recommandation == "Surveiller" else ("awt-badge--bad" if recommandation == "Éviter" else "awt-badge--warn")
    ui.markdown(
        f'<div class="awt-card"><span class="awt-badge {classe}">{escape(recommandation)}</span>'
        f'<div class="awt-card-title">{escape(str(donnees.get("conclusion", "Conclusion indisponible.")))}</div></div>',
        unsafe_allow_html=True,
    )

    ui.subheader("2. Pourquoi cette conclusion")
    _liste(ui, "Éléments analysés", donnees.get("pourquoi"), "Justification indisponible.")
    _liste(ui, "Facteurs défavorables", donnees.get("facteurs_defavorables"), "Aucun facteur défavorable documenté.")

    ui.subheader("3. Qualité des données")
    qualite = donnees.get("qualite", {}) if isinstance(donnees.get("qualite"), dict) else {}
    ui.markdown(f'<span class="awt-badge awt-badge--warn">Qualité · {escape(str(qualite.get("niveau", "Non évaluée")))}</span>', unsafe_allow_html=True)
    _liste(ui, "Limites connues", qualite.get("justification"), "Aucune limite supplémentaire documentée.")

    ui.subheader("4. Données de marché")
    marche = donnees.get("marche", {}) if isinstance(donnees.get("marche"), dict) else {}
    colonnes = ui.columns(3)
    colonnes[0].metric("Prix", _format_nombre(marche.get("prix")))
    colonnes[1].metric("Variation", _format_nombre(marche.get("variation"), " %"))
    colonnes[2].metric("Date des données", marche.get("date_donnees", "Indisponible"))

    ui.subheader("5. Score, décision et confiance")
    analyse = donnees.get("analyse", {}) if isinstance(donnees.get("analyse"), dict) else {}
    colonnes = ui.columns(4)
    colonnes[0].metric("Score technique", "—" if analyse.get("score") is None else f"{analyse['score']}/100")
    colonnes[1].metric("Signal", analyse.get("signal", "Indisponible"))
    colonnes[2].metric("Décision prudente", analyse.get("decision", "Attendre"))
    colonnes[3].metric("Couverture technique", "—" if analyse.get("confiance") is None else f"{analyse['confiance']}/100")
    ui.caption("La couverture technique ne représente pas une probabilité de gain.")

    ui.subheader("6. Risques identifiés")
    _liste(ui, "Risques et limites", donnees.get("risques"), "Risques spécifiques indisponibles.")
    if donnees.get("donnees_manquantes"):
        _liste(ui, "Données manquantes", donnees.get("donnees_manquantes"), "")

    ui.subheader("7. Scénarios")
    if afficher_scenarios_fn is not None:
        afficher_scenarios_fn(donnees.get("scenarios", {}), ui)
    else:
        ui.caption("Scénarios indisponibles.")

    ui.subheader("8. Actualités")
    actualites = donnees.get("actualites", [])
    if afficher_actualites_fn is not None:
        afficher_actualites_fn(actualites, limite=5)
    elif not actualites:
        ui.info("Aucune actualité chargée pour cet actif.")
    ui.caption(donnees.get("rappel_prudence", "La décision finale appartient à l’utilisateur."))
