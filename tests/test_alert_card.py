"""Tests du composant Streamlit des alertes."""
import copy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from ui.alert_card import AUCUNE_ALERTE, RAPPEL_DECISION, TITRE, afficher_alertes

class _St:
    def __init__(self): self.appels=[]
    def subheader(self, x): self.appels.append(("subheader",x))
    def caption(self, x): self.appels.append(("caption",x))
    def info(self, x): self.appels.append(("info",x))
    def warning(self, x): self.appels.append(("warning",x))
    def error(self, x): self.appels.append(("error",x))
    def write(self, x): self.appels.append(("write",x))
def alerte(niveau="information", categorie="decision", titre="Titre"):
    return {"identifiant":"id", "niveau":niveau, "categorie":categorie, "titre":titre, "message":"Message prudent.", "facteurs":["Un","Deux","Trois","Quatre"], "action_suggeree":"Vérifier.", "decision_finale_utilisateur":True}
class AlertCardTests(unittest.TestCase):
    def afficher(self, valeur):
        st=_St()
        with patch("ui.alert_card.st", st): afficher_alertes(valeur)
        return st.appels
    def test_titre_et_liste_vide(self):
        self.assertEqual(self.afficher([]), [("subheader",TITRE),("caption",AUCUNE_ALERTE)])
    def test_information_vigilance_attention(self):
        self.assertTrue(any(a[0]=="info" for a in self.afficher([alerte("information")])))
        self.assertTrue(any(a[0]=="warning" for a in self.afficher([alerte("vigilance")])))
        self.assertTrue(any(a[0]=="error" for a in self.afficher([alerte("attention","donnees")])))
        self.assertTrue(any(a[0]=="warning" for a in self.afficher([alerte("attention","decision")])))
    def test_ordre_action_facteurs_et_rappel(self):
        appels=self.afficher([alerte(titre="Premier"), alerte(titre="Second")])
        self.assertLess(str(appels).index("Premier"),str(appels).index("Second"))
        self.assertEqual(sum(a[0]=="write" for a in appels),6)
        self.assertIn(("caption","Action suggérée : Vérifier."),appels)
        self.assertIn(("caption",RAPPEL_DECISION),appels)
    def test_invalide_sans_exception(self):
        self.assertIn(("caption",AUCUNE_ALERTE),self.afficher([None,{},"x"]))
        self.assertIn(("caption",AUCUNE_ALERTE),self.afficher(None))
    def test_non_mutation(self):
        valeur=[alerte()]; copie=copy.deepcopy(valeur); self.afficher(valeur); self.assertEqual(valeur,copie)
    def test_aucune_promesse_ou_ordre(self):
        texte=str(self.afficher([alerte()])).lower()
        for mot in ("gain garanti","profit certain","achetez maintenant","vendez maintenant"): self.assertNotIn(mot,texte)
    def test_aucun_moteur_ni_acces_donnees(self):
        source=(Path(__file__).resolve().parents[1]/"ui/alert_card.py").read_text(encoding="utf-8").lower()
        for mot in ("calculer_score","construire_decision","calculer_atr","construire_plan_risque","construire_alertes","market_data","pandas","numpy","yfinance","openai"): self.assertNotIn(mot,source)
    def test_import_isole(self):
        code="import sys,types; sys.modules['streamlit']=types.ModuleType('streamlit'); import ui.alert_card; interdits={'pandas','numpy','yfinance','openai'}; charges=interdits.intersection(sys.modules); assert not charges, charges"
        resultat=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,check=False)
        self.assertEqual(resultat.returncode,0,resultat.stderr)
if __name__ == "__main__": unittest.main()
