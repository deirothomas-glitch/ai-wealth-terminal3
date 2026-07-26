"""Affichage d'un résultat de stratégie déjà calculé."""
def afficher_carte_strategie(st,resultat):
    score="—" if resultat.get("score_strategie") is None else f"{resultat['score_strategie']:.1f}/100"; st.subheader(f"Signal {resultat.get('strategie_nom','')}"); c=st.columns(3); c[0].metric("Score stratégie",score); c[1].metric("Signal",resultat.get("signal","indisponible")); c[2].metric("Confiance",resultat.get("confiance","faible")); st.caption(resultat.get("contexte",""));
    if resultat.get("forces"): st.markdown("**Forces :** "+" · ".join(resultat["forces"][:3]))
    if resultat.get("faiblesses"): st.markdown("**Fragilités :** "+" · ".join(resultat["faiblesses"][:3]))
