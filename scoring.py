"""Score technique cohérent pour le dashboard, le marché et le scanner."""

import math

from indicators import bollinger_bands, ema, macd, rsi
from signals import SIGNAL_DONNEES_INSUFFISANTES, determiner_signal

SCORE_BASE = 50


def _resultat_insuffisant():
    """Retourne un résultat déterministe et compatible avec l'API historique."""
    return {
        "score": 0, "signal": SIGNAL_DONNEES_INSUFFISANTES, "raisons": [],
        "prix": 0.0, "ema20": 0.0, "rsi": 50.0,
        "ventilation": [
            {"critere": "Score de base", "valeur": SCORE_BASE,
             "contribution": SCORE_BASE,
             "raison": "Base théorique non appliquée : données insuffisantes"},
            {"critere": "Données insuffisantes", "valeur": None,
             "contribution": -SCORE_BASE,
             "raison": "Score neutralisé faute de données exploitables"},
        ],
    }


def _fini(valeur):
    try:
        return math.isfinite(float(valeur))
    except (TypeError, ValueError):
        return False


def _ajouter(ventilation, raisons, critere, valeur, contribution, raison):
    ventilation.append({"critere": critere, "valeur": valeur,
                        "contribution": contribution, "raison": raison})
    raisons.append(raison)


def calculer_score(info, historique):
    """Calcule un score explicable; ``info`` est conservé pour compatibilité."""
    _ = info
    if (historique is None or historique.empty or len(historique) < 26
            or "Close" not in historique.columns):
        return _resultat_insuffisant()

    prix = historique["Close"].iloc[-1]
    ema20 = ema(historique, 20).iloc[-1]
    rsi_valeur = rsi(historique).iloc[-1]
    macd_data = macd(historique)
    macd_valeur = macd_data["macd"].iloc[-1]
    macd_signal = macd_data["signal"].iloc[-1]
    bandes = bollinger_bands(historique)
    bas, haut = bandes["lower"].iloc[-1], bandes["upper"].iloc[-1]
    if not all(_fini(v) for v in (prix, ema20, rsi_valeur, macd_valeur,
                                  macd_signal, bas, haut)):
        return _resultat_insuffisant()

    prix, ema20, rsi_valeur = float(prix), float(ema20), float(rsi_valeur)
    score, raisons = SCORE_BASE, []
    ventilation = [{"critere": "Score de base", "valeur": SCORE_BASE,
                    "contribution": SCORE_BASE, "raison": "Point de départ neutre"}]

    contribution, raison = ((10, "Prix au-dessus de l'EMA 20") if prix > ema20
                            else (-10, "Prix sous l'EMA 20"))
    score += contribution
    _ajouter(ventilation, raisons, "Tendance EMA 20", prix - ema20, contribution, raison)

    if 45 <= rsi_valeur <= 65:
        contribution, raison = 10, "RSI équilibré"
    elif rsi_valeur < 30:
        contribution, raison = 5, "RSI en survente"
    elif rsi_valeur > 70:
        contribution, raison = -10, "RSI en surachat"
    else:
        contribution, raison = 0, "RSI hors zone de pondération"
    score += contribution
    _ajouter(ventilation, raisons, "RSI", rsi_valeur, contribution, raison)

    contribution, raison = ((10, "MACD haussier") if macd_valeur > macd_signal
                            else (-10, "MACD baissier"))
    score += contribution
    _ajouter(ventilation, raisons, "MACD", float(macd_valeur - macd_signal),
             contribution, raison)

    if prix < bas:
        contribution, raison = 5, "Sous la bande de Bollinger inférieure"
    elif prix > haut:
        contribution, raison = -5, "Au-dessus de la bande de Bollinger supérieure"
    else:
        contribution, raison = 0, "Prix dans les bandes de Bollinger"
    score += contribution
    _ajouter(ventilation, raisons, "Bandes de Bollinger", prix, contribution, raison)

    contribution, valeur_volume = 0, None
    raison = "Volume indisponible ou sans signal"
    if "Volume" in historique.columns:
        actuel = historique["Volume"].iloc[-1]
        moyen = historique["Volume"].rolling(20).mean().iloc[-1]
        if _fini(actuel) and _fini(moyen):
            valeur_volume = float(actuel)
            if float(actuel) > float(moyen):
                contribution, raison = 10, "Volume supérieur à sa moyenne"
            else:
                raison = "Volume inférieur ou égal à sa moyenne"
    score += contribution
    _ajouter(ventilation, raisons, "Volume", valeur_volume, contribution, raison)

    score = max(0, min(int(score), 100))
    return {"score": score, "signal": determiner_signal(score), "raisons": raisons,
            "prix": prix, "ema20": ema20, "rsi": rsi_valeur,
            "ventilation": ventilation}
