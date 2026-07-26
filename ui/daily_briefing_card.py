"""Présentation Streamlit du briefing déterministe."""
import streamlit as st
def afficher_briefing(briefing):
    d=briefing if isinstance(briefing,dict) else {};st.subheader("🧭 Briefing du marché");st.caption(f"Généré le {d.get('date_generation','date indisponible')} · sans appel IA automatique")
    for text in d.get("resume_marche",[])[:6] if isinstance(d.get("resume_marche"),list) else []:st.write(f"• {text}")
    if d.get("opportunites_a_surveiller"):st.markdown("**Opportunités à surveiller**");[st.write(f"• {x.get('symbole','—')} · {x.get('decision','—')}") for x in d["opportunites_a_surveiller"][:5] if isinstance(x,dict)]
    if d.get("risques_du_jour"):st.markdown("**Risques du jour**");[st.warning(x) for x in d["risques_du_jour"][:5] if isinstance(x,str)]
    if d.get("donnees_manquantes"):st.caption("Données manquantes : "+", ".join(d["donnees_manquantes"]))
