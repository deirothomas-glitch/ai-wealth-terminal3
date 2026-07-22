import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

from data import get_stock_history
from charts import create_candlestick_chart


# ==========================================
# Calcul du RSI
# ==========================================

def calcul_rsi(df, periode=14):

    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0)
    perte = -delta.where(delta < 0, 0)

    gain_moyen = gain.rolling(periode).mean()
    perte_moyenne = perte.rolling(periode).mean()

    rs = gain_moyen / perte_moyenne

    rsi = 100 - (100 / (1 + rs))

    return rsi


# ==========================================
# Calcul du MACD
# ==========================================

def calcul_macd(df):

    ema12 = df["Close"].ewm(span=12).mean()

    ema26 = df["Close"].ewm(span=26).mean()

    macd = ema12 - ema26

    signal = macd.ewm(span=9).mean()

    histogramme = macd - signal

    return macd, signal, histogramme


# ==========================================
# Bandes de Bollinger
# ==========================================

def calcul_bollinger(df):

    moyenne = df["Close"].rolling(20).mean()

    ecart = df["Close"].rolling(20).std()

    haut = moyenne + 2 * ecart

    bas = moyenne - 2 * ecart

    return haut, moyenne, bas


# ==========================================
# Affichage Marché
# ==========================================

def afficher_marche():

    st.header("📈 Marchés")

    watchlist = [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "META",
        "GOOGL",
        "TSLA",
        "NFLX",
        "AMD",
        "^GSPC",
        "^IXIC",
        "^DJI"
    ]

    symbole = st.sidebar.selectbox(
        "📋 Watchlist",
        watchlist
    )

    periode = st.selectbox(
        "Période",
        [
            "1mo",
            "3mo",
            "6mo",
            "1y",
            "2y",
            "5y"
        ],
        index=3
    )

    historique = yf.Ticker(symbole).history(period=periode)

    if historique.empty:
        st.error("Impossible de récupérer les données.")
        return

    historique["EMA20"] = historique["Close"].ewm(span=20).mean()
    historique["EMA50"] = historique["Close"].ewm(span=50).mean()
    historique["EMA200"] = historique["Close"].ewm(span=200).mean()

    historique["RSI"] = calcul_rsi(historique)

    macd, signal, hist = calcul_macd(historique)

    historique["MACD"] = macd
    historique["Signal"] = signal
    historique["Histogramme"] = hist

    bb_haut, bb_mid, bb_bas = calcul_bollinger(historique)

    historique["BB_HAUT"] = bb_haut
    historique["BB_MID"] = bb_mid
    historique["BB_BAS"] = bb_bas
# ==========================================
# Statistiques
# ==========================================

    dernier_prix = historique["Close"].iloc[-1]

    variation = (
        historique["Close"].pct_change().iloc[-1]
    ) * 100

    plus_haut = historique["High"].max()

    plus_bas = historique["Low"].min()

    volume = historique["Volume"].iloc[-1]

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "💲 Cours",
        f"{dernier_prix:.2f}"
    )

    col2.metric(
        "📈 Variation",
        f"{variation:.2f}%"
    )

    col3.metric(
        "⬆ Plus haut",
        f"{plus_haut:.2f}"
    )

    col4.metric(
        "⬇ Plus bas",
        f"{plus_bas:.2f}"
    )

    col5.metric(
        "📊 Volume",
        f"{volume:,.0f}"
    )

    st.divider()

# ==========================================
# Graphique principal
# ==========================================

    fig = create_candlestick_chart(
        historique,
        symbole
    )

    # EMA 20
    fig.add_trace(
        go.Scatter(
            x=historique.index,
            y=historique["EMA20"],
            name="EMA 20",
            line=dict(width=2)
        )
    )

    # EMA 50
    fig.add_trace(
        go.Scatter(
            x=historique.index,
            y=historique["EMA50"],
            name="EMA 50",
            line=dict(width=2)
        )
    )

    # EMA 200
    fig.add_trace(
        go.Scatter(
            x=historique.index,
            y=historique["EMA200"],
            name="EMA 200",
            line=dict(width=3)
        )
    )

    # Bollinger Haut
    fig.add_trace(
        go.Scatter(
            x=historique.index,
            y=historique["BB_HAUT"],
            name="BB Haut",
            line=dict(dash="dot")
        )
    )

    # Bollinger Bas
    fig.add_trace(
        go.Scatter(
            x=historique.index,
            y=historique["BB_BAS"],
            name="BB Bas",
            line=dict(dash="dot")
        )
    )

    fig.update_layout(
        height=700,
        template="plotly_dark",
        legend_orientation="h"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
# ==========================================
# RSI
# ==========================================

    st.divider()
    st.subheader("📉 RSI (Relative Strength Index)")

    fig_rsi = go.Figure()

    fig_rsi.add_trace(
        go.Scatter(
            x=historique.index,
            y=historique["RSI"],
            name="RSI"
        )
    )

    fig_rsi.add_hline(y=70)

    fig_rsi.add_hline(y=30)

    fig_rsi.update_layout(
        height=250,
        template="plotly_dark",
        yaxis_title="RSI"
    )

    st.plotly_chart(
        fig_rsi,
        use_container_width=True
    )

# ==========================================
# MACD
# ==========================================

    st.subheader("📊 MACD")

    fig_macd = go.Figure()

    fig_macd.add_trace(
        go.Scatter(
            x=historique.index,
            y=historique["MACD"],
            name="MACD"
        )
    )

    fig_macd.add_trace(
        go.Scatter(
            x=historique.index,
            y=historique["Signal"],
            name="Signal"
        )
    )

    fig_macd.add_trace(
        go.Bar(
            x=historique.index,
            y=historique["Histogramme"],
            name="Histogramme"
        )
    )

    fig_macd.update_layout(
        height=300,
        template="plotly_dark"
    )

    st.plotly_chart(
        fig_macd,
        use_container_width=True
    )

# ==========================================
# Analyse automatique
# ==========================================

    st.divider()

    st.subheader("🧠 Analyse Technique")

    score = 50

    if dernier_prix > historique["EMA20"].iloc[-1]:
        score += 10

    if dernier_prix > historique["EMA50"].iloc[-1]:
        score += 10

    if dernier_prix > historique["EMA200"].iloc[-1]:
        score += 15

    rsi = historique["RSI"].iloc[-1]

    if 45 <= rsi <= 65:
        score += 10

    if historique["MACD"].iloc[-1] > historique["Signal"].iloc[-1]:
        score += 15

    score = min(score, 100)

    if score >= 80:
        tendance = "🟢 Très haussière"
        recommandation = "🟢 Achat"

    elif score >= 65:
        tendance = "🟢 Haussière"
        recommandation = "Acheter"

    elif score >= 50:
        tendance = "🟡 Neutre"
        recommandation = "Conserver"

    elif score >= 35:
        tendance = "🟠 Baissière"
        recommandation = "Alléger"

    else:
        tendance = "🔴 Très baissière"
        recommandation = "Vendre"

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "🎯 Score Technique",
        f"{score}/100"
    )

    c2.metric(
        "📈 Tendance",
        tendance
    )

    c3.metric(
        "💡 Recommandation",
        recommandation
    )
# ==========================================
# Résumé Technique
# ==========================================

    st.divider()

    st.subheader("📋 Résumé Technique")

    points_forts = []
    risques = []

    if dernier_prix > historique["EMA20"].iloc[-1]:
        points_forts.append("✅ Prix au-dessus de l'EMA20")
    else:
        risques.append("⚠️ Prix sous l'EMA20")

    if dernier_prix > historique["EMA50"].iloc[-1]:
        points_forts.append("✅ Prix au-dessus de l'EMA50")
    else:
        risques.append("⚠️ Prix sous l'EMA50")

    if dernier_prix > historique["EMA200"].iloc[-1]:
        points_forts.append("✅ Tendance long terme haussière")
    else:
        risques.append("⚠️ Tendance long terme fragile")

    if historique["MACD"].iloc[-1] > historique["Signal"].iloc[-1]:
        points_forts.append("✅ MACD positif")
    else:
        risques.append("⚠️ MACD baissier")

    if 45 <= rsi <= 65:
        points_forts.append("✅ RSI équilibré")
    elif rsi > 70:
        risques.append("⚠️ RSI en surachat")
    elif rsi < 30:
        points_forts.append("✅ RSI en zone de survente")

    col1, col2 = st.columns(2)

    with col1:
        st.success("### ✅ Points forts")
        if points_forts:
            for point in points_forts:
                st.write(point)
        else:
            st.write("Aucun point fort majeur détecté.")

    with col2:
        st.warning("### ⚠️ Points de vigilance")
        if risques:
            for risque in risques:
                st.write(risque)
        else:
            st.write("Aucun risque particulier détecté.")

    st.divider()

# ==========================================
# Synthèse
# ==========================================

    st.subheader("🧠 Synthèse")

    if score >= 80:
        st.success(
            "L'analyse technique est très favorable. "
            "La tendance est solide et les indicateurs sont majoritairement positifs."
        )
    elif score >= 65:
        st.info(
            "La tendance reste positive mais mérite une surveillance régulière."
        )
    elif score >= 50:
        st.warning(
            "Le marché est actuellement neutre. "
            "Attendre une confirmation peut être judicieux."
        )
    else:
        st.error(
            "Les indicateurs techniques sont défavorables. "
            "Une approche prudente est recommandée."
        )

    st.progress(score / 100)

    st.caption(
        "⚠️ Cette analyse est basée sur des indicateurs techniques "
        "et ne constitue pas un conseil en investissement."
    )