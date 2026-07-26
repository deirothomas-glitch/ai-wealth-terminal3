"""Affichage des statistiques du journal."""
def _v(v,suffixe=" €"): return "—" if v is None else f"{v:.2f}{suffixe}"
def afficher_statistiques_portefeuille(st,stats):
    c=st.columns(4); c[0].metric("Positions clôturées",stats["nombre_positions_cloturees"]); c[1].metric("Taux de réussite",_v(stats["taux_reussite"]," %")); c[2].metric("Gain réalisé total",_v(stats["gain_total_realise"])); c[3].metric("Meilleure opération",_v(stats["meilleure_operation"]))
