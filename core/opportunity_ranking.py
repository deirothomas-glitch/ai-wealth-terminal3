"""Classement pur et déterministe des opportunités calculées."""
import math
def _f(v): return float(v) if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) else None
def classer_opportunites(resultats):
    lignes=[]
    for entree in resultats if isinstance(resultats,list) else []:
        x=dict(entree) if isinstance(entree,dict) else {}; tech=_f(x.get("score_technique")); strat=_f(x.get("score_strategie")); qual=_f(x.get("score_qualite")); niveau=str(x.get("qualite_donnees","insuffisant")); confiance=str(x.get("confiance","faible")); decision=str(x.get("decision","Indisponible"))
        if tech is None or strat is None or niveau=="insuffisant": global_=None
        else:
            global_=tech*.45+strat*.35+(qual or 0)*.20+({"elevee":5,"moderee":0,"faible":-8}.get(confiance,-8))+(3 if x.get("plan_risque_disponible") else -4)+(-12 if decision=="Éviter" else 0); global_=round(max(0,min(100,global_)),2)
        lignes.append({"rang":0,"symbole":str(x.get("symbole","")),"nom":str(x.get("nom",x.get("symbole",""))),"categorie":str(x.get("categorie","")),"strategie":str(x.get("strategie","")),"score_global":global_,"score_technique":tech,"score_strategie":strat,"confiance":confiance,"decision":decision,"qualite_donnees":niveau,"plan_risque_disponible":bool(x.get("plan_risque_disponible")),"raisons_principales":[str(v) for v in x.get("raisons_principales",[]) if isinstance(v,str)][:3],"points_vigilance":[str(v) for v in x.get("points_vigilance",[]) if isinstance(v,str)][:3],"prix":_f(x.get("prix")),"variation":_f(x.get("variation")),"date_donnees":str(x.get("date_donnees") or "Indisponible"),"atr":_f(x.get("atr"))})
    lignes.sort(key=lambda x:(x["score_global"] is None,-(x["score_global"] or 0),x["symbole"]));
    for n,x in enumerate(lignes,1): x["rang"]=n
    return lignes
