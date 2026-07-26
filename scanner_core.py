"""Moteur pur du scanner de watchlist."""

from __future__ import annotations

import csv
import io
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from core.risk import calculer_atr

CSV_COLUMNS = (
    "Catégorie", "Actif", "Prix", "Variation %", "RSI", "Score", "Signal",
)
ProgressCallback = Callable[[int, int], None]
ErrorCallback = Callable[[str, str], None]
ResultValue = str | int | float | bool | None | list[str] | list[dict[str, Any]]


def _nombre_natif(valeur: Any, type_cible: type[int] | type[float]):
    """Convertit explicitement un scalaire NumPy/Pandas en nombre Python fini."""
    nombre = type_cible(valeur)
    if isinstance(nombre, float) and not math.isfinite(nombre):
        raise ValueError("Valeur numérique non finie")
    return nombre


def _convertir_valeur_json_native(valeur: Any) -> Any:
    """Copie récursivement une valeur en types natifs strictement JSON-safe."""
    if valeur is None or isinstance(valeur, (str, bool)):
        return valeur
    if isinstance(valeur, int):
        return int(valeur)
    if isinstance(valeur, float):
        return float(valeur) if math.isfinite(valeur) else None
    if isinstance(valeur, (list, tuple)):
        return [_convertir_valeur_json_native(element) for element in valeur]
    if isinstance(valeur, dict):
        return {
            cle if isinstance(cle, str) else str(cle):
            _convertir_valeur_json_native(element)
            for cle, element in valeur.items()
        }
    try:
        scalaire = valeur.item()
    except Exception:
        return None
    if scalaire is valeur:
        return None
    return _convertir_valeur_json_native(scalaire)


def _copier_ventilation_json_native(ventilation: Any) -> list[dict[str, Any]]:
    """Conserve uniquement les entrées dictionnaires d'une ventilation."""
    if not isinstance(ventilation, list):
        return []
    return [
        _convertir_valeur_json_native(entree)
        for entree in ventilation
        if isinstance(entree, dict)
    ]


def _historique_vide(historique: Any) -> bool:
    return historique is None or bool(historique.empty)


def _prix_et_variation(historique: Any) -> tuple[float, float]:
    clotures = historique["Close"]
    prix = _nombre_natif(clotures.iloc[-1], float)
    variation = 0.0
    if len(clotures) >= 2:
        precedent = _nombre_natif(clotures.iloc[-2], float)
        if precedent:
            variation = (prix - precedent) / precedent * 100
    return round(prix, 2), round(variation, 2)



def _date_donnees(historique: Any) -> str:
    try:
        valeur = historique.index[-1]
        if hasattr(valeur, "isoformat"):
            return str(valeur.isoformat())
        texte = str(valeur).strip()
        return texte if texte else "Indisponible"
    except Exception:
        return "Indisponible"


def _atr_depuis_historique(historique: Any) -> float | None:
    try:
        if not {"High", "Low", "Close"}.issubset(historique.columns):
            return None
        atr = calculer_atr(
            [_nombre_natif(x, float) for x in historique["High"].tolist()],
            [_nombre_natif(x, float) for x in historique["Low"].tolist()],
            [_nombre_natif(x, float) for x in historique["Close"].tolist()],
        )
        return float(atr) if atr is not None else None
    except Exception:
        return None


def analyser_watchlist(
    watchlist: Mapping[str, Sequence[str]],
    charger_historique: Callable[[str], Any],
    calculateur_score: Callable[[dict[str, Any], Any], Mapping[str, Any]],
    progress_callback: ProgressCallback | None = None,
    error_callback: ErrorCallback | None = None,
) -> list[dict[str, ResultValue]]:
    """Analyse la watchlist et ignore les actifs vides ou en erreur.

    Le callback de progression est appelé exactement une fois après chaque
    actif. Une erreur est signalée sans exception au callback d'erreur.
    """
    actifs = [
        (str(categorie), str(symbole))
        for categorie, symboles in watchlist.items()
        for symbole in symboles
    ]
    total = len(actifs)
    resultats: list[dict[str, ResultValue]] = []

    for traites, (categorie, symbole) in enumerate(actifs, start=1):
        try:
            historique = charger_historique(symbole)
            if _historique_vide(historique):
                continue
            score = calculateur_score({}, historique)
            prix, variation = _prix_et_variation(historique)
            atr = _atr_depuis_historique(historique)
            resultats.append({
                "Catégorie": str(categorie.rstrip("s")),
                "Actif": str(symbole),
                "Prix": float(prix),
                "Variation %": float(variation),
                "RSI": float(round(_nombre_natif(score["rsi"], float), 1)),
                "Score": int(_nombre_natif(score["score"], int)),
                "Signal": str(score["signal"]),
                "Date données": _date_donnees(historique),
                "ATR": atr,
                "Nombre points": int(len(historique)),
                "Volume disponible": bool("Volume" in historique.columns),
                "Volatilité disponible": bool(atr is not None),
                "Raisons": [str(raison) for raison in score.get("raisons", [])],
                "Ventilation": _copier_ventilation_json_native(
                    score.get("ventilation", [])
                ),
            })
        except Exception:
            if error_callback is not None:
                error_callback(categorie, symbole)
        finally:
            if progress_callback is not None:
                progress_callback(traites, total)

    return sorted(resultats, key=lambda ligne: (
        -int(ligne["Score"]), str(ligne["Catégorie"]), str(ligne["Actif"]),
    ))


def generer_csv(resultats: Iterable[Mapping[str, Any]]) -> bytes:
    """Produit un CSV scalaire, stable, séparé par des points-virgules."""
    flux = io.StringIO(newline="")
    writer = csv.DictWriter(
        flux, fieldnames=CSV_COLUMNS, delimiter=";", extrasaction="ignore",
    )
    writer.writeheader()
    for resultat in resultats:
        writer.writerow({colonne: resultat.get(colonne) for colonne in CSV_COLUMNS})
    return flux.getvalue().encode("utf-8-sig")
