def moving_average(data, period=20):
    return data["Close"].rolling(window=period).mean()


def ema(data, period):
    return data["Close"].ewm(span=period, adjust=False).mean()


def rsi(data, period=14):

    delta = data["Close"].diff()

    gain = delta.clip(lower=0)
    perte = -delta.clip(upper=0)

    gain_moyen = gain.rolling(period).mean()
    perte_moyenne = perte.rolling(period).mean()

    rs = gain_moyen / perte_moyenne

    return 100 - (100 / (1 + rs))


def macd(data, short_period=12, long_period=26, signal_period=9):
    """
    Calcule le MACD, la ligne de signal et l'histogramme.
    """

    ema_short = data["Close"].ewm(span=short_period, adjust=False).mean()
    ema_long = data["Close"].ewm(span=long_period, adjust=False).mean()

    macd_line = ema_short - ema_long
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }


def bollinger_bands(data, period=20, std_dev=2):
    """
    Calcule les Bandes de Bollinger.
    """

    moyenne = data["Close"].rolling(window=period).mean()
    ecart_type = data["Close"].rolling(window=period).std()

    bande_superieure = moyenne + (ecart_type * std_dev)
    bande_inferieure = moyenne - (ecart_type * std_dev)

    return {
        "middle": moyenne,
        "upper": bande_superieure,
        "lower": bande_inferieure
    }