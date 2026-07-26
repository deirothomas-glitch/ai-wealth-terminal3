# AI Wealth Terminal
# AI Prompts & Development Instructions

Version : 1.0

---

# Mission

Toute intelligence artificielle intervenant sur ce projet doit contribuer à construire un terminal d'investissement professionnel, fiable et évolutif.

L'objectif est d'améliorer le projet sans casser les fonctionnalités existantes.

---

# Avant toute modification

Toujours :

- comprendre le fonctionnement actuel
- analyser les dépendances
- identifier les impacts
- préserver la compatibilité
- expliquer les changements importants

---

# Style de développement

Toujours privilégier :

✔ une architecture modulaire

✔ une responsabilité par fichier

✔ du code lisible

✔ des fonctions courtes

✔ des commentaires utiles

✔ une documentation claire

---

# Structure

Respecter l'organisation du projet.

Ne jamais déplacer des fichiers sans justification.

Ne jamais créer de doublons.

Créer un nouveau module lorsque cela améliore la lisibilité.

---

# Python

Respecter PEP8.

Utiliser le typage lorsque cela apporte de la clarté.

Éviter les variables globales.

Créer des fonctions réutilisables.

---

# Streamlit

Les pages Streamlit doivent uniquement gérer :

- l'affichage
- les interactions utilisateur

La logique métier doit rester dans les modules dédiés.

---

# Intelligence artificielle

Toutes les analyses doivent être argumentées.

Ne jamais produire une recommandation sans justification.

Présenter :

- les points positifs
- les points négatifs
- les risques
- un niveau de confiance

---

# Gestion des erreurs

Toutes les erreurs doivent être :

- anticipées
- gérées proprement
- compréhensibles

Aucune exception ne doit interrompre brutalement l'application.

---

# Refactoring

Lors d'un refactoring :

- conserver le comportement existant
- améliorer la lisibilité
- réduire la complexité
- documenter les changements

---

# Qualité

Toujours privilégier :

la qualité

la stabilité

la maintenabilité

avant la rapidité de développement.