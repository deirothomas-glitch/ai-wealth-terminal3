"""Alertes déterministes liées aux seuils enregistrés."""
import math
from core.portfolio import normaliser_position
MARGE_PROXIMITE_STOP=0.03

def _prix(v):
    try: n=float(v)
    except (TypeError,ValueError): return None
    return n if math.isfinite(n) and n>0 else None

def construire_alertes_position(position, prix_courant):
    p=normaliser_position(position)
    if not p["identifiant"] or not p["symbole"]: return []
    def a(suffixe,niveau,categorie,titre,message,action): return {"identifiant":f"{p['identifiant']}:{suffixe}","position_id":p["identifiant"],"symbole":p["symbole"],"niveau":niveau,"categorie":categorie,"titre":titre,"message":message,"action_suggeree":action,"decision_finale_utilisateur":True}
    prix=_prix(prix_courant)
    if prix is None: return [a("prix-indisponible","vigilance","donnees","Prix indisponible",f"Aucun prix courant fiable n’est disponible pour {p['symbole']}.","Rafraîchir les prix ou vérifier le symbole avant d’interpréter la performance.")]
    r=[]; stop=p["stop_loss"]; objectif=p["objectif"]
    if stop is None: r.append(a("stop-absent","vigilance","risque","Aucun stop enregistré",f"La position {p['symbole']} ne possède pas de seuil de protection.","Évaluer si un seuil de protection correspond à votre stratégie."))
    elif prix<=stop: r.append(a("stop-atteint","attention","stop","Seuil de stop atteint",f"Le prix courant a atteint ou dépassé à la baisse le seuil défini à {stop:.2f}.","Réexaminer la position et décider personnellement de la suite."))
    elif (prix-stop)/prix<=MARGE_PROXIMITE_STOP: r.append(a("stop-proche","vigilance","stop","Prix proche du stop",f"Le prix se situe à moins de 3 % du seuil enregistré à {stop:.2f}.","Surveiller l’évolution et réexaminer le niveau de risque."))
    if stop is not None and p["prix_entree"] and stop>=p["prix_entree"]: r.append(a("stop-remonte","information","risque","Stop au-dessus du prix d’entrée","Le seuil enregistré peut correspondre à un stop remonté.","Vérifier que ce seuil reflète toujours votre stratégie."))
    if objectif is not None and prix>=objectif: r.append(a("objectif-atteint","information","objectif","Objectif atteint",f"Le prix courant a atteint l’objectif enregistré à {objectif:.2f}.","Réévaluer la position selon votre stratégie et votre horizon."))
    return r

def generer_alertes_positions(positions, prix_courants):
    r=[]
    for p in positions:
        n=normaliser_position(p); r.extend(construire_alertes_position(p,prix_courants.get(n["symbole"])))
    return r
