"""Backtest long only, sans anticipation : signal J, exécution ouverture J+1."""
import math
from copy import deepcopy
def _positif(v):
    try: n=float(v)
    except (TypeError,ValueError): return None
    return n if math.isfinite(n) and n>0 else None
def _resultat(strategie,symbole,capital,avertissements):
    return {"strategie":str(strategie),"symbole":str(symbole),"capital_initial":capital,"capital_final":capital,"performance_pourcentage":0.0,"nombre_operations":0,"operations_gagnantes":0,"operations_perdantes":0,"taux_reussite":None,"gain_moyen":None,"perte_moyenne":None,"profit_factor":None,"drawdown_maximum_pourcentage":None,"meilleure_operation":None,"pire_operation":None,"courbe_capital":[],"operations":[],"avertissements":avertissements}
def executer_backtest(historique,strategie,symbole,capital_initial=10000.0,taille_position_pct=100.0,frais_pct=0.0,slippage_pct=0.0):
    capital=_positif(capital_initial); taille=_positif(taille_position_pct); frais=float(frais_pct) if isinstance(frais_pct,(int,float)) else -1; slip=float(slippage_pct) if isinstance(slippage_pct,(int,float)) else -1
    if capital is None or taille is None or taille>100 or frais<0 or slip<0 or not math.isfinite(frais+slip): return _resultat(strategie,symbole,capital or 0.0,["Paramètres de backtest invalides."])
    rows=deepcopy(historique) if isinstance(historique,list) else []
    if len(rows)<2: return _resultat(strategie,symbole,capital,["Historique vide ou trop court."])
    cash=capital; position=None; ops=[]; curve=[]; peak=capital; max_dd=0.0; entree_pending=False; sortie_pending=False
    for idx,row in enumerate(rows):
        if not isinstance(row,dict): continue
        o=_positif(row.get("open")); h=_positif(row.get("high")); l=_positif(row.get("low")); c=_positif(row.get("close")); dt=str(row.get("date",idx))
        if None in (o,h,l,c) or not (l<=min(o,c)<=max(o,c)<=h): continue
        if position and sortie_pending:
            prix=o*(1-slip/100); raison="signal_invalidation"; sortie_pending=False
            position,cash=_fermer(position,prix,dt,raison,cash,frais,ops)
        if not position and entree_pending:
            prix=o*(1+slip/100); budget=cash*taille/100; cout_frais=budget*frais/100; quantite=(budget-cout_frais)/prix
            if quantite>0: position={"date_entree":dt,"prix_entree":prix,"quantite":quantite,"frais_entree":cout_frais,"capital_avant":cash,"stop":_positif(row.get("stop")),"objectif":_positif(row.get("objectif"))}; cash-=quantite*prix+cout_frais
            entree_pending=False
        if position:
            raison=prix_sortie=None; stop=position.get("stop"); objectif=position.get("objectif")
            if stop and l<=stop: raison,prix_sortie="stop",stop*(1-slip/100)
            elif objectif and h>=objectif: raison,prix_sortie="objectif",objectif*(1-slip/100)
            if prix_sortie: position,cash=_fermer(position,prix_sortie,dt,raison,cash,frais,ops)
        valeur=cash+(position["quantite"]*c if position else 0); peak=max(peak,valeur); max_dd=max(max_dd,(peak-valeur)/peak*100 if peak else 0); curve.append({"date":dt,"capital":valeur})
        if position and row.get("signal_sortie") is True: sortie_pending=True
        elif not position and row.get("signal_entree") is True: entree_pending=True
    if position:
        last=next((r for r in reversed(rows) if _positif(r.get("close"))),None); position,cash=_fermer(position,float(last["close"])*(1-slip/100),str(last.get("date",len(rows)-1)),"fin_historique",cash,frais,ops); curve[-1]["capital"]=cash
    gains=[o["resultat"] for o in ops]; pos=[g for g in gains if g>0]; neg=[g for g in gains if g<0]; gross_pos=sum(pos); gross_neg=abs(sum(neg)); final=cash
    r=_resultat(strategie,symbole,capital,[] if ops else ["Aucune opération déclenchée."]); r.update({"capital_final":final,"performance_pourcentage":(final-capital)/capital*100,"nombre_operations":len(ops),"operations_gagnantes":len(pos),"operations_perdantes":len(neg),"taux_reussite":None if not ops else len(pos)/len(ops)*100,"gain_moyen":None if not pos else sum(pos)/len(pos),"perte_moyenne":None if not neg else sum(neg)/len(neg),"profit_factor":None if not ops or gross_neg==0 else gross_pos/gross_neg,"drawdown_maximum_pourcentage":max_dd if curve else None,"meilleure_operation":None if not gains else max(gains),"pire_operation":None if not gains else min(gains),"courbe_capital":curve,"operations":ops}); return r
def _fermer(p,prix,date_sortie,raison,cash,frais_pct,ops):
    brut=p["quantite"]*prix; frais_sortie=brut*frais_pct/100; cash+=brut-frais_sortie; investi=p["quantite"]*p["prix_entree"]+p["frais_entree"]; resultat=brut-frais_sortie-investi
    ops.append({"date_entree":p["date_entree"],"prix_entree":p["prix_entree"],"date_sortie":date_sortie,"prix_sortie":prix,"raison_sortie":raison,"resultat":resultat,"performance_pourcentage":resultat/investi*100 if investi else 0.0,"frais":p["frais_entree"]+frais_sortie}); return None,cash
