"""Contrat pur de la fiche d’opportunité du parcours investisseur."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any


def _nombre(valeur: Any) -> float | None:
    if isinstance(valeur, bool):
        return None
    try:
        nombre = float(valeur)
    except (TypeError, ValueError, OverflowError):
        return None
    return nombre if math.isfinite(nombre) else None


def _texte(valeur: Any, defaut: str = "Indisponible") -> str:
    return valeur.strip() if isinstance(valeur, str) and valeur.strip() else defaut


def _textes(valeur: Any, limite: int = 12) -> list[str]:
    if not isinstance(valeur, Sequence) or isinstance(valeur, (str, bytes)):
        return []
    resultat = []
    for element in valeur:
        if isinstance(element, str) and element.strip() and element.strip() not in resultat:
            resultat.append(element.strip())
        if len(resultat) >= limite:
            break
    return resultat


def construire_fiche_opportunite(
    resultat_scanner: Mapping[str, Any] | None,
    opportunite: Mapping[str, Any] | None,
    decision: Mapping[str, Any] | None,
    plan_risque: Mapping[str, Any] | None,
    scenarios: Mapping[str, Any] | None,
    actualites: Any = None,
) -> dict[str, Any]:
    """Assemble les contrats existants sans score, réseau ni fait nouveau."""
    ligne = resultat_scanner if isinstance(resultat_scanner, Mapping) else {}
    classement = opportunite if isinstance(opportunite, Mapping) else {}
    choix = decision if isinstance(decision, Mapping) else {}
    plan = plan_risque if isinstance(plan_risque, Mapping) else {}
    scenarios_valides = dict(scenarios) if isinstance(scenarios, Mapping) else {}
    actualites_valides = [dict(x) for x in actualites if isinstance(x, Mapping)] if isinstance(actualites, list) else []

    score = _nombre(ligne.get("Score"))
    confiance = _nombre(choix.get("confiance"))
    qualite = _texte(classement.get("qualite_donnees"), "Non évaluée")
    raisons = _textes(ligne.get("Raisons"))
    favorables = _textes(choix.get("facteurs_favorables"))
    defavorables = _textes(choix.get("facteurs_defavorables"))
    risques = _textes(choix.get("risques"))
    risques.extend(x for x in _textes(plan.get("risques")) if x not in risques)
    manquantes = _textes(choix.get("donnees_manquantes"))
    manquantes.extend(
        f"risque.{x}" for x in _textes(plan.get("donnees_manquantes"))
        if f"risque.{x}" not in manquantes
    )
    recommandation = _texte(choix.get("recommandation"), "Attendre")
    conclusion = _texte(
        choix.get("resume"),
        "Les données disponibles ne permettent pas encore de formuler une conclusion suffisamment étayée.",
    )
    resultat = {
        "symbole": _texte(ligne.get("Actif"), _texte(classement.get("symbole"), "—")),
        "categorie": _texte(ligne.get("Catégorie"), _texte(classement.get("categorie"))),
        "conclusion": conclusion,
        "recommandation": recommandation,
        "pourquoi": raisons or favorables or ["Justification technique indisponible."],
        "facteurs_favorables": favorables,
        "facteurs_defavorables": defavorables,
        "qualite": {
            "niveau": qualite,
            "justification": _textes(classement.get("points_vigilance")) or manquantes,
        },
        "marche": {
            "prix": _nombre(ligne.get("Prix")),
            "variation": _nombre(ligne.get("Variation %")),
            "date_donnees": _texte(ligne.get("Date données")),
        },
        "analyse": {
            "score": int(score) if score is not None else None,
            "signal": _texte(ligne.get("Signal")),
            "decision": recommandation,
            "confiance": int(confiance) if confiance is not None else None,
        },
        "risques": risques or ["Les risques spécifiques ne sont pas suffisamment documentés."],
        "donnees_manquantes": manquantes,
        "scenarios": scenarios_valides,
        "actualites": actualites_valides[:5],
        "plan_risque": dict(plan),
        "decision_finale_utilisateur": True,
        "rappel_prudence": (
            "Cette fiche organise des informations disponibles ; elle ne constitue "
            "ni une garantie de gain ni un ordre d’investissement."
        ),
    }
    json.dumps(resultat, ensure_ascii=False, allow_nan=False)
    return resultat
