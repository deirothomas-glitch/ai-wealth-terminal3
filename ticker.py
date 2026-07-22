import streamlit as st
import yfinance as yf

def afficher_ticker():

    actifs = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "OR": "GC=F",
        "EUR/USD": "EURUSD=X"
    }

    cols = st.columns(len(actifs))

    for col, (nom, symbole) in zip(cols, actifs.items()):

        try:
            data = yf.Ticker(symbole).history(period="2d")

            dernier = data["Close"].iloc[-1]
            precedent = data["Close"].iloc[-2]

            variation = ((dernier - precedent) / precedent) * 100

            col.metric(
                nom,
                f"{dernier:.2f}",
                f"{variation:+.2f}%"
            )

        except:
            col.metric(nom, "N/A", "N/A")