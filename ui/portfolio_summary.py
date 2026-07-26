"""Affichage du contrat de résumé global."""
def _argent(v): return "Indisponible" if v is None else f"{v:,.2f} €".replace(","," ")
def afficher_resume_portefeuille(st,resume):
    cols=st.columns(5)
    cols[0].metric("Capital investi",_argent(resume["capital_investi"]))
    cols[1].metric("Valeur actuelle",_argent(resume["valeur_actuelle"]))
    cols[2].metric("Gain/perte non réalisé",_argent(resume["gain_perte_non_realise"]))
    cols[3].metric("Gain/perte réalisé",_argent(resume["gain_perte_realise"]))
    cols[4].metric("Positions",str(resume["nombre_positions"]))
