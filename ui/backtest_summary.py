"""Affichage des statistiques d'un backtest calculé."""
def _v(v,s=""): return "—" if v is None else f"{v:.2f}{s}"
def afficher_resume_backtest(st,r):
    c=st.columns(4); c[0].metric("Performance totale",_v(r.get("performance_pourcentage")," %")); c[1].metric("Drawdown maximal",_v(r.get("drawdown_maximum_pourcentage")," %")); c[2].metric("Profit factor",_v(r.get("profit_factor"))); c[3].metric("Opérations",str(r.get("nombre_operations",0))); c=st.columns(3); c[0].metric("Capital final",_v(r.get("capital_final")," €")); c[1].metric("Taux de réussite",_v(r.get("taux_reussite")," %")); c[2].metric("Résultat moyen gagnant",_v(r.get("gain_moyen")," €"))
