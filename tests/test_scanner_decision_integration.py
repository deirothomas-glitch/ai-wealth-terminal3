from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scanner.py").read_text(encoding="utf-8")
CORE = (ROOT / "scanner_core.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION = next(x for x in TREE.body if isinstance(x, ast.FunctionDef) and x.name == "afficher_scanner")


class ScannerDecisionIntegrationTests(unittest.TestCase):
    def test_selection_provient_exactement_du_classement_filtre(self):
        self.assertIn('identifiants = [', SOURCE)
        self.assertIn('opportunite_selectionnee = classement[index_actif]', SOURCE)
        self.assertIn('st.session_state.selected_asset = symbole_selectionne', SOURCE)
        self.assertIn("index_actif = identifiants.index(identifiant_selectionne)", SOURCE)
        self.assertIn('x.get("Actif") == symbole_selectionne', SOURCE)

    def test_score_non_recalcule_et_donnees_non_rechargees(self):
        segment = SOURCE[SOURCE.index("def afficher_scanner"):]
        self.assertNotIn("calculer_score(", segment)
        self.assertNotIn("charger_donnees(", segment)
        self.assertEqual(segment.count("construire_decision("), 1)

    def test_fiche_recoit_meme_ligne_opportunite_et_decision(self):
        self.assertIn("construire_fiche_opportunite(", SOURCE)
        for nom in ("ligne_selectionnee", "opportunite_selectionnee", "decision"):
            self.assertIn(nom, SOURCE)
        self.assertEqual(SOURCE.count("afficher_fiche_opportunite("), 1)

    def test_csv_reste_identique_et_objets_complexes_masques(self):
        self.assertIn('colonnes_masquees = ["Raisons", "Historique", "Ventilation", "ATR"]', SOURCE)
        self.assertIn("generer_csv(resultat.to_dict", SOURCE)
        self.assertNotIn("Date données", str(__import__("scanner_core").CSV_COLUMNS))

    def test_decision_absente_du_moteur_scanner(self):
        self.assertNotIn("core.decision", CORE)
        self.assertNotIn("construire_decision", CORE)


if __name__ == "__main__": unittest.main()
