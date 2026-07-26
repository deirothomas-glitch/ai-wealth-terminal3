"""Tests de l'intégration initiale des alertes dans le Scanner."""
import ast
from pathlib import Path
import unittest
RACINE=Path(__file__).resolve().parents[1]; SOURCE=(RACINE/"scanner.py").read_text(encoding="utf-8"); ARBRE=ast.parse(SOURCE)
FONCTION=next(n for n in ARBRE.body if isinstance(n,ast.FunctionDef) and n.name=="afficher_scanner"); SEGMENT=ast.get_source_segment(SOURCE,FONCTION)
def appels(nom): return [n for n in ast.walk(FONCTION) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==nom]
class ScannerAlertIntegrationTests(unittest.TestCase):
    def test_scanner_py_orchestre_et_core_reste_pur(self):
        self.assertIn("from core.alerts import construire_alertes",SOURCE); self.assertIn("from ui.alert_card import afficher_alertes",SOURCE)
        core=(RACINE/"scanner_core.py").read_text(encoding="utf-8")
        for interdit in ("construire_alertes","afficher_alertes","construire_plan_risque","calculer_atr"): self.assertNotIn(interdit,core)
    def test_alertes_uniques_pour_actif_en_tete(self):
        for nom in ("construire_decision","construire_plan_risque","construire_alertes","afficher_alertes"): self.assertEqual(len(appels(nom)),1)
        self.assertEqual([ast.unparse(a) for a in appels("construire_alertes")[0].args],["resultat_score_selectionne","decision","plan_risque"])
        for boucle in (n for n in ast.walk(FONCTION) if isinstance(n,(ast.For,ast.While))):
            self.assertNotIn(appels("construire_plan_risque")[0],set(ast.walk(boucle)))
    def test_plan_indisponible_sans_atr_ni_chargement(self):
        self.assertEqual([ast.unparse(a) for a in appels("construire_plan_risque")[0].args],["None","None","None","None"])
        self.assertEqual(len(appels("calculer_atr")),0); self.assertNotIn("charger_donnees(",SEGMENT); self.assertEqual(SEGMENT.count("scanner_marche("),1)
    def test_ordre_tableau_decision_alertes_ia_csv(self):
        marques=["st.dataframe(","construire_decision(resultat_score_selectionne)","construire_plan_risque(None, None, None, None)","afficher_alertes(alertes)","Analyse complémentaire par l’IA","generer_csv("]
        positions=[SEGMENT.index(m) for m in marques]; self.assertEqual(positions,sorted(positions))
    def test_bloc_local_sans_casser_ia_csv(self):
        blocs=[n for n in FONCTION.body if isinstance(n,ast.Try)]; self.assertEqual(len(blocs),2)
        noms={n.func.id for n in ast.walk(blocs[1]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertTrue({"construire_plan_risque","construire_alertes","afficher_alertes"}<=noms); self.assertFalse({"scanner_marche","analyser_actif","generer_csv"}&noms)
        self.assertIn("Les alertes d’analyse sont temporairement indisponibles. Les autres fonctions restent accessibles."," ".join(n.value for n in ast.walk(FONCTION) if isinstance(n,ast.Constant) and isinstance(n.value,str)))
    def test_tableau_et_export_non_enrichis(self):
        self.assertIn('colonnes_masquees = ["Raisons", "Historique", "Ventilation"]',SEGMENT); self.assertEqual(SEGMENT.count("generer_csv("),1)
        for colonne in ('"Alertes"','"Décision"','"Plan de risque"'): self.assertNotIn(colonne,SEGMENT)
if __name__=="__main__": unittest.main()
