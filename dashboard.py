import streamlit as st
import yfinance as yf

from news import afficher_actualites

def afficher_dashboard():

    st.title("📈 AI Wealth Terminal")

    st.subheader("Dashboard des marchés")

    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DAX": "^GDAXI",
        "CAC 40": "^FCHI"
    }

    col1, col2, col3, col4 = st.columns(4)

    colonnes = [col1, col2, col3, col4]

    for colonne, (nom, ticker) in zip(colonnes, indices.items()):

        try:
            data = yf.Ticker(ticker).history(period="2d")

            dernier = data["Close"].iloc[-1]
            precedent = data["Close"].iloc[-2]

            variation = ((dernier - precedent) / precedent) * 100

            colonne.metric(
                nom,
                f"{dernier:,.2f}",
                f"{variation:.2f}%"
            )

        except Exception:
            colonne.metric(nom, "N/A", "N/A")

    st.divider()

    st.subheader("⭐ Valeurs à surveiller")

    afficher_actualites("AAPL")

    watchlist = [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "TSLA",
        "BTC-USD"
    ]

    cols = st.columns(3)

    for i, symbole in enumerate(watchlist):

        try:
            info = yf.Ticker(symbole).history(period="2d")

            prix = info["Close"].iloc[-1]
            ancien = info["Close"].iloc[-2]

            variation = ((prix - ancien) / ancien) * 100

            cols[i % 3].metric(
                symbole,
                f"{prix:.2f}",
                f"{variation:.2f}%"
            )

        except Exception:
            cols[i % 3].metric(symbole, "N/A", "N/A")

