"""Référentiel canonique des signaux et génération d'un plan de trade."""

SEUIL_ACHAT = 75
SEUIL_SURVEILLER = 50
SIGNAL_ACHAT = "ACHAT"
SIGNAL_SURVEILLER = "SURVEILLER"
SIGNAL_VENTE = "VENTE"
SIGNAL_DONNEES_INSUFFISANTES = "DONNÉES INSUFFISANTES"


def determiner_signal(score):
    """Retourne le libellé canonique correspondant à un score sur 100."""
    if score >= SEUIL_ACHAT:
        return SIGNAL_ACHAT
    if score >= SEUIL_SURVEILLER:
        return SIGNAL_SURVEILLER
    return SIGNAL_VENTE


def generer_signal(score_data):
    """Génère un plan de trade selon le référentiel canonique."""
    score = score_data["score"]
    prix = score_data["prix"]
    signal = determiner_signal(score)
    if signal == SIGNAL_ACHAT:
        confiance, stop, objectif1, objectif2 = 90, prix * 0.98, prix * 1.03, prix * 1.06
    elif signal == SIGNAL_SURVEILLER:
        confiance, stop, objectif1, objectif2 = 60, prix * 0.95, prix * 1.03, prix * 1.05
    else:
        confiance, stop, objectif1, objectif2 = 35, prix * 0.94, prix, prix
    risque = prix - stop
    ratio = (objectif1 - prix) / risque if risque > 0 else 0
    return {
        "signal": signal, "confiance": confiance, "entree": round(prix, 2),
        "stop_loss": round(stop, 2), "objectif1": round(objectif1, 2),
        "objectif2": round(objectif2, 2), "ratio": round(ratio, 2),
    }
