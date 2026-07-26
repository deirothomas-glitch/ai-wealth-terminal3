"""Analyse pure et descriptive de la composition d’un portefeuille."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from core.portfolio import convertir_nombre_positif, normaliser_position

TYPES_ORDONNES = ("action", "ETF", "crypto", "autre")
LIBELLES_TYPES = {
    "action": "Actions",
    "ETF": "ETF",
    "crypto": "Crypto",
    "autre": "Autres",
}
RAPPEL_PRUDENCE = (
    "Cette synthèse décrit uniquement la composition observée du portefeuille ; "
    "elle ne constitue ni un conseil, ni un ordre automatique."
)


def _liste_positions(valeur: Any) -> list[Any]:
    if not isinstance(valeur, Sequence) or isinstance(valeur, (str, bytes)):
        return []
    return list(valeur)


def _prix_valides(prix: Any) -> dict[str, float]:
    if not isinstance(prix, Mapping):
        return {}
    resultat = {}
    for symbole, valeur in prix.items():
        cle = str(symbole).strip().upper()
        nombre = convertir_nombre_positif(valeur)
        if cle and nombre is not None:
            resultat[cle] = nombre
    return resultat


def _niveau_diversification(nombre: int, poids_principal: float | None) -> tuple[str, str]:
    if nombre == 0:
        return "Faible", "Aucune position ne peut être valorisée avec les données disponibles."
    if nombre <= 2 or (poids_principal is not None and poids_principal >= 50):
        return "Faible", "Le portefeuille valorisé repose sur peu de lignes ou présente une concentration élevée."
    if nombre < 5 or (poids_principal is not None and poids_principal >= 35):
        return "Modérée", "Plusieurs lignes sont valorisées, mais leur nombre ou leur concentration reste intermédiaire."
    return "Bonne", "Au moins cinq lignes sont valorisées et aucune ne représente 35 % ou plus de la valeur calculée."


def analyser_portefeuille(positions: Any, prix_courants: Any) -> dict[str, Any]:
    """Décrit les expositions à partir des seules positions et valeurs disponibles.

    Le total correspond à la somme des lignes effectivement valorisables. Les
    lignes exclues sont toujours explicitées dans ``donnees_manquantes``.
    """
    donnees_chargees = isinstance(positions, Sequence) and not isinstance(positions, (str, bytes))
    sources = _liste_positions(positions)
    prix = _prix_valides(prix_courants)
    prix_absents: list[str] = []
    valeurs_impossibles: list[str] = []
    positions_incompletes: list[str] = []
    lignes: list[dict[str, Any]] = []

    for index, source in enumerate(sources, 1):
        if not isinstance(source, Mapping):
            positions_incompletes.append(f"Position {index} : format invalide.")
            valeurs_impossibles.append(f"Position {index} : valorisation impossible.")
            continue
        position = normaliser_position(source)
        symbole = position["symbole"]
        libelle = symbole or f"Position {index}"
        if not symbole:
            positions_incompletes.append(f"Position {index} : symbole absent.")
        if position["quantite"] is None:
            positions_incompletes.append(f"{libelle} : quantité absente ou invalide.")
        type_brut = str(source.get("type_actif", "")).strip().casefold()
        if type_brut not in ("action", "etf", "crypto", "autre"):
            positions_incompletes.append(f"{libelle} : type d’actif absent ou invalide, classé dans Autres.")
        prix_courant = prix.get(symbole) if symbole else None
        if symbole and prix_courant is None:
            prix_absents.append(symbole)
        if not symbole or position["quantite"] is None or prix_courant is None:
            valeurs_impossibles.append(f"{libelle} : valorisation impossible.")
            continue
        lignes.append({
            "symbole": symbole,
            "type_actif": position["type_actif"],
            "valeur": position["quantite"] * prix_courant,
        })

    agregats: dict[str, dict[str, Any]] = {}
    for ligne in lignes:
        symbole = ligne["symbole"]
        if symbole not in agregats:
            agregats[symbole] = dict(ligne)
        else:
            agregats[symbole]["valeur"] += ligne["valeur"]
            if agregats[symbole]["type_actif"] != ligne["type_actif"]:
                agregats[symbole]["type_actif"] = "autre"
                message = f"{symbole} : types d’actif contradictoires, classé dans Autres."
                if message not in positions_incompletes:
                    positions_incompletes.append(message)

    total = sum(x["valeur"] for x in agregats.values())
    principales = sorted(agregats.values(), key=lambda x: (-x["valeur"], x["symbole"]))
    principales_positions = [
        {
            "symbole": x["symbole"],
            "type_actif": x["type_actif"],
            "valeur": round(x["valeur"], 2),
            "poids": round(x["valeur"] / total * 100, 2) if total > 0 else None,
        }
        for x in principales[:5]
    ]
    poids_principal = principales_positions[0]["poids"] if principales_positions else None
    poids_top_5 = round(sum(x["valeur"] for x in principales[:5]) / total * 100, 2) if total > 0 else None

    valeurs_types = {type_actif: 0.0 for type_actif in TYPES_ORDONNES}
    for ligne in agregats.values():
        valeurs_types[ligne["type_actif"]] += ligne["valeur"]
    repartition = [
        {
            "type_actif": LIBELLES_TYPES[type_actif],
            "valeur": round(valeurs_types[type_actif], 2),
            "poids": round(valeurs_types[type_actif] / total * 100, 2),
        }
        for type_actif in TYPES_ORDONNES if total > 0 and valeurs_types[type_actif] > 0
    ]
    exposition_actions = round(valeurs_types["action"] / total * 100, 2) if total > 0 else None
    exposition_crypto = round(valeurs_types["crypto"] / total * 100, 2) if total > 0 else None
    niveau, justification = _niveau_diversification(len(agregats), poids_principal)

    constats = []
    if poids_principal is not None and poids_principal >= 50:
        constats.append(f"Concentration élevée : la première ligne représente {poids_principal:.2f} % de la valeur calculée.")
    if exposition_crypto is not None and exposition_crypto >= 50:
        constats.append(f"Forte exposition crypto constatée : {exposition_crypto:.2f} % de la valeur calculée.")
    if niveau == "Faible" and agregats:
        constats.append("Portefeuille peu diversifié selon le nombre et le poids des lignes valorisées.")

    manquantes = {
        "prix_absents": sorted(set(prix_absents)),
        "valeurs_impossibles": list(dict.fromkeys(valeurs_impossibles)),
        "positions_incompletes": list(dict.fromkeys(positions_incompletes)),
    }
    incomplet = any(manquantes.values())
    qualite = "Bonne" if agregats and not incomplet else ("Partielle" if agregats else "Insuffisante")
    resultat = {
        "donnees_chargees": donnees_chargees,
        "portefeuille_vide": donnees_chargees and not sources,
        "valeur_totale": round(total, 2) if agregats else (0.0 if donnees_chargees and not sources else None),
        "positions_total": len(sources),
        "positions_valorisees": len(agregats),
        "repartition_types": repartition,
        "concentration": {
            "position_principale": principales_positions[0]["symbole"] if principales_positions else None,
            "poids_principal": poids_principal,
            "poids_top_5": poids_top_5,
        },
        "diversification": {"niveau": niveau, "justification": justification},
        "expositions": {"actions": exposition_actions, "crypto": exposition_crypto},
        "principales_positions": principales_positions,
        "constats": constats,
        "donnees_manquantes": manquantes,
        "qualite_analyse": qualite,
        "rappel_prudence": RAPPEL_PRUDENCE,
    }
    json.dumps(resultat, ensure_ascii=False, allow_nan=False)
    return resultat
