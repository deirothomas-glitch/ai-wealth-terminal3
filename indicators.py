"""Indicateurs techniques réutilisables."""

import pandas as pd


def moving_average(data, period=20):
    return data["Close"].rolling(window=period).mean()


def ema(data, period=20):
    return data["Close"].ewm(span=period, adjust=False).mean()


def rsi(data, period=14):
    """Calcule le RSI et gère les séries monotones, stables ou trop courtes."""
    delta = data["Close"].diff()
    gains = delta.clip(lower=0)
    pertes = -delta.clip(upper=0)
    gain_moyen = gains.rolling(period, min_periods=period).mean()
    perte_moyenne = pertes.rolling(period, min_periods=period).mean()
    rs = gain_moyen / perte_moyenne
    resultat = 100 - (100 / (1 + rs))
    complete = gain_moyen.notna() & perte_moyenne.notna()
    resultat = resultat.mask(complete & gain_moyen.eq(0) & perte_moyenne.eq(0), 50.0)
    resultat = resultat.mask(complete & gain_moyen.gt(0) & perte_moyenne.eq(0), 100.0)
    resultat = resultat.mask(complete & gain_moyen.eq(0) & perte_moyenne.gt(0), 0.0)
    return pd.to_numeric(resultat, errors="coerce")


def macd(data, short_period=12, long_period=26, signal_period=9):
    ligne = ema(data, short_period) - ema(data, long_period)
    signal = ligne.ewm(span=signal_period, adjust=False).mean()
    return {"macd": ligne, "signal": signal, "histogram": ligne - signal}


def bollinger_bands(data, period=20, std_dev=2):
    milieu = moving_average(data, period)
    ecart = data["Close"].rolling(window=period).std()
    return {"middle": milieu, "upper": milieu + ecart * std_dev, "lower": milieu - ecart * std_dev}
