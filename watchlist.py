"""Persistance et gestion de la watchlist du scanner."""

import json
from pathlib import Path

from config import DEFAULT_WATCHLIST

FICHIER = Path("watchlist.json")


def charger_watchlist():
    if not FICHIER.exists():
        sauvegarder_watchlist(DEFAULT_WATCHLIST)
        return {
            categorie: list(actifs)
            for categorie, actifs in DEFAULT_WATCHLIST.items()
        }

    try:
        with FICHIER.open("r", encoding="utf-8") as fichier:
            data = json.load(fichier)

        if isinstance(data, dict):
            return data

    except (OSError, json.JSONDecodeError):
        pass

    return {
        categorie: list(actifs)
        for categorie, actifs in DEFAULT_WATCHLIST.items()
    }


def sauvegarder_watchlist(data):
    with FICHIER.open("w", encoding="utf-8") as fichier:
        json.dump(data, fichier, ensure_ascii=False, indent=2)


def ajouter_actif(categorie, symbole):
    watchlist = charger_watchlist()

    categorie = categorie.upper()
    symbole = symbole.upper().strip()

    if categorie not in watchlist:
        watchlist[categorie] = []

    if symbole and symbole not in watchlist[categorie]:
        watchlist[categorie].append(symbole)
        watchlist[categorie].sort()

    sauvegarder_watchlist(watchlist)


def supprimer_actif(categorie, symbole):
    watchlist = charger_watchlist()

    categorie = categorie.upper()
    symbole = symbole.upper().strip()

    if categorie in watchlist and symbole in watchlist[categorie]:
        watchlist[categorie].remove(symbole)

    sauvegarder_watchlist(watchlist)


def tous_les_actifs():
    watchlist = charger_watchlist()

    actifs = []

    for liste in watchlist.values():
        actifs.extend(liste)

    return actifs
