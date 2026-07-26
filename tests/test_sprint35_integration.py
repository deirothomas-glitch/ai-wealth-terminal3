import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Sprint35IntegrationTests(unittest.TestCase):
    def test_pages_navigation(self):
        source=(ROOT/"app.py").read_text(encoding="utf-8");self.assertIn("afficher_page_actualites()",source);self.assertIn("afficher_assistant()",source)
    def test_dashboard_pas_ia_automatique_ni_scan(self):
        source=(ROOT/"dashboard.py").read_text(encoding="utf-8");tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="afficher_dashboard")
        ai=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="analyser_contexte_marche");buttons=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="button"];self.assertTrue(any(ai in set(ast.walk(b)) for b in (n for n in ast.walk(fn) if isinstance(n,ast.If))));self.assertNotIn("scanner_marche(",source)
    def test_actualites_actions_portefeuille_strategies_sur_bouton(self):
        for file in ("app.py","portfolio.py","pages/strategies.py"):
            source=(ROOT/file).read_text(encoding="utf-8");self.assertIn("agreger_actualites",source);self.assertIn("st.button",source)
    def test_scanner_ia_unique_et_pas_par_ligne(self):
        source=(ROOT/"scanner.py").read_text(encoding="utf-8");self.assertEqual(source.count("analyser_actif("),1);self.assertIn("Analyser la sélection",source)
    def test_core_imports_interdits_absents(self):
        for path in (ROOT/"core").glob("*.py"):
            source=path.read_text(encoding="utf-8").lower()
            for forbidden in ("import streamlit","import pandas","import yfinance","import openai","import requests","from services"):
                self.assertNotIn(forbidden,source,path.name)
    def test_secrets_ignores(self):
        text=(ROOT/".gitignore").read_text(encoding="utf-8");self.assertIn(".env",text);self.assertIn(".streamlit/secrets.toml",text)
if __name__=="__main__":unittest.main()
