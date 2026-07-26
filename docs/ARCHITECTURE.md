[t# AI Wealth Terminal
# Architecture

Version 1.0

---

# Objectif

Le projet est construit selon une architecture modulaire.

Chaque dossier possède une responsabilité précise.

Chaque fichier possède une seule responsabilité.

---

# Structure

app.py

Point d'entrée de l'application.

---

pages/

Pages Streamlit.

Chaque page correspond à une fonctionnalité.

---

services/

Communication avec les API.

Téléchargement des données.

Analyse IA.

News.

---

core/

Fonctions métier.

Calculs.

Scoring.

Gestion du portefeuille.

Gestion du risque.

---

ui/

Composants graphiques.

Widgets.

Cartes.

Graphiques.

---

docs/

Documentation complète du projet.

---

.streamlit/

Configuration Streamlit.

Secrets.

---

# Règles

Aucun fichier ne doit devenir trop volumineux.

Lorsqu'un fichier dépasse environ 300 lignes, envisager de le découper en plusieurs modules cohérents.

---

Les dépendances doivent toujours aller dans le même sens :

Interface

↓

Services

↓

Core

↓

Données