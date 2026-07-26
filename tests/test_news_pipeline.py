import copy,json,unittest
from datetime import datetime,timezone
from core.news_normalization import normaliser_actualite
from core.news_deduplication import dedupliquer_actualites
from core.news_quality import evaluer_qualite_actualite
from core.news_relevance import evaluer_pertinence_actualite
from core.news_sentiment import analyser_sentiment_actualite
from services.news_aggregator import agreger_actualites
class Source:
    nom="Test"
    def __init__(self,data=None,error=False):self.data=data or [];self.error=error;self.calls=0
    def fetch(self,symbole,limite):
        self.calls+=1
        if self.error:raise RuntimeError("secret detail")
        return self.data[:limite]
def article(**kw):
    base={"titre":"Apple annonce une croissance record","resume":"Le bénéfice progresse malgré un risque de dette.","source":"Reuters","url":"https://example.com/a?utm_source=x","date_publication":"2026-01-10T10:00:00+00:00","symboles":["AAPL"],"categories":["actions"],"langue":"fr","image_url":None};base.update(kw);return base
class NewsPipelineTests(unittest.TestCase):
    def test_normalisation_contrat_json_non_mutation(self):
        raw=article();copy_=copy.deepcopy(raw);result=normaliser_actualite(raw)
        self.assertEqual(list(result),["identifiant","titre","resume","source","url","date_publication","symboles","categories","langue","image_url"]);json.dumps(result,ensure_ascii=False,allow_nan=False);self.assertEqual(raw,copy_)
    def test_normalisation_champs_absents_date_url_symboles(self):
        result=normaliser_actualite({"date":"invalide","url":"javascript:alert(1)"},"bad symbol!")
        self.assertEqual(result["titre"],"");self.assertEqual(result["source"],"");self.assertEqual(result["url"],"");self.assertIsNone(result["date_publication"]);self.assertEqual(result["symboles"],[])
    def test_dedup_url_titre_similaire_et_ordre(self):
        a=normaliser_actualite(article());b=normaliser_actualite(article(url="https://example.com/a?utm_medium=y",titre="Apple annonce une croissance record !"));c=normaliser_actualite(article(url="https://example.com/c",titre="Tesla ouvre une usine"))
        original=copy.deepcopy([a,b,c]);result=dedupliquer_actualites([a,b,c]);self.assertEqual([x["titre"] for x in result],[a["titre"],c["titre"]]);self.assertEqual([a,b,c],original)
    def test_dedup_articles_differents(self):
        titres=["Tesla ouvre une usine au Mexique","La BCE maintient ses taux directeurs","Bitcoin adopte une nouvelle mise à jour"]
        values=[normaliser_actualite(article(url=f"https://x.test/{i}",titre=titre)) for i,titre in enumerate(titres)];self.assertEqual(len(dedupliquer_actualites(values)),3)
    def test_qualite_complete_absences_ancien_borne_deterministe(self):
        ref=datetime(2026,2,20,tzinfo=timezone.utc);good=evaluer_qualite_actualite(normaliser_actualite(article()),ref);self.assertTrue(good["valide"]);self.assertIn("Article ancien.",good["avertissements"])
        bad=evaluer_qualite_actualite(normaliser_actualite({}),ref);self.assertEqual(bad["niveau"],"insuffisant");self.assertGreaterEqual(bad["score_qualite"],0);self.assertLessEqual(bad["score_qualite"],100);self.assertEqual(bad,evaluer_qualite_actualite(normaliser_actualite({}),ref))
    def test_source_inconnue_formulation_neutre(self):
        q=evaluer_qualite_actualite(normaliser_actualite(article(source="Blog nouveau")));self.assertNotIn("fausse",str(q).lower())
    def test_pertinence_symbole_nom_general_non_pertinent(self):
        a=normaliser_actualite(article());self.assertEqual(evaluer_pertinence_actualite(a,"AAPL","Apple")["niveau"],"forte")
        general=normaliser_actualite(article(titre="Le marché évolue",resume="Actualité économique générale",symboles=[]));self.assertEqual(evaluer_pertinence_actualite(general,"NVDA","Nvidia")["niveau"],"faible")
        self.assertEqual(evaluer_pertinence_actualite(general,"NVDA","Nvidia"),evaluer_pertinence_actualite(general,"NVDA","Nvidia"))
    def test_sentiments_et_absence_prediction(self):
        cases=(("croissance record bénéfice solide","positif"),("chute perte dette faible","negatif"),("croissance record mais perte dette","mixte"),("","indetermine"))
        for text,expected in cases:self.assertEqual(analyser_sentiment_actualite({"titre":text})["sentiment"],expected)
        result=analyser_sentiment_actualite({"titre":"croissance"});self.assertIn(result["confiance"],{"faible","moderee","elevee"});self.assertIn("ne prédit pas",result["limites"][0])
    def test_aggregateur_isole_erreur_un_appel_et_enrichit(self):
        ok=Source([article(),article()]);bad=Source(error=True);result,errors=agreger_actualites([ok,bad],"AAPL",limite=5);self.assertEqual(ok.calls,1);self.assertEqual(bad.calls,1);self.assertEqual(len(result),1);self.assertTrue(errors);self.assertTrue({"qualite","pertinence","sentiment"}<=set(result[0]))
if __name__=="__main__":unittest.main()
