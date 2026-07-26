from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "dashboard.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION = next(x for x in TREE.body if isinstance(x, ast.FunctionDef) and x.name == "afficher_dashboard")


class DashboardIntegrationTests(unittest.TestCase):
    def test_dashboard_est_uniquement_le_cockpit(self):
        self.assertEqual(SOURCE.count("afficher_cockpit("), 1)
        for interdit in ("calculer_score", "construire_decision", "afficher_decision_prudente", "charger_donnees"):
            self.assertNotIn(interdit, SOURCE)

    def test_reutilise_classement_session_sans_relancer_scanner(self):
        self.assertIn('session.get("opportunites_classees", [])', SOURCE)
        self.assertNotIn("scanner_marche", SOURCE)
        self.assertNotIn("classer_resultats_scanner", SOURCE)

    def test_briefing_ia_reste_conditionnel(self):
        appel = next(x for x in ast.walk(FUNCTION) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "analyser_contexte_marche")
        self.assertTrue(any(appel in set(ast.walk(bloc)) for bloc in ast.walk(FUNCTION) if isinstance(bloc, ast.If)))

    def test_repli_conserve_un_point_de_depart(self):
        self.assertIn("Vous pouvez continuer depuis le Scanner", SOURCE)


if __name__ == "__main__": unittest.main()
