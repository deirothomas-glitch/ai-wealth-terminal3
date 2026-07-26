"""Accès centralisé et mis en cache aux données Yahoo Finance."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from config import CACHE_TTL, CRYPTO_ASSETS, DEFAULT_PERIOD, MARKET_INDICES


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def charger_donnees(symbole: str, periode: str = DEFAULT_PERIOD):
    try:
        historique = yf.Ticker(symbole).history(
            period=periode, auto_adjust=False)
        return historique.dropna() if historique is not None and not historique.empty else None
    except Exception:
        return None


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def recuperer_infos(symbole: str):
    try:
        return yf.Ticker(symbole).info or {}
    except Exception:
        return {}


def dernier_prix(dataframe):
    return round(float(dataframe["Close"].iloc[-1]), 2) if dataframe is not None and not dataframe.empty else 0.0


def variation_journaliere(dataframe):
    if dataframe is None or len(dataframe) < 2:
        return 0.0
    precedent = float(dataframe["Close"].iloc[-2])
    return round((dernier_prix(dataframe) - precedent) / precedent * 100, 2) if precedent else 0.0


def dernier_volume(dataframe):
    return int(dataframe["Volume"].iloc[-1]) if dataframe is not None and not dataframe.empty else 0


def snapshot(symbole):
    historique = charger_donnees(symbole)
    if historique is None:
        return None
    return {"symbole": symbole, "prix": dernier_prix(historique), "variation": variation_journaliere(historique), "volume": dernier_volume(historique), "historique": historique}


def _recuperer_liste(actifs):
    resultat = []
    for nom, ticker in actifs.items():
        donnees = snapshot(ticker)
        if donnees:
            resultat.append({"nom": nom, "ticker": ticker, **donnees})
    return resultat


def recuperer_indices():
    return _recuperer_liste(MARKET_INDICES)


def recuperer_cryptos():
    return _recuperer_liste(CRYPTO_ASSETS)
