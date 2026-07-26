"""Enrichissement des résultats déjà chargés par le scanner."""
from core.data_quality import evaluer_qualite_donnees
from core.decision import construire_decision
from core.opportunity_ranking import classer_opportunites
from core.strategy_engine import evaluer_strategie
def classer_resultats_scanner(resultats,profil):
    candidats=[]
    for ligne in resultats:
        score={"score":ligne.get("Score"),"signal":ligne.get("Signal"),"raisons":ligne.get("Raisons",[]),"ventilation":ligne.get("Ventilation",[])}; decision=construire_decision(score); insuffisant=ligne.get("Signal")=="DONNÉES INSUFFISANTES"
        qualite=evaluer_qualite_donnees({"nombre_points":ligne.get("Nombre points",0),"minimum_requis":profil["regles"]["historique_minimum"],"prix":ligne.get("Prix"),"volume_disponible":ligne.get("Volume disponible") is True,"volatilite_disponible":ligne.get("Volatilité disponible") is True,"indicateurs_essentiels":{"score":not insuffisant,"rsi":ligne.get("RSI") is not None}}); strategie=evaluer_strategie(score,score,decision,profil,qualite)
        candidats.append({"symbole":ligne.get("Actif"),"nom":ligne.get("Actif"),"categorie":ligne.get("Catégorie"),"strategie":profil["nom"],"score_technique":ligne.get("Score"),"score_strategie":strategie["score_strategie"],"confiance":strategie["confiance"],"decision":decision.get("recommandation","Indisponible"),"score_qualite":qualite["score_qualite"],"qualite_donnees":qualite["niveau"],"plan_risque_disponible":ligne.get("ATR") is not None,"prix":ligne.get("Prix"),"variation":ligne.get("Variation %"),"date_donnees":ligne.get("Date données"),"atr":ligne.get("ATR"),"raisons_principales":strategie["forces"] or ligne.get("Raisons",[]),"points_vigilance":strategie["faiblesses"]+qualite["problemes"]+qualite["avertissements"]})
    return classer_opportunites(candidats)
