"""Client OpenAI centralisé, sans exposition des secrets."""
import os
from config import AI_DEFAULT_MODEL,AI_TIMEOUT

SYSTEM_INSTRUCTION="""Tu es un assistant prudent d'analyse de marché. Sépare les faits des interprétations, mentionne les données manquantes et le risque, présente des scénarios opposés et ne formule ni certitude, ni promesse de performance, ni ordre impératif. Réponds exclusivement avec le contrat JSON demandé. La décision finale appartient à l'utilisateur."""

def obtenir_cle_api(secrets=None,environ=None):
    env=environ if isinstance(environ,dict) else os.environ
    if secrets is not None:
        try:
            value=secrets.get("OPENAI_API_KEY")
            if isinstance(value,str) and value.strip():return value.strip()
        except Exception:pass
    value=env.get("OPENAI_API_KEY");return value.strip() if isinstance(value,str) and value.strip() else None

def appeler_modele(messages,api_key=None,client_factory=None,model=AI_DEFAULT_MODEL,timeout=AI_TIMEOUT):
    key=api_key or obtenir_cle_api()
    if not key:return {"ok":False,"contenu":None,"erreur":"Clé OpenAI absente. L’analyse déterministe reste disponible."}
    try:
        if client_factory is None:
            from openai import OpenAI
            client_factory=OpenAI
        client=client_factory(api_key=key,timeout=timeout)
        response=client.chat.completions.create(model=model,messages=messages,response_format={"type":"json_object"})
        content=response.choices[0].message.content
        if not isinstance(content,str) or not content.strip():return {"ok":False,"contenu":None,"erreur":"Réponse IA vide."}
        return {"ok":True,"contenu":content,"erreur":None}
    except Exception as error:
        name=type(error).__name__.casefold(); message="Limite de débit atteinte. Réessayez plus tard." if "rate" in name else "Service IA temporairement indisponible."
        return {"ok":False,"contenu":None,"erreur":message}
