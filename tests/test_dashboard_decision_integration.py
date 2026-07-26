import ast
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "dashboard.py").read_text(encoding="utf-8")
ARBRE = ast.parse(SOURCE)


class DashboardIntegrationTests(unittest.TestCase):
    def test_appels_uniques_score_et_donnees(self):
        appels = [n.func.id for n in ast.walk(ARBRE) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        self.assertEqual(appels.count("calculer_score"), 1)
        self.assertEqual(appels.count("charger_donnees"), 1)

    def test_meme_objet_et_raisons_masquees(self):
        self.assertIn("afficher_resume_technique(resultat_score, afficher_raisons=False)", SOURCE)
        self.assertIn("construire_decision(resultat_score)", SOURCE)
        self.assertNotIn("resultat_score.copy", SOURCE)

    def test_decision_affichee_et_ancien_signal_absent(self):
        self.assertIn("afficher_decision_prudente(decision)", SOURCE)
        self.assertNotIn('metric("Signal"', SOURCE)
        self.assertNotIn('metric("Score technique"', SOURCE)

    def test_ordre_visuel(self):
        marqueurs = ["afficher_resume_technique(", "Le signal technique résume les indicateurs.",
                     "construire_decision(resultat_score)", 'st.expander("📰 Actualités"',
                     'st.expander("🤖 Analyse complémentaire par l’IA"']
        positions = [SOURCE.index(marqueur) for marqueur in marqueurs]
        self.assertEqual(positions, sorted(positions))

    def test_textes_exacts(self):
        normalise = " ".join(n.value for n in ast.walk(ARBRE) if isinstance(n, ast.Constant) and isinstance(n.value, str))
        self.assertIn("Le signal technique résume les indicateurs. La recommandation prudente tient compte de la couverture et de la cohérence des preuves disponibles.", normalise)
        self.assertIn("La recommandation prudente est indisponible. Le score et le signal techniques restent consultables.", normalise)
        self.assertIn("L’analyse IA apporte un commentaire complémentaire. Elle ne remplace pas la recommandation déterministe ni votre décision.", normalise)
        self.assertIn("« Éviter » signifie ne pas initier une position sur la base des données actuelles. Cela ne suppose pas que vous détenez l’actif.", normalise)

    def test_actualites_ia_et_parametres_preserves(self):
        self.assertIn("afficher_actualites(symbole)", SOURCE)
        self.assertEqual(SOURCE.count("analyser_actif("), 1)
        self.assertIn("resultat_score[\"score\"]", SOURCE)
        self.assertIn("resultat_score[\"signal\"]", SOURCE)

    def test_try_separes_decision_et_risque(self):
        fonction = next(n for n in ARBRE.body if isinstance(n, ast.FunctionDef) and n.name == "afficher_dashboard")
        blocs = [n for n in fonction.body if isinstance(n, ast.Try)]
        self.assertEqual(len(blocs), 3)
        appels_decision = {n.func.id for n in ast.walk(blocs[0]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        appels_risque = {n.func.id for n in ast.walk(blocs[1]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        appels_alertes = {n.func.id for n in ast.walk(blocs[2]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertTrue({"construire_decision", "afficher_decision_prudente"} <= appels_decision)
        self.assertTrue({"calculer_atr", "construire_plan_risque", "afficher_resume_risque"} <= appels_risque)
        self.assertTrue({"construire_alertes", "afficher_alertes"} <= appels_alertes)
        hors_blocs = {"afficher_resume_technique", "afficher_actualites", "analyser_actif"}
        self.assertFalse(hors_blocs & appels_decision)
        self.assertFalse(hors_blocs & appels_risque)
        self.assertFalse(hors_blocs & appels_alertes)

    def test_aucun_scanner_export_ou_nouvelle_dependance(self):
        self.assertNotIn("scanner", SOURCE.lower())
        self.assertNotIn("download_button", SOURCE)
        composant = (Path(__file__).resolve().parents[1] / "ui/technical_summary.py").read_text(encoding="utf-8")
        for interdit in ("openai", "yfinance", "market_data", "ai_analysis", "scoring", "core.decision"):
            self.assertNotIn(interdit, composant.lower())


if __name__ == "__main__": unittest.main()
