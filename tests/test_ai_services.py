import json,unittest
from services.ai_client import appeler_modele,obtenir_cle_api
from services.ai_market_analysis import analyser_contexte_marche
class Message: pass
class Factory:
    calls=[];content='{}';error=None
    def __init__(self,**kwargs):self.kwargs=kwargs;self.chat=self;self.completions=self
    def create(self,**kwargs):
        Factory.calls.append(kwargs)
        if Factory.error:raise Factory.error
        m=Message();m.content=Factory.content;c=Message();c.message=m;r=Message();r.choices=[c];return r
class RateLimitError(Exception):pass
class AIServicesTests(unittest.TestCase):
    def setUp(self):Factory.calls=[];Factory.error=None;Factory.content=json.dumps({"resume":"Analyse prudente","niveau_confiance":"faible"})
    def test_cle_absente_aucun_appel(self):
        self.assertIsNone(obtenir_cle_api({},{}));result=appeler_modele([],api_key=None,client_factory=Factory);self.assertFalse(result["ok"]);self.assertEqual(Factory.calls,[])
    def test_reponse_valide_modele_centralise(self):
        result=appeler_modele([{"role":"user","content":"x"}],api_key="test",client_factory=Factory);self.assertTrue(result["ok"]);self.assertEqual(len(Factory.calls),1);self.assertIn("model",Factory.calls[0]);self.assertEqual(Factory.calls[0]["response_format"],{"type":"json_object"})
    def test_erreur_reseau_limite_et_secret_non_expose(self):
        for error in (RuntimeError("clé-secrète"),RateLimitError("clé-secrète")):
            Factory.error=error;result=appeler_modele([],api_key="clé-secrète",client_factory=Factory);self.assertFalse(result["ok"]);self.assertNotIn("clé-secrète",result["erreur"])
    def test_analyse_contextuelle_validee(self):
        result=analyser_contexte_marche({"actif":{"symbole":"AAPL"}},"Risques ?",api_key="test",client_factory=Factory);self.assertEqual(result["resume"],"Analyse prudente");self.assertIs(result["decision_finale_utilisateur"],True)
if __name__=="__main__":unittest.main()
