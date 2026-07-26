"""Persistance JSON locale, défensive et atomique."""
import json
import os
import tempfile
from pathlib import Path
PORTFOLIO_FILE=Path("portfolio.json")
JOURNAL_FILE=Path("trading_journal.json")
FICHIER=PORTFOLIO_FILE

def _lire_liste(chemin):
    if not chemin.exists(): return [], None
    try:
        texte=chemin.read_text(encoding="utf-8")
        if not texte.strip(): return [], None
        data=json.loads(texte)
        if not isinstance(data,list): return [], f"{chemin.name} ne contient pas une liste JSON."
        return [x for x in data if isinstance(x,dict)], None
    except (OSError,UnicodeError,json.JSONDecodeError) as e:
        return [], f"Impossible de lire {chemin.name} : {e}. Le fichier a été conservé."

def _ecrire_atomique(chemin, donnees):
    chemin.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix=f".{chemin.name}.",suffix=".tmp",dir=str(chemin.parent),text=True)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(donnees,f,ensure_ascii=False,indent=2,allow_nan=False); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(temp,chemin)
    except Exception:
        try: os.unlink(temp)
        except OSError: pass
        raise

def charger_portefeuille(chemin=PORTFOLIO_FILE): return _lire_liste(Path(chemin))[0]
def charger_portefeuille_avec_erreur(chemin=PORTFOLIO_FILE): return _lire_liste(Path(chemin))
def sauvegarder_portefeuille(portefeuille,chemin=PORTFOLIO_FILE): _ecrire_atomique(Path(chemin),list(portefeuille))
def charger_journal(chemin=JOURNAL_FILE): return _lire_liste(Path(chemin))[0]
def charger_journal_avec_erreur(chemin=JOURNAL_FILE): return _lire_liste(Path(chemin))
def sauvegarder_journal(journal,chemin=JOURNAL_FILE): _ecrire_atomique(Path(chemin),list(journal))
