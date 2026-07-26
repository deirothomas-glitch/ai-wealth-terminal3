"""Tests statiques de l'intégration des alertes dans dashboard."""
import ast
from pathlib import Path
import unittest
RACINE=Path(__file__).resolve().parents[1]
SOURCE=(RACINE/"dashboard.py").read_text(encoding="utf-8")
ARBRE=ast.parse(SOURCE)
FONCTION=next(n for n in ARBRE.body if isinstance(n,ast.FunctionDef) and n.name=="afficher_dashboard")
SEGMENT=ast.get_source_segment(SOURCE,FONCTION)
def appels(nom): return [n for n in ast.walk(FONCTION) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==nom]
class DashboardAlertIntegrationTests(unittest.TestCase):
    def test_imports_appels_uniques_et_memes_objets(self):
        self.assertIn("from core.alerts import construire_alertes",SOURCE); self.assertIn("from ui.alert_card import afficher_alertes",SOURCE)
        self.assertEqual(len(appels("construire_alertes")),1); self.assertEqual(len(appels("afficher_alertes")),1)
        appel=appels("construire_alertes")[0]; self.assertEqual([ast.unparse(a) for a in appel.args],["resultat_score","decision","plan_risque"]); self.assertIn("afficher_alertes(alertes)",SEGMENT)
    def test_aucun_recalcul_ni_rechargement(self):
        for fn in ("charger_donnees","calculer_score","construire_decision","calculer_atr","construire_plan_risque"):
            self.assertEqual(len(appels(fn)),1,fn)
    def test_ordre_et_protection_locale(self):
        positions=[SEGMENT.index("afficher_resume_risque(plan_risque)"),SEGMENT.index("construire_alertes("),SEGMENT.index("afficher_alertes(alertes)")]
        self.assertEqual(positions,sorted(positions))
        blocs=[n for n in FONCTION.body if isinstance(n,ast.Try)]; self.assertEqual(len(blocs),3)
        noms={n.func.id for n in ast.walk(blocs[2]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertTrue({"construire_alertes","afficher_alertes"}<=noms); self.assertFalse({"calculer_score","construire_decision","calculer_atr","construire_plan_risque","analyser_actif","afficher_actualites"}&noms)
    def test_repli_exact_et_suite_accessible(self):
        self.assertIn("Les alertes d’analyse sont temporairement indisponibles. Les autres fonctions restent accessibles."," ".join(n.value for n in ast.walk(FONCTION) if isinstance(n,ast.Constant) and isinstance(n.value,str)))
        self.assertLess(SEGMENT.index("afficher_alertes(alertes)"),SEGMENT.index('st.expander("📰 Actualités"'))
if __name__=="__main__": unittest.main()
