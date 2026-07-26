"""Construction pure du modèle du Cockpit Investisseur."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from core.data_quality import construire_etat_sources, evaluer_qualite_globale
from core.portfolio import construire_resume_global, convertir_nombre_fini
from core.portfolio_intelligence import analyser_portefeuille


def _liste(valeur: Any) -> list[dict[str, Any]]:
    return [dict(x) for x in valeur if isinstance(x, Mapping)] if isinstance(valeur, Sequence) and not isinstance(valeur, (str, bytes)) else []


def _texte(valeur: Any, defaut: str = "Indisponible") -> str:
    return str(valeur).strip() if isinstance(valeur, str) and valeur.strip() else defaut


def _tendance(elements: list[dict[str, Any]]) -> tuple[str, float | None]:
    variations = [convertir_nombre_fini(x.get("variation")) for x in elements]
    valides = [x for x in variations if x is not None]
    if not valides:
        return "Indisponible", None
    moyenne = sum(valides) / len(valides)
    if moyenne > 0.25:
        return "Orientation positive", round(moyenne, 2)
    if moyenne < -0.25:
        return "Orientation négative", round(moyenne, 2)
    return "Orientation partagée", round(moyenne, 2)


def _sentiment(actualites: list[dict[str, Any]]) -> str:
    valeurs = [
        str((x.get("sentiment") or {}).get("sentiment", "")).casefold()
        for x in actualites if isinstance(x.get("sentiment"), Mapping)
    ]
    positifs = sum(x == "positif" for x in valeurs)
    negatifs = sum(x == "negatif" for x in valeurs)
    if not positifs and not negatifs:
        return "Indisponible"
    if positifs > negatifs:
        return "Plutôt positif"
    if negatifs > positifs:
        return "Plutôt négatif"
    return "Partagé"


def _top_opportunites(opportunites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    resultat = []
    for entree in opportunites[:5]:
        raisons = entree.get("raisons_principales")
        resume = next((x.strip() for x in raisons if isinstance(x, str) and x.strip()), "Résumé indisponible") if isinstance(raisons, list) else "Résumé indisponible"
        score = convertir_nombre_fini(entree.get("score_global"))
        resultat.append({
            "symbole": _texte(entree.get("symbole"), "—"),
            "score": round(score, 1) if score is not None else None,
            "risque": "Disponible" if entree.get("plan_risque_disponible") is True else "À compléter",
            "qualite": _texte(entree.get("qualite_donnees")),
            "strategie": _texte(entree.get("strategie")),
            "resume": resume[:180],
        })
    return resultat


def _alertes_prioritaires(alertes: list[dict[str, Any]]) -> list[dict[str, str]]:
    resultat = []
    identifiants = set()
    for alerte in alertes:
        categorie = _texte(alerte.get("categorie"), "").casefold()
        niveau = _texte(alerte.get("niveau"), "").casefold()
        titre = _texte(alerte.get("titre"), "").casefold()
        prioritaire = (
            (categorie == "stop" and ("proche" in titre or niveau == "attention"))
            or categorie == "objectif"
            or niveau == "attention"
        )
        cle = _texte(alerte.get("identifiant"), f"{alerte.get('symbole')}:{titre}")
        if not prioritaire or cle in identifiants:
            continue
        identifiants.add(cle)
        resultat.append({
            "symbole": _texte(alerte.get("symbole"), "Actif"),
            "titre": _texte(alerte.get("titre")),
            "message": _texte(alerte.get("message")),
            "niveau": niveau or "vigilance",
        })
    return resultat[:8]


def _resume_portefeuille(positions, prix, journal, portefeuille_charge):
    if not portefeuille_charge:
        return {
            "valeur_totale": None, "variation": None, "positions_ouvertes": None,
            "positions_cloturees": None, "gains": None, "pertes": None,
            "exposition": None,
        }
    resume = construire_resume_global(positions, prix, journal)
    clotures = [x for x in journal if x.get("type_evenement") == "cloture"]
    gains = [convertir_nombre_fini(x.get("gain_perte_realise")) for x in clotures]
    gains_valides = [x for x in gains if x is not None]
    return {
        "valeur_totale": resume["valeur_actuelle"],
        "variation": resume["performance_globale_pourcentage"],
        "positions_ouvertes": resume["nombre_positions"],
        "positions_cloturees": len(clotures),
        "gains": sum(x for x in gains_valides if x > 0),
        "pertes": sum(x for x in gains_valides if x < 0),
        "exposition": resume["capital_investi"],
    }



def _construire_agenda(evenements):
    resultat = []
    identifiants = set()
    for evenement in _liste(evenements):
        titre = _texte(evenement.get("titre"), "")
        if not titre:
            continue
        date_evenement = _texte(evenement.get("date"), "")
        source = _texte(evenement.get("source"), "")
        cle = (titre, date_evenement, source)
        if cle in identifiants:
            continue
        identifiants.add(cle)
        resultat.append({"titre": titre, "date": date_evenement or None, "source": source or None})
        if len(resultat) >= 10:
            break
    return {
        "titre": "Évènements de marché",
        "evenements": resultat,
        "message": "Aucun événement disponible." if not resultat else "",
    }


def construire_cockpit(
    *,
    indices=None,
    cryptos=None,
    opportunites=None,
    positions=None,
    prix_portefeuille=None,
    journal=None,
    alertes=None,
    actualites=None,
    evenements=None,
    portefeuille_charge=False,
    openai_disponible=False,
    yahoo_interroge=False,
    mise_a_jour="",
) -> dict[str, Any]:
    """Agrège les contrats existants sans mutation, réseau ou donnée inventée."""
    indices_valides = _liste(indices)
    cryptos_valides = _liste(cryptos)
    marche = indices_valides + cryptos_valides
    opportunites_valides = _liste(opportunites)
    positions_valides = _liste(positions)
    journal_valide = _liste(journal)
    alertes_valides = _liste(alertes)
    actualites_valides = _liste(actualites)
    agenda = _construire_agenda(evenements)
    prix_valides = dict(prix_portefeuille) if isinstance(prix_portefeuille, Mapping) else {}
    tendance, variation_moyenne = _tendance(marche)
    yahoo_disponible = bool(marche)
    alertes_prioritaires = _alertes_prioritaires(alertes_valides)
    symboles = {
        _texte(x.get("symbole"), "") for x in positions_valides + opportunites_valides
        if _texte(x.get("symbole"), "")
    }
    portefeuille = _resume_portefeuille(
        positions_valides, prix_valides, journal_valide, bool(portefeuille_charge)
    )
    intelligence_portefeuille = analyser_portefeuille(
        positions if portefeuille_charge else None,
        prix_valides,
    )
    qualite_globale = evaluer_qualite_globale({
        "Marché": {
            "disponible": yahoo_disponible,
            "complet": bool(indices_valides) and bool(cryptos_valides),
        },
        "Scanner": {
            "disponible": bool(opportunites_valides),
            "complet": bool(opportunites_valides) and all(
                _texte(x.get("qualite_donnees"), "insuffisant").casefold() != "insuffisant"
                for x in opportunites_valides
            ),
        },
        "Portefeuille": {
            "disponible": bool(portefeuille_charge) and intelligence_portefeuille["positions_valorisees"] > 0,
            "complet": intelligence_portefeuille["qualite_analyse"] == "Bonne",
        },
        "Actualités": {
            "disponible": bool(actualites_valides),
            "complet": bool(actualites_valides),
        },
    })
    qualite = qualite_globale["niveau"]
    etat_sources = construire_etat_sources(
        yahoo_interroge=yahoo_interroge,
        yahoo_disponible=yahoo_disponible if yahoo_interroge else None,
        openai_configure=openai_disponible,
        stockage_charge=bool(portefeuille_charge),
    )
    if not portefeuille_charge:
        resume_portefeuille = "Indisponible"
    elif portefeuille["valeur_totale"] is None:
        resume_portefeuille = (
            f"{portefeuille['positions_ouvertes']} position(s) ouverte(s) ; "
            "valorisation totale indisponible."
        )
    else:
        resume_portefeuille = (
            f"{portefeuille['positions_ouvertes']} position(s) ouverte(s), "
            f"valeur totale {portefeuille['valeur_totale']:.2f} €."
        )
    positifs = []
    vigilances = []
    if tendance == "Orientation positive":
        positifs.append("La moyenne des variations de marché disponibles est positive.")
    if opportunites_valides:
        positifs.append(f"{len(opportunites_valides)} opportunité(s) issue(s) du dernier classement sont disponibles.")
    if tendance in ("Orientation négative", "Orientation partagée"):
        vigilances.append("Les variations de marché disponibles appellent à la prudence.")
    if alertes_prioritaires:
        vigilances.append(f"{len(alertes_prioritaires)} alerte(s) prioritaire(s) nécessitent une revue.")
    donnees_partielles = qualite != "Bonne"
    return {
        "bandeau": {
            "mise_a_jour": _texte(mise_a_jour),
            "connexion": etat_sources["Yahoo Finance"]["etat"],
            "openai": etat_sources["OpenAI"]["etat"],
            "yahoo": etat_sources["Yahoo Finance"]["etat"],
            "stockage": etat_sources["Stockage local"]["etat"],
            "qualite": qualite,
            "justification_qualite": qualite_globale["justification"],
        },
        "sources": etat_sources,
        "qualite_donnees": qualite_globale,
        "marche": {
            "tendance": tendance,
            "variation_moyenne": variation_moyenne,
            "sentiment": _sentiment(actualites_valides),
            "volatilite": "Indisponible",
            "actifs_surveilles": len(symboles),
            "opportunites": len(opportunites_valides),
            "risque_global": "Élevé" if any(x["niveau"] == "attention" for x in alertes_prioritaires) else ("À surveiller" if alertes_prioritaires else "Non évalué"),
        },
        "portefeuille": portefeuille,
        "intelligence_portefeuille": intelligence_portefeuille,
        "opportunites": _top_opportunites(opportunites_valides),
        "alertes": alertes_prioritaires,
        "briefing": {
            "resume_marche": tendance,
            "resume_portefeuille": resume_portefeuille,
            "contexte": "Synthèse des données déjà chargées dans la session.",
            "points_positifs": positifs,
            "points_vigilance": vigilances,
            "donnees_partielles": donnees_partielles,
        },
        "agenda": agenda,
    }
