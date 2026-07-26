"""Orchestration tolérante aux pannes du pipeline d'actualités."""
from core.news_deduplication import dedupliquer_actualites
from core.news_normalization import normaliser_actualite
from core.news_quality import evaluer_qualite_actualite
from core.news_relevance import evaluer_pertinence_actualite
from core.news_sentiment import analyser_sentiment_actualite

def agreger_actualites(sources,symbole,nom_actif="",categorie="",mots_cles=None,limite=10,date_reference=None):
    normalisees=[]; erreurs=[]
    for source in sources if isinstance(sources,(list,tuple)) else []:
        try:
            for article in source.fetch(symbole,limite): normalisees.append(normaliser_actualite(article,symbole))
        except Exception:
            erreurs.append(f"Source temporairement indisponible : {getattr(source,'nom','source inconnue')}.")
    uniques=dedupliquer_actualites(normalisees); resultat=[]
    for article in uniques:
        enrichi=dict(article); enrichi["qualite"]=evaluer_qualite_actualite(article,date_reference); enrichi["pertinence"]=evaluer_pertinence_actualite(article,symbole,nom_actif,categorie,mots_cles); enrichi["sentiment"]=analyser_sentiment_actualite(article); resultat.append(enrichi)
    resultat.sort(key=lambda x:(-x["pertinence"]["score_pertinence"],str(x.get("date_publication") or ""),x["identifiant"]),reverse=False)
    resultat.sort(key=lambda x:x["pertinence"]["score_pertinence"],reverse=True)
    return resultat[:max(0,int(limite))],erreurs
