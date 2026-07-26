"""Tests de l'intégration du risque dans Actions et Cryptomonnaies."""

import ast
import copy
from pathlib import Path
import unittest
from unittest.mock import MagicMock

import pandas as pd


RACINE = Path(__file__).resolve().parents[1]
SOURCE = (RACINE / "app.py").read_text(encoding="utf-8")
ARBRE = ast.parse(SOURCE)
FONCTION_AST = next(
    noeud for noeud in ARBRE.body
    if isinstance(noeud, ast.FunctionDef)
    and noeud.name == "afficher_analyse_actif"
)
SEGMENT = ast.get_source_segment(SOURCE, FONCTION_AST)
REPLI = (
    "Le plan de risque est temporairement indisponible. L’analyse technique "
    "et la décision prudente restent accessibles."
)


class _Colonne:
    def metric(self, *args, **kwargs):
        return None


class _Contexte:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _Streamlit:
    def __init__(self, cliquer=False):
        self.cliquer = cliquer
        self.appels = []

    def header(self, texte):
        self.appels.append(("header", texte))

    def text_input(self, *args, **kwargs):
        return args[1]

    def warning(self, texte):
        self.appels.append(("warning", texte))

    def columns(self, nombre):
        return [_Colonne() for _ in range(nombre)]

    def plotly_chart(self, *args, **kwargs):
        self.appels.append(("graphique",))

    def caption(self, texte):
        self.appels.append(("caption", texte))

    def info(self, texte):
        self.appels.append(("info", texte))

    def subheader(self, texte):
        self.appels.append(("subheader", texte))

    def button(self, *args, **kwargs):
        self.appels.append(("button", args[0], kwargs.get("key")))
        return self.cliquer

    def spinner(self, texte):
        self.appels.append(("spinner", texte))
        return _Contexte()

    def markdown(self, texte):
        self.appels.append(("markdown", texte))


def _historique(ohlc=True):
    donnees = {"Close": [99.5, 100.123456789], "Volume": [10, 12]}
    if ohlc:
        donnees.update({
            "High": [100.0, 101.25],
            "Low": [98.5, 99.75],
            "Open": [99.0, 100.0],
        })
    return pd.DataFrame(donnees)


def _environnement(historique=None, cliquer=False):
    historique = _historique() if historique is None else historique
    st = _Streamlit(cliquer)
    dependances = {
        "st": st,
        "charger_donnees": MagicMock(return_value=historique),
        "recuperer_infos": MagicMock(return_value={"longName": "Test"}),
        "calculer_score": MagicMock(return_value={
            "score": 70, "signal": "SURVEILLER", "raisons": ["Raison"],
            "ventilation": [],
        }),
        "create_candlestick_chart": MagicMock(return_value=object()),
        "dernier_prix": MagicMock(return_value=100.12),
        "afficher_resume_technique": MagicMock(),
        "construire_decision": MagicMock(return_value={
            "recommandation": "Surveiller",
        }),
        "afficher_decision_prudente": MagicMock(),
        "calculer_atr": MagicMock(return_value=1.5),
        "construire_plan_risque": MagicMock(return_value={"statut": "partiel"}),
        "afficher_plan_risque": MagicMock(),
        "rsi": MagicMock(return_value=pd.Series([50.0])),
        "analyser_actif": MagicMock(return_value="Analyse"),
    }
    module = ast.Module(body=[FONCTION_AST], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, "app.py", "exec"), dependances)
    return dependances["afficher_analyse_actif"], dependances, st, historique


def _appels_ast(nom):
    return [
        noeud for noeud in ast.walk(FONCTION_AST)
        if isinstance(noeud, ast.Call)
        and isinstance(noeud.func, ast.Name)
        and noeud.func.id == nom
    ]


class AssetAnalysisRiskIntegrationTests(unittest.TestCase):
    def test_fonction_partagee_et_valeurs_initiales(self):
        self.assertIn(
            "afficher_analyse_actif(\"📊 Analyse d'une action\", \"AAPL\")",
            SOURCE,
        )
        self.assertIn(
            "afficher_analyse_actif(\"₿ Analyse d'une cryptomonnaie\", "
            "\"BTC-USD\")",
            SOURCE,
        )
        for branche in (
            "if action", "if crypto", "endswith", '"-USD" in symbole',
        ):
            self.assertNotIn(branche, SEGMENT)

    def test_imports_et_appels_statiques_uniques(self):
        self.assertIn(
            "from core.risk import calculer_atr, construire_plan_risque", SOURCE
        )
        self.assertIn("from ui.risk_card import afficher_plan_risque", SOURCE)
        for nom in (
            "charger_donnees", "recuperer_infos", "calculer_score",
            "construire_decision", "calculer_atr",
            "construire_plan_risque", "afficher_plan_risque",
            "analyser_actif",
        ):
            with self.subTest(nom=nom):
                self.assertEqual(len(_appels_ast(nom)), 1)

    def test_cas_nominal_reutilise_historique_sans_mutation(self):
        fonction, deps, _, historique = _environnement()
        copie = historique.copy(deep=True)
        fonction("Action", "AAPL")
        deps["charger_donnees"].assert_called_once_with("AAPL", "1y")
        deps["recuperer_infos"].assert_called_once_with("AAPL")
        deps["calculer_score"].assert_called_once()
        self.assertIs(deps["calculer_score"].call_args.args[1], historique)
        deps["construire_decision"].assert_called_once()
        deps["calculer_atr"].assert_called_once_with(
            [100.0, 101.25], [98.5, 99.75], [99.5, 100.123456789]
        )
        deps["construire_plan_risque"].assert_called_once_with(
            prix_entree=100.123456789,
            atr=1.5,
            capital_reference=None,
            risque_max_pct=None,
        )
        deps["afficher_plan_risque"].assert_called_once_with(
            {"statut": "partiel"}
        )
        pd.testing.assert_frame_equal(historique, copie)

    def test_ordre_resume_decision_risque_ia(self):
        marqueurs = [
            "afficher_resume_technique(resultat_score)",
            "construire_decision(resultat_score)",
            "calculer_atr(",
            "construire_plan_risque(",
            "afficher_plan_risque(plan_risque)",
            'st.subheader("🤖 Analyse complémentaire par l’IA")',
            'st.button("🤖 Analyser avec GPT"',
        ]
        positions = [SEGMENT.index(marqueur) for marqueur in marqueurs]
        self.assertEqual(positions, sorted(positions))

    def test_colonnes_manquantes_produisent_plan_indisponible(self):
        fonction, deps, _, _ = _environnement(_historique(ohlc=False))
        fonction("Action", "AAPL")
        deps["calculer_atr"].assert_not_called()
        deps["construire_plan_risque"].assert_called_once_with(
            prix_entree=None, atr=None,
            capital_reference=None, risque_max_pct=None,
        )
        deps["afficher_plan_risque"].assert_called_once()
        deps["charger_donnees"].assert_called_once()

    def test_atr_none_conserve_dernier_close_brut(self):
        fonction, deps, _, _ = _environnement()
        deps["calculer_atr"].return_value = None
        fonction("Crypto", "BTC-USD")
        deps["construire_plan_risque"].assert_called_once_with(
            prix_entree=100.123456789, atr=None,
            capital_reference=None, risque_max_pct=None,
        )
        deps["afficher_plan_risque"].assert_called_once()

    def test_exceptions_risque_affichent_repli_et_page_continue(self):
        for dependance in (
            "calculer_atr", "construire_plan_risque", "afficher_plan_risque",
        ):
            with self.subTest(dependance=dependance):
                fonction, deps, st, _ = _environnement()
                deps[dependance].side_effect = RuntimeError("test")
                fonction("Action", "AAPL")
                self.assertIn(("warning", REPLI), st.appels)
                self.assertTrue(any(appel[0] == "button" for appel in st.appels))
                self.assertFalse(any("Traceback" in str(a) for a in st.appels))

    def test_ia_absente_sans_clic_et_rsi_reste_conditionnel(self):
        fonction, deps, _, _ = _environnement(cliquer=False)
        fonction("Action", "AAPL")
        deps["rsi"].assert_not_called()
        deps["analyser_actif"].assert_not_called()

    def test_ia_inchangee_apres_clic_meme_si_risque_echoue(self):
        historique = pd.DataFrame({
            "Close": [100.0 + index for index in range(15)],
            "High": [101.0 + index for index in range(15)],
            "Low": [99.0 + index for index in range(15)],
            "Volume": [10] * 15,
        })
        fonction, deps, st, historique = _environnement(
            historique=historique, cliquer=True
        )
        deps["calculer_atr"].side_effect = RuntimeError("test")
        fonction("Crypto", "BTC-USD")
        deps["rsi"].assert_called_once_with(historique)
        deps["analyser_actif"].assert_called_once_with(
            "Test", "BTC-USD", 100.12, 70, 50.0, "SURVEILLER"
        )
        self.assertIn(("button", "🤖 Analyser avec GPT", "ia_BTC-USD"), st.appels)

    def test_aucune_formule_metier_ni_autre_ecran_touche(self):
        for terme in (
            "distance_stop", "risque_par_unite",
            "taille_position", "ratio_risque_rendement",
        ):
            self.assertNotIn(terme, SEGMENT)
        for fichier in ("dashboard.py", "scanner.py", "portfolio.py"):
            source = (RACINE / fichier).read_text(encoding="utf-8")
            self.assertNotIn("afficher_plan_risque", source)


if __name__ == "__main__":
    unittest.main()
