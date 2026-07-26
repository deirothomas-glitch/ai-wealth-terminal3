"""Accès centralisé et mis en cache aux données Yahoo Finance."""

from __future__ import annotations

import math
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


def _nombre_fini(valeur):
    if isinstance(valeur, bool):
        return None
    try:
        nombre = float(valeur)
    except (TypeError, ValueError):
        return None
    return nombre if math.isfinite(nombre) else None


def dernier_prix(dataframe):
    try:
        valeur = dataframe["Close"].iloc[-1] if dataframe is not None and not dataframe.empty else None
    except (KeyError, IndexError, TypeError, AttributeError):
        return 0.0
    nombre = _nombre_fini(valeur)
    return round(nombre, 2) if nombre is not None and nombre > 0 else 0.0


def variation_journaliere(dataframe):
    try:
        if dataframe is None or len(dataframe) < 2:
            return 0.0
        precedent = _nombre_fini(dataframe["Close"].iloc[-2])
    except (KeyError, IndexError, TypeError, AttributeError):
        return 0.0
    actuel = dernier_prix(dataframe)
    return round((actuel - precedent) / precedent * 100, 2) if precedent is not None and precedent > 0 and actuel > 0 else 0.0


def dernier_volume(dataframe):
    try:
        valeur = dataframe["Volume"].iloc[-1] if dataframe is not None and not dataframe.empty else None
    except (KeyError, IndexError, TypeError, AttributeError):
        return 0
    nombre = _nombre_fini(valeur)
    return int(nombre) if nombre is not None and nombre >= 0 else 0


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


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def recuperer_indices():
    return _recuperer_liste(MARKET_INDICES)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def recuperer_cryptos():
    return _recuperer_liste(CRYPTO_ASSETS)
