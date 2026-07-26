"""Tests du moteur pur d'analyse multi-scénarios."""

import copy
import json
import unittest

from core.scenario_engine import (
    construire_scenarios,
    construire_scenarios_depuis_contrats,
    enrichir_redaction_scenarios,
)


class ScenarioEngineTests(unittest.TestCase):
    def complet(self):
        return {
            "facteurs_favorables": ["Tendance positive", "Volume confirmé"],
            "facteurs_defavorables": ["Valorisation exigeante"],
            "risques": ["Volatilité élevée"],
            "donnees_manquantes": [],
            "conditions_invalidation": ["Rupture du support documenté"],
            "qualite": "bon",
        }

    def test_donnees_completes_contrat_json_et_confiance_elevee(self):
        resultat = construire_scenarios(self.complet(), "tendance")
        self.assertEqual(resultat["scenario_principal"], "haussier")
        self.assertFalse(resultat["donnees_partielles"])
        for nom in ("haussier", "neutre", "baissier"):
            scenario = resultat[f"scenario_{nom}"]
            self.assertEqual(scenario["niveau_confiance"], "Élevée")
            self.assertEqual(scenario["horizon"], "tendance")
        json.dumps(resultat, ensure_ascii=False, allow_nan=False)

    def test_donnees_partielles_baissent_confiance_sans_hypothese(self):
        resultat = construire_scenarios({
            "facteurs_favorables": ["RSI favorable"],
            "donnees_manquantes": ["volume", "actualites", "risque"],
        })
        self.assertTrue(resultat["donnees_partielles"])
        self.assertEqual(resultat["scenario_haussier"]["niveau_confiance"], "Faible")
        self.assertEqual(resultat["scenario_haussier"]["facteurs_defavorables"], [])
        self.assertIn("volume", resultat["scenario_haussier"]["elements_manquants"])

    def test_absence_openai_ne_change_rien(self):
        entree = self.complet()
        self.assertEqual(construire_scenarios(entree), construire_scenarios(entree))

    def test_niveaux_qualitatifs_uniquement(self):
        niveaux = set()
        for entree in ({}, self.complet(), {**self.complet(), "donnees_manquantes": ["volume"]}):
            niveaux.add(construire_scenarios(entree)["scenario_neutre"]["niveau_confiance"])
        self.assertTrue(niveaux <= {"Faible", "Modérée", "Élevée"})
        self.assertNotIn("%", str(niveaux))

    def test_invalidation_absente_est_signalee_comme_manquante(self):
        resultat = construire_scenarios(self.complet() | {"conditions_invalidation": []})
        self.assertEqual(resultat["scenario_neutre"]["conditions_invalidation"], [])
        self.assertIn("conditions_invalidation", resultat["scenario_neutre"]["elements_manquants"])

    def test_adaptateur_reutilise_decision_et_risque(self):
        resultat = construire_scenarios_depuis_contrats(
            {"facteurs_favorables": ["EMA"], "facteurs_defavorables": ["RSI"], "risques": ["Risque technique"], "donnees_manquantes": []},
            {"stop_loss": 95.0, "risques": ["Risque de gap"], "donnees_manquantes": ["capital_reference"]},
            {"qualite_donnees": "bon"},
            "Court terme",
        )
        scenario = resultat["scenario_neutre"]
        self.assertEqual(scenario["horizon"], "court")
        self.assertIn("Risque de gap", scenario["risques_identifies"])
        self.assertIn("risque.capital_reference", scenario["elements_manquants"])
        self.assertIn("95", scenario["conditions_invalidation"][0])

    def test_enrichissement_ia_modifie_seulement_resume(self):
        original = construire_scenarios(self.complet())
        avant = copy.deepcopy(original)
        enrichi = enrichir_redaction_scenarios(original, {"haussier": "Rédaction enrichie et prudente."})
        self.assertEqual(original, avant)
        self.assertEqual(enrichi["scenario_haussier"]["resume"], "Rédaction enrichie et prudente.")
        enrichi["scenario_haussier"]["resume"] = avant["scenario_haussier"]["resume"]
        self.assertEqual(enrichi, avant)

    def test_enrichissement_ia_trop_affirmatif_est_ignore(self):
        original = construire_scenarios(self.complet())
        enrichi = enrichir_redaction_scenarios(
            original,
            {"haussier": "Gain garanti et hausse certaine."},
        )
        self.assertEqual(enrichi, original)

    def test_stop_non_fini_ne_devient_pas_une_invalidation(self):
        resultat = construire_scenarios_depuis_contrats({}, {"stop_loss": float("nan")})
        self.assertEqual(resultat["scenario_neutre"]["conditions_invalidation"], [])
        self.assertIn("conditions_invalidation", resultat["scenario_neutre"]["elements_manquants"])

    def test_entree_non_valide_ne_provoque_aucune_exception(self):
        resultat = construire_scenarios(None, "inconnu")
        self.assertEqual(resultat["scenario_principal"], "neutre")
        self.assertEqual(resultat["scenario_neutre"]["niveau_confiance"], "Faible")
        self.assertEqual(resultat["scenario_neutre"]["horizon"], "swing")


if __name__ == "__main__":
    unittest.main()
