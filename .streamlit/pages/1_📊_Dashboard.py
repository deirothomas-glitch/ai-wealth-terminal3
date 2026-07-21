import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Dashboard", page_icon="📊")

st.title("📊 Dashboard des marchés")

indices = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "CAC 40": "^FCHI",
    "DAX": "^GDAXI",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD"
}

cols = st.columns(3)

for i, (nom, ticker) in enumerate(indices.items()):
    try:
        info = yf.Ticker(ticker).history(period="2d")

        dernier = info["Close"].iloc[-1]
        precedent = info["Close"].iloc[-2]

        variation = dernier - precedent
        variation_pct = (variation / precedent) * 100

        with cols[i % 3]:
            st.metric(
                nom,
                f"{dernier:.2f}",
                f"{variation_pct:.2f}%"
            )

    except Exception:
        with cols[i % 3]:
            st.metric(nom, "N/A")
