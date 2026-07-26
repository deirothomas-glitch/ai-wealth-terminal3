"""Affichage de la qualité des données déjà évaluée."""
def afficher_qualite_donnees(st,qualite):
    st.subheader("Qualité des données"); st.metric("Niveau",f"{qualite.get('niveau','insuffisant')} — {qualite.get('score_qualite',0):.0f}/100");
    for texte in qualite.get("problemes",[]): st.error(texte)
    for texte in qualite.get("avertissements",[]): st.warning(texte)
