"""Tests de qualité globale et d’état factuel des sources."""

import copy
import json
import unittest

from core.data_quality import construire_etat_sources, evaluer_qualite_globale


class DataQualityGlobalTests(unittest.TestCase):
    def test_donnees_completes_donnent_qualite_bonne(self):
        resultat = evaluer_qualite_globale({
            "Marché": {"disponible": True, "complet": True},
            "Portefeuille": {"disponible": True, "complet": True},
        })
        self.assertEqual(resultat["niveau"], "Bonne")
        self.assertEqual([x["statut"] for x in resultat["details"]], ["Complètes", "Complètes"])

    def test_donnees_partielles_donnent_qualite_moyenne(self):
        resultat = evaluer_qualite_globale({
            "Marché": {"disponible": True, "complet": False},
            "Portefeuille": {"disponible": True, "complet": True},
        })
        self.assertEqual(resultat["niveau"], "Moyenne")
        self.assertEqual(resultat["details"][0]["statut"], "Partielles")

    def test_donnees_absentes_donnent_qualite_faible(self):
        resultat = evaluer_qualite_globale({
            "Marché": {"disponible": False},
            "Portefeuille": {"disponible": False},
        })
        self.assertEqual(resultat["niveau"], "Faible")
        self.assertTrue(all(x["statut"] == "Absentes" for x in resultat["details"]))

    def test_donnees_anciennes_uniquement_si_information_fournie(self):
        anciennes = evaluer_qualite_globale({"Marché": {"disponible": True, "complet": True, "ancien": True}})
        inconnues = evaluer_qualite_globale({"Marché": {"disponible": True, "complet": True}})
        self.assertEqual(anciennes["details"][0]["statut"], "Anciennes")
        self.assertEqual(inconnues["details"][0]["statut"], "Complètes")

    def test_entrees_invalides_deterministes_json_et_non_mutees(self):
        entree = {"Marché": None, "": {"disponible": True}, "Divers": {"disponible": float("nan")}}
        avant = copy.deepcopy(entree)
        premier = evaluer_qualite_globale(entree)
        self.assertEqual(premier, evaluer_qualite_globale(entree))
        self.assertEqual(entree, avant)
        json.dumps(premier, ensure_ascii=False, allow_nan=False)

    def test_sources_distinguent_configuration_et_connexion_reelle(self):
        etat = construire_etat_sources(
            yahoo_interroge=False,
            yahoo_disponible=True,
            openai_configure=True,
            stockage_charge=True,
        )
        self.assertEqual(etat["Yahoo Finance"]["etat"], "Non vérifié")
        self.assertEqual(etat["OpenAI"]["etat"], "Configuré")
        self.assertIn("aucune connexion n’est déduite", etat["OpenAI"]["detail"])
        self.assertEqual(etat["Stockage local"]["etat"], "Chargé")

    def test_yahoo_interroge_sans_donnee_est_indisponible(self):
        etat = construire_etat_sources(yahoo_interroge=True, yahoo_disponible=False)
        self.assertEqual(etat["Yahoo Finance"]["etat"], "Indisponible")


if __name__ == "__main__":
    unittest.main()
