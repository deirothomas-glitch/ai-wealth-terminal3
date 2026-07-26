"""Tests Sprint 3.4 : profils, qualité, stratégie, classement et backtest."""
import json,subprocess,sys,unittest
from copy import deepcopy
from core.backtest import executer_backtest
from core.data_quality import evaluer_qualite_donnees
from core.opportunity_ranking import classer_opportunites
from core.strategy_engine import evaluer_strategie
from core.strategy_profiles import obtenir_profil,obtenir_profils

def qualite(**kw):
 d={"nombre_points":100,"minimum_requis":40,"prix":100,"valeurs_manquantes":0,"volume_disponible":True,"volatilite_disponible":True,"indicateurs_essentiels":{"score":True,"rsi":True}}; d.update(kw); return d
def score(n=75): return {"score":n,"signal":"ACHAT","raisons":[],"ventilation":[{"contribution":10,"raison":"Tendance positive"},{"contribution":10,"raison":"Momentum cohérent"}]}
def decision(rec="Surveiller"): return {"recommandation":rec}
def rows(sortie=110,stop=None,objectif=None): return [{"date":"J0","open":100,"high":101,"low":99,"close":100,"signal_entree":True},{"date":"J1","open":100,"high":102,"low":98,"close":101,"stop":stop,"objectif":objectif},{"date":"J2","open":sortie,"high":max(sortie,111),"low":min(sortie,99),"close":sortie}]
def candidat(symbole="AAA",tech=80,strat=80,qual=90,niveau="bon",risque=True): return {"symbole":symbole,"nom":symbole,"categorie":"Action","strategie":"Swing","score_technique":tech,"score_strategie":strat,"confiance":"elevee","decision":"Surveiller","score_qualite":qual,"qualite_donnees":niveau,"plan_risque_disponible":risque,"raisons_principales":["raison"],"points_vigilance":[]}
class StrategyBacktestTests(unittest.TestCase):
 def test_trois_profils_contrats_json(self):
  p=obtenir_profils(); self.assertEqual([x["identifiant"] for x in p],["court_terme","swing","tendance"]); json.dumps(p,allow_nan=False); self.assertTrue(all(set(("identifiant","nom","description","horizon","periode_donnees","intervalle","seuil_score_surveillance","seuil_score_favorable","poids","regles")).issubset(x) for x in p))
 def test_profils_frais_et_non_mutables(self):
  a=obtenir_profils(); a[0]["poids"]["technique"]=999; self.assertNotEqual(obtenir_profils()[0]["poids"]["technique"],999); self.assertIsNone(obtenir_profil("absent"))
 def test_qualite_valide(self): self.assertEqual(evaluer_qualite_donnees(qualite())["niveau"],"bon")
 def test_qualite_historique_court(self): self.assertIn("Historique trop court.",evaluer_qualite_donnees(qualite(nombre_points=5))["problemes"])
 def test_qualite_prix_invalide(self): self.assertEqual(evaluer_qualite_donnees(qualite(prix=-1))["niveau"],"insuffisant")
 def test_qualite_manquantes_indicateurs(self):
  q=evaluer_qualite_donnees(qualite(valeurs_manquantes=3,indicateurs_essentiels={})); self.assertEqual(len(q["problemes"]),2)
 def test_qualite_bornee_deterministe_non_mutation(self):
  d=qualite(prix=-1,nombre_points=0,valeurs_manquantes=999,donnees_incoherentes=True); avant=deepcopy(d); a=evaluer_qualite_donnees(d); self.assertEqual(a,evaluer_qualite_donnees(d)); self.assertEqual(d,avant); self.assertGreaterEqual(a["score_qualite"],0)
 def test_strategie_valide_elevee_forces(self):
  r=evaluer_strategie({},score(90),decision(),obtenir_profil("swing"),evaluer_qualite_donnees(qualite())); self.assertEqual(r["confiance"],"elevee"); self.assertEqual(r["signal"],"favorable"); self.assertEqual(len(r["forces"]),2)
 def test_strategie_partielle_faible(self):
  r=evaluer_strategie({},score(),decision(),obtenir_profil("swing"),evaluer_qualite_donnees(qualite(prix=-1))); self.assertIsNone(r["score_strategie"]); self.assertEqual(r["confiance"],"faible")
 def test_strategie_faiblesses_confirmations_invalidations(self):
  s=score(); s["ventilation"].append({"contribution":-10,"raison":"Volume fragile"}); r=evaluer_strategie({},s,decision(),obtenir_profil("swing"),evaluer_qualite_donnees(qualite())); self.assertIn("Volume fragile",r["faiblesses"]); self.assertTrue(r["conditions_confirmation"]); self.assertTrue(r["conditions_invalidation"])
 def test_strategie_non_mutation_json_vocabulaire(self):
  s=score(); avant=deepcopy(s); r=evaluer_strategie({},s,decision(),obtenir_profil("swing"),evaluer_qualite_donnees(qualite())); self.assertEqual(s,avant); json.dumps(r,allow_nan=False); self.assertNotIn(r["signal"],["acheter","vendre"])
 def test_classement_ordre_et_egalite_symbole(self): self.assertEqual([x["symbole"] for x in classer_opportunites([candidat("BBB"),candidat("AAA")])],["AAA","BBB"])
 def test_classement_insuffisant_penalise(self): self.assertIsNone(classer_opportunites([candidat(niveau="insuffisant")])[0]["score_global"])
 def test_classement_plan_risque(self): self.assertGreater(classer_opportunites([candidat("A",risque=True)])[0]["score_global"],classer_opportunites([candidat("A",risque=False)])[0]["score_global"])
 def test_classement_manquants_deterministe_non_mutation(self):
  x=[candidat(),candidat("X",strat=None)]; avant=deepcopy(x); self.assertEqual(classer_opportunites(x),classer_opportunites(x)); self.assertEqual(x,avant); self.assertIsNone(classer_opportunites(x)[-1]["score_global"])
 def test_backtest_vide(self): self.assertEqual(executer_backtest([],"Swing","A")["nombre_operations"],0)
 def test_backtest_capital_invalide(self): self.assertIn("invalides",executer_backtest(rows(),"Swing","A",capital_initial=0)["avertissements"][0])
 def test_backtest_aucune_operation(self): self.assertEqual(executer_backtest([{**r,"signal_entree":False} for r in rows()],"Swing","A")["nombre_operations"],0)
 def test_backtest_gagnant(self): self.assertGreater(executer_backtest(rows(110),"Swing","A")["operations"][0]["resultat"],0)
 def test_backtest_perdant(self): self.assertLess(executer_backtest(rows(90),"Swing","A")["operations"][0]["resultat"],0)
 def test_backtest_frais_et_slippage(self): self.assertLess(executer_backtest(rows(110),"Swing","A",frais_pct=1,slippage_pct=1)["capital_final"],executer_backtest(rows(110),"Swing","A")["capital_final"])
 def test_backtest_stop(self): self.assertEqual(executer_backtest(rows(110,stop=99),"Swing","A")["operations"][0]["raison_sortie"],"stop")
 def test_backtest_objectif(self): self.assertEqual(executer_backtest(rows(110,objectif=102),"Swing","A")["operations"][0]["raison_sortie"],"objectif")
 def test_backtest_drawdown_profit_factor(self):
  r=executer_backtest(rows(90),"Swing","A"); self.assertGreater(r["drawdown_maximum_pourcentage"],0); self.assertEqual(r["profit_factor"],0)
 def test_backtest_pas_anticipation(self): self.assertEqual(executer_backtest(rows(110),"Swing","A")["operations"][0]["date_entree"],"J1")
 def test_backtest_json_non_mutation(self):
  h=rows(); avant=deepcopy(h); json.dumps(executer_backtest(h,"Swing","A"),allow_nan=False); self.assertEqual(h,avant)
 def test_core_imports_interdits_absents(self):
  code="import sys; import core.strategy_profiles,core.data_quality,core.strategy_engine,core.opportunity_ranking,core.backtest; assert not ({'streamlit','pandas','yfinance','openai'} & set(sys.modules))"; r=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True); self.assertEqual(r.returncode,0,r.stderr)
if __name__=="__main__": unittest.main()
