"""Tableau professionnel d'opportunités, sans calcul métier."""

import pandas as pd


def _libelle_risque(opportunite):
    return "Disponible" if opportunite.get("plan_risque_disponible") else "À compléter"


def afficher_table_opportunites(st, opportunites):
    lignes = []
    for opportunite in opportunites:
        lignes.append({
            "Rang": opportunite.get("rang"),
            "Symbole": opportunite.get("symbole"),
            "Stratégie": opportunite.get("strategie"),
            "Score global": "—" if opportunite.get("score_global") is None else opportunite.get("score_global"),
            "Confiance": opportunite.get("confiance"),
            "Décision": opportunite.get("decision"),
            "Risque": _libelle_risque(opportunite),
            "Volatilité": opportunite.get("volatilite", "Non calculée"),
            "Qualité": opportunite.get("qualite_donnees"),
            "Raison principale": next(iter(opportunite.get("raisons_principales", [])), "—"),
            "Vigilance": next(iter(opportunite.get("points_vigilance", [])), "—"),
        })
    dataframe = pd.DataFrame(lignes)
    configuration = {}
    if hasattr(st, "column_config"):
        configuration = {
            "Rang": st.column_config.NumberColumn(width="small"),
            "Score global": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
            "Raison principale": st.column_config.TextColumn(width="large"),
            "Vigilance": st.column_config.TextColumn(width="large"),
        }
    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
        column_config=configuration,
    )
