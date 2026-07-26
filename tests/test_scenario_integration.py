"""Garanties d'intégration du moteur universel de scénarios."""

import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ScenarioIntegrationTests(unittest.TestCase):
    def test_core_reste_pur_et_sans_openai(self):
        source=(ROOT/'core/scenario_engine.py').read_text(encoding='utf-8').lower()
        for interdit in ('streamlit','openai','yfinance','pandas','from services'):
            self.assertNotIn(interdit,source)

    def test_cockpit_affiche_uniquement_principal(self):
        source=(ROOT/'ui/investor_cockpit.py').read_text(encoding='utf-8')
        self.assertIn('afficher_scenario_principal',source)
        self.assertNotIn('afficher_scenarios(',source)

    def test_assistant_affiche_trois_scenarios_apres_action(self):
        source=(ROOT/'pages/assistant_page.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        fonction=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='afficher_assistant')
        appel=next(x for x in ast.walk(fonction) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='afficher_scenarios')
        blocs=[x for x in ast.walk(fonction) if isinstance(x,ast.If)]
        self.assertTrue(any(appel in set(ast.walk(bloc)) for bloc in blocs))
        self.assertIn('enrichir_redaction_scenarios',source)

    def test_actions_crypto_partagent_un_seul_helper(self):
        source=(ROOT/'app.py').read_text(encoding='utf-8')
        self.assertEqual(source.count('def _afficher_scenarios_actif('),1)
        tree=ast.parse(source)
        appels=[x for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='_afficher_scenarios_actif']
        self.assertEqual(len(appels),1)
        self.assertIn('afficher_analyse_actif("📊 Analyse d\'une action", "AAPL")',source)
        self.assertIn('afficher_analyse_actif("₿ Analyse d\'une cryptomonnaie", "BTC-USD")',source)

    def test_scanner_scenarios_uniquement_sur_bouton_et_selection_tete(self):
        source=(ROOT/'scanner.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        fonction=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='afficher_scanner')
        appel=next(x for x in ast.walk(fonction) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='afficher_scenarios')
        blocs=[x for x in ast.walk(fonction) if isinstance(x,ast.If)]
        self.assertTrue(any(appel in set(ast.walk(bloc)) for bloc in blocs))
        self.assertIn('scanner_scenarios',source)
        self.assertEqual(source.count('analyser_actif('),1)
        self.assertEqual(source.count('construire_scenarios_depuis_contrats('),1)


if __name__=='__main__': unittest.main()
