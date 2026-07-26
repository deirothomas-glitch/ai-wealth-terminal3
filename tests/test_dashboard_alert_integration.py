from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "dashboard.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION = next(x for x in TREE.body if isinstance(x, ast.FunctionDef) and x.name == "afficher_dashboard")


class DashboardAlertIntegrationTests(unittest.TestCase):
    def test_dashboard_ne_recalcule_plus_les_alertes(self):
        self.assertNotIn("construire_alertes", SOURCE)
        self.assertNotIn("afficher_alertes", SOURCE)

    def test_alertes_de_session_sont_transmises_au_cockpit(self):
        self.assertIn('alertes=session.get("alertes_positions", [])', SOURCE)
        self.assertEqual(SOURCE.count("afficher_cockpit("), 1)

    def test_aucun_appel_ia_automatique(self):
        appel = next(x for x in ast.walk(FUNCTION) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "analyser_contexte_marche")
        self.assertTrue(any(appel in set(ast.walk(bloc)) for bloc in ast.walk(FUNCTION) if isinstance(bloc, ast.If)))


if __name__ == "__main__": unittest.main()
