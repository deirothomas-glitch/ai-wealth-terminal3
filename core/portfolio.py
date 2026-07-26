"""Logique métier pure du portefeuille long only."""
from __future__ import annotations
import math
from datetime import date
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union

ValeurValorisation = Union[float, str]
TYPES_ACTIFS = ("action", "ETF", "crypto", "autre")

def convertir_nombre_fini(v):
    """Convertit une valeur en float fini, ou retourne None sans exception."""
    if isinstance(v, bool): return None
    try: n=float(v)
    except (TypeError, ValueError): return None
    return n if math.isfinite(n) else None

def convertir_nombre_positif(v):
    """Convertit une valeur en float strictement positif, ou retourne None."""
    n=convertir_nombre_fini(v)
    return n if n is not None and n > 0 else None

def _positif(v):
    return convertir_nombre_positif(v)

def _seuil(v):
    return None if v in (None, "") else _positif(v)

def normaliser_position(position: Mapping[str, Any]) -> Dict[str, Any]:
    s=dict(position) if isinstance(position, Mapping) else {}
    typ=str(s.get("type_actif", "autre")).strip().lower()
    typ="ETF" if typ == "etf" else typ
    if typ not in TYPES_ACTIFS: typ="autre"
    prix_entree=_positif(s.get("prix_entree"))
    if prix_entree is None: prix_entree=_positif(s.get("prix_achat"))
    objectif=_seuil(s.get("objectif"))
    if objectif is None: objectif=_seuil(s.get("objectif_prix"))
    date_ouverture=s.get("date_ouverture")
    if date_ouverture in (None, ""): date_ouverture=s.get("date_ajout", date.today().isoformat())
    return {
      "identifiant": str(s.get("identifiant", "")).strip(),
      "symbole": str(s.get("symbole", "")).strip().upper(),
      "nom": str(s.get("nom", "")).strip(), "type_actif": typ,
      "quantite": _positif(s.get("quantite")),
      "prix_entree": prix_entree,
      "stop_loss": _seuil(s.get("stop_loss")),
      "objectif": objectif,
      "date_ouverture": str(date_ouverture or "").strip(),
      "notes": str(s.get("notes", s.get("notes_suivi", s.get("these_achat", "")))).strip(),
    }

def valider_position(position):
    p=normaliser_position(position); erreurs=[]
    if not p["symbole"]: erreurs.append("Le symbole est obligatoire.")
    if p["quantite"] is None: erreurs.append("La quantité doit être un nombre strictement positif.")
    if p["prix_entree"] is None: erreurs.append("Le prix d’entrée doit être un nombre strictement positif.")
    if position.get("stop_loss") not in (None, "", 0, 0.0) and p["stop_loss"] is None: erreurs.append("Le stop doit être un nombre strictement positif.")
    brut=position.get("objectif", position.get("objectif_prix"))
    if brut not in (None, "", 0, 0.0) and p["objectif"] is None: erreurs.append("L’objectif doit être un nombre strictement positif.")
    if not p["date_ouverture"]: erreurs.append("La date d’ouverture est obligatoire.")
    return erreurs

def calculer_montant_investi(position):
    p=normaliser_position(position)
    return None if p["quantite"] is None or p["prix_entree"] is None else p["quantite"]*p["prix_entree"]

def calculer_valeur_actuelle(position, prix_courant):
    p=normaliser_position(position); prix=_positif(prix_courant)
    return None if p["quantite"] is None or prix is None else p["quantite"]*prix

def calculer_gain_perte_non_realise(position, prix_courant):
    a=calculer_montant_investi(position); b=calculer_valeur_actuelle(position, prix_courant)
    return None if a is None or b is None else b-a

def calculer_performance_pourcentage(position, prix_courant):
    a=calculer_montant_investi(position); g=calculer_gain_perte_non_realise(position, prix_courant)
    return None if not a or g is None else g/a*100

def calculer_gain_perte_realise(position, prix_sortie):
    return calculer_gain_perte_non_realise(position, prix_sortie)

def resumer_position(position, prix_courant):
    p=normaliser_position(position); prix=_positif(prix_courant); investi=calculer_montant_investi(p)
    if p["quantite"] is None: statut="quantité indisponible"
    elif p["prix_entree"] is None: statut="prix d’entrée indisponible"
    elif prix is None: statut="prix indisponible"
    else: statut="valorisée"
    return {"identifiant":p["identifiant"],"symbole":p["symbole"],"quantite":p["quantite"],"prix_entree":p["prix_entree"],"prix_courant":prix,"montant_investi":investi,"valeur_actuelle":calculer_valeur_actuelle(p,prix),"gain_perte":calculer_gain_perte_non_realise(p,prix),"performance_pourcentage":calculer_performance_pourcentage(p,prix),"stop_loss":p["stop_loss"],"objectif":p["objectif"],"statut":statut}

def construire_resume_global(positions, prix_courants, journal=()):
    lignes=[resumer_position(p, prix_courants.get(normaliser_position(p)["symbole"])) for p in positions]
    sans=sum(x["prix_courant"] is None for x in lignes)
    capital=None if any(x["montant_investi"] is None for x in lignes) else sum(x["montant_investi"] for x in lignes)
    valeur=None if any(x["valeur_actuelle"] is None for x in lignes) else sum(x["valeur_actuelle"] for x in lignes)
    nr=None if valeur is None or capital is None else valeur-capital
    gains_realises=[convertir_nombre_fini(e.get("gain_perte_realise")) for e in journal if e.get("type_evenement")=="cloture"]
    realise=sum(x for x in gains_realises if x is not None)
    return {"nombre_positions":len(lignes),"capital_investi":capital,"valeur_actuelle":valeur,"gain_perte_non_realise":nr,"gain_perte_realise":realise,"performance_globale_pourcentage":None if nr is None or not capital else nr/capital*100,"positions_sans_prix":sans}

def construire_statistiques_journal(journal):
    gains=[float(e["gain_perte_realise"]) for e in journal if e.get("type_evenement")=="cloture" and isinstance(e.get("gain_perte_realise"),(int,float)) and math.isfinite(float(e["gain_perte_realise"]))]
    pos=[x for x in gains if x>0]; neg=[x for x in gains if x<0]
    return {"nombre_positions_cloturees":len(gains),"positions_gagnantes":len(pos),"positions_perdantes":len(neg),"taux_reussite":None if not gains else len(pos)/len(gains)*100,"gain_total_realise":sum(gains),"gain_moyen":None if not pos else sum(pos)/len(pos),"perte_moyenne":None if not neg else sum(neg)/len(neg),"meilleure_operation":None if not gains else max(gains),"pire_operation":None if not gains else min(gains)}

def calculer_score_diversification(nombre_positions: int) -> int:
    """Retourne le score historique de diversification sur 10."""
    if nombre_positions >= 10:
        return 10
    if nombre_positions >= 8:
        return 8
    if nombre_positions >= 5:
        return 6
    if nombre_positions >= 3:
        return 4
    return 2


def calculer_taille_position(
    prix_achat: float,
    stop_loss: float,
    capital_reference: float,
    risque_max_pct: float,
) -> Optional[float]:
    """Calcule la taille de position selon le comportement historique."""
    perte_par_unite = prix_achat - stop_loss
    if perte_par_unite <= 0 or capital_reference <= 0:
        return None

    return capital_reference * risque_max_pct / 100 / perte_par_unite


def calculer_valorisation_position(
    symbole: str,
    quantite: float,
    prix_achat: float,
    stop_loss: float,
    objectif_prix: float,
    prix_actuel: float,
    prix_precedent: float,
    capital_reference: float,
    risque_max_position: float,
) -> Dict[str, ValeurValorisation]:
    """Construit la ligne de valorisation avec les arrondis historiques."""
    valeur = prix_actuel * quantite
    cout_total = prix_achat * quantite
    gain = valeur - cout_total
    gain_pct = gain / cout_total * 100 if cout_total > 0 else 0.0
    variation_jour = (
        (prix_actuel - prix_precedent) / prix_precedent * 100
        if prix_precedent > 0
        else 0.0
    )
    risque_potentiel = (
        max(prix_achat - stop_loss, 0.0) * quantite
        if stop_loss > 0
        else 0.0
    )
    distance_stop = (
        (prix_achat - stop_loss) / prix_achat * 100
        if prix_achat > 0 and stop_loss > 0
        else 0.0
    )
    risque_capital = (
        risque_potentiel / capital_reference * 100
        if capital_reference > 0
        else 0.0
    )
    taille_suggeree = calculer_taille_position(
        prix_achat,
        stop_loss,
        capital_reference,
        risque_max_position,
    )

    return {
        "Actif": symbole,
        "Quantité": quantite,
        "Prix achat": round(prix_achat, 2),
        "Cours actuel": round(prix_actuel, 2),
        "Valeur": round(valeur, 2),
        "Gain (€)": round(gain, 2),
        "Gain (%)": round(gain_pct, 2),
        "Variation jour (%)": round(variation_jour, 2),
        "Stop-loss": round(stop_loss, 2),
        "Objectif prix": round(objectif_prix, 2),
        "Distance stop (%)": round(distance_stop, 2),
        "Risque potentiel (€)": round(risque_potentiel, 2),
        "Risque capital (%)": round(risque_capital, 2),
        "Taille suggérée": (
            round(taille_suggeree, 4) if taille_suggeree else "—"
        ),
    }


def calculer_allocation(valeur: float, valeur_totale: float) -> float:
    """Calcule l'allocation arrondie d'une ligne déjà valorisée."""
    if valeur_totale <= 0:
        return 0.0
    return round(valeur / valeur_totale * 100, 2)
