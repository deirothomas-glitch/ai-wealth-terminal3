"""Moteur pur et déterministe de gestion du risque."""

import math


STATUT_DISPONIBLE = "disponible"
STATUT_PARTIEL = "partiel"
STATUT_INDISPONIBLE = "indisponible"

ORDRE_DONNEES_MANQUANTES = (
    "prix_entree",
    "atr",
    "multiplicateur_stop",
    "ratio_risque_rendement",
    "stop_loss",
    "capital_reference",
    "risque_max_pct",
)

RISQUES_PERMANENTS = (
    "Le stop-loss et l’objectif sont calculés à partir de la volatilité "
    "historique et ne garantissent aucun résultat.",
    "Les frais, le slippage, les gaps de marché, la liquidité et les "
    "événements exceptionnels ne sont pas intégrés.",
)
RISQUE_PLAN_INDISPONIBLE = (
    "Les données disponibles ne permettent pas de construire un plan de "
    "risque fiable."
)
DECISION_FINALE = (
    "Ce plan est une estimation de gestion du risque. La décision finale "
    "d’investir, de ne pas investir ou de clôturer une position appartient "
    "à l’utilisateur."
)


def _nombre_positif(valeur):
    if type(valeur) not in (int, float):
        return None
    try:
        nombre = float(valeur)
    except (OverflowError, TypeError, ValueError):
        return None
    return nombre if math.isfinite(nombre) and nombre > 0 else None


def calculer_atr(plus_hauts, plus_bas, clotures, periode=14):
    """Retourne la moyenne simple des derniers True Range, ou ``None``."""
    if type(periode) is not int or periode <= 0:
        return None
    if not all(isinstance(serie, (list, tuple))
               for serie in (plus_hauts, plus_bas, clotures)):
        return None
    if not (len(plus_hauts) == len(plus_bas) == len(clotures)):
        return None
    if len(clotures) < periode + 1:
        return None

    hauts = [_nombre_positif(valeur) for valeur in plus_hauts]
    bas = [_nombre_positif(valeur) for valeur in plus_bas]
    fermetures = [_nombre_positif(valeur) for valeur in clotures]
    if any(valeur is None for serie in (hauts, bas, fermetures)
           for valeur in serie):
        return None
    if any(haut < bas_ for haut, bas_ in zip(hauts, bas)):
        return None

    true_ranges = []
    for index in range(1, len(fermetures)):
        true_range = max(
            hauts[index] - bas[index],
            abs(hauts[index] - fermetures[index - 1]),
            abs(bas[index] - fermetures[index - 1]),
        )
        if not math.isfinite(true_range):
            return None
        true_ranges.append(true_range)
    try:
        atr = math.fsum(true_ranges[-periode:]) / periode
    except (OverflowError, ValueError):
        return None
    return float(atr) if math.isfinite(atr) else None


def construire_plan_risque(
    prix_entree,
    atr,
    capital_reference=None,
    risque_max_pct=None,
    multiplicateur_stop=2.0,
    ratio_risque_rendement=2.0,
):
    """Construit un plan descriptif JSON-safe sans produire d'ordre."""
    prix = _nombre_positif(prix_entree)
    atr_valide = _nombre_positif(atr)
    multiplicateur = _nombre_positif(multiplicateur_stop)
    ratio = _nombre_positif(ratio_risque_rendement)
    capital = _nombre_positif(capital_reference)
    risque_pct = _nombre_positif(risque_max_pct)
    if risque_pct is not None and risque_pct > 100:
        risque_pct = None

    invalides = {
        "prix_entree": prix is None,
        "atr": atr_valide is None,
        "multiplicateur_stop": multiplicateur is None,
        "ratio_risque_rendement": ratio is None,
        "stop_loss": False,
        "capital_reference": capital is None,
        "risque_max_pct": risque_pct is None,
    }

    stop_loss = objectif = risque_par_unite = None
    plan_prix_disponible = not any(
        invalides[cle]
        for cle in (
            "prix_entree",
            "atr",
            "multiplicateur_stop",
            "ratio_risque_rendement",
        )
    )
    if plan_prix_disponible:
        try:
            distance_stop = atr_valide * multiplicateur
            stop_calcule = prix - distance_stop
            risque_calcule = prix - stop_calcule
            objectif_calcule = prix + risque_calcule * ratio
            plan_prix_disponible = (
                all(math.isfinite(valeur) for valeur in (
                    distance_stop, stop_calcule, risque_calcule,
                    objectif_calcule,
                ))
                and stop_calcule > 0
                and stop_calcule < prix
                and risque_calcule > 0
                and objectif_calcule > prix
            )
        except (OverflowError, TypeError, ValueError):
            plan_prix_disponible = False
        if plan_prix_disponible:
            stop_loss = stop_calcule
            risque_par_unite = risque_calcule
            objectif = objectif_calcule
        else:
            invalides["stop_loss"] = True

    risque_capital = taille_position = None
    taille_disponible = (
        plan_prix_disponible and capital is not None and risque_pct is not None
    )
    if taille_disponible:
        try:
            risque_capital_calcule = capital * risque_pct / 100
            taille_calculee = risque_capital_calcule / risque_par_unite
            taille_disponible = (
                math.isfinite(risque_capital_calcule)
                and math.isfinite(taille_calculee)
            )
        except (OverflowError, TypeError, ValueError, ZeroDivisionError):
            taille_disponible = False
        if taille_disponible:
            risque_capital = risque_capital_calcule
            taille_position = taille_calculee

    if not plan_prix_disponible:
        statut = STATUT_INDISPONIBLE
    elif taille_disponible:
        statut = STATUT_DISPONIBLE
    else:
        statut = STATUT_PARTIEL

    donnees_manquantes = [
        cle for cle in ORDRE_DONNEES_MANQUANTES if invalides[cle]
    ]
    risques = list(RISQUES_PERMANENTS)
    if statut == STATUT_INDISPONIBLE:
        risques.append(RISQUE_PLAN_INDISPONIBLE)

    return {
        "statut": statut,
        "prix_entree": round(prix, 8) if prix is not None else None,
        "atr": round(atr_valide, 8) if atr_valide is not None else None,
        "multiplicateur_stop": (
            round(multiplicateur, 4) if multiplicateur is not None else None
        ),
        "stop_loss": round(stop_loss, 8) if stop_loss is not None else None,
        "objectif": round(objectif, 8) if objectif is not None else None,
        "risque_par_unite": (
            round(risque_par_unite, 8)
            if risque_par_unite is not None else None
        ),
        "ratio_risque_rendement": round(ratio, 4) if ratio is not None else None,
        "capital_reference": round(capital, 2) if capital is not None else None,
        "risque_max_pct": round(risque_pct, 4) if risque_pct is not None else None,
        "risque_capital": (
            round(risque_capital, 2) if risque_capital is not None else None
        ),
        "taille_position": (
            round(taille_position, 8) if taille_position is not None else None
        ),
        "donnees_manquantes": donnees_manquantes,
        "risques": risques,
        "decision_finale_utilisateur": DECISION_FINALE,
    }
