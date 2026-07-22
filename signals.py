def generer_signal(score_data):
    """
    Génère un plan de trade à partir du score IA.
    """

    score = score_data["score"]
    prix = score_data["prix"]

    if score >= 85:

        signal = "🟢 ACHAT FORT"
        confiance = 90

        entree = prix
        stop_loss = prix * 0.98
        objectif1 = prix * 1.03
        objectif2 = prix * 1.06

    elif score >= 70:

        signal = "🟢 ACHAT"
        confiance = 80

        entree = prix
        stop_loss = prix * 0.97
        objectif1 = prix * 1.04
        objectif2 = prix * 1.08

    elif score >= 55:

        signal = "🟡 SURVEILLANCE"
        confiance = 60

        entree = prix
        stop_loss = prix * 0.95
        objectif1 = prix * 1.03
        objectif2 = prix * 1.05

    else:

        signal = "🔴 ATTENDRE"
        confiance = 35

        entree = prix
        stop_loss = prix * 0.94
        objectif1 = prix
        objectif2 = prix

    risque = entree - stop_loss
    gain = objectif1 - entree

    if risque > 0:
        ratio = gain / risque
    else:
        ratio = 0

    return {

        "signal": signal,

        "confiance": confiance,

        "entree": round(entree, 2),

        "stop_loss": round(stop_loss, 2),

        "objectif1": round(objectif1, 2),

        "objectif2": round(objectif2, 2),

        "ratio": round(ratio, 2)

    }
