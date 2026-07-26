"""Orchestration de la valorisation du portefeuille."""

from typing import Any, Callable, Dict, List, Tuple

from core.portfolio import calculer_allocation, calculer_valorisation_position


def collecter_valorisation(
    positions: List[Dict],
    capital_reference: float,
    risque_max_position: float,
    charger_historique: Callable[[str], Any],
    extraire_dernier_prix: Callable[[Any], float],
    normaliser_position: Callable[[Dict], Dict],
) -> Tuple[List[Dict], List[str]]:
    """Valorise les positions avec les dépendances fournies par l'appelant."""
    lignes: List[Dict] = []
    erreurs: List[str] = []

    for position in positions:
        position = normaliser_position(position)
        symbole = str(position.get("symbole", "")).upper().strip()

        try:
            quantite = float(position.get("quantite", 0))
            prix_achat = float(position.get("prix_achat", 0))
            stop_loss = float(position.get("stop_loss", 0))
            objectif_prix = float(position.get("objectif_prix", 0))
            historique = charger_historique(symbole)

            if historique is None or historique.empty:
                erreurs.append(f"Aucune donnée de marché disponible pour {symbole}.")
                continue

            prix = float(extraire_dernier_prix(historique))
            ancien_prix = float(historique["Close"].iloc[-2]) if len(historique) >= 2 else prix
            lignes.append(
                calculer_valorisation_position(
                    symbole,
                    quantite,
                    prix_achat,
                    stop_loss,
                    objectif_prix,
                    prix,
                    ancien_prix,
                    capital_reference,
                    risque_max_position,
                )
            )
        except Exception as erreur:
            erreurs.append(f"Erreur pour {symbole or 'la position'} : {erreur}")

    total = sum(ligne["Valeur"] for ligne in lignes)
    if total > 0:
        for ligne in lignes:
            ligne["Allocation (%)"] = calculer_allocation(ligne["Valeur"], total)
    else:
        for ligne in lignes:
            ligne["Allocation (%)"] = 0.0

    return lignes, erreurs
