from indicators import ema, rsi, macd, bollinger_bands


def calculer_score(info, historique):
    """
    Calcule un score IA entre 0 et 100
    basé sur plusieurs indicateurs techniques.
    """

    if historique is None or historique.empty:
        return {
            "score": 0,
            "signal": "Données insuffisantes",
            "raisons": []
        }

    score = 50
    raisons = []

    close = historique["Close"]

    dernier_prix = close.iloc[-1]

    # ==========================
    # EMA 20
    # ==========================

    ema20 = ema(historique, 20).iloc[-1]

    if dernier_prix > ema20:
        score += 10
        raisons.append("✅ Prix au-dessus de l'EMA20")

    else:
        score -= 10
        raisons.append("❌ Prix sous l'EMA20")

    # ==========================
    # RSI
    # ==========================

    rsi_value = rsi(historique).iloc[-1]

    if 45 <= rsi_value <= 65:
        score += 10
        raisons.append("✅ RSI équilibré")

    elif rsi_value < 30:
        score += 5
        raisons.append("📉 RSI en zone de survente")

    elif rsi_value > 70:
        score -= 10
        raisons.append("⚠ RSI en zone de surachat")

    # ==========================
    # MACD
    # ==========================

    macd_data = macd(historique)

    macd_line = macd_data["macd"].iloc[-1]
    signal_line = macd_data["signal"].iloc[-1]

    if macd_line > signal_line:
        score += 10
        raisons.append("✅ MACD haussier")

    else:
        score -= 10
        raisons.append("❌ MACD baissier")

    # ==========================
    # Bollinger
    # ==========================

    bandes = bollinger_bands(historique)

    upper = bandes["upper"].iloc[-1]
    lower = bandes["lower"].iloc[-1]

    if dernier_prix < lower:
        score += 5
        raisons.append("📈 Prix sous la bande inférieure")

    elif dernier_prix > upper:
        score -= 5
        raisons.append("⚠ Prix au-dessus de la bande supérieure")

    # ==========================
    # Volume
    # ==========================

    volume = historique["Volume"].iloc[-1]
    volume_moyen = historique["Volume"].rolling(20).mean().iloc[-1]

    if volume > volume_moyen:
        score += 10
        raisons.append("✅ Volume supérieur à la moyenne")

    # ==========================
    # Encadrement du score
    # ==========================

    score = max(0, min(score, 100))

    if score >= 80:
        signal = "🟢 Achat"

    elif score >= 60:
        signal = "🟡 Surveillance"

    else:
        signal = "🔴 Attendre"

    return {
        "score": score,
        "signal": signal,
        "raisons": raisons,
        "prix": dernier_prix,
        "ema20": ema20,
        "rsi": rsi_value
    }
