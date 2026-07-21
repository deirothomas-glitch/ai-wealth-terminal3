import json
import os

FICHIER = "portfolio.json"


def charger_portefeuille():
    if os.path.exists(FICHIER):
        with open(FICHIER, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def sauvegarder_portefeuille(portefeuille):
    with open(FICHIER, "w", encoding="utf-8") as f:
        json.dump(portefeuille, f, indent=4)