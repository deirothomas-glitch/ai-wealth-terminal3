from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def analyse_marche(ticker, prix):
    prompt = f"""
Tu es un analyste financier professionnel.

Analyse l'action ou le crypto-actif {ticker}.

Prix actuel : {prix}

Donne :
- La tendance
- Les points forts
- Les risques
- Une conclusion en quelques phrases.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
