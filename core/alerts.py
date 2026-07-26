"""Construction pure et déterministe d'alertes d'analyse."""

import math


NIVEAUX = ("information", "vigilance", "attention")
CATEGORIES = ("donnees", "decision", "risque")
STATUTS_PLAN = ("disponible", "partiel", "indisponible")
RECOMMANDATIONS = ("Surveiller", "Attendre", "Éviter")
DONNEES_PLAN_NON_SIGNIFICATIVES = ("capital_reference", "risque_max_pct")


def _nombre_fini(valeur):
    return (
        not isinstance(valeur, bool)
        and isinstance(valeur, (int, float))
        and math.isfinite(valeur)
    )


def _liste_textes(valeur):
    if not isinstance(valeur, list):
        return []
    resultat = []
    for element in valeur:
        if isinstance(element, str) and element.strip():
            texte = element.strip()
            if texte not in resultat:
                resultat.append(texte)
    return resultat


def _score_valide(score_data):
    return (
        isinstance(score_data, dict)
        and _nombre_fini(score_data.get("score"))
        and 0 <= score_data["score"] <= 100
        and isinstance(score_data.get("signal"), str)
        and bool(score_data["signal"].strip())
        and isinstance(score_data.get("raisons"), list)
        and isinstance(score_data.get("ventilation"), list)
    )


def _decision_valide(decision):
    return (
        isinstance(decision, dict)
        and isinstance(decision.get("recommandation"), str)
        and bool(decision["recommandation"].strip())
        and _nombre_fini(decision.get("confiance"))
        and isinstance(decision.get("donnees_manquantes"), list)
    )


def _plan_valide(plan_risque):
    return (
        isinstance(plan_risque, dict)
        and plan_risque.get("statut") in STATUTS_PLAN
        and isinstance(plan_risque.get("donnees_manquantes"), list)
    )


def _alerte(identifiant, niveau, categorie, titre, message, facteurs, action):
    return {
        "identifiant": identifiant,
        "niveau": niveau,
        "categorie": categorie,
        "titre": titre,
        "message": message,
        "facteurs": _liste_textes(facteurs),
        "action_suggeree": action,
        "decision_finale_utilisateur": True,
    }


def construire_alertes(
    score_data: dict,
    decision: dict,
    plan_risque: dict,
) -> list[dict]:
    """Transforme trois contrats existants en alertes JSON strictes.

    Aucun score, recommandation, ATR ou niveau de risque n'est recalculé.
    """
    score_ok = _score_valide(score_data)
    decision_ok = _decision_valide(decision)
    plan_ok = _plan_valide(plan_risque)
    alertes = []

    contrats_invalides = []
    if not score_ok:
        contrats_invalides.append("Score technique absent ou invalide.")
    if not decision_ok:
        contrats_invalides.append("Décision prudente absente ou invalide.")
    if not plan_ok:
        contrats_invalides.append("Plan de risque absent ou invalide.")

    manquantes_decision = (
        _liste_textes(decision.get("donnees_manquantes"))
        if decision_ok else []
    )
    manquantes_plan = (
        _liste_textes(plan_risque.get("donnees_manquantes"))
        if plan_ok else []
    )
    manquantes_significatives = [
        element for element in manquantes_plan
        if element not in DONNEES_PLAN_NON_SIGNIFICATIVES
    ]
    plan_indisponible = plan_ok and plan_risque["statut"] == "indisponible"

    facteurs_donnees = list(contrats_invalides)
    facteurs_donnees.extend(
        f"Donnée de décision manquante : {element}."
        for element in manquantes_decision
    )
    facteurs_donnees.extend(
        f"Donnée de risque manquante : {element}."
        for element in manquantes_significatives
    )
    if plan_indisponible:
        facteurs_donnees.append("Le plan de risque est indisponible.")
    if facteurs_donnees:
        niveau = "attention" if len(contrats_invalides) >= 2 else "vigilance"
        alertes.append(_alerte(
            "donnees-incompletes", niveau, "donnees",
            "Données à vérifier",
            "Certaines données nécessaires à l’analyse sont incomplètes ou indisponibles.",
            facteurs_donnees,
            "Vérifier la disponibilité et la fraîcheur des données avant de poursuivre.",
        ))

    if decision_ok:
        recommandation = decision["recommandation"].strip()
        facteurs = (
            _liste_textes(decision.get("facteurs_favorables"))
            + _liste_textes(decision.get("facteurs_defavorables"))
            + _liste_textes(decision.get("facteurs_neutres"))
            + _liste_textes(decision.get("risques"))
        )
        action_existante = decision.get("action_suggeree")
        if recommandation == "Surveiller":
            niveau, titre = "vigilance", "Signal à surveiller"
            message = "Le signal mérite un suivi, sans suggérer une entrée immédiate."
            action = "Attendre une confirmation supplémentaire et vérifier la fraîcheur des données."
        elif recommandation == "Attendre":
            niveau, titre = "information", "Attendre une configuration plus claire"
            message = "La décision prudente ne suggère aucune entrée immédiate."
            action = "Attendre une configuration plus claire avant de réévaluer l’actif."
        elif recommandation == "Éviter":
            niveau, titre = "attention", "Nouvelle exposition à éviter"
            message = (
                "Le risque ou la qualité des éléments disponibles est insuffisant "
                "pour envisager une nouvelle exposition. Ce message ne suppose "
                "pas que l’actif est déjà détenu."
            )
            action = "Ne pas initier de nouvelle exposition sur la base de cette analyse."
        elif recommandation == "Acheter":
            niveau = titre = message = action = None
        else:
            niveau, titre = "vigilance", "Recommandation non reconnue"
            message = "La recommandation reçue ne permet pas de formuler une alerte fiable."
            action = "Vérifier les informations disponibles avant toute décision."
        if niveau is not None:
            if isinstance(action_existante, str) and action_existante.strip():
                facteurs.append(action_existante.strip())
            alertes.append(_alerte(
                f"decision-{recommandation.casefold()}", niveau, "decision",
                titre, message, facteurs, action,
            ))

    if plan_ok:
        statut = plan_risque["statut"]
        risques = _liste_textes(plan_risque.get("risques"))
        if statut == "disponible" and risques:
            alertes.append(_alerte(
                "risque-disponible", "information", "risque",
                "Plan de risque disponible",
                "Des niveaux indicatifs de gestion du risque sont disponibles.",
                risques, "Consulter le plan et vérifier qu’il correspond au risque accepté.",
            ))
        elif statut == "partiel":
            alertes.append(_alerte(
                "risque-partiel", "vigilance", "risque",
                "Plan de risque partiel",
                "Le plan ne permet pas de déterminer une taille de position complète.",
                risques + manquantes_plan,
                "Définir un capital de référence et un risque maximal avant toute décision.",
            ))
        elif statut == "indisponible":
            alertes.append(_alerte(
                "risque-indisponible", "attention", "risque",
                "Plan de risque indisponible",
                "Aucun stop-loss ou objectif indicatif fiable n’est disponible.",
                risques, "Attendre des données suffisantes avant de définir un plan de risque.",
            ))

    return alertes[:3]
