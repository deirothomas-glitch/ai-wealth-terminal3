import copy,json,unittest
from core.analysis_context import construire_contexte_analyse
from core.ai_response_validation import FIELDS,valider_reponse_ia
class AnalysisContextAITests(unittest.TestCase):
    def test_contexte_complet_limite_json_non_mutation(self):
        news=[{"titre":str(i),"score":float(i)} for i in range(12)];original=copy.deepcopy(news);result=construire_contexte_analyse(actif={"symbole":"AAPL"},marche={},technique={"score":70},strategie={},decision={},risque={},qualite_donnees={},actualites=news,sentiment_actualites={},portefeuille=None,limites=["Limite"],max_actualites=5)
        self.assertEqual(len(result["actualites"]),5);self.assertEqual(news,original);json.dumps(result,allow_nan=False);self.assertEqual(list(result),["actif","marche","technique","strategie","decision","risque","qualite_donnees","actualites","sentiment_actualites","portefeuille","limites"])
    def test_contexte_valeurs_non_finies_sures(self):
        result=construire_contexte_analyse(technique={"x":float("nan"),"y":float("inf")});self.assertIsNone(result["technique"]["x"]);json.dumps(result,allow_nan=False)
    def valide(self):return {"resume":"Résumé prudent","contexte_marche":"Faits","lecture_technique":"Interprétation","lecture_actualites":"Lecture","scenario_favorable":"Scénario","scenario_defavorable":"Scénario inverse","conditions_confirmation":["C"]*12,"conditions_invalidation":["I"],"risques_principaux":["R"],"points_a_surveiller":["P"],"niveau_confiance":"moderee","limites":["L"],"decision_finale_utilisateur":False,"inconnu":"x"}
    def test_validation_valide_champs_inconnus_listes_bornees(self):
        result=valider_reponse_ia(self.valide());self.assertEqual(list(result),list(FIELDS));self.assertEqual(len(result["conditions_confirmation"]),8);self.assertIs(result["decision_finale_utilisateur"],True);self.assertNotIn("inconnu",result)
    def test_validation_json_invalide_vide_manquant_confiance(self):
        for raw in (None,"", "{",{}, {"resume":"OK","niveau_confiance":"certaine"}):
            result=valider_reponse_ia(raw);self.assertIs(result["decision_finale_utilisateur"],True);self.assertIn(result["niveau_confiance"],{"faible","moderee","elevee"})
    def test_formulation_interdite_retourne_contrat_sur(self):
        value=self.valide();value["resume"]="Achetez maintenant";result=valider_reponse_ia(value);self.assertEqual(result["resume"],"Analyse IA indisponible.")
if __name__=="__main__":unittest.main()
