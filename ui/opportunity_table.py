"""Tableau d'opportunités sans calcul métier."""
import pandas as pd
def afficher_table_opportunites(st,opportunites):
    lignes=[]
    for x in opportunites: lignes.append({"Rang":x.get("rang"),"Symbole":x.get("symbole"),"Stratégie":x.get("strategie"),"Score global":"—" if x.get("score_global") is None else x.get("score_global"),"Confiance":x.get("confiance"),"Décision":x.get("decision"),"Qualité":x.get("qualite_donnees"),"Raison principale":next(iter(x.get("raisons_principales",[])),"—"),"Vigilance":next(iter(x.get("points_vigilance",[])),"—")})
    st.dataframe(pd.DataFrame(lignes),use_container_width=True,hide_index=True)
