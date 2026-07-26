import json,tempfile,unittest
from pathlib import Path
from services.news_cache import charger_cache_actualites,sauvegarder_cache_actualites
class NewsCacheTests(unittest.TestCase):
    def test_absent_vide_invalide_et_conservation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cache.json";self.assertEqual(charger_cache_actualites(p)[0]["donnees"],[]);p.write_text("");self.assertEqual(charger_cache_actualites(p)[0]["donnees"],[]);p.write_text("{bad");data,error=charger_cache_actualites(p);self.assertTrue(error);self.assertEqual(p.read_text(),"{bad")
    def test_ecriture_atomique_json_strict(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cache.json";sauvegarder_cache_actualites([{"titre":"é"}],p);data,error=charger_cache_actualites(p);self.assertIsNone(error);self.assertEqual(data["donnees"],[{"titre":"é"}]);json.loads(p.read_text())
if __name__=="__main__":unittest.main()
