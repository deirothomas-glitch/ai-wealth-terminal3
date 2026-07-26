"""Évaluation pure de la qualité de données déjà résumées."""
import math
from datetime import date,datetime,timezone
def _fini(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def evaluer_qualite_donnees(informations):
    d=dict(informations) if isinstance(informations,dict) else {}; problemes=[]; avert=[]; score=100.0
    n=d.get("nombre_points",0)
    if not isinstance(n,int) or n<1: problemes.append("Historique absent."); score-=60
    elif n<int(d.get("minimum_requis",40) or 40): problemes.append("Historique trop court."); score-=35
    prix=d.get("prix")
    if not _fini(prix) or prix<=0: problemes.append("Prix non positif ou invalide."); score-=45
    manquantes=d.get("valeurs_manquantes",0)
    if not isinstance(manquantes,int) or manquantes<0: manquantes=1
    if manquantes: problemes.append("Valeurs manquantes détectées."); score-=min(30,5+manquantes)
    if not d.get("volume_disponible",False): avert.append("Volume absent."); score-=10
    if not d.get("volatilite_disponible",False): avert.append("Volatilité non calculable."); score-=15
    essentiels=d.get("indicateurs_essentiels",{})
    if not isinstance(essentiels,dict) or not essentiels or not all(essentiels.values()): problemes.append("Indicateurs essentiels absents."); score-=25
    if d.get("donnees_incoherentes",False): problemes.append("Données incohérentes."); score-=40
    age=d.get("age_jours")
    if _fini(age) and age>7: avert.append("Données anciennes."); score-=15
    score=max(0.0,min(100.0,score)); critique=any(x in problemes for x in ("Historique absent.","Prix non positif ou invalide.","Données incohérentes.")); niveau="insuffisant" if critique or score<45 else ("bon" if score>=80 and not problemes else "partiel")
    return {"valide":niveau!="insuffisant","niveau":niveau,"score_qualite":score,"problemes":problemes,"avertissements":avert}


def evaluer_qualite_globale(sources):
    """Évalue des jeux de données déjà observés, sans supposer leur contenu.

    Chaque entrée accepte ``disponible``, ``complet`` et, uniquement lorsque
    cette information est connue, ``ancien``. Aucun âge n'est déduit ici.
    """
    from collections.abc import Mapping
    import json

    donnees = sources if isinstance(sources, Mapping) else {}
    details = []
    for nom, brut in donnees.items():
        if not isinstance(nom, str) or not nom.strip():
            continue
        info = brut if isinstance(brut, Mapping) else {}
        disponible = info.get("disponible")
        complet = info.get("complet")
        ancien = info.get("ancien")
        if disponible is not True:
            statut = "Absentes"
            justification = "Aucune donnée disponible n’a été confirmée."
        elif ancien is True:
            statut = "Anciennes"
            justification = "La date disponible indique que les données sont anciennes."
        elif complet is True:
            statut = "Complètes"
            justification = "Les champs attendus déclarés sont disponibles."
        else:
            statut = "Partielles"
            justification = "Une partie seulement des champs attendus est disponible."
        details.append({
            "source": nom.strip(),
            "statut": statut,
            "justification": justification,
        })

    statuts = [x["statut"] for x in details]
    if details and all(x == "Complètes" for x in statuts):
        niveau = "Bonne"
        justification = "Tous les jeux de données évalués sont complets."
    elif not details or all(x == "Absentes" for x in statuts):
        niveau = "Faible"
        justification = "Aucun jeu de données exploitable n’est disponible."
    elif statuts.count("Absentes") > len(statuts) / 2:
        niveau = "Faible"
        justification = "La majorité des jeux de données attendus est absente."
    else:
        niveau = "Moyenne"
        justification = "L’analyse repose sur des données partielles, anciennes ou inégalement disponibles."
    resultat = {"niveau": niveau, "justification": justification, "details": details}
    json.dumps(resultat, ensure_ascii=False, allow_nan=False)
    return resultat


def construire_etat_sources(*, yahoo_interroge=False, yahoo_disponible=None, openai_configure=None, stockage_charge=None):
    """Décrit uniquement les états effectivement connus des fournisseurs."""
    import json

    if yahoo_interroge is not True:
        yahoo = {"etat": "Non vérifié", "detail": "Yahoo Finance n’a pas été interrogé dans ce contexte."}
    elif yahoo_disponible is True:
        yahoo = {"etat": "Données reçues", "detail": "Yahoo Finance a retourné des données exploitables."}
    else:
        yahoo = {"etat": "Indisponible", "detail": "Aucune donnée Yahoo Finance exploitable n’a été reçue."}
    if openai_configure is True:
        openai = {"etat": "Configuré", "detail": "Une configuration OpenAI est présente ; aucune connexion n’est déduite."}
    elif openai_configure is False:
        openai = {"etat": "Non configuré", "detail": "Aucune configuration OpenAI n’est disponible."}
    else:
        openai = {"etat": "Non vérifié", "detail": "La configuration OpenAI n’a pas été vérifiée."}
    if stockage_charge is True:
        stockage = {"etat": "Chargé", "detail": "Les données locales sont présentes dans la session."}
    elif stockage_charge is False:
        stockage = {"etat": "Non chargé", "detail": "Les données locales ne sont pas présentes dans la session."}
    else:
        stockage = {"etat": "Non vérifié", "detail": "L’état du stockage local n’a pas été vérifié."}
    resultat = {"Yahoo Finance": yahoo, "OpenAI": openai, "Stockage local": stockage}
    json.dumps(resultat, ensure_ascii=False, allow_nan=False)
    return resultat
