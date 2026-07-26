"""Déduplication pure et stable des actualités."""
import re
import unicodedata
from difflib import SequenceMatcher
from urllib.parse import parse_qsl,urlsplit,urlunsplit,urlencode

def _titre(text):
    value=unicodedata.normalize("NFKD",text if isinstance(text,str) else "").encode("ascii","ignore").decode().casefold()
    return " ".join(re.findall(r"[a-z0-9]+",value))

def _url(text):
    if not isinstance(text,str) or not text: return ""
    p=urlsplit(text); query=urlencode([(k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith(("utm_","fbclid","gclid"))])
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/"),query,""))

def dedupliquer_actualites(actualites, seuil_similarite=0.88):
    resultat=[]; signatures=[]
    for article in actualites if isinstance(actualites,list) else []:
        if not isinstance(article,dict): continue
        copie={k:(list(v) if isinstance(v,list) else v) for k,v in article.items()}
        url=_url(copie.get("url")); titre=_titre(copie.get("titre")); source=str(copie.get("source") or "").casefold(); date=str(copie.get("date_publication") or "")[:10]
        duplicate=False
        for u,t,s,d in signatures:
            if url and u and url==u: duplicate=True
            elif titre and t and titre==t: duplicate=True
            elif titre and t and SequenceMatcher(None,titre,t).ratio()>=seuil_similarite: duplicate=True
            elif source and date and source==s and date==d and titre and t and SequenceMatcher(None,titre,t).ratio()>=0.75: duplicate=True
            if duplicate: break
        if not duplicate: resultat.append(copie); signatures.append((url,titre,source,date))
    return resultat
