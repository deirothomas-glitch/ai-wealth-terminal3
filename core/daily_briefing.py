"""Construction pure du briefing quotidien à partir de contrats existants."""
import json
def construire_briefing(indices=None,opportunites=None,positions=None,actualites=None,qualite=None,date_generation=None):
    idx=[x for x in indices if isinstance(x,dict)][:6] if isinstance(indices,list) else []; opp=[dict(x) for x in opportunites if isinstance(x,dict)][:5] if isinstance(opportunites,list) else []; pos=[dict(x) for x in positions if isinstance(x,dict)][:5] if isinstance(positions,list) else []; news=[dict(x) for x in actualites if isinstance(x,dict)][:5] if isinstance(actualites,list) else []
    summary=[]
    for x in idx:
        name=str(x.get("nom") or x.get("symbole") or "Marché"); variation=x.get("variation"); summary.append(f"{name} : variation indisponible." if not isinstance(variation,(int,float)) else f"{name} : {variation:+.2f}% sur la dernière séance.")
    missing=[]
    if not idx:missing.append("indices")
    if not opp:missing.append("scanner")
    if not news:missing.append("actualites")
    risks=[]
    for x in pos:
        for key in ("message","titre"):
            if isinstance(x.get(key),str) and x[key] not in risks:risks.append(x[key]);break
    if isinstance(qualite,dict) and qualite.get("niveau")!="bon":risks.append("La qualité générale des données doit être vérifiée.")
    result={"date_generation":str(date_generation or ""),"resume_marche":summary,"opportunites_a_surveiller":opp,"positions_a_surveiller":pos,"actualites_principales":news,"risques_du_jour":risks[:8],"donnees_manquantes":missing}
    json.dumps(result,ensure_ascii=False,allow_nan=False);return result
