import streamlit as st
import yfinance as yf
import pandas as pd
from ai_analysis import analyser_actif

# ==========================================
# Watchlist
# ==========================================

WATCHLIST = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Nvidia": "NVDA",
    "Amazon": "AMZN",
    "Meta": "META",
    "Google": "GOOGL",
    "Tesla": "TSLA",
    "Netflix": "NFLX",
    "AMD": "AMD",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Solana": "SOL-USD"
}


# ==========================================
# Récupération des données
# ==========================================

def charger_donnees(symbole, periode="6mo"):

    try:
        df = yf.Ticker(symbole).history(period=periode)

        if df.empty:
            return None

        df = df.dropna()

        return df

    except Exception as e:
        st.write(f"Erreur pour {symbole} :", e)
        return None

# ==========================================
# EMA
# ==========================================

def ajouter_ema(df):

    df["EMA20"] = df["Close"].ewm(span=20).mean()

    df["EMA50"] = df["Close"].ewm(span=50).mean()

    df["EMA200"] = df["Close"].ewm(span=200).mean()

    return df


# ==========================================
# RSI
# ==========================================

def calcul_rsi(df, periode=14):

    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0)

    perte = -delta.where(delta < 0, 0)

    gain = gain.rolling(periode).mean()

    perte = perte.rolling(periode).mean()

    rs = gain / perte

    df["RSI"] = 100 - (100 / (1 + rs))

    return df
# ==========================================
# MACD
# ==========================================

def ajouter_macd(df):

    ema12 = df["Close"].ewm(span=12, adjust=False).mean()

    ema26 = df["Close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26

    df["MACD_SIGNAL"] = (
        df["MACD"]
        .ewm(span=9, adjust=False)
        .mean()
    )

    df["MACD_HIST"] = (
        df["MACD"] - df["MACD_SIGNAL"]
    )

    return df


# ==========================================
# Score Technique
# ==========================================

def calcul_score(df):

    if df is None or len(df) < 60:
        return None

    df = ajouter_ema(df)

    df = calcul_rsi(df)

    df = ajouter_macd(df)

    prix = float(df["Close"].iloc[-1])

    ema20 = float(df["EMA20"].iloc[-1])

    ema50 = float(df["EMA50"].iloc[-1])

    ema200 = float(df["EMA200"].iloc[-1])

    rsi = float(df["RSI"].iloc[-1])

    macd = float(df["MACD"].iloc[-1])

    signal = float(df["MACD_SIGNAL"].iloc[-1])

    score = 50

    # EMA
    if prix > ema20:
        score += 10

    if prix > ema50:
        score += 10

    if prix > ema200:
        score += 15

    # RSI
    if 45 <= rsi <= 65:
        score += 10
    elif rsi < 30:
        score += 15
    elif rsi > 70:
        score -= 10

    # MACD
    if macd > signal:
        score += 15

    return max(0, min(score, 100))


# ==========================================
# Tendance
# ==========================================

def determiner_tendance(score):

    if score >= 80:
        return "🟢 Très haussière"

    elif score >= 65:
        return "🟢 Haussière"

    elif score >= 50:
        return "🟡 Neutre"

    elif score >= 35:
        return "🟠 Baissière"

    return "🔴 Très baissière"

# ==========================================
# Scanner
# ==========================================

def scanner_marche():

    resultat = []

    total = len(WATCHLIST)

    barre = st.progress(0)

    for i, (nom, symbole) in enumerate(WATCHLIST.items()):

        df = charger_donnees(symbole)

        barre.progress((i + 1) / total)

        if df is None:
            continue

        score = calcul_score(df)

        if score is None:
            continue

        prix = round(float(df["Close"].iloc[-1]), 2)

        variation = round(
            (
                (df["Close"].iloc[-1] - df["Close"].iloc[-2])
                / df["Close"].iloc[-2]
            ) * 100,
            2
        )

        rsi = round(float(df["RSI"].iloc[-1]), 1)

        resultat.append(
            {
                "Actif": nom,
                "Symbole": symbole,
                "Prix": prix,
                "Variation %": variation,
                "RSI": rsi,
                "Score": score,
                "Tendance": determiner_tendance(score)
            }
        )

    barre.empty()

    if len(resultat) == 0:
        return pd.DataFrame()

    df_resultat = pd.DataFrame(resultat)

    df_resultat = df_resultat.sort_values(
        by="Score",
        ascending=False
    )

    return df_resultat


# ==========================================
# Interface Scanner
# ==========================================
if "resultat_scanner" not in st.session_state:
    st.session_state.resultat_scanner = None
def afficher_scanner():

    st.header("🔎 Scanner IA")

    st.write(
        "Analyse automatique de la watchlist "
        "avec score technique."
    )

    if st.button("🚀 Scanner les marchés"):

        with st.spinner("Analyse en cours..."):
            try:
                st.session_state.resultat_scanner = scanner_marche()

            except Exception as e:
                st.error(f"ERREUR : {e}")
                st.stop()

    resultat = st.session_state.resultat_scanner

    if resultat is None:
        return

    if resultat.empty:

            st.error(
                "Aucun actif n'a pu être analysé."
            )

            return

    st.success(
            f"{len(resultat)} actifs analysés."
        )

    st.dataframe(
            resultat,
            use_container_width=True,
            hide_index=True
        )
    st.divider()

    st.subheader("🤖 Analyse IA")

    actif = st.selectbox(
            "Choisir un actif",
            resultat["Actif"]
        )

    if st.button("Analyser avec l'IA"):

            ligne = resultat[resultat["Actif"] == actif].iloc[0]

            with st.spinner("Analyse par l'IA..."):
                try:
                    st.write("Avant analyser_actif")

                    analyse = analyser_actif(
                        nom=ligne["Actif"],
                        symbole=ligne["Symbole"],
                        prix=ligne["Prix"],
                        score=ligne["Score"],
                        rsi=ligne["RSI"],
                        tendance=ligne["Tendance"]
                    )
                    
                    st.write("Après analyser_actif")
                    st.success("Réponse reçue")

                except Exception as e:
                    st.error(str(e))
            st.markdown(analyse)

    top = resultat.iloc[0]

    st.subheader("🏆 Meilleure opportunité")

    c1, c2, c3 = st.columns(3)

    c1.metric(
            "Actif",
            top["Actif"]
        )

    c2.metric(
            "Score",
            f"{top['Score']}/100"
        )

    c3.metric(
            "Tendance",
            top["Tendance"]
        )
# ==========================================
# Filtres et export
# ==========================================

    st.divider()

    st.subheader("🎯 Filtrer les résultats")

    score_min = st.slider(
            "Score minimum",
            min_value=0,
            max_value=100,
            value=60,
            step=5
        )

    resultat_filtre = resultat[
            resultat["Score"] >= score_min
        ]

    st.dataframe(
            resultat_filtre,
            use_container_width=True,
            hide_index=True
        )

    csv = resultat_filtre.to_csv(index=False).encode("utf-8")

    st.download_button(
            label="📥 Exporter en CSV",
            data=csv,
            file_name="scanner_ai_wealth_terminal.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.divider()

    st.subheader("📈 Résumé")

    moyenne = resultat["Score"].mean()

    if moyenne >= 75:
            st.success(
                "Le marché présente actuellement un contexte technique globalement haussier."
            )

    elif moyenne >= 60:
            st.info(
                "Le marché est plutôt positif mais certaines opportunités demandent confirmation."
            )

    elif moyenne >= 45:
            st.warning(
                "Le marché est neutre. Il est conseillé d'attendre des signaux plus forts."
            )

    else:
            st.error(
                "Le marché est actuellement fragile. Une gestion prudente du risque est recommandée."
            )

    st.progress(moyenne / 100)

    st.caption(
            "⚠️ Les scores sont calculés à partir d'indicateurs techniques (EMA, RSI et MACD). "
            "Ils ne constituent pas un conseil en investissement."
        )