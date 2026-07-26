"""Chargement isolé d’un prix par symbole unique."""
from core.portfolio import convertir_nombre_positif
def charger_prix_portefeuille(positions, charger_historique, extraire_prix):
    symboles=[]
    for p in positions:
        s=str(p.get("symbole","")).strip().upper()
        if s and s not in symboles: symboles.append(s)
    prix={}; erreurs=[]
    for symbole in symboles:
        try:
            historique=charger_historique(symbole)
            if historique is None or getattr(historique,"empty",False): raise ValueError("aucune donnée disponible")
            prix[symbole]=convertir_nombre_positif(extraire_prix(historique))
            if prix[symbole] is None: erreurs.append(f"Prix indisponible pour {symbole}.")
        except Exception as e:
            prix[symbole]=None; erreurs.append(f"Prix indisponible pour {symbole} : {e}")
    return prix, erreurs
