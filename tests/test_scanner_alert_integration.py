from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scanner.py").read_text(encoding="utf-8")
CORE = (ROOT / "scanner_core.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION = next(x for x in TREE.body if isinstance(x, ast.FunctionDef) and x.name == "afficher_scanner")


class ScannerAlertIntegrationTests(unittest.TestCase):
    def test_plan_utilise_prix_et_atr_transportes(self):
        self.assertIn('ligne_selectionnee.get("Prix")', SOURCE)
        self.assertIn('ligne_selectionnee.get("ATR")', SOURCE)
        self.assertIn("atr = _atr_depuis_historique(historique)", CORE)
        self.assertIn('"ATR": atr', CORE)

    def test_aucun_second_chargement_et_ia_unique(self):
        segment = SOURCE[SOURCE.index("def afficher_scanner"):]
        self.assertNotIn("charger_donnees(", segment)
        self.assertEqual(SOURCE.count("analyser_actif("), 1)
        self.assertIn("Analyse IA uniquement sur demande", SOURCE)

    def test_ordre_fiche_ia_risque_actions_export(self):
        marqueurs = [
            "afficher_fiche_opportunite(",
            'st.subheader("9. Analyse IA uniquement sur demande")',
            'st.subheader("10. Plan de risque")',
            'st.subheader("11. Décision et prochaines actions")',
            'with st.expander("Résultats techniques et export")',
        ]
        positions = [SOURCE.index(x) for x in marqueurs]
        self.assertEqual(positions, sorted(positions))

    def test_scanner_core_reste_sans_interface_ni_reseau(self):
        for interdit in ("streamlit", "yfinance", "openai", "market_data"):
            self.assertNotIn(interdit, CORE.casefold())


if __name__ == "__main__": unittest.main()
