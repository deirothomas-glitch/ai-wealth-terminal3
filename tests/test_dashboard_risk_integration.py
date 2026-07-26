"""Tests de l'intégration du résumé de risque dans le Dashboard."""

import ast
import copy
from pathlib import Path
import unittest
from unittest.mock import MagicMock
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
SOURCE = (RACINE / "dashboard.py").read_text(encoding="utf-8")
ARBRE = ast.parse(SOURCE)
FONCTION_AST = next(n for n in ARBRE.body if isinstance(n, ast.FunctionDef) and n.name == "afficher_dashboard")
SEGMENT = ast.get_source_segment(SOURCE, FONCTION_AST)
REPLI = "Le résumé du risque est temporairement indisponible. Le Dashboard, les actualités et l’analyse IA restent accessibles."

class _Colonne:
    def text_input(self, *args, **kwargs): return args[1]
    def selectbox(self, *args, **kwargs): return "1y"
    def metric(self, *args, **kwargs): pass
class _Contexte:
    def __enter__(self): return self
    def __exit__(self, *args): return False
class _Streamlit:
    def __init__(self, cliquer=False): self.cliquer, self.appels = cliquer, []
    def title(self, texte): self.appels.append(("title", texte))
    def caption(self, texte): self.appels.append(("caption", texte))
    def divider(self): pass
    def columns(self, nombre): return [_Colonne() for _ in range(nombre)]
    def plotly_chart(self, *args, **kwargs): self.appels.append(("graphique",))
    def metric(self, *args, **kwargs): pass
    def warning(self, texte): self.appels.append(("warning", texte))
    def info(self, texte): self.appels.append(("info", texte))
    def expander(self, titre, **kwargs): self.appels.append(("expander", titre)); return _Contexte()
    def button(self, *args, **kwargs): self.appels.append(("button", args[0])); return self.cliquer
    def spinner(self, texte): return _Contexte()
    def markdown(self, texte): self.appels.append(("markdown", texte))

def _historique(ohlc=True, vide=False):
    if vide: return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    donnees = {"Close": [99.5, 100.123456789], "Volume": [10, 12]}
    if ohlc: donnees.update({"High": [100.0, 101.25], "Low": [98.5, 99.75], "Open": [99.0, 100.0]})
    return pd.DataFrame(donnees)

def _environnement(historique=None, cliquer=False):
    historique = _historique() if historique is None else historique
    st, ordre = _Streamlit(cliquer), []
    def noter(nom, retour=None):
        def appel(*args, **kwargs): ordre.append(nom); return retour
        return MagicMock(side_effect=appel)
    deps = {"st": st, "APP_NAME": "AIWT", "APP_VERSION": "test", "AVAILABLE_PERIODS": ["1y"], "_cartes_marche": MagicMock(), "recuperer_indices": MagicMock(return_value=[]), "recuperer_cryptos": MagicMock(return_value=[]), "charger_donnees": MagicMock(return_value=historique), "dernier_prix": MagicMock(return_value=100.12), "variation_journaliere": MagicMock(return_value=.5), "dernier_volume": MagicMock(return_value=12), "create_candlestick_chart": noter("graphique", object()), "calculer_score": noter("score", {"score": 70, "signal": "SURVEILLER", "raisons": [], "ventilation": []}), "rsi": MagicMock(return_value=pd.Series([50.])), "macd": MagicMock(return_value={}), "afficher_resume_technique": noter("resume"), "construire_decision": noter("decision_construite", {"recommandation": "Surveiller"}), "afficher_decision_prudente": noter("decision_affichee"), "calculer_atr": noter("atr", 1.5), "construire_plan_risque": noter("plan", {"statut": "partiel"}), "afficher_resume_risque": noter("risque"), "afficher_actualites": noter("actualites"), "analyser_actif": noter("ia", "Analyse")}
    module = ast.Module(body=[FONCTION_AST], type_ignores=[]); ast.fix_missing_locations(module)
    exec(compile(module, "dashboard.py", "exec"), deps)
    return deps["afficher_dashboard"], deps, st, ordre, historique

def _appels(nom):
    return [n for n in ast.walk(FONCTION_AST) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == nom]

class DashboardRiskIntegrationTests(unittest.TestCase):
    def test_imports_et_appels_uniques(self):
        self.assertIn("from core.risk import calculer_atr, construire_plan_risque", SOURCE)
        self.assertIn("from ui.risk_summary import afficher_resume_risque", SOURCE)
        for nom in ("charger_donnees", "calculer_score", "calculer_atr", "construire_plan_risque", "afficher_resume_risque", "recuperer_indices", "recuperer_cryptos"):
            with self.subTest(nom=nom): self.assertEqual(len(_appels(nom)), 1)

    def test_cas_nominal_meme_historique_listes_natives_sans_mutation(self):
        fonction, deps, _, _, historique = _environnement(); copie = copy.deepcopy(historique); fonction()
        deps["charger_donnees"].assert_called_once_with("AAPL", "1y")
        self.assertIs(deps["calculer_score"].call_args.args[1], historique)
        self.assertIs(deps["create_candlestick_chart"].call_args.args[0], historique)
        deps["calculer_atr"].assert_called_once_with([100.0, 101.25], [98.5, 99.75], [99.5, 100.123456789])
        deps["construire_plan_risque"].assert_called_once_with(prix_entree=100.123456789, atr=1.5, capital_reference=None, risque_max_pct=None)
        deps["afficher_resume_risque"].assert_called_once_with({"statut": "partiel"})
        pd.testing.assert_frame_equal(historique, copie)

    def test_ordre_visuel(self):
        marqueurs = ["afficher_resume_technique(resultat_score", "construire_decision(resultat_score)", "afficher_resume_risque(plan_risque)", 'st.expander("📰 Actualités"', 'st.expander("🤖 Analyse complémentaire par l’IA"']
        positions = [SEGMENT.index(m) for m in marqueurs]; self.assertEqual(positions, sorted(positions))

    def test_historique_incomplet_ou_vide_produit_plan_indisponible(self):
        for historique in (_historique(ohlc=False), _historique(vide=True)):
            with self.subTest(vide=historique.empty):
                fonction, deps, _, _, _ = _environnement(historique); fonction()
                deps["calculer_atr"].assert_not_called()
                deps["construire_plan_risque"].assert_called_once_with(prix_entree=None, atr=None, capital_reference=None, risque_max_pct=None)
                deps["charger_donnees"].assert_called_once()

    def test_atr_none_conserve_close_brut(self):
        fonction, deps, _, _, _ = _environnement(); deps["calculer_atr"].side_effect = None; deps["calculer_atr"].return_value = None; fonction()
        deps["construire_plan_risque"].assert_called_once_with(prix_entree=100.123456789, atr=None, capital_reference=None, risque_max_pct=None)

    def test_exceptions_risque_affichent_repli_et_page_continue(self):
        for nom in ("calculer_atr", "construire_plan_risque", "afficher_resume_risque"):
            with self.subTest(nom=nom):
                fonction, deps, st, ordre, _ = _environnement(); deps[nom].side_effect = RuntimeError("test"); fonction()
                self.assertIn(("warning", REPLI), st.appels); self.assertIn("actualites", ordre)
                self.assertTrue(any(a[0] == "button" for a in st.appels)); self.assertNotIn("Traceback", str(st.appels))

    def test_ia_conditionnelle_et_accessible_apres_echec(self):
        fonction, deps, _, _, _ = _environnement(); fonction(); deps["analyser_actif"].assert_not_called()
        fonction, deps, _, ordre, _ = _environnement(cliquer=True); deps["calculer_atr"].side_effect = RuntimeError("test"); fonction()
        deps["analyser_actif"].assert_called_once(); self.assertLess(ordre.index("actualites"), ordre.index("ia"))

    def test_try_local_aucune_formule_ni_appel_indesirable(self):
        blocs = [n for n in FONCTION_AST.body if isinstance(n, ast.Try)]; self.assertEqual(len(blocs), 3)
        appels = {n.func.id for n in ast.walk(blocs[1]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertTrue({"calculer_atr", "construire_plan_risque", "afficher_resume_risque"} <= appels)
        self.assertFalse({"afficher_resume_technique", "afficher_actualites", "analyser_actif", "rsi", "macd"} & appels)
        for terme in ("distance_stop", "risque_par_unite", "taille_position", "ratio_risque_rendement"): self.assertNotIn(terme, SEGMENT)

    def test_fichiers_hors_perimetre_sans_resume(self):
        for fichier in ("market.py", "app.py", "scanner.py", "portfolio.py", "core/risk.py", "ui/risk_card.py"):
            self.assertNotIn("afficher_resume_risque", (RACINE / fichier).read_text(encoding="utf-8"))

if __name__ == "__main__": unittest.main()
