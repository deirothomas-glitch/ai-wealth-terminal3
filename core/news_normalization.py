"""Normalisation pure des actualités externes."""
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

SYMBOL_RE = re.compile(r"^[A-Z0-9.^=-]{1,20}$")

def _texte(value, default=""):
    return value.strip() if isinstance(value, str) else default

def _url(value):
    text=_texte(value)
    if not text: return ""
    parts=urlsplit(text)
    if parts.scheme not in ("http","https") or not parts.netloc: return ""
    return urlunsplit((parts.scheme.lower(),parts.netloc.lower(),parts.path,parts.query,""))

def _date(value):
    if value is None: return None
    if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value):
        try: return datetime.fromtimestamp(value,tz=timezone.utc).isoformat()
        except (OSError,OverflowError,ValueError): return None
    if isinstance(value,str) and value.strip():
        text=value.strip().replace("Z","+00:00")
        try: return datetime.fromisoformat(text).isoformat()
        except ValueError: return None
    return None

def _list_text(value, upper=False):
    result=[]
    for item in value if isinstance(value,(list,tuple,set)) else []:
        text=_texte(item)
        if upper: text=text.upper()
        if text and (not upper or SYMBOL_RE.fullmatch(text)) and text not in result: result.append(text)
    return result

def normaliser_actualite(article, symbole=None):
    """Retourne un contrat sûr sans inventer titre, source ou URL."""
    data=dict(article) if isinstance(article,dict) else {}
    title=_texte(data.get("titre") or data.get("title"))
    source=_texte(data.get("source") or data.get("publisher") or data.get("provider"))
    url=_url(data.get("url") or data.get("lien") or data.get("link"))
    symbols=_list_text(data.get("symboles") or data.get("symbols"),upper=True)
    if isinstance(symbole,str) and SYMBOL_RE.fullmatch(symbole.upper()) and symbole.upper() not in symbols: symbols.append(symbole.upper())
    raw_id=_texte(data.get("identifiant") or data.get("id"))
    identity=raw_id or url or "|".join((title.casefold(),source.casefold(),str(_date(data.get("date_publication") or data.get("date") or data.get("providerPublishTime")))))
    identifier=raw_id or (hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24] if identity.strip("|") else "")
    result={"identifiant":identifier,"titre":title,"resume":_texte(data.get("resume") or data.get("summary") or data.get("description")),"source":source,"url":url,"date_publication":_date(data.get("date_publication") or data.get("date") or data.get("pubDate") or data.get("providerPublishTime")),"symboles":symbols,"categories":_list_text(data.get("categories")),"langue":_texte(data.get("langue") or data.get("language"),"indetermine"),"image_url":_url(data.get("image_url") or data.get("image")) or None}
    json.dumps(result,ensure_ascii=False,allow_nan=False)
    return result
