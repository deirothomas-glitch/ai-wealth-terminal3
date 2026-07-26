"""Adaptation pandas et reconstruction causale des signaux de backtest."""
from core.backtest import executer_backtest
def preparer_historique(dataframe,profil):
    if dataframe is None or getattr(dataframe,"empty",True): return []
    closes=[float(v) for v in dataframe["Close"].tolist()]; opens=[float(v) for v in dataframe["Open"].tolist()] if "Open" in dataframe else closes; highs=[float(v) for v in dataframe["High"].tolist()] if "High" in dataframe else closes; lows=[float(v) for v in dataframe["Low"].tolist()] if "Low" in dataframe else closes; dates=[str(v) for v in dataframe.index.tolist()]; rows=[]
    fenetre={"court_terme":10,"swing":20,"tendance":50}.get(profil.get("identifiant"),20)
    for i,c in enumerate(closes):
        moyenne=sum(closes[max(0,i-fenetre+1):i+1])/min(i+1,fenetre); precedente=sum(closes[max(0,i-fenetre):i])/min(i,fenetre) if i else moyenne
        rows.append({"date":dates[i],"open":opens[i],"high":highs[i],"low":lows[i],"close":c,"signal_entree":i>=fenetre and c>moyenne and closes[i-1]<=precedente,"signal_sortie":i>=fenetre and c<moyenne and closes[i-1]>=precedente})
    return rows
def lancer_backtest(symbole,profil,charger_historique,**parametres):
    historique=charger_historique(symbole,profil["periode_donnees"]); rows=preparer_historique(historique,profil); return executer_backtest(rows,profil["nom"],symbole,**parametres)
