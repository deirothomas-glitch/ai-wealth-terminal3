"""Profils centralisés des stratégies disponibles."""
from copy import deepcopy
_PROFILES=(
 {"identifiant":"court_terme","nom":"Court terme","description":"Recherche des impulsions récentes confirmées par le momentum et le volume.","horizon":"Quelques séances","periode_donnees":"6mo","intervalle":"1d","seuil_score_surveillance":60.0,"seuil_score_favorable":75.0,"poids":{"technique":0.45,"momentum":0.35,"volume":0.20},"regles":{"historique_minimum":40,"rsi_min":45,"rsi_max":68}},
 {"identifiant":"swing","nom":"Swing","description":"Recherche des mouvements de plusieurs jours avec tendance et momentum cohérents.","horizon":"Une à plusieurs semaines","periode_donnees":"1y","intervalle":"1d","seuil_score_surveillance":58.0,"seuil_score_favorable":72.0,"poids":{"technique":0.50,"momentum":0.25,"volume":0.10,"tendance":0.15},"regles":{"historique_minimum":80,"rsi_min":40,"rsi_max":70}},
 {"identifiant":"tendance","nom":"Tendance","description":"Privilégie la persistance de la tendance et filtre davantage les mouvements courts.","horizon":"Plusieurs semaines à plusieurs mois","periode_donnees":"2y","intervalle":"1d","seuil_score_surveillance":55.0,"seuil_score_favorable":70.0,"poids":{"technique":0.40,"tendance":0.40,"momentum":0.10,"volume":0.10},"regles":{"historique_minimum":150,"rsi_min":38,"rsi_max":72}},
)
def obtenir_profils(): return deepcopy(list(_PROFILES))
def obtenir_profil(identifiant):
    return next((p for p in obtenir_profils() if p["identifiant"]==identifiant),None)
