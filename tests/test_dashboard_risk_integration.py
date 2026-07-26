from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "dashboard.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION = next(x for x in TREE.body if isinstance(x, ast.FunctionDef) and x.name == "afficher_dashboard")


class DashboardRiskIntegrationTests(unittest.TestCase):
    def test_dashboard_ne_construit_plus_de_plan_de_risque(self):
        for interdit in ("calculer_atr", "construire_plan_risque", "afficher_resume_risque"):
            self.assertNotIn(interdit, SOURCE)

    def test_risque_reste_resume_par_le_cockpit(self):
        self.assertIn('alertes=session.get("alertes_positions", [])', SOURCE)
        self.assertIn("afficher_cockpit", SOURCE)

    def test_aucun_chargement_actif_detaille(self):
        self.assertNotIn("historique", SOURCE)
        self.assertNotIn("dashboard_symbole", SOURCE)


if __name__ == "__main__": unittest.main()
