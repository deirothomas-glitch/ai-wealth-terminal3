"""Carte partagée de synthèse descriptive du portefeuille."""

from html import escape
import math


def _pourcentage(valeur):
    if not isinstance(valeur, (int, float)) or isinstance(valeur, bool) or not math.isfinite(valeur):
        return "Indisponible"
    return f"{valeur:.2f} %"


def _montant(valeur):
    if not isinstance(valeur, (int, float)) or isinstance(valeur, bool) or not math.isfinite(valeur):
        return "Indisponible"
    return f"{valeur:,.2f} €".replace(",", " ")


def afficher_intelligence_portefeuille(interface, analyse, compact=False):
    """Affiche le contrat pur sans calcul, mutation ou chargement externe."""
    ui = interface
    donnees = analyse if isinstance(analyse, dict) else {}
    ui.subheader("🧩 Intelligence du portefeuille")
    if not donnees.get("donnees_chargees"):
        ui.info("Les données du portefeuille ne sont pas encore disponibles dans cette session.")
        ui.caption(donnees.get("rappel_prudence", "Synthèse descriptive uniquement."))
        return
    if donnees.get("portefeuille_vide"):
        ui.info("Le portefeuille est vide. La synthèse de composition sera disponible après l’ajout d’une position.")
        ui.caption(donnees.get("rappel_prudence", "Synthèse descriptive uniquement."))
        return

    qualite = donnees.get("qualite_analyse", "Insuffisante")
    niveau = donnees.get("diversification", {}).get("niveau", "Faible")
    classe_qualite = "awt-badge--good" if qualite == "Bonne" else ("awt-badge--warn" if qualite == "Moyenne" else "awt-badge--bad")
    classe_diversification = "awt-badge--good" if niveau == "Bonne" else ("awt-badge--warn" if niveau == "Modérée" else "awt-badge--bad")
    ui.markdown(
        '<div class="awt-card">'
        f'<span class="awt-badge {classe_qualite}">Qualité · {escape(qualite)}</span>'
        f'<span class="awt-badge {classe_diversification}">Diversification · {escape(niveau)}</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    mesures = [
        ("Exposition actions", _pourcentage(donnees.get("expositions", {}).get("actions"))),
        ("Exposition crypto", _pourcentage(donnees.get("expositions", {}).get("crypto"))),
        ("Poids des cinq premières", _pourcentage(donnees.get("concentration", {}).get("poids_top_5"))),
    ]
    if not compact:
        mesures.insert(0, ("Valeur calculée", _montant(donnees.get("valeur_totale"))))
    taille_ligne = 2 if len(mesures) == 4 else 3
    for debut in range(0, len(mesures), taille_ligne):
        groupe = mesures[debut:debut + taille_ligne]
        colonnes = ui.columns(taille_ligne)
        for colonne, (libelle, valeur) in zip(colonnes, groupe):
            colonne.metric(libelle, valeur)
    ui.caption(donnees.get("justification_qualite", "Qualité non évaluée."))
    ui.caption(donnees.get("diversification", {}).get("justification", "Diversification non évaluée."))

    repartition = donnees.get("repartition_types", [])
    if repartition:
        ui.markdown("**Répartition par type d’actif**")
        ui.write(" · ".join(f"{x.get('type_actif', 'Autres')} : {_pourcentage(x.get('poids'))}" for x in repartition))
    principales = donnees.get("principales_positions", [])
    if principales:
        ui.markdown("**Principales positions**")
        ui.write(" · ".join(f"{x.get('symbole', '—')} : {_pourcentage(x.get('poids'))}" for x in principales))
    for constat in donnees.get("constats", []):
        if isinstance(constat, str):
            ui.warning(constat)

    manquantes = donnees.get("donnees_manquantes", {})
    details = []
    prix_absents = manquantes.get("prix_absents", []) if isinstance(manquantes, dict) else []
    impossibles = manquantes.get("valeurs_impossibles", []) if isinstance(manquantes, dict) else []
    incompletes = manquantes.get("positions_incompletes", []) if isinstance(manquantes, dict) else []
    if prix_absents:
        details.append("Prix absents ou invalides : " + ", ".join(prix_absents))
    details.extend(impossibles)
    details.extend(incompletes)
    if details:
        ui.markdown("**Données manquantes ou incomplètes**")
        for detail in details:
            ui.caption(f"• {detail}")
    ui.caption(donnees.get("rappel_prudence", "Synthèse descriptive uniquement."))
