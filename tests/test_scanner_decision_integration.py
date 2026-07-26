import ast
from pathlib import Path
import unittest

RACINE = Path(__file__).resolve().parents[1]
SOURCE = (RACINE / "scanner.py").read_text(encoding="utf-8")
ARBRE = ast.parse(SOURCE)
FONCTION = next(n for n in ARBRE.body if isinstance(n, ast.FunctionDef) and n.name == "afficher_scanner")
SEGMENT = ast.get_source_segment(SOURCE, FONCTION)


def appels(nom):
    return [n for n in ast.walk(FONCTION) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == nom]


class ScannerDecisionIntegrationTests(unittest.TestCase):
    def test_imports_et_moteur_sans_decision(self):
        self.assertIn("from core.decision import construire_decision", SOURCE)
        self.assertIn("from ui.technical_summary import afficher_resume_technique", SOURCE)
        self.assertIn("from ui.decision_card import afficher_decision_prudente", SOURCE)
        core = (RACINE / "scanner_core.py").read_text(encoding="utf-8")
        self.assertNotIn("construire_decision", core)
        self.assertNotIn("ui.decision_card", core)

    def test_selection_et_decision_uniques(self):
        self.assertEqual(SEGMENT.count("resultat_score_selectionne = {"), 1)
        self.assertIn("meilleur = filtre.iloc[0]", SEGMENT)
        self.assertEqual(len(appels("construire_decision")), 1)
        appel = appels("construire_decision")[0]
        for boucle in (n for n in ast.walk(FONCTION) if isinstance(n, (ast.For, ast.While))):
            self.assertNotIn(appel, set(ast.walk(boucle)))

    def test_adaptateur_exact(self):
        affectation = next(n for n in ast.walk(FONCTION) if isinstance(n, ast.Assign) and any(isinstance(c, ast.Name) and c.id == "resultat_score_selectionne" for c in n.targets))
        self.assertEqual([c.value for c in affectation.value.keys], ["score", "signal", "raisons", "ventilation"])
        self.assertEqual([ast.unparse(v) for v in affectation.value.values], [
            "int(meilleur['Score'])", "str(meilleur['Signal'])",
            "list(meilleur['Raisons'])", "list(meilleur['Ventilation'])",
        ])

    def test_meme_adaptateur_transmis(self):
        self.assertIn("afficher_resume_technique(resultat_score_selectionne)", SEGMENT)
        self.assertIn("construire_decision(resultat_score_selectionne)", SEGMENT)
        self.assertIn("afficher_decision_prudente(decision)", SEGMENT)

    def test_tableau_prioritaire_et_ordre(self):
        marqueurs = ["st.dataframe(", "resultat_score_selectionne = {", "Actif en tête du classement technique",
                     "afficher_resume_technique(resultat_score_selectionne)", "Le signal technique résume les indicateurs.",
                     "construire_decision(resultat_score_selectionne)", "Analyse complémentaire par l’IA",
                     'st.button("🤖 Analyser la sélection"', "generer_csv(", "st.download_button("]
        positions = [SEGMENT.index(m) for m in marqueurs]
        self.assertEqual(positions, sorted(positions))

    def test_vocabulaire_et_ancienne_boucle_supprimes(self):
        self.assertNotIn("Meilleure opportunité", SEGMENT)
        self.assertNotIn('for raison in meilleur["Raisons"]', SEGMENT)
        self.assertIn("🔎 Actif en tête du classement technique", SEGMENT)

    def test_textes_exacts(self):
        textes = {n.value for n in ast.walk(FONCTION) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        attendus = {
            "Le signal technique résume les indicateurs. La recommandation prudente tient compte de la couverture et de la cohérence des preuves disponibles.",
            "La recommandation prudente est temporairement indisponible. Le classement technique, l’analyse IA et l’export restent accessibles.",
            "« Éviter » signifie ne pas initier une position sur la base des données actuelles. Cela ne suppose pas que vous détenez l’actif.",
            "L’analyse IA apporte un commentaire complémentaire. Elle ne remplace pas la recommandation déterministe ni votre décision.",
        }
        self.assertTrue(attendus <= textes)

    def test_try_limite_a_la_decision(self):
        blocs = [n for n in FONCTION.body if isinstance(n, ast.Try)]
        self.assertEqual(len(blocs), 2)
        noms = {n.func.id for n in ast.walk(blocs[0]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        noms_alertes = {n.func.id for n in ast.walk(blocs[1]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertTrue({"construire_decision", "afficher_decision_prudente"} <= noms)
        self.assertTrue({"construire_plan_risque", "construire_alertes", "afficher_alertes"} <= noms_alertes)
        self.assertFalse({"afficher_resume_technique", "analyser_actif", "generer_csv"} & noms)
        self.assertFalse({"afficher_resume_technique", "analyser_actif", "generer_csv"} & noms_alertes)

    def test_aucun_recalcul_ni_rechargement(self):
        self.assertNotIn("calculer_score(", SEGMENT)
        self.assertNotIn("charger_donnees(", SEGMENT)
        self.assertEqual(SEGMENT.count("scanner_marche("), 1)

    def test_csv_et_colonnes_masquees_inchanges(self):
        self.assertIn('colonnes_masquees = ["Raisons", "Historique", "Ventilation"]', SEGMENT)
        self.assertEqual(SEGMENT.count("generer_csv("), 1)
        self.assertEqual(SEGMENT.count("st.download_button("), 1)
        for colonne in ('"Décision"', '"Recommandation"', '"Confiance"'):
            self.assertNotIn(colonne, SEGMENT)


if __name__ == "__main__": unittest.main()
