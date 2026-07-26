"""Compatibilité avec les anciennes pages de l'application."""

from market_data import charger_donnees, recuperer_infos


def get_stock_history(symbol, period="1mo"):
    return charger_donnees(symbol, period)


def get_stock_info(symbol):
    return recuperer_infos(symbol)
