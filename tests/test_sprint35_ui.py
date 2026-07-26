import copy,unittest
from unittest.mock import patch
from ui.news_card import afficher_actualites_normalisees
from ui.news_sentiment_card import afficher_sentiment_actualites
from ui.daily_briefing_card import afficher_briefing
from ui.ai_analysis_card import afficher_analyse_ia
class Context:
    def __enter__(self):return self
    def __exit__(self,*a):return False
class St:
    def __init__(self):self.calls=[]
    def __getattr__(self,name):
        def call(*args,**kwargs):self.calls.append((name,args,kwargs));return Context()
        return call
class Sprint35UITests(unittest.TestCase):
    def test_news_card_source_date_lien_sans_none_brut(self):
        st=St();articles=[{"titre":"Titre","source":"Reuters","date_publication":"2026-01-01","resume":"Résumé","url":"https://example.com","pertinence":{"niveau":"forte"}}]
        with patch("ui.news_card.st",st):afficher_actualites_normalisees(articles)
        text=str(st.calls);self.assertIn("Reuters",text);self.assertIn("source originale",text);self.assertNotIn("None",text)
    def test_news_card_vide(self):
        st=St()
        with patch("ui.news_card.st",st):afficher_actualites_normalisees([])
        self.assertEqual(st.calls[0][0],"info")
    def test_sentiment_prudent(self):
        st=St()
        with patch("ui.news_sentiment_card.st",st):afficher_sentiment_actualites({"sentiment":"positif","confiance":"faible","limites":[]})
        self.assertIn("ne constitue pas une prévision",str(st.calls))
    def test_briefing_sans_dictionnaire_brut(self):
        st=St();brief={"date_generation":"2026-01-01","resume_marche":["CAC : +1%"],"opportunites_a_surveiller":[{"symbole":"AAPL","decision":"Surveiller"}],"risques_du_jour":["Risque"],"donnees_manquantes":[]}
        with patch("ui.daily_briefing_card.st",st):afficher_briefing(brief)
        self.assertNotIn("{'symbole'",str(st.calls))
    def test_ai_card_contrat_sur(self):
        st=St();analysis={"resume":"Résumé","risques_principaux":["Risque"],"niveau_confiance":"faible","decision_finale_utilisateur":True}
        with patch("ui.ai_analysis_card.st",st):afficher_analyse_ia(analysis)
        self.assertIn("décision finale",str(st.calls))
    def test_non_mutation(self):
        value=[{"titre":"Titre","source":"S","date_publication":None,"resume":"","url":"","pertinence":{}}];original=copy.deepcopy(value);st=St()
        with patch("ui.news_card.st",st):afficher_actualites_normalisees(value)
        self.assertEqual(value,original)
if __name__=="__main__":unittest.main()
