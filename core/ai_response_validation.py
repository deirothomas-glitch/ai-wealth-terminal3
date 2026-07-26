"""Validation défensive pure des réponses structurées de l'IA."""
import json
FIELDS=("resume","contexte_marche","lecture_technique","lecture_actualites","scenario_favorable","scenario_defavorable","conditions_confirmation","conditions_invalidation","risques_principaux","points_a_surveiller","niveau_confiance","limites","decision_finale_utilisateur")
LISTS={"conditions_confirmation","conditions_invalidation","risques_principaux","points_a_surveiller","limites"}; CONF={"faible","moderee","elevee"}
FORBIDDEN=("achetez maintenant","vendez immédiatement","gain garanti","rendement certain","cette action va monter","aucune perte possible","opportunité sûre","signal infaillible")
def _fallback(reason):
    return {"resume":"Analyse IA indisponible.","contexte_marche":"","lecture_technique":"","lecture_actualites":"","scenario_favorable":"","scenario_defavorable":"","conditions_confirmation":[],"conditions_invalidation":[],"risques_principaux":[],"points_a_surveiller":[],"niveau_confiance":"faible","limites":[reason],"decision_finale_utilisateur":True}
def valider_reponse_ia(value):
    if isinstance(value,str):
        try:data=json.loads(value)
        except (json.JSONDecodeError,TypeError):return _fallback("Réponse IA invalide ou non structurée.")
    elif isinstance(value,dict):data=value
    else:return _fallback("Réponse IA vide ou invalide.")
    if not data:return _fallback("Réponse IA vide ou invalide.")
    result={}
    for field in FIELDS:
        raw=data.get(field)
        if field in LISTS: result[field]=[str(x).strip()[:500] for x in raw if isinstance(x,str) and x.strip()][:8] if isinstance(raw,list) else []
        elif field=="decision_finale_utilisateur":result[field]=True
        elif field=="niveau_confiance":result[field]=raw if raw in CONF else "faible"
        else:result[field]=raw.strip()[:2000] if isinstance(raw,str) else ""
    combined=" ".join(str(v) for v in result.values()).casefold()
    if any(x in combined for x in FORBIDDEN):return _fallback("La réponse IA contenait une formulation incompatible avec les règles de prudence.")
    if not result["resume"]:return _fallback("La réponse IA ne contient pas de résumé exploitable.")
    return result
