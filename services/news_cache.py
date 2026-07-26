"""Cache JSON local, défensif et atomique des actualités et briefings."""
import json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
NEWS_CACHE_FILE=Path("data_cache/news_latest.json"); BRIEFING_CACHE_FILE=Path("data_cache/daily_briefing.json")
def _read(path):
    p=Path(path)
    if not p.exists():return {"date_rafraichissement":None,"donnees":[]},None
    try:
        text=p.read_text(encoding="utf-8")
        if not text.strip():return {"date_rafraichissement":None,"donnees":[]},None
        data=json.loads(text)
        if not isinstance(data,dict):raise ValueError("contrat JSON invalide")
        return data,None
    except (OSError,UnicodeError,json.JSONDecodeError,ValueError) as e:return {"date_rafraichissement":None,"donnees":[]},f"Cache illisible, fichier conservé : {e}"
def _write(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=f".{p.name}.",suffix=".tmp",dir=str(p.parent),text=True)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n");f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    except Exception:
        try:os.unlink(tmp)
        except OSError:pass
        raise
def charger_cache_actualites(path=NEWS_CACHE_FILE):return _read(path)
def sauvegarder_cache_actualites(actualites,path=NEWS_CACHE_FILE):_write(path,{"date_rafraichissement":datetime.now(timezone.utc).isoformat(),"donnees":list(actualites)})
def charger_cache_briefing(path=BRIEFING_CACHE_FILE):return _read(path)
def sauvegarder_cache_briefing(briefing,path=BRIEFING_CACHE_FILE):_write(path,{"date_rafraichissement":datetime.now(timezone.utc).isoformat(),"donnees":briefing})
