"""Sources extensibles d'actualités financières."""
from typing import Protocol
from core.news_normalization import SYMBOL_RE

class NewsSource(Protocol):
    nom: str
    def fetch(self,symbole:str,limite:int)->list[dict]: ...

class YahooNewsSource:
    nom="Yahoo Finance"
    def __init__(self,ticker_factory=None):
        if ticker_factory is None:
            import yfinance as yf
            ticker_factory=yf.Ticker
        self._ticker_factory=ticker_factory
    def fetch(self,symbole,limite):
        symbole=str(symbole or "").upper().strip()
        if not SYMBOL_RE.fullmatch(symbole):
            return []
        raw=self._ticker_factory(symbole).news or []; result=[]
        for item in raw[:max(0,int(limite))]:
            if not isinstance(item,dict):continue
            c=item.get("content") if isinstance(item.get("content"),dict) else item
            provider=c.get("provider") if isinstance(c.get("provider"),dict) else {}
            canonical=c.get("canonicalUrl") if isinstance(c.get("canonicalUrl"),dict) else {}
            thumbnail=c.get("thumbnail") if isinstance(c.get("thumbnail"),dict) else {}
            resolutions=thumbnail.get("resolutions") if isinstance(thumbnail.get("resolutions"),list) else []
            image=next((x.get("url") for x in resolutions if isinstance(x,dict) and x.get("url")),None)
            result.append({"identifiant":str(item.get("id") or c.get("id") or ""),"titre":c.get("title"),"resume":c.get("summary") or c.get("description"),"source":provider.get("displayName") or c.get("publisher"),"url":canonical.get("url") or c.get("link"),"date_publication":c.get("pubDate") or c.get("providerPublishTime"),"symboles":[symbole],"categories":c.get("categories",[]),"langue":c.get("language","indetermine"),"image_url":image})
        return result
