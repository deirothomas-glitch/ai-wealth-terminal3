"""Tests du modèle pur du Cockpit Investisseur."""

import copy
import json
import unittest

from core.cockpit import construire_cockpit


class CockpitTests(unittest.TestCase):
    def donnees(self):
        return {
            "indices": [{"nom": "CAC 40", "variation": 1.0}],
            "cryptos": [{"nom": "Bitcoin", "variation": -0.2}],
            "opportunites": [{
                "symbole": "AAPL", "score_global": 82.25,
                "plan_risque_disponible": False, "qualite_donnees": "bon",
                "strategie": "Swing", "raisons_principales": ["Momentum favorable"],
            }],
            "positions": [{
                "identifiant": "p1", "symbole": "AAPL", "quantite": 2,
                "prix_entree": 100, "date_ouverture": "2026-01-01",
            }],
            "prix_portefeuille": {"AAPL": 110},
            "journal": [{"type_evenement": "cloture", "gain_perte_realise": -5}],
            "alertes": [{
                "identifiant": "p1:stop", "symbole": "AAPL", "niveau": "vigilance",
                "categorie": "stop", "titre": "Prix proche du stop", "message": "À surveiller",
            }],
            "actualites": [{"sentiment": {"sentiment": "positif"}}],
            "portefeuille_charge": True,
            "openai_disponible": True,
            "mise_a_jour": "26/07/2026 12:00",
        }

    def test_contrat_complet_deterministe_json_et_non_mutation(self):
        entree = self.donnees(); avant = copy.deepcopy(entree)
        premier = construire_cockpit(**entree); second = construire_cockpit(**entree)
        self.assertEqual(premier, second)
        self.assertEqual(entree, avant)
        self.assertEqual(list(premier), ["bandeau", "marche", "portefeuille", "opportunites", "alertes", "scenario_principal", "briefing", "agenda"])
        json.dumps(premier, ensure_ascii=False, allow_nan=False)

    def test_bandeau_repose_uniquement_sur_disponibilites_reelles(self):
        cockpit = construire_cockpit(mise_a_jour="maintenant")
        self.assertEqual(cockpit["bandeau"]["connexion"], "Données indisponibles")
        self.assertEqual(cockpit["bandeau"]["yahoo"], "Indisponible")
        self.assertEqual(cockpit["bandeau"]["openai"], "Non configuré")
        self.assertEqual(cockpit["bandeau"]["qualite"], "Indisponible")

    def test_marche_sans_volatilite_ne_linvente_pas(self):
        cockpit = construire_cockpit(**self.donnees())
        self.assertEqual(cockpit["marche"]["tendance"], "Orientation positive")
        self.assertEqual(cockpit["marche"]["sentiment"], "Plutôt positif")
        self.assertEqual(cockpit["marche"]["volatilite"], "Indisponible")

    def test_resume_portefeuille_utilise_prix_et_journal_existants(self):
        cockpit = construire_cockpit(**self.donnees())
        portefeuille = cockpit["portefeuille"]
        self.assertEqual(portefeuille["valeur_totale"], 220.0)
        self.assertEqual(portefeuille["variation"], 10.0)
        self.assertEqual(portefeuille["positions_ouvertes"], 1)
        self.assertEqual(portefeuille["positions_cloturees"], 1)
        self.assertEqual(portefeuille["gains"], 0)
        self.assertEqual(portefeuille["pertes"], -5.0)
        self.assertEqual(portefeuille["exposition"], 200.0)

    def test_scenario_cockpit_signale_volatilite_non_calculee(self):
        cockpit = construire_cockpit(**self.donnees())
        scenario = cockpit["scenario_principal"]["scenario_haussier"]
        self.assertIn("volatilite_globale", scenario["elements_manquants"])
        self.assertTrue(cockpit["scenario_principal"]["donnees_partielles"])

    def test_portefeuille_non_charge_reste_indisponible(self):
        cockpit = construire_cockpit(positions=[], prix_portefeuille={}, journal=[])
        self.assertTrue(all(valeur is None for valeur in cockpit["portefeuille"].values()))
        self.assertEqual(cockpit["briefing"]["resume_portefeuille"], "Indisponible")

    def test_top_cinq_et_resume_court(self):
        entree = self.donnees(); entree["opportunites"] *= 7
        cockpit = construire_cockpit(**entree)
        self.assertEqual(len(cockpit["opportunites"]), 5)
        self.assertEqual(cockpit["opportunites"][0]["resume"], "Momentum favorable")
        self.assertEqual(cockpit["opportunites"][0]["risque"], "À compléter")

    def test_alertes_prioritaires_filtrees_et_dedupliquees(self):
        entree = self.donnees()
        entree["alertes"] += [
            dict(entree["alertes"][0]),
            {"identifiant": "info", "symbole": "AAPL", "niveau": "information", "categorie": "risque", "titre": "Stop enregistré", "message": "Info"},
            {"identifiant": "objectif", "symbole": "MSFT", "niveau": "information", "categorie": "objectif", "titre": "Objectif atteint", "message": "Revoir"},
        ]
        alertes = construire_cockpit(**entree)["alertes"]
        self.assertEqual([x["symbole"] for x in alertes], ["AAPL", "MSFT"])

    def test_agenda_extensible_sans_evenement_invente(self):
        agenda = construire_cockpit()["agenda"]
        self.assertEqual(agenda["titre"], "Évènements de marché")
        self.assertEqual(agenda["evenements"], [])
        self.assertIn("Aucun calendrier", agenda["message"])


if __name__ == "__main__":
    unittest.main()
