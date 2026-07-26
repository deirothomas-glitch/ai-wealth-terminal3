"""Opérations atomiques du portefeuille et alimentation du journal."""
from datetime import datetime,timezone
from uuid import uuid4
from core.portfolio import calculer_gain_perte_realise,convertir_nombre_positif,normaliser_position,valider_position
from storage import sauvegarder_journal,sauvegarder_portefeuille

def _maintenant(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _evenement(position,type_evenement,**extra):
    p=normaliser_position(position)
    return {"identifiant":str(uuid4()),"position_id":p["identifiant"],"type_evenement":type_evenement,"symbole":p["symbole"],"quantite":p["quantite"],"prix_entree":p["prix_entree"],"date_evenement":extra.pop("date_evenement",_maintenant()),"notes":extra.pop("notes",p["notes"]),**extra}
def ajouter_position(positions,journal,position):
    erreurs=valider_position(position)
    if erreurs: raise ValueError(" ".join(erreurs))
    p=normaliser_position(position); p["identifiant"]=p["identifiant"] or str(uuid4())
    nouvelles=[*positions,p]; nouveau_journal=[*journal,_evenement(p,"ouverture")]; sauvegarder_portefeuille(nouvelles); sauvegarder_journal(nouveau_journal); return nouvelles,nouveau_journal
def modifier_position(positions,journal,position_id,changements):
    nouvelles=[]; modifie=None
    for original in positions:
        if original.get("identifiant")==position_id:
            candidat={**normaliser_position(original),**changements,"identifiant":position_id}; erreurs=valider_position(candidat)
            if erreurs: raise ValueError(" ".join(erreurs))
            modifie=normaliser_position(candidat); nouvelles.append(modifie)
        else: nouvelles.append(dict(original))
    if modifie is None: raise KeyError("Position introuvable.")
    j=[*journal,_evenement(modifie,"modification")]; sauvegarder_portefeuille(nouvelles); sauvegarder_journal(j); return nouvelles,j
def supprimer_position(positions,journal,position_id):
    cible=next((p for p in positions if p.get("identifiant")==position_id),None)
    if cible is None: raise KeyError("Position introuvable.")
    nouvelles=[dict(p) for p in positions if p.get("identifiant")!=position_id]; j=[*journal,_evenement(cible,"suppression")]; sauvegarder_portefeuille(nouvelles); sauvegarder_journal(j); return nouvelles,j
def cloturer_position(positions,journal,position_id,prix_sortie,date_sortie,notes=""):
    cible=next((p for p in positions if p.get("identifiant")==position_id),None)
    if cible is None: raise KeyError("Position introuvable.")
    p=normaliser_position(cible)
    if p["quantite"] is None: raise ValueError("Renseignez une quantité valide avant de clôturer cette position.")
    if p["prix_entree"] is None: raise ValueError("Renseignez un prix d’entrée valide avant de clôturer cette position.")
    sortie=convertir_nombre_positif(prix_sortie)
    if sortie is None: raise ValueError("Le prix de sortie doit être strictement positif.")
    gain=calculer_gain_perte_realise(p,sortie); perf=gain/(p["quantite"]*p["prix_entree"])*100
    j=[*journal,_evenement(p,"cloture",prix_sortie=sortie,gain_perte_realise=gain,performance_pourcentage=perf,date_evenement=str(date_sortie),notes=str(notes).strip())]
    nouvelles=[dict(x) for x in positions if x.get("identifiant")!=position_id]; sauvegarder_portefeuille(nouvelles); sauvegarder_journal(j); return nouvelles,j
