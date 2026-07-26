# 📈 AI Wealth Terminal

> Un terminal d'investissement intelligent assisté par l'IA, conçu pour aider les investisseurs à analyser les marchés financiers de manière claire, structurée et argumentée.

---

# 🎯 Vision

AI Wealth Terminal est un projet personnel visant à construire un assistant d'analyse financière moderne.

L'objectif est d'aider l'utilisateur à :

- analyser les actions
- analyser les ETF
- analyser les cryptomonnaies
- suivre un portefeuille
- comprendre les risques
- prendre des décisions plus éclairées grâce à l'intelligence artificielle

L'application ne remplace jamais le jugement de l'investisseur. Elle fournit des informations, des analyses et des scénarios pour faciliter la prise de décision.

---

# ✨ Fonctionnalités actuelles

- 📊 Dashboard interactif
- 📈 Graphiques en chandeliers (Plotly)
- 👀 Watchlist
- 💼 Gestion du portefeuille
- 📰 Actualités financières
- 🤖 Analyse assistée par l'IA
- 📉 Scanner de marché
- 📋 Système de scoring
- ⚙️ Architecture modulaire
- 📚 Documentation complète

---

# 🚀 Feuille de route

## Release V2

- Dashboard professionnel
- Scanner intelligent
- Scoring avancé
- Analyse IA
- Actualités
- Gestion du portefeuille
- Gestion du risque

## Release V3

- Journal d'investissement
- Backtesting
- Analyse multi-timeframes
- Assistant conversationnel
- Historique des performances
- Alertes intelligentes

## Release V4

- Connexion aux courtiers
- Passage d'ordres
- Synchronisation Cloud
- Application mobile
- Rapports automatiques

---

# 🏗️ Architecture

Le projet suit une architecture modulaire.

```text
AI-WEALTH-TERMINAL3
│
├── app.py
├── pages/
├── services/
├── core/
├── ui/
├── docs/
└── .streamlit/
```

Chaque dossier possède une responsabilité précise afin de garantir une bonne maintenabilité.

---

# 🛠️ Technologies

- Python
- Streamlit
- Plotly
- Pandas
- yfinance
- OpenAI API
- GitHub
- GitHub Codespaces

---

# 📦 Installation

Cloner le dépôt :

```bash
git clone <URL_DU_DEPOT>
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Créer le fichier :

```text
.streamlit/secrets.toml
```

Ajouter votre clé OpenAI :

```toml
OPENAI_API_KEY="votre_cle_api"
```

Lancer l'application :

```bash
streamlit run app.py
```

---

## Utiliser le portefeuille

Ouvrez **💼 Portefeuille** dans la navigation. Le formulaire permet d’enregistrer le symbole, la quantité, le prix d’entrée et, si vous le souhaitez, un stop, un objectif et des notes. Un stop est un seuil personnel de protection : il peut être situé sous le prix d’entrée ou avoir été remonté. L’objectif est le niveau auquel vous souhaitez réévaluer la position.

Le bouton **Rafraîchir les prix** récupère une fois le dernier prix de chaque symbole unique. Le gain/perte non réalisé compare la valeur courante au capital investi ; lorsqu’un prix manque, l’application l’indique sans inventer de valeur. Les alertes signalent notamment un prix indisponible, un stop absent, proche ou atteint, et un objectif atteint. Elles restent informatives : la décision finale appartient toujours à l’utilisateur.

Sous chaque position, les actions natives permettent de la modifier, de la clôturer totalement avec un prix et une date de sortie, ou de la supprimer après confirmation. Une clôture calcule le résultat réalisé. Les ouvertures, modifications, clôtures et suppressions alimentent automatiquement le **Journal**, affiché en bas de page avec les positions clôturées et leurs statistiques.

> L’application fournit une aide à l’analyse et à la gestion du risque. Elle ne garantit aucun rendement et ne remplace pas une décision personnelle ou un conseil financier professionnel.

## Stratégies, classement et backtest

Trois profils centralisés sont disponibles : **Court terme** pour les impulsions de quelques séances, **Swing** pour les mouvements de plusieurs jours à plusieurs semaines et **Tendance** pour les mouvements plus persistants. Le Scanner permet de choisir un profil, puis classe les résultats selon le score technique, le score propre à la stratégie, la qualité des données, la confiance, la décision prudente et la disponibilité du plan de risque. Les filtres de confiance, qualité et décision facilitent la lecture sans relancer les téléchargements.

La page **Stratégies** lance un backtest uniquement après confirmation par le bouton dédié. Choisissez un symbole, un profil, un capital, une taille de position, des frais et un slippage. Le signal d’une séance est exécuté au plus tôt à l’ouverture suivante afin d’éviter d’utiliser une information future. Le résultat reste disponible dans la session et peut préparer, sans l’ajouter automatiquement, une position dans le Portefeuille.

Le **drawdown maximal** mesure la plus forte baisse entre un sommet de la courbe de capital et le creux suivant. Le **profit factor** compare les gains bruts aux pertes brutes ; il doit toujours être lu avec la performance totale et le nombre d’opérations. Le score décrit les indicateurs actuels, la confiance leur cohérence et leur couverture, la décision reste une recommandation prudente, et la performance historique décrit uniquement la simulation passée.

Le backtest est une simplification : il ne garantit aucun résultat futur et ne reproduit pas parfaitement la liquidité, les gaps, l’exécution réelle ou la fiscalité. Les données de marché sont mises en cache cinq minutes (`CACHE_TTL = 300`) afin de réduire les téléchargements répétés ; les données personnelles du portefeuille ne sont pas placées dans ce cache global.

# 📚 Documentation

Toute la documentation est disponible dans le dossier **docs/**.

- DEVELOPMENT_GUIDE.md
- PROJECT_VISION.md
- ARCHITECTURE.md
- ROADMAP.md
- CODING_STANDARDS.md
- AI_PROMPTS.md
- CONTRIBUTING.md

---

# 🎯 Philosophie

Chaque recommandation produite par AI Wealth Terminal doit être :

- argumentée
- transparente
- compréhensible
- accompagnée des risques associés

L'intelligence artificielle est un assistant d'analyse, pas un décideur.

---

# 📄 Licence

Ce projet est développé à des fins d'apprentissage et d'évolution continue.

---

# 👨‍💻 Auteur

Développé par Thomas Escudeiro.

Avec l'assistance de ChatGPT et Codex.

## Intelligence de marché, actualités et Assistant IA

La page **Actualités** agrège les fournisseurs configurés, normalise les métadonnées, supprime les doublons et évalue séparément la qualité, la pertinence et le sentiment lexical. Une source non répertoriée n’est pas déclarée fausse : elle est signalée avec une formulation neutre. Les titres, sources et liens ne sont jamais inventés, et seuls les résumés courts et métadonnées sont affichés.

Les actualités ne sont rafraîchies qu’après un clic utilisateur. Le cache applicatif est limité à 15 minutes (`NEWS_CACHE_TTL = 900`) et un cache JSON local atomique peut conserver le dernier lot normalisé. Le dossier `data_cache/` est ignoré par Git. Une panne d’un fournisseur est isolée et ne bloque pas les autres fonctions.

Le **Briefing du marché** du Dashboard fonctionne sans OpenAI. Il réutilise les indices, le dernier classement Scanner, les actualités déjà disponibles et les alertes de positions présentes dans la session. Il ne relance ni scan, ni backtest, ni analyse IA. La synthèse IA du briefing nécessite un clic explicite.

L’**Assistant IA** permet de choisir un actif et un profil, puis de poser une question libre ou suggérée. Seules les données nécessaires de l’actif et, lorsqu’elle existe, sa position correspondante sont transmises. L’historique de conversation est limité à la session et n’est pas écrit sur disque.

### Configuration facultative d’OpenAI

L’application reste utilisable sans clé IA. Pour activer les synthèses structurées, définir `OPENAI_API_KEY` dans une variable d’environnement ou dans un fichier local non versionné :

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY="votre_cle"
```

Le modèle est configuré une seule fois avec `AI_DEFAULT_MODEL` dans `config.py`. La clé n’est ni enregistrée dans le cache, ni affichée, ni incluse dans les erreurs. Les réponses sont validées avant affichage et doivent distinguer faits et interprétations, présenter des scénarios opposés, les risques, les données manquantes et leurs limites.

### Limites

Le sentiment lexical n’est pas une prévision de prix. Une actualité favorable ne signifie pas que le cours montera. Les dates, résumés et symboles peuvent manquer selon le fournisseur. Une synthèse IA peut être incomplète ou erronée ; elle ne constitue ni une promesse de performance, ni une instruction financière. La décision finale appartient toujours à l’utilisateur.
