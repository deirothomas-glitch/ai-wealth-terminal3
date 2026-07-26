"""Tests du contrat pur de fiche d’opportunité."""

import copy
import json
import unittest

from core.opportunity_sheet import construire_fiche_opportunite


class OpportunitySheetTests(unittest.TestCase):
    def donnees(self):
        return (
            {"Catégorie": "Action", "Actif": "AAPL", "Prix": 101.5, "Variation %": 1.2, "Date données": "2026-07-26", "Score": 78, "Signal": "SURVEILLER", "Raisons": ["EMA favorable"]},
            {"symbole": "AAPL", "qualite_donnees": "bon", "points_vigilance": ["Volume absent"]},
            {"recommandation": "Surveiller", "confiance": 72, "resume": "Configuration à confirmer.", "facteurs_favorables": ["Tendance"], "facteurs_defavorables": ["Volume"], "risques": ["Risque technique"], "donnees_manquantes": ["volume"]},
            {"statut": "partiel", "risques": ["Risque de gap"], "donnees_manquantes": ["capital_reference"]},
            {"scenario_principal": "neutre"},
        )

    def test_contrat_ordonne_json_deterministe_et_non_mute(self):
        entrees = self.donnees(); avant = copy.deepcopy(entrees)
        fiche = construire_fiche_opportunite(*entrees)
        self.assertEqual(list(fiche), ["symbole", "categorie", "conclusion", "recommandation", "pourquoi", "facteurs_favorables", "facteurs_defavorables", "qualite", "marche", "analyse", "risques", "donnees_manquantes", "scenarios", "actualites", "plan_risque", "decision_finale_utilisateur", "rappel_prudence"])
        self.assertEqual(fiche, construire_fiche_opportunite(*entrees))
        self.assertEqual(entrees, avant)
        json.dumps(fiche, ensure_ascii=False, allow_nan=False)

    def test_actif_prix_date_score_decision_et_confiance_sont_transmis(self):
        fiche = construire_fiche_opportunite(*self.donnees())
        self.assertEqual(fiche["symbole"], "AAPL")
        self.assertEqual(fiche["marche"], {"prix": 101.5, "variation": 1.2, "date_donnees": "2026-07-26"})
        self.assertEqual(fiche["analyse"]["score"], 78)
        self.assertEqual(fiche["analyse"]["decision"], "Surveiller")
        self.assertEqual(fiche["analyse"]["confiance"], 72)

    def test_risques_et_manquantes_restent_distincts(self):
        fiche = construire_fiche_opportunite(*self.donnees())
        self.assertEqual(fiche["risques"], ["Risque technique", "Risque de gap"])
        self.assertEqual(fiche["donnees_manquantes"], ["volume", "risque.capital_reference"])

    def test_entrees_invalides_ne_provoquent_pas_exception(self):
        fiche = construire_fiche_opportunite(None, None, None, None, None)
        self.assertEqual(fiche["symbole"], "—")
        self.assertEqual(fiche["recommandation"], "Attendre")
        self.assertTrue(fiche["risques"])


if __name__ == "__main__": unittest.main()
