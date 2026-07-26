"""Construction des requêtes d'analyse IA et validation de leur réponse."""
import json
from core.ai_response_validation import valider_reponse_ia
from services.ai_client import SYSTEM_INSTRUCTION,appeler_modele

def analyser_contexte_marche(contexte,question=None,api_key=None,client_factory=None):
    question_texte=str(question or "Produis une analyse complète.").strip()[:1000]
    payload=json.dumps(contexte,ensure_ascii=False,allow_nan=False,separators=(",",":"))
    messages=[{"role":"system","content":SYSTEM_INSTRUCTION},{"role":"user","content":f"Contexte structuré : {payload}\nQuestion : {question_texte}"}]
    response=appeler_modele(messages,api_key=api_key,client_factory=client_factory)
    if not response["ok"]:
        safe=valider_reponse_ia(None);safe["limites"]=[response["erreur"]];return safe
    return valider_reponse_ia(response["contenu"])
