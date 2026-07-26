import json,unittest
from core.daily_briefing import construire_briefing
class DailyBriefingTests(unittest.TestCase):
    def test_sans_donnees_contrat_json_deterministe(self):
        result=construire_briefing(date_generation="2026-07-26");self.assertEqual(result,construire_briefing(date_generation="2026-07-26"));self.assertEqual(result["donnees_manquantes"],["indices","scanner","actualites"]);json.dumps(result,allow_nan=False)
    def test_avec_indices_opportunites_positions_actualites(self):
        result=construire_briefing(indices=[{"nom":"CAC","variation":1.2}],opportunites=[{"symbole":"AAPL","decision":"Surveiller"}],positions=[{"message":"Stop proche"}],actualites=[{"titre":"News"}],qualite={"niveau":"partiel"},date_generation="2026-07-26");self.assertIn("CAC",result["resume_marche"][0]);self.assertEqual(result["opportunites_a_surveiller"][0]["symbole"],"AAPL");self.assertIn("Stop proche",result["risques_du_jour"]);self.assertIn("qualité",result["risques_du_jour"][-1])
    def test_limites_et_ordre_stable(self):
        result=construire_briefing(opportunites=[{"symbole":str(i)} for i in range(9)],actualites=[{"titre":str(i)} for i in range(9)],date_generation="x");self.assertEqual(len(result["opportunites_a_surveiller"]),5);self.assertEqual(len(result["actualites_principales"]),5)
if __name__=="__main__":unittest.main()
