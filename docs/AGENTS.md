# AGENTS.md

# AI Wealth Terminal - Agent Instructions

Ce dépôt est développé selon une architecture modulaire.

Avant toute modification :

- Lire le README.md.
- Lire les documents du dossier `docs/`.
- Comprendre le fonctionnement existant avant de modifier le code.

## Architecture

- `app.py` : point d'entrée.
- `pages/` : interface Streamlit.
- `core/` : logique métier.
- `services/` : accès aux API et services externes.
- `ui/` : composants graphiques.
- `docs/` : documentation du projet.

## Règles

- Une responsabilité par fichier.
- Préserver la compatibilité des fonctionnalités existantes.
- Éviter les duplications.
- Favoriser des fonctions courtes et lisibles.
- Respecter les conventions PEP 8.
- Ajouter de la documentation lorsqu'une fonctionnalité importante est créée.

## Objectif

Construire un terminal d'investissement assisté par l'IA, fiable, évolutif et pédagogique.

L'IA doit aider l'utilisateur à comprendre les marchés, pas décider à sa place.

Chaque recommandation doit être expliquée et accompagnée des risques associés.
