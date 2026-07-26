"""Interprétation pure d'un score selon un profil de stratégie."""
import math
def _score(v): return float(v) if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and 0<=v<=100 else None
def evaluer_strategie(indicateurs,score_existant,decision,profil,qualite):
    i=dict(indicateurs) if isinstance(indicateurs,dict) else {}; s=dict(score_existant) if isinstance(score_existant,dict) else {}; d=dict(decision) if isinstance(decision,dict) else {}; p=dict(profil) if isinstance(profil,dict) else {}; q=dict(qualite) if isinstance(qualite,dict) else {}
    technique=_score(s.get("score")); forces=[]; faiblesses=[]
    for entree in s.get("ventilation",[]) if isinstance(s.get("ventilation"),list) else []:
        if not isinstance(entree,dict): continue
        c=entree.get("contribution"); raison=entree.get("raison")
        if isinstance(c,(int,float)) and isinstance(raison,str): (forces if c>0 else faiblesses if c<0 else []).append(raison)
    qualite_valide=q.get("valide") is True; score_q=_score(q.get("score_qualite")) or 0
    if technique is None or not p.get("identifiant") or not qualite_valide: strategie=None
    else:
        bonus=5 if d.get("recommandation")=="Surveiller" else (-10 if d.get("recommandation")=="Éviter" else 0)
        strategie=max(0.0,min(100.0,technique*0.8+score_q*0.2+bonus))
    if strategie is None: signal="indisponible"
    elif strategie>=float(p.get("seuil_score_favorable",75)): signal="favorable"
    elif strategie>=float(p.get("seuil_score_surveillance",60)): signal="a_confirmer"
    elif strategie>=45: signal="neutre"
    else: signal="fragile"
    if strategie is None or score_q<60: confiance="faible"
    elif score_q>=85 and len(forces)>=2 and len(faiblesses)<=1: confiance="elevee"
    else: confiance="moderee"
    confirmations=["Attendre la confirmation du signal sur une nouvelle clôture.","Vérifier que le volume et le momentum restent cohérents."]
    invalidations=["Réévaluer si la tendance technique se retourne.","Réévaluer si la qualité des données devient insuffisante."]
    contexte=f"Profil {p.get('nom','indisponible')} — {p.get('horizon','horizon non défini')}."
    return {"strategie_id":str(p.get("identifiant","")),"strategie_nom":str(p.get("nom","")),"score_strategie":strategie,"confiance":confiance,"contexte":contexte,"signal":signal,"forces":forces,"faiblesses":faiblesses,"conditions_confirmation":confirmations,"conditions_invalidation":invalidations,"donnees_valides":qualite_valide,"decision_finale_utilisateur":True}
