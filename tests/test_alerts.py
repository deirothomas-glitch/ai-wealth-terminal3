"""Tests du moteur pur d'alertes d'analyse."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from core.alerts import construire_alertes


def score():
    return {"score": 70, "signal": "SURVEILLER", "raisons": ["Raison"], "ventilation": []}
def decision(recommandation="Surveiller", manquantes=None):
    return {"recommandation": recommandation, "confiance": 80, "resume": "Résumé", "facteurs_favorables": ["Facteur favorable"], "facteurs_defavorables": ["Facteur défavorable"], "facteurs_neutres": [], "risques": ["Risque technique"], "donnees_manquantes": [] if manquantes is None else manquantes, "action_suggeree": "Réévaluer.", "decision_finale_utilisateur": True}
def plan(statut="disponible", manquantes=None, risques=None):
    return {"statut": statut, "donnees_manquantes": [] if manquantes is None else manquantes, "risques": [] if risques is None else risques, "decision_finale_utilisateur": "Décision utilisateur."}

class AlertsTests(unittest.TestCase):
    def test_import_sortie_liste_et_absence_alerte(self):
        self.assertTrue(callable(construire_alertes))
        self.assertEqual(construire_alertes(score(), decision("Acheter"), plan()), [])

    def test_contrat_exact_types_json_et_json_strict(self):
        resultat = construire_alertes(score(), decision(), plan("partiel", ["capital_reference"]))
        cles = {"identifiant", "niveau", "categorie", "titre", "message", "facteurs", "action_suggeree", "decision_finale_utilisateur"}
        for alerte in resultat:
            self.assertEqual(set(alerte), cles)
            self.assertIn(alerte["niveau"], {"information", "vigilance", "attention"})
            self.assertIn(alerte["categorie"], {"donnees", "decision", "risque"})
            self.assertIs(alerte["decision_finale_utilisateur"], True)
        json.dumps(resultat, ensure_ascii=False, allow_nan=False)

    def test_determinisme_non_mutation_et_maximum(self):
        entrees = [score(), decision(manquantes=["RSI"]), plan("indisponible", ["atr"], ["Risque"])]
        copies = copy.deepcopy(entrees)
        premier = construire_alertes(*entrees)
        self.assertEqual(premier, construire_alertes(*entrees))
        self.assertEqual(entrees, copies)
        self.assertLessEqual(len(premier), 3)

    def test_ordre_donnees_decision_risque(self):
        resultat = construire_alertes(score(), decision(manquantes=["RSI"]), plan("indisponible", ["atr"]))
        self.assertEqual([a["categorie"] for a in resultat], ["donnees", "decision", "risque"])

    def test_contrats_absents_ou_mal_formes(self):
        cas = ((None, None, None), ([], "x", 3), ({}, {}, {}))
        for entree in cas:
            with self.subTest(entree=entree):
                resultat = construire_alertes(*entree)
                self.assertEqual(resultat[0]["categorie"], "donnees")
                self.assertEqual(resultat[0]["niveau"], "attention")

    def test_score_absent_ou_mal_forme(self):
        for valeur in (None, {}, {"score": float("nan")}, {"score": True}):
            with self.subTest(valeur=valeur):
                self.assertEqual(construire_alertes(valeur, decision(), plan())[0]["categorie"], "donnees")

    def test_recommandations_sans_recalcul(self):
        attendus = {"Surveiller": "vigilance", "Attendre": "information", "Éviter": "attention", "Inconnue": "vigilance"}
        for recommandation, niveau in attendus.items():
            with self.subTest(recommandation=recommandation):
                alerte = next(a for a in construire_alertes(score(), decision(recommandation), plan()) if a["categorie"] == "decision")
                self.assertEqual(alerte["niveau"], niveau)
                if recommandation == "Éviter": self.assertNotIn("vendre", str(alerte).lower())

    def test_plan_disponible_partiel_indisponible(self):
        cas = (("disponible", ["Risque"], "information"), ("partiel", [], "vigilance"), ("indisponible", [], "attention"))
        for statut, risques, niveau in cas:
            with self.subTest(statut=statut):
                alertes = construire_alertes(score(), decision(), plan(statut, risques=risques))
                alerte = next(a for a in alertes if a["categorie"] == "risque")
                self.assertEqual(alerte["niveau"], niveau)
                if statut == "indisponible": self.assertNotIn("stop_loss", alerte)

    def test_donnees_manquantes_facteurs_et_risques_transportes(self):
        resultat = construire_alertes(score(), decision(manquantes=["RSI"]), plan("partiel", ["capital_reference"], ["Gap possible"]))
        donnees = resultat[0]
        self.assertIn("RSI", str(donnees["facteurs"]))
        decision_a = next(a for a in resultat if a["categorie"] == "decision")
        self.assertIn("Facteur favorable", decision_a["facteurs"])
        self.assertIn("Facteur défavorable", decision_a["facteurs"])
        risque = next(a for a in resultat if a["categorie"] == "risque")
        self.assertIn("Gap possible", risque["facteurs"])

    def test_plan_partiel_explique_absence_de_taille(self):
        alerte = construire_alertes(score(), decision(), plan("partiel", ["capital_reference", "risque_max_pct"]))[-1]
        self.assertIn("taille de position", alerte["message"])

    def test_aucune_promesse_ordre_ou_formule_dupliquee(self):
        source = (Path(__file__).resolve().parents[1] / "core/alerts.py").read_text(encoding="utf-8").lower()
        for interdit in ("calculer_score", "construire_decision", "calculer_atr", "construire_plan_risque", "distance_stop", "stop_calcule", "taille_calculee", "achat garanti", "vente obligatoire", "gain garanti", "profit certain", "sans risque", "opportunité urgente", "achetez maintenant", "vendez maintenant"):
            self.assertNotIn(interdit, source)

    def test_import_isole_bibliotheque_standard_uniquement(self):
        code = "import sys; import core.alerts; interdits={'streamlit','pandas','numpy','yfinance','openai','scoring','core.decision','core.risk'}; charges=interdits.intersection(sys.modules); assert not charges, charges"
        resultat = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)

if __name__ == "__main__": unittest.main()
