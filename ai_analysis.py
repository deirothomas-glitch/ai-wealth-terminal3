from openai import OpenAI
import streamlit as st

# Création du client OpenAI
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)


def analyse_marche(ticker, prix):
    prompt = f"""
Tu es un analyste financier professionnel.

Analyse l'actif : {ticker}

Prix actuel : {prix}

Réponds exactement sous ce format :

## Score IA
Donne une note sur 100.

## Tendance
Haussière, Baissière ou Neutre.

## Analyse
Explique pourquoi en quelques phrases.

## Points forts
- ...

## Risques
- ...

## Conclusion
Termine par UNE recommandation parmi :
Acheter
Conserver
Attendre
Vendre

Important :
Ce n'est pas un conseil financier mais une analyse basée sur les informations fournies.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Tu es un analyste financier expérimenté."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=700
    )

    return response.choices[0].message.content
