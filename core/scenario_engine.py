"""Moteur pur et universel d'analyse multi-scénarios."""

from __future__ import annotations

import copy
import math
import json
from collections.abc import Mapping, Sequence
from typing import Any

SCENARIOS = ("haussier", "neutre", "baissier")
HORIZONS = ("court", "swing", "tendance")
CONFIANCES = ("Faible", "Modérée", "Élevée")
RAPPEL_PRUDENCE = (
    "Ces scénarios décrivent des possibilités conditionnelles, jamais une "
    "certitude, une garantie de gain ou un ordre automatique."
)
FORMULATIONS_INTERDITES = (
    "gain garanti",
    "rendement garanti",
    "hausse certaine",
    "baisse certaine",
    "sans risque",
    "signal infaillible",
    "achetez",
    "vendez",
)
RESUMES = {
    "haussier": (
        "Scénario conditionnel à considérer seulement si les facteurs "
        "favorables disponibles se maintiennent."
    ),
    "neutre": (
        "Scénario d’attente lorsque les informations disponibles ne donnent "
        "pas de direction suffisamment claire."
    ),
    "baissier": (
        "Scénario de dégradation à surveiller si les facteurs défavorables "
        "disponibles persistent."
    ),
}


def _textes(valeur: Any, limite: int = 12) -> list[str]:
    if not isinstance(valeur, Sequence) or isinstance(valeur, (str, bytes)):
        return []
    resultat = []
    vus = set()
    for element in valeur:
        if not isinstance(element, str) or not element.strip():
            continue
        texte = element.strip()
        if texte not in vus:
            resultat.append(texte)
            vus.add(texte)
        if len(resultat) >= limite:
            break
    return resultat


def _horizon(valeur: Any) -> str:
    texte = str(valeur or "").strip().casefold()
    correspondances = {
        "court": "court", "court terme": "court",
        "swing": "swing",
        "tendance": "tendance", "long terme": "tendance",
    }
    return correspondances.get(texte, "swing")


def _redaction_prudente(valeur: Any) -> str | None:
    if not isinstance(valeur, str) or not valeur.strip():
        return None
    texte = valeur.strip()[:800]
    texte_normalise = texte.casefold()
    if any(formulation in texte_normalise for formulation in FORMULATIONS_INTERDITES):
        return None
    return texte


def _confiance(favorables, defavorables, risques, manquantes, invalidations, qualite):
    couverture = sum(bool(x) for x in (favorables, defavorables, risques, invalidations))
    qualite_normalisee = str(qualite or "").strip().casefold()
    if len(manquantes) >= 3 or couverture <= 1 or qualite_normalisee == "insuffisant":
        return "Faible"
    if manquantes or couverture < 4 or qualite_normalisee in ("partiel", "partielle", ""):
        return "Modérée"
    return "Élevée"


def construire_scenarios(donnees: Mapping[str, Any] | None, horizon: str = "swing") -> dict[str, Any]:
    """Construit trois scénarios conditionnels à partir de faits fournis.

    Aucun fait absent n'est complété. La confiance décrit uniquement la
    couverture et la qualité des informations reçues ; elle ne représente pas
    une probabilité de performance future.
    """
    source = dict(donnees) if isinstance(donnees, Mapping) else {}
    favorables = _textes(source.get("facteurs_favorables"))
    defavorables = _textes(source.get("facteurs_defavorables"))
    risques = _textes(source.get("risques"))
    manquantes = _textes(source.get("donnees_manquantes"))
    invalidations = _textes(source.get("conditions_invalidation"))
    if not invalidations and "conditions_invalidation" not in manquantes:
        manquantes.append("conditions_invalidation")
    horizon_normalise = _horizon(horizon)
    confiance = _confiance(
        favorables, defavorables, risques, manquantes, invalidations,
        source.get("qualite"),
    )
    if len(favorables) > len(defavorables):
        principal = "haussier"
    elif len(defavorables) > len(favorables):
        principal = "baissier"
    else:
        principal = "neutre"

    resultat = {
        "scenario_principal": principal,
        "donnees_partielles": bool(manquantes),
    }
    for nom in SCENARIOS:
        resultat[f"scenario_{nom}"] = {
            "type": nom,
            "resume": RESUMES[nom],
            "facteurs_favorables": list(favorables),
            "facteurs_defavorables": list(defavorables),
            "risques_identifies": list(risques),
            "elements_manquants": list(manquantes),
            "horizon": horizon_normalise,
            "niveau_confiance": confiance,
            "conditions_invalidation": list(invalidations),
        }
    resultat["rappel_prudence"] = RAPPEL_PRUDENCE
    json.dumps(resultat, ensure_ascii=False, allow_nan=False)
    return resultat


def construire_scenarios_depuis_contrats(
    decision: Mapping[str, Any] | None = None,
    risque: Mapping[str, Any] | None = None,
    strategie: Mapping[str, Any] | None = None,
    horizon: str = "swing",
) -> dict[str, Any]:
    """Adapte les contrats existants sans recalculer leur logique métier."""
    decision_valide = decision if isinstance(decision, Mapping) else {}
    risque_valide = risque if isinstance(risque, Mapping) else {}
    strategie_valide = strategie if isinstance(strategie, Mapping) else {}
    invalidations = _textes(strategie_valide.get("conditions_invalidation"))
    stop = risque_valide.get("stop_loss")
    if isinstance(stop, (int, float)) and not isinstance(stop, bool) and math.isfinite(stop) and stop > 0:
        invalidations.append(f"Réévaluer le scénario si le seuil documenté à {stop:.8g} est atteint.")
    manquantes = _textes(decision_valide.get("donnees_manquantes"))
    manquantes.extend(
        f"risque.{x}" for x in _textes(risque_valide.get("donnees_manquantes"))
        if f"risque.{x}" not in manquantes
    )
    return construire_scenarios({
        "facteurs_favorables": decision_valide.get("facteurs_favorables", []),
        "facteurs_defavorables": decision_valide.get("facteurs_defavorables", []),
        "risques": _textes(
            _textes(decision_valide.get("risques"))
            + _textes(risque_valide.get("risques"))
        ),
        "donnees_manquantes": manquantes,
        "conditions_invalidation": invalidations,
        "qualite": strategie_valide.get("qualite_donnees", ""),
    }, horizon=horizon)


def enrichir_redaction_scenarios(resultat: Mapping[str, Any], redactions: Mapping[str, Any] | None) -> dict[str, Any]:
    """Enrichit uniquement les résumés, sans altérer les faits calculés."""
    copie = copy.deepcopy(dict(resultat)) if isinstance(resultat, Mapping) else construire_scenarios({})
    textes = redactions if isinstance(redactions, Mapping) else {}
    for nom in SCENARIOS:
        texte = _redaction_prudente(textes.get(nom))
        cle = f"scenario_{nom}"
        if texte is not None and isinstance(copie.get(cle), dict):
            copie[cle]["resume"] = texte
    json.dumps(copie, ensure_ascii=False, allow_nan=False)
    return copie
