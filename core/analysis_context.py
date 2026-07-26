"""Construction pure d'un contexte d'analyse borné et JSON strict."""
import copy,json,math
SECTIONS=("actif","marche","technique","strategie","decision","risque","qualite_donnees","actualites","sentiment_actualites","portefeuille","limites")
def _safe(v,depth=0):
    if depth>5:return None
    if v is None or isinstance(v,(str,bool,int)):return v
    if isinstance(v,float):return v if math.isfinite(v) else None
    if isinstance(v,(list,tuple)):return [_safe(x,depth+1) for x in v[:20]]
    if isinstance(v,dict):return {str(k):_safe(x,depth+1) for k,x in list(v.items())[:40]}
    return str(v)[:500]
def construire_contexte_analyse(actif=None,marche=None,technique=None,strategie=None,decision=None,risque=None,qualite_donnees=None,actualites=None,sentiment_actualites=None,portefeuille=None,limites=None,max_actualites=5):
    news=(actualites if isinstance(actualites,list) else [])[:max(0,min(int(max_actualites),10))]
    result={"actif":_safe(actif if isinstance(actif,dict) else {}),"marche":_safe(marche if isinstance(marche,dict) else {}),"technique":_safe(technique if isinstance(technique,dict) else {}),"strategie":_safe(strategie if isinstance(strategie,dict) else {}),"decision":_safe(decision if isinstance(decision,dict) else {}),"risque":_safe(risque if isinstance(risque,dict) else {}),"qualite_donnees":_safe(qualite_donnees if isinstance(qualite_donnees,dict) else {}),"actualites":_safe(news),"sentiment_actualites":_safe(sentiment_actualites if isinstance(sentiment_actualites,dict) else {}),"portefeuille":_safe(portefeuille) if isinstance(portefeuille,dict) else None,"limites":[str(x) for x in limites if isinstance(x,str)][:10] if isinstance(limites,list) else []}
    json.dumps(result,ensure_ascii=False,allow_nan=False); return result
