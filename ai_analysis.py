import streamlit as st
from openai import OpenAI
from news import recuperer_actualites

# ==========================================
# Client OpenAI
# ==========================================

def get_client():

    api_key = st.secrets.get("OPENAI_API_KEY")
    st.write("Clé trouvée :", api_key is not None)
    st.write("Longueur :", len(api_key) if api_key else 0)

    if not api_key:
        st.error("Clé API OpenAI introuvable.")
        return None

    return OpenAI(api_key=api_key)


# ==========================================
# Analyse IA
# ==========================================

def analyser_actif(
    nom,
    symbole,
    prix,
    score,
    rsi,
    tendance
):

    client = get_client()

    if client is None:
        return "❌ Clé API OpenAI introuvable."
    
    actualites = recuperer_actualites(symbole)

    texte_actualites = ""

    for article in actualites:
        texte_actualites += (
            f"- {article['titre']} "
            f"({article['source']})\n"
        )

    prompt = f"""
Tu es un analyste financier professionnel.

Dernières actualités :

{texte_actualites}

Tiens compte de ces actualités dans ton analyse.
Explique leur impact potentiel sur le cours.

Analyse cet actif :

Nom : {nom}
Symbole : {symbole}

Prix : {prix}

Score technique : {score}/100

RSI : {rsi}

Tendance : {tendance}

Explique :

1. Les points forts.
2. Les risques.
3. Le contexte actuel.

Puis ajoute une section appelée :

===== SIGNAL IA =====

Décision :
- ACHAT FORT
- ACHAT
- SURVEILLER
- CONSERVER
- VENTE
- VENTE FORTE

Confiance : xx %

Horizon conseillé :
- Court terme
- Moyen terme
- Long terme

Prix d'entrée idéal (si pertinent)

Objectif 1

Objectif 2

Stop-loss conseillé

Ratio risque/rendement

Catalyseurs à surveiller

Conclusion finale en une phrase.

Réponds en français avec une mise en forme claire en Markdown.

    """

    try:
        reponse = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
    
        return reponse.choices[0].message.content
    
    except Exception as e:
        st.error(f"Erreur lors de l'analyse par l'IA : {e}")
        return None