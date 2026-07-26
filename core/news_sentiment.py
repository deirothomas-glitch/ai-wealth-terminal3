"""Lecture lexicale prudente et explicable des actualités."""
import re
POS={"hausse","croissance","record","progression","benefice","bénéfice","accord","innovation","ameliore","améliore","solide","rebond"}
NEG={"baisse","perte","chute","enquete","enquête","risque","alerte","recul","fraude","licenciement","dette","faible"}
def analyser_sentiment_actualite(article):
    d=dict(article) if isinstance(article,dict) else {}; text=(str(d.get("titre","")+" "+str(d.get("resume","")))).casefold(); words=set(re.findall(r"[a-zà-ÿ]+",text)); pos=sorted(words&POS); neg=sorted(words&NEG)
    if not text.strip(): sentiment="indetermine"
    elif pos and neg: sentiment="mixte"
    elif pos: sentiment="positif"
    elif neg: sentiment="negatif"
    else: sentiment="neutre"
    total=len(pos)+len(neg); score=0.0 if not total else round((len(pos)-len(neg))/total,2); confidence="elevee" if total>=4 else "moderee" if total>=2 else "faible"
    limits=["Le sentiment lexical ne prédit pas l’évolution future du prix."]
    if sentiment in ("neutre","indetermine"): limits.append("Le texte fournit peu d’indices directionnels explicites.")
    return {"sentiment":sentiment,"score":score,"confiance":confidence,"facteurs_positifs":pos,"facteurs_negatifs":neg,"limites":limits}
