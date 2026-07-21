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
  