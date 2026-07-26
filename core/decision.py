"""Construction déterministe d'une décision technique expliquée."""

import math
from typing import Dict


CRITERES_ATTENDUS = (
    "Tendance EMA 20",
    "RSI",
    "MACD",
    "Bandes de Bollinger",
    "Volume",
)

RECOMMANDATION_ACHETER = "Acheter"
RECOMMANDATION_SURVEILLER = "Surveiller"
RECOMMANDATION_ATTENDRE = "Attendre"
RECOMMANDATION_EVITER = "Éviter"
RECOMMANDATIONS_AUTORISEES = (
    RECOMMANDATION_ACHETER,
    RECOMMANDATION_SURVEILLER,
    RECOMMANDATION_ATTENDRE,
    RECOMMANDATION_EVITER,
)

CRITERE_SCORE_BASE = "Score de base"
CRITERE_DONNEES_INSUFFISANTES = "Données insuffisantes"
SIGNAL_DONNEES_INSUFFISANTES = "DONNÉES INSUFFISANTES"

PENALITE_CRITERE_MANQUANT = 12
PENALITE_CONTRADICTION_MAX = 30
PENALITE_NEUTRALITE = 40
PENALITE_SCORE_INVALIDE = 25
PENALITE_SIGNAL_INVALIDE = 5
PENALITE_RAISONS_INVALIDES = 5
PENALITE_VENTILATION_INVALIDE = 40
PENALITE_CONTRIBUTION_INVALIDE = 10
PLAFOND_CONTRIBUTIONS_INVALIDES = 30
PENALITE_RAISON_ABSENTE = 3
PLAFOND_RAISONS_ABSENTES = 15
PENALITE_DOUBLON = 5
PLAFOND_DOUBLONS = 15

PLAFOND_GENERAL = 90
PLAFOND_DONNEES_INSUFFISANTES = 20
PLAFOND_COUVERTURE_INSUFFISANTE = 40
PLAFOND_CRITERES_NEUTRES = 35
PLAFOND_CONTRADICTION_FORTE = 50
SEUIL_CONTRADICTION_FORTE = 0.20

RISQUES_PERMANENTS = (
    "Une analyse technique ne garantit pas l'évolution future du prix.",
    "Le contexte de risque et la situation personnelle ne sont pas évalués dans cette étape.",
)
RISQUE_DONNEES_MANQUANTES = (
    "Certaines données techniques sont manquantes ou invalides."
)
RISQUE_CONTRADICTION_FORTE = "Les critères techniques se contredisent fortement."
FACTEUR_REPLI = "Aucun critère technique exploitable."

ORDRE_CLES_SORTIE = (
    "recommandation",
    "confiance",
    "resume",
    "facteurs_favorables",
    "facteurs_defavorables",
    "facteurs_neutres",
    "risques",
    "donnees_manquantes",
    "action_suggeree",
    "decision_finale_utilisateur",
)


def _nombre_fini(valeur):
    return (
        not isinstance(valeur, bool)
        and isinstance(valeur, (int, float))
        and math.isfinite(valeur)
    )


def _ajouter_unique(liste, valeurs_vues, texte):
    if texte not in valeurs_vues:
        liste.append(texte)
        valeurs_vues.add(texte)


def _textes_decision(recommandation, donnees_insuffisantes, tous_neutres):
    if donnees_insuffisantes:
        return (
            "Les données techniques sont insuffisantes pour prendre position.",
            "Attendre des données techniques plus complètes avant de réévaluer l'actif.",
        )
    if tous_neutres:
        return (
            "Les critères techniques ne donnent pas de direction claire.",
            "Ne rien faire pour le moment et attendre une direction technique plus claire.",
        )
    if recommandation == RECOMMANDATION_SURVEILLER:
        return (
            "Les éléments techniques justifient une surveillance, pas une décision d'achat.",
            "Surveiller l'actif et évaluer le risque avant toute décision.",
        )
    if recommandation == RECOMMANDATION_EVITER:
        return (
            "Les éléments techniques sont défavorables ; mieux vaut écarter l'actif pour le moment.",
            "Ne pas initier de position sur la base des données techniques actuelles.",
        )
    return (
        "Le signal technique est trop faible pour justifier une action immédiate.",
        "Ne rien faire pour le moment et attendre un signal technique plus clair.",
    )


def construire_decision(score_data: Dict) -> Dict:
    """Construit une décision technique prudente et entièrement déterministe.

    La confiance mesure seulement la couverture des critères, leur cohérence et
    la qualité structurelle des données reçues. Elle ne représente ni une
    probabilité de gain, ni une prévision de performance, ni une certitude sur
    l'évolution future du prix.
    """
    entree_valide = isinstance(score_data, dict)
    donnees = score_data if entree_valide else {}

    facteurs_favorables = []
    facteurs_defavorables = []
    facteurs_neutres = []
    textes_favorables = set()
    textes_defavorables = set()
    textes_neutres = set()
    donnees_manquantes = []

    score = donnees.get("score")
    score_valide = _nombre_fini(score) and 0 <= score <= 100
    if not score_valide:
        donnees_manquantes.append("score")

    signal = donnees.get("signal")
    signal_valide = isinstance(signal, str) and bool(signal.strip())
    if not signal_valide:
        donnees_manquantes.append("signal")

    raisons = donnees.get("raisons")
    raisons_valides = (
        isinstance(raisons, list)
        and all(isinstance(raison, str) for raison in raisons)
    )
    if not raisons_valides:
        donnees_manquantes.append("raisons")

    ventilation = donnees.get("ventilation")
    ventilation_valide = isinstance(ventilation, list)
    if not ventilation_valide:
        donnees_manquantes.append("ventilation")
        ventilation = []

    criteres_valides = {}
    doublons = 0
    contributions_invalides = 0
    raisons_absentes = 0
    marqueur_donnees_insuffisantes = False

    for entree in ventilation:
        if not isinstance(entree, dict):
            continue
        critere = entree.get("critere")
        if not isinstance(critere, str) or not critere.strip():
            continue
        critere = critere.strip()

        if critere == CRITERE_SCORE_BASE:
            continue
        if critere == CRITERE_DONNEES_INSUFFISANTES:
            marqueur_donnees_insuffisantes = True
            raison = entree.get("raison")
            texte = raison.strip() if isinstance(raison, str) and raison.strip() else critere
            _ajouter_unique(facteurs_neutres, textes_neutres, texte)
            continue
        if critere not in CRITERES_ATTENDUS:
            continue

        contribution = entree.get("contribution")
        if not _nombre_fini(contribution):
            contributions_invalides += 1
            continue
        if critere in criteres_valides:
            doublons += 1
            continue

        raison = entree.get("raison")
        if isinstance(raison, str) and raison.strip():
            texte = raison.strip()
        else:
            texte = critere
            raisons_absentes += 1

        criteres_valides[critere] = contribution
        if contribution > 0:
            _ajouter_unique(facteurs_favorables, textes_favorables, texte)
        elif contribution < 0:
            _ajouter_unique(facteurs_defavorables, textes_defavorables, texte)
        else:
            _ajouter_unique(facteurs_neutres, textes_neutres, texte)

    for critere in CRITERES_ATTENDUS:
        if critere not in criteres_valides:
            donnees_manquantes.append(critere)

    positif = sum(
        contribution for contribution in criteres_valides.values()
        if contribution > 0
    )
    negatif = sum(
        abs(contribution) for contribution in criteres_valides.values()
        if contribution < 0
    )
    tous_neutres = bool(criteres_valides) and positif == 0 and negatif == 0

    if positif + negatif > 0:
        coherence = abs(positif - negatif) / (positif + negatif)
        penalite_contradiction = round(
            PENALITE_CONTRADICTION_MAX * (1 - coherence)
        )
    else:
        coherence = 0.0
        penalite_contradiction = PENALITE_NEUTRALITE

    contradiction_forte = (
        positif > 0
        and negatif > 0
        and coherence <= SEUIL_CONTRADICTION_FORTE
    )

    nombre_criteres = len(criteres_valides)
    penalite_couverture = (
        len(CRITERES_ATTENDUS) - nombre_criteres
    ) * PENALITE_CRITERE_MANQUANT

    confiance = min(
        100 - penalite_couverture - penalite_contradiction,
        PLAFOND_GENERAL,
    )
    if not entree_valide:
        confiance = 0
    else:
        if not score_valide:
            confiance -= PENALITE_SCORE_INVALIDE
        if not signal_valide:
            confiance -= PENALITE_SIGNAL_INVALIDE
        if not raisons_valides:
            confiance -= PENALITE_RAISONS_INVALIDES
        if not ventilation_valide:
            confiance -= PENALITE_VENTILATION_INVALIDE
        confiance -= min(
            contributions_invalides * PENALITE_CONTRIBUTION_INVALIDE,
            PLAFOND_CONTRIBUTIONS_INVALIDES,
        )
        confiance -= min(
            raisons_absentes * PENALITE_RAISON_ABSENTE,
            PLAFOND_RAISONS_ABSENTES,
        )
        confiance -= min(
            doublons * PENALITE_DOUBLON,
            PLAFOND_DOUBLONS,
        )

    insuffisance_explicite = (
        not score_valide
        or signal == SIGNAL_DONNEES_INSUFFISANTES
        or marqueur_donnees_insuffisantes
    )
    donnees_insuffisantes = (
        insuffisance_explicite or nombre_criteres < 3
    )

    if donnees_insuffisantes:
        recommandation = RECOMMANDATION_ATTENDRE
    elif tous_neutres:
        recommandation = RECOMMANDATION_ATTENDRE
    elif score < 40:
        recommandation = RECOMMANDATION_EVITER
    elif score < 50:
        recommandation = RECOMMANDATION_ATTENDRE
    else:
        recommandation = RECOMMANDATION_SURVEILLER

    if insuffisance_explicite:
        confiance = min(confiance, PLAFOND_DONNEES_INSUFFISANTES)
    if nombre_criteres < 3:
        confiance = min(confiance, PLAFOND_COUVERTURE_INSUFFISANTE)
    if tous_neutres:
        confiance = min(confiance, PLAFOND_CRITERES_NEUTRES)
    if contradiction_forte:
        confiance = min(confiance, PLAFOND_CONTRADICTION_FORTE)
    confiance = int(max(0, min(confiance, 100)))

    if not facteurs_favorables and not facteurs_defavorables and not facteurs_neutres:
        facteurs_neutres.append(FACTEUR_REPLI)

    risques = list(RISQUES_PERMANENTS)
    if donnees_manquantes:
        risques.append(RISQUE_DONNEES_MANQUANTES)
    if contradiction_forte:
        risques.append(RISQUE_CONTRADICTION_FORTE)

    resume, action_suggeree = _textes_decision(
        recommandation,
        donnees_insuffisantes,
        tous_neutres,
    )

    return {
        "recommandation": recommandation,
        "confiance": confiance,
        "resume": resume,
        "facteurs_favorables": facteurs_favorables,
        "facteurs_defavorables": facteurs_defavorables,
        "facteurs_neutres": facteurs_neutres,
        "risques": risques,
        "donnees_manquantes": donnees_manquantes,
        "action_suggeree": action_suggeree,
        "decision_finale_utilisateur": True,
    }
