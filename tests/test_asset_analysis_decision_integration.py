import ast
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
ARBRE = ast.parse(SOURCE)
FONCTION = next(n for n in ARBRE.body if isinstance(n, ast.FunctionDef) and n.name == "afficher_analyse_actif")


def appels(nom):
    return [n for n in ast.walk(FONCTION) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == nom]


class AssetAnalysisIntegrationTests(unittest.TestCase):
    def test_fonction_partagee_et_valeurs_par_defaut(self):
        self.assertIn('afficher_analyse_actif("📊 Analyse d\'une action", "AAPL")', SOURCE)
        self.assertIn('afficher_analyse_actif("₿ Analyse d\'une cryptomonnaie", "BTC-USD")', SOURCE)

    def test_appels_uniques(self):
        self.assertEqual(len(appels("calculer_score")), 1)
        self.assertEqual(len(appels("analyser_actif")), 1)
        self.assertEqual(len(appels("charger_donnees")), 1)

    def test_meme_resultat_sans_copie(self):
        self.assertIn("afficher_resume_technique(resultat_score)", SOURCE)
        self.assertIn("construire_decision(resultat_score)", SOURCE)
        self.assertNotIn("resultat_score.copy", SOURCE)
        self.assertNotIn("dict(resultat_score)", SOURCE)

    def test_decision_affichee_et_metriques_directes_supprimees(self):
        segment = ast.get_source_segment(SOURCE, FONCTION)
        self.assertIn("afficher_decision_prudente(decision)", segment)
        self.assertIn("🤖 Analyse complémentaire par l’IA", segment)
        self.assertNotIn('metric("Signal"', segment)
        self.assertNotIn('metric("Score technique"', segment)

    def test_ordre_resume_decision_ia(self):
        segment = ast.get_source_segment(SOURCE, FONCTION)
        marqueurs = ["afficher_resume_technique(resultat_score)", "Le signal technique résume les indicateurs.",
                     "construire_decision(resultat_score)", "L’analyse IA apporte un commentaire complémentaire.",
                     'st.button("🤖 Analyser avec GPT"', "analyser_actif("]
        positions = [segment.index(m) for m in marqueurs]
        self.assertEqual(positions, sorted(positions))

    def test_textes_exacts(self):
        textes = {n.value for n in ast.walk(FONCTION) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        attendus = {
            "Le signal technique résume les indicateurs. La recommandation prudente tient compte de la couverture et de la cohérence des preuves disponibles.",
            "La recommandation prudente est indisponible. Le score et le signal techniques restent consultables.",
            "L’analyse IA apporte un commentaire complémentaire. Elle ne remplace pas la recommandation déterministe ni votre décision.",
            "« Éviter » signifie ne pas initier une position sur la base des données actuelles. Cela ne suppose pas que vous détenez l’actif.",
        }
        self.assertTrue(attendus <= textes)

    def test_try_separes_decision_risque_et_alertes(self):
        blocs = [n for n in FONCTION.body if isinstance(n, ast.Try)]
        self.assertEqual(len(blocs), 3)
        appels_par_bloc = [
            {
                n.func.id for n in ast.walk(bloc)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            }
            for bloc in blocs
        ]
        appels_decision, appels_risque, appels_alertes = appels_par_bloc
        self.assertTrue({
            "construire_decision", "afficher_decision_prudente",
        } <= appels_decision)
        self.assertFalse({
            "afficher_resume_technique", "calculer_atr",
            "construire_plan_risque", "afficher_plan_risque",
            "construire_alertes", "afficher_alertes", "rsi", "analyser_actif",
        } & appels_decision)
        self.assertTrue({
            "calculer_atr", "construire_plan_risque", "afficher_plan_risque",
        } <= appels_risque)
        self.assertFalse({
            "construire_decision", "afficher_decision_prudente",
            "afficher_resume_technique", "construire_alertes",
            "afficher_alertes", "rsi", "analyser_actif",
        } & appels_risque)
        self.assertTrue({"construire_alertes", "afficher_alertes"} <= appels_alertes)
        self.assertFalse({
            "construire_decision", "calculer_atr", "construire_plan_risque",
            "afficher_resume_technique", "rsi", "analyser_actif",
        } & appels_alertes)
        noeuds_try = set().union(*(set(ast.walk(bloc)) for bloc in blocs))
        bouton_ia = next(
            n for n in ast.walk(FONCTION)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "button"
        )
        self.assertNotIn(bouton_ia, noeuds_try)
        self.assertNotIn(appels("rsi")[0], noeuds_try)
        self.assertNotIn(appels("analyser_actif")[0], noeuds_try)

    def test_bouton_rsi_et_arguments_ia_preserves(self):
        segment = ast.get_source_segment(SOURCE, FONCTION)
        bouton = segment.index('st.button("🤖 Analyser avec GPT", key=f"ia_{valeur_defaut}")')
        self.assertGreater(segment.index("rsi_actuel =", bouton), bouton)
        args = [ast.unparse(a) for a in appels("analyser_actif")[0].args]
        self.assertEqual(args, ["info.get('longName', symbole)", "symbole", "dernier_prix(historique)",
                                "resultat_score['score']", "rsi_actuel", "resultat_score['signal']"])

    def test_aucun_autre_ecran_ou_export(self):
        segment = ast.get_source_segment(SOURCE, FONCTION).lower()
        for interdit in ("scanner", "afficher_dashboard", "afficher_marche", "download_button", "generer_csv"):
            self.assertNotIn(interdit, segment)


if __name__ == "__main__": unittest.main()
