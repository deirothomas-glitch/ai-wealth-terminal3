# AI Wealth Terminal
## Development Guide

Version : 1.0

---

# 1. Vision du projet

AI Wealth Terminal est un terminal d'investissement intelligent développé pour assister son utilisateur dans l'analyse des marchés financiers grâce à l'intelligence artificielle.

L'objectif n'est pas de remplacer l'investisseur, mais de lui fournir une aide à la décision fiable, argumentée et compréhensible.

Chaque décision proposée doit pouvoir être expliquée.

Le projet doit évoluer progressivement jusqu'à devenir un véritable assistant d'investissement professionnel.

---

# 2. Objectif personnel du projet

Ce projet est développé dans le but de construire un outil d'aide à l'investissement capable d'accompagner son utilisateur dans la création progressive d'un patrimoine financier.

Le terminal devra permettre de :

- détecter des opportunités d'investissement
- analyser les risques
- améliorer la qualité des décisions
- suivre les performances
- apprendre des investissements réalisés

Le projet est pensé pour une utilisation quotidienne.

---

# 3. Philosophie

Le logiciel doit toujours privilégier :

✔ la qualité

✔ la simplicité

✔ la lisibilité

✔ la stabilité

✔ la modularité

Chaque nouvelle fonctionnalité doit apporter une réelle valeur.

Aucune fonctionnalité ne doit être ajoutée uniquement pour faire "plus de fonctionnalités".

---

# 4. Types d'actifs supportés

Le terminal doit progressivement prendre en charge :

- Actions
- ETF
- Cryptomonnaies
- Indices
- Matières premières

Version future :

- Forex
- Obligations

---

# 5. Architecture du projet

Le projet doit rester entièrement modulaire.

Une responsabilité par fichier.

Chaque module doit être indépendant.

Organisation recommandée :

/core

/services

/pages

/ui

/docs

.streamlit

---

# 6. Règles de développement

Toujours :

✔ écrire du code clair

✔ éviter les duplications

✔ créer des fonctions courtes

✔ commenter uniquement lorsque cela apporte une réelle valeur

✔ conserver une architecture propre

✔ respecter le principe "une responsabilité par fichier"

Ne jamais casser une fonctionnalité existante pour en ajouter une nouvelle.

---

# 7. Règles pour ChatGPT et Codex

Avant toute modification :

1. Comprendre le fonctionnement actuel.

2. Vérifier les dépendances.

3. Préserver la compatibilité.

4. Expliquer les modifications importantes.

5. Fournir du code professionnel.

Lorsque cela est possible :

- privilégier un remplacement complet du fichier plutôt que quelques lignes isolées

- éviter les modifications partielles difficiles à suivre

- documenter les changements importants

---

# 8. Style du code Python

Le code doit être :

- lisible
- documenté
- robuste
- facilement maintenable

Les noms des fonctions doivent être explicites.

Les constantes doivent être centralisées.

Les appels API doivent être isolés dans leurs propres modules.

---

# 9. Interface utilisateur

L'interface doit rester simple.

Professionnelle.

Moderne.

Lisible.

Priorités :

- rapidité
- ergonomie
- compréhension immédiate

L'utilisateur doit comprendre en quelques secondes l'état du marché.

---

# 10. Intelligence Artificielle

L'IA doit toujours expliquer :

Pourquoi acheter.

Pourquoi vendre.

Pourquoi attendre.

Pour chaque analyse, l'IA devra présenter :

Résumé.

Forces.

Faiblesses.

Risques.

Opportunités.

Scénario optimiste.

Scénario neutre.

Scénario pessimiste.

Niveau de confiance.

---

# 11. Système de scoring

Chaque actif devra être évalué selon plusieurs critères.

Exemple :

Analyse technique

Analyse fondamentale

Momentum

Volume

Actualités

Sentiment

Volatilité

Liquidité

Gestion du risque

Le résultat devra produire un score global sur 100.

---

# 12. Gestion du risque

Le terminal devra progressivement intégrer :

taille de position

stop-loss conseillé

take-profit conseillé

ratio risque/rendement

volatilité

drawdown

allocation optimale

Le risque est aussi important que le rendement.

---

# 13. Fonctionnalités principales

Dashboard

Watchlist

Scanner

Scoring

Analyse IA

Actualités

Portefeuille

Alertes

Historique

Journal d'investissement

---

# 14. Roadmap

## Release V2

Architecture propre

Dashboard professionnel

Scanner

Watchlist

Portefeuille

Analyse IA

Scoring

Actualités

Gestion du risque

Alertes

---

## Release V3

Journal d'investissement

Historique

Backtesting

Comparaison de plusieurs actifs

Assistant conversationnel

Analyse multi-timeframes

Performances du portefeuille

---

## Release V4

Connexion aux courtiers

Exécution des ordres

Synchronisation Cloud

Notifications intelligentes

Application mobile

Rapports automatiques

---

# 15. Vision long terme

Le projet doit progressivement devenir un véritable terminal d'analyse financière assisté par l'IA.

L'objectif est de disposer d'un outil personnel puissant, moderne, fiable et évolutif.

Chaque nouvelle version devra améliorer :

la qualité des analyses

la rapidité

la stabilité

l'expérience utilisateur

la précision des recommandations

sans jamais sacrifier la lisibilité du code.

---

# 16. Documentation

Toute nouvelle fonctionnalité importante doit être documentée.

Le dossier docs doit devenir la référence du projet.

Les principaux documents seront :

DEVELOPMENT_GUIDE.md

ARCHITECTURE.md

ROADMAP.md

CHANGELOG.md

RELEASE_NOTES.md

AI_PROMPTS.md

---

# 17. Principe fondamental

La priorité absolue est de construire un logiciel fiable, maintenable et évolutif.

Chaque amélioration doit rendre AI Wealth Terminal plus intelligent, plus robuste et plus utile.

La qualité du code est une fonctionnalité à part entière.

## 12. Stratégies et backtest

Les paramètres des profils résident uniquement dans `core/strategy_profiles.py`. `core/data_quality.py`, `core/strategy_engine.py`, `core/opportunity_ranking.py` et `core/backtest.py` restent purs et ne chargent aucune donnée. Les adaptations pandas et les téléchargements appartiennent aux services. Un signal historique calculé à la clôture ne peut être exécuté qu’à partir de la séance suivante. Les composants `ui/` affichent des contrats calculés sans relancer les moteurs.


# 14. Pipeline d’actualités et d’IA

Le pipeline suit cette direction : sources externes (`services/news_sources.py`), normalisation, déduplication, qualité, pertinence et sentiment (`core/`), agrégation (`services/news_aggregator.py`), construction d’un contexte JSON borné (`core/analysis_context.py`), appel externe (`services/ai_client.py`) puis validation défensive (`core/ai_response_validation.py`). Les composants `ui/` ne téléchargent rien et ne calculent aucun contrat.

Les moteurs `core` utilisent uniquement la bibliothèque standard, ne lisent ni le réseau ni l’horloge implicitement et ne mutent jamais leurs entrées. Toute date de référence doit être injectée. Les listes envoyées au modèle sont bornées et les champs inconnus de sa réponse sont ignorés.

Le modèle et le délai d’expiration sont centralisés dans `config.py`. Aucun appel IA ne doit avoir lieu au chargement d’une page : un bouton explicite est obligatoire. Sans clé, le client retourne un contrat sûr. Les erreurs ne doivent contenir ni secret ni détail réseau sensible.

Le cache d’actualités expire après 900 secondes. La persistance JSON locale utilise une écriture atomique, une lecture défensive et ne remplace jamais silencieusement un fichier invalide. Les clés API, conversations et données personnelles ne sont jamais placées dans le cache global.

Le briefing déterministe consomme exclusivement des contrats déjà calculés. Il ne relance ni Scanner, ni backtest, ni fournisseur. Sa synthèse IA reste facultative et explicitement déclenchée.
