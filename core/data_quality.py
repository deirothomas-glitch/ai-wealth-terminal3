"""Évaluation pure de la qualité de données déjà résumées."""
import math
from datetime import date,datetime,timezone
def _fini(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def evaluer_qualite_donnees(informations):
    d=dict(informations) if isinstance(informations,dict) else {}; problemes=[]; avert=[]; score=100.0
    n=d.get("nombre_points",0)
    if not isinstance(n,int) or n<1: problemes.append("Historique absent."); score-=60
    elif n<int(d.get("minimum_requis",40) or 40): problemes.append("Historique trop court."); score-=35
    prix=d.get("prix")
    if not _fini(prix) or prix<=0: problemes.append("Prix non positif ou invalide."); score-=45
    manquantes=d.get("valeurs_manquantes",0)
    if not isinstance(manquantes,int) or manquantes<0: manquantes=1
    if manquantes: problemes.append("Valeurs manquantes détectées."); score-=min(30,5+manquantes)
    if not d.get("volume_disponible",False): avert.append("Volume absent."); score-=10
    if not d.get("volatilite_disponible",False): avert.append("Volatilité non calculable."); score-=15
    essentiels=d.get("indicateurs_essentiels",{})
    if not isinstance(essentiels,dict) or not essentiels or not all(essentiels.values()): problemes.append("Indicateurs essentiels absents."); score-=25
    if d.get("donnees_incoherentes",False): problemes.append("Données incohérentes."); score-=40
    age=d.get("age_jours")
    if _fini(age) and age>7: avert.append("Données anciennes."); score-=15
    score=max(0.0,min(100.0,score)); critique=any(x in problemes for x in ("Historique absent.","Prix non positif ou invalide.","Données incohérentes.")); niveau="insuffisant" if critique or score<45 else ("bon" if score>=80 and not problemes else "partiel")
    return {"valide":niveau!="insuffisant","niveau":niveau,"score_qualite":score,"problemes":problemes,"avertissements":avert}
