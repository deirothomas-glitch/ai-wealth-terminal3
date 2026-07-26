"""Tests de services et d’intégration produit du Sprint 3.4."""
import unittest
from pathlib import Path
from unittest.mock import Mock
import pandas as pd
from core.strategy_profiles import obtenir_profil
from services.backtest_runner import lancer_backtest,preparer_historique
ROOT=Path(__file__).resolve().parents[1]
class StrategyIntegrationTests(unittest.TestCase):
 def historique(self):
  valeurs=list(range(80,140)); return pd.DataFrame({"Open":valeurs,"High":[v+1 for v in valeurs],"Low":[v-1 for v in valeurs],"Close":valeurs,"Volume":[1000]*len(valeurs)},index=pd.date_range("2025-01-01",periods=len(valeurs)))
 def test_adaptation_pandas_native(self):
  rows=preparer_historique(self.historique(),obtenir_profil("court_terme")); self.assertEqual(len(rows),60); self.assertIsInstance(rows[-1]["close"],float)
 def test_un_chargement_par_lancement(self):
  chargeur=Mock(return_value=self.historique()); lancer_backtest("ABC",obtenir_profil("swing"),chargeur); chargeur.assert_called_once_with("ABC","1y")
 def test_service_erreur_isolee_par_action(self):
  chargeur=Mock(side_effect=RuntimeError("indisponible"));
  with self.assertRaisesRegex(RuntimeError,"indisponible"): lancer_backtest("BAD",obtenir_profil("swing"),chargeur)
  self.assertEqual(chargeur.call_count,1)
 def test_page_lancement_explicite_et_session(self):
  source=(ROOT/"pages/strategies.py").read_text(); self.assertIn('st.button("▶️ Lancer le backtest"',source); self.assertIn('st.session_state.strategie_resultat',source); self.assertIn('st.dataframe',source); self.assertIn('st.line_chart',source)
 def test_page_avertissements_methodologiques(self):
  source=(ROOT/"pages/strategies.py").read_text(); self.assertIn("performances passées",source); self.assertIn("slippage",source); self.assertIn("faible nombre d’opérations",source)
 def test_scanner_ameliore_sans_backtest(self):
  source=(ROOT/"scanner.py").read_text(); self.assertIn("Profil de stratégie",source); self.assertIn("filtre_confiance",source); self.assertNotIn("lancer_backtest",source)
 def test_dashboard_reutilise_session_sans_chargement_scan(self):
  source=(ROOT/"dashboard.py").read_text(); self.assertIn("opportunites_classees",source); self.assertNotIn("classer_resultats_scanner",source)
 def test_prefill_portefeuille_confirme(self):
  strategie=(ROOT/"pages/strategies.py").read_text(); portefeuille=(ROOT/"portfolio.py").read_text(); self.assertIn("portfolio_prefill",strategie); self.assertIn("portfolio_prefill",portefeuille); self.assertIn("ajouter_position",portefeuille)
 def test_ui_ne_charge_ni_moteur_ni_donnees(self):
  for nom in ("strategy_card.py","data_quality_card.py","backtest_summary.py","opportunity_table.py"):
   source=(ROOT/"ui"/nom).read_text(); self.assertNotIn("charger_donnees",source); self.assertNotIn("executer_backtest",source); self.assertNotIn("evaluer_strategie",source)
if __name__=="__main__": unittest.main()
