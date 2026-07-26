"""Évaluation pure de la qualité d'une actualité."""
from datetime import datetime,timezone
KNOWN_SOURCES={"reuters","associated press","bloomberg","yahoo finance","afp","cnbc","financial times","les echos"}
def evaluer_qualite_actualite(article, date_reference=None):
    d=dict(article) if isinstance(article,dict) else {}; problems=[]; warnings=[]; score=100.0
    if not isinstance(d.get("titre"),str) or not d["titre"].strip(): problems.append("Titre absent."); score-=45
    source=d.get("source")
    if not isinstance(source,str) or not source.strip(): problems.append("Source absente."); score-=25
    elif source.strip().casefold() not in KNOWN_SOURCES: warnings.append("Source non répertoriée ; sa fiabilité n’est pas déterminée."); score-=5
    if not isinstance(d.get("url"),str) or not d["url"].startswith(("http://","https://")): problems.append("URL absente ou invalide."); score-=20
    raw_date=d.get("date_publication")
    if not raw_date: warnings.append("Date de publication absente."); score-=10
    else:
        try:
            dt=datetime.fromisoformat(str(raw_date).replace("Z","+00:00")); dt=dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            if date_reference is not None:
                ref=date_reference if date_reference.tzinfo else date_reference.replace(tzinfo=timezone.utc)
                if (ref-dt).days>30: warnings.append("Article ancien."); score-=15
        except (TypeError,ValueError): problems.append("Date de publication invalide."); score-=15
    if not isinstance(d.get("resume"),str) or not d["resume"].strip(): warnings.append("Résumé absent."); score-=10
    if not d.get("symboles"): warnings.append("Aucun symbole identifié."); score-=5
    score=max(0.0,min(100.0,score)); level="bon" if score>=80 and not problems else "partiel" if score>=45 else "insuffisant"
    return {"valide":level!="insuffisant","score_qualite":round(score,2),"niveau":level,"problemes":problems,"avertissements":warnings}
