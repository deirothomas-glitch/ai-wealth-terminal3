"""Tests statiques de l'intégration du risque dans Marchés."""

import ast
from pathlib import Path
import unittest


RACINE = Path(__file__).resolve().parents[1]
SOURCE = (RACINE / "market.py").read_text(encoding="utf-8")
ARBRE = ast.parse(SOURCE)
FONCTION = next(
    noeud for noeud in ARBRE.body
    if isinstance(noeud, ast.FunctionDef) and noeud.name == "afficher_marche"
)
SEGMENT = ast.get_source_segment(SOURCE, FONCTION)


def _appels(nom):
    return [
        noeud for noeud in ast.walk(FONCTION)
        if isinstance(noeud, ast.Call)
        and isinstance(noeud.func, ast.Name)
        and noeud.func.id == nom
    ]


class MarketRiskIntegrationTests(unittest.TestCase):
    def test_imports_exacts(self):
        self.assertIn(
            "from core.risk import calculer_atr, construire_plan_risque", SOURCE
        )
        self.assertIn("from ui.risk_card import afficher_plan_risque", SOURCE)

    def test_appels_uniques_sans_second_chargement(self):
        for nom in (
            "calculer_score", "construire_decision", "calculer_atr",
            "construire_plan_risque", "afficher_plan_risque",
            "charger_donnees",
        ):
            with self.subTest(nom=nom):
                self.assertEqual(len(_appels(nom)), 1)

    def test_ordre_resume_decision_risque(self):
        positions = [
            SEGMENT.index('st.subheader("🧠 Synthèse technique")'),
            SEGMENT.index("construire_decision(resultat_score)"),
            SEGMENT.index("calculer_atr("),
            SEGMENT.index("construire_plan_risque("),
            SEGMENT.index("afficher_plan_risque(plan_risque)"),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_historique_reutilise_et_series_natives(self):
        appel = _appels("calculer_atr")[0]
        self.assertEqual([ast.unparse(argument) for argument in appel.args], [
            "[float(valeur) for valeur in historique['High'].tolist()]",
            "[float(valeur) for valeur in historique['Low'].tolist()]",
            "[float(valeur) for valeur in historique['Close'].tolist()]",
        ])
        self.assertIn(
            'prix_entree_risque = float(historique["Close"].iloc[-1])',
            SEGMENT,
        )

    def test_plan_partiel_sans_capital(self):
        appel = _appels("construire_plan_risque")[0]
        mots_cles = {
            mot_cle.arg: ast.unparse(mot_cle.value)
            for mot_cle in appel.keywords
        }
        self.assertEqual(mots_cles, {
            "prix_entree": "prix_entree_risque",
            "atr": "atr_actuel",
            "capital_reference": "None",
            "risque_max_pct": "None",
        })

    def test_colonnes_ohlc_verifiees_sans_rechargement(self):
        self.assertIn('colonnes_atr = {"High", "Low", "Close"}', SEGMENT)
        self.assertIn(
            "if colonnes_atr.issubset(historique.columns):", SEGMENT
        )
        self.assertIn("atr_actuel = None", SEGMENT)
        self.assertIn("prix_entree_risque = None", SEGMENT)

    def test_protection_locale_et_repli_exact(self):
        blocs = [noeud for noeud in FONCTION.body if isinstance(noeud, ast.Try)]
        self.assertEqual(len(blocs), 3)
        appels = {
            noeud.func.id for noeud in ast.walk(blocs[1])
            if isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Name)
        }
        self.assertTrue({
            "calculer_atr", "construire_plan_risque", "afficher_plan_risque",
        } <= appels)
        textes = {
            noeud.value for noeud in ast.walk(blocs[1])
            if isinstance(noeud, ast.Constant) and isinstance(noeud.value, str)
        }
        self.assertIn(
            "Le plan de risque est temporairement indisponible. L’analyse "
            "technique et la décision prudente restent accessibles.",
            textes,
        )

    def test_aucune_formule_de_risque_dans_market(self):
        for terme in (
            "distance_stop", "risque_par_unite", "taille_position",
            "ratio_risque_rendement",
        ):
            self.assertNotIn(terme, SOURCE)

    def test_autres_ecrans_respectent_leur_perimetre_risque(self):
        source_scanner = (RACINE / "scanner.py").read_text(encoding="utf-8")
        arbre_scanner = ast.parse(source_scanner)
        scanner = next(
            noeud for noeud in arbre_scanner.body
            if isinstance(noeud, ast.FunctionDef)
            and noeud.name == "afficher_scanner"
        )
        appels_scanner = [
            noeud.func.id for noeud in ast.walk(scanner)
            if isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Name)
        ]
        self.assertEqual(appels_scanner.count("construire_plan_risque"), 1)
        self.assertEqual(appels_scanner.count("construire_alertes"), 1)
        self.assertNotIn("calculer_atr", appels_scanner)
        self.assertNotIn("afficher_plan_risque", appels_scanner)

        source_portfolio = (RACINE / "portfolio.py").read_text(encoding="utf-8")
        for interdit in (
            "afficher_plan_risque", "afficher_resume_risque", "calculer_atr",
            "construire_plan_risque", "construire_alertes",
            "from ui.alert_card import",
        ):
            self.assertNotIn(interdit, source_portfolio)

        source_dashboard = (RACINE / "dashboard.py").read_text(encoding="utf-8")
        arbre_dashboard = ast.parse(source_dashboard)
        dashboard = next(
            noeud for noeud in arbre_dashboard.body
            if isinstance(noeud, ast.FunctionDef)
            and noeud.name == "afficher_dashboard"
        )
        appels_dashboard = [
            noeud.func.id for noeud in ast.walk(dashboard)
            if isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Name)
        ]
        self.assertEqual(appels_dashboard.count("calculer_atr"), 1)
        self.assertEqual(appels_dashboard.count("construire_plan_risque"), 1)
        self.assertEqual(appels_dashboard.count("afficher_resume_risque"), 1)
        self.assertNotIn("afficher_plan_risque", appels_dashboard)

        source_app = (RACINE / "app.py").read_text(encoding="utf-8")
        arbre_app = ast.parse(source_app)
        analyse_actif = next(
            noeud for noeud in arbre_app.body
            if isinstance(noeud, ast.FunctionDef)
            and noeud.name == "afficher_analyse_actif"
        )
        appels_analyse = [
            noeud.func.id for noeud in ast.walk(analyse_actif)
            if isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Name)
        ]
        self.assertEqual(appels_analyse.count("calculer_atr"), 1)
        self.assertEqual(appels_analyse.count("afficher_plan_risque"), 1)


if __name__ == "__main__":
    unittest.main()
