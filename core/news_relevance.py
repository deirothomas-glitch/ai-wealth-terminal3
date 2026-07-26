"""Pertinence déterministe d'une actualité pour un actif."""
import re
import unicodedata
def _norm(v): return " ".join(re.findall(r"[a-z0-9]+",unicodedata.normalize("NFKD",str(v or "")).encode("ascii","ignore").decode().casefold()))
def evaluer_pertinence_actualite(article,symbole,nom_actif="",categorie="",mots_cles=None):
    d=dict(article) if isinstance(article,dict) else {}; text=_norm(" ".join((str(d.get("titre","")),str(d.get("resume",""))))); reasons=[]; score=0.0
    sym=str(symbole or "").upper(); symbols=[str(x).upper() for x in d.get("symboles",[]) if isinstance(x,str)]
    if sym and sym in symbols: score+=65; reasons.append("Symbole explicitement associé à l’article.")
    elif sym and re.search(rf"(?<![A-Z0-9]){re.escape(sym)}(?![A-Z0-9])",str(d.get("titre","")).upper()): score+=55; reasons.append("Symbole présent dans le titre.")
    name=_norm(nom_actif)
    if len(name)>=4 and name in text: score+=30; reasons.append("Nom de l’actif présent.")
    matched=[]
    for word in mots_cles if isinstance(mots_cles,list) else []:
        w=_norm(word)
        if len(w)>=4 and w in text and w not in matched: matched.append(w)
    if matched: score+=min(20,5*len(matched)); reasons.append("Mots-clés spécifiques présents.")
    cat=_norm(categorie)
    if cat and len(cat)>=4 and cat in text: score+=5; reasons.append("Catégorie mentionnée.")
    score=min(100.0,score); level="forte" if score>=65 else "moyenne" if score>=30 else "faible"
    if not reasons: reasons.append("Aucun lien spécifique suffisant avec l’actif.")
    return {"score_pertinence":round(score,2),"niveau":level,"raisons":reasons}
