"""Contrat exécutable du moteur de décision technique expliquée."""

import copy
import json
import subprocess
import sys
import unittest

from core.decision import (
    CRITERES_ATTENDUS,
    FACTEUR_REPLI,
    ORDRE_CLES_SORTIE,
    RECOMMANDATIONS_AUTORISEES,
    RISQUES_PERMANENTS,
    construire_decision,
)


def ventilation(contributions, raisons=None):
    raisons = raisons or {}
    resultat = [{
        "critere": "Score de base",
        "valeur": 50,
        "contribution": 50,
        "raison": "Point de départ neutre",
    }]
    for critere, contribution in zip(CRITERES_ATTENDUS, contributions):
        resultat.append({
            "critere": critere,
            "valeur": 1.0,
            "contribution": contribution,
            "raison": raisons.get(critere, f"Raison {critere}"),
        })
    return resultat


def score_complet(score=60, contributions=(10, 10, 10, 5, 10),
                   signal="SURVEILLER"):
    return {
        "score": score,
        "signal": signal,
        "raisons": ["Raison technique"],
        "prix": 100.0,
        "ema20": 99.0,
        "rsi": 55.0,
        "ventilation": ventilation(contributions),
    }


def toutes_les_chaines(objet):
    if isinstance(objet, str):
        return [objet]
    if isinstance(objet, dict):
        return [texte for valeur in objet.values()
                for texte in toutes_les_chaines(valeur)]
    if isinstance(objet, list):
        return [texte for valeur in objet for texte in toutes_les_chaines(valeur)]
    return []


class DecisionTests(unittest.TestCase):
    def verifier_invariants(self, resultat):
        self.assertEqual(tuple(resultat), ORDRE_CLES_SORTIE)
        self.assertIn(resultat["recommandation"], RECOMMANDATIONS_AUTORISEES)
        self.assertIs(type(resultat["confiance"]), int)
        self.assertGreaterEqual(resultat["confiance"], 0)
        self.assertLessEqual(resultat["confiance"], 100)
        self.assertIs(resultat["decision_finale_utilisateur"], True)
        self.assertEqual(resultat["risques"][:2], list(RISQUES_PERMANENTS))
        self.assertTrue(resultat["risques"])
        self.assertTrue(
            resultat["facteurs_favorables"]
            or resultat["facteurs_defavorables"]
            or resultat["facteurs_neutres"]
        )
        json.dumps(resultat, ensure_ascii=False, allow_nan=False)

    def test_01_donnees_insuffisantes_reelles(self):
        entree = {
            "score": 0,
            "signal": "DONNÉES INSUFFISANTES",
            "raisons": [],
            "prix": 0.0,
            "ema20": 0.0,
            "rsi": 50.0,
            "ventilation": [
                {
                    "critere": "Score de base",
                    "valeur": 50,
                    "contribution": 50,
                    "raison": "Base théorique non appliquée : données insuffisantes",
                },
                {
                    "critere": "Données insuffisantes",
                    "valeur": None,
                    "contribution": -50,
                    "raison": "Score neutralisé faute de données exploitables",
                },
            ],
        }
        resultat = construire_decision(entree)
        self.assertEqual(resultat["recommandation"], "Attendre")
        self.assertEqual(resultat["confiance"], 0)
        self.assertEqual(
            resultat["facteurs_neutres"],
            ["Score neutralisé faute de données exploitables"],
        )
        self.assertEqual(resultat["facteurs_defavorables"], [])
        self.assertEqual(
            resultat["donnees_manquantes"], list(CRITERES_ATTENDUS)
        )
        self.verifier_invariants(resultat)

    def test_02_score_tres_eleve_ne_produit_pas_acheter(self):
        resultat = construire_decision(score_complet(90, signal="ACHAT"))
        self.assertEqual(resultat["recommandation"], "Surveiller")
        self.assertEqual(resultat["confiance"], 90)
        self.assertEqual(len(resultat["facteurs_favorables"]), 5)
        self.assertNotEqual(resultat["recommandation"], "Acheter")

    def test_03_score_intermediaire(self):
        resultat = construire_decision(score_complet(60))
        self.assertEqual(resultat["recommandation"], "Surveiller")
        self.assertEqual(resultat["confiance"], 90)

    def test_04_zone_attente(self):
        resultat = construire_decision(score_complet(45))
        self.assertEqual(resultat["recommandation"], "Attendre")
        self.assertEqual(resultat["confiance"], 90)
        self.assertEqual(
            resultat["action_suggeree"],
            "Ne rien faire pour le moment et attendre un signal technique plus clair.",
        )

    def test_05_score_faible_signifie_eviter_pas_vendre(self):
        resultat = construire_decision(
            score_complet(30, (-10, -10, -10, -5, -10), "VENTE")
        )
        self.assertEqual(resultat["recommandation"], "Éviter")
        self.assertEqual(resultat["confiance"], 90)
        sortie = " ".join(toutes_les_chaines(resultat)).lower()
        self.assertNotIn("vendre", sortie)
        self.assertNotIn("vente", sortie)

    def test_06_contributions_coherentes_positives(self):
        resultat = construire_decision(
            score_complet(80, (10, 10, 10, 5, 10))
        )
        self.assertEqual(len(resultat["facteurs_favorables"]), 5)
        self.assertEqual(resultat["facteurs_defavorables"], [])
        self.assertEqual(resultat["confiance"], 90)

    def test_07_contributions_coherentes_negatives(self):
        resultat = construire_decision(
            score_complet(30, (-10, -10, -10, -5, -10), "VENTE")
        )
        self.assertEqual(len(resultat["facteurs_defavorables"]), 5)
        self.assertEqual(resultat["facteurs_favorables"], [])
        self.assertEqual(resultat["confiance"], 90)

    def test_08_contributions_contradictoires(self):
        resultat = construire_decision(
            score_complet(60, (10, 10, -10, -10, 0))
        )
        self.assertEqual(resultat["recommandation"], "Surveiller")
        self.assertEqual(resultat["confiance"], 50)
        self.assertEqual(len(resultat["facteurs_favorables"]), 2)
        self.assertEqual(len(resultat["facteurs_defavorables"]), 2)
        self.assertEqual(len(resultat["facteurs_neutres"]), 1)
        self.assertEqual(
            resultat["risques"][-1],
            "Les critères techniques se contredisent fortement.",
        )

    def test_09_criteres_tous_neutres(self):
        resultat = construire_decision(score_complet(50, (0, 0, 0, 0, 0)))
        self.assertEqual(resultat["recommandation"], "Attendre")
        self.assertEqual(resultat["confiance"], 35)
        self.assertEqual(len(resultat["facteurs_neutres"]), 5)
        self.assertEqual(
            resultat["action_suggeree"],
            "Ne rien faire pour le moment et attendre une direction technique plus claire.",
        )

    def test_10_ventilation_partielle_trois_criteres(self):
        entree = score_complet(80)
        entree["ventilation"] = entree["ventilation"][:4]
        resultat = construire_decision(entree)
        self.assertEqual(resultat["recommandation"], "Surveiller")
        self.assertEqual(resultat["confiance"], 76)
        self.assertEqual(
            resultat["donnees_manquantes"],
            ["Bandes de Bollinger", "Volume"],
        )

    def test_11_ventilation_trop_partielle(self):
        entree = score_complet(80)
        entree["ventilation"] = entree["ventilation"][:3]
        resultat = construire_decision(entree)
        self.assertEqual(resultat["recommandation"], "Attendre")
        self.assertEqual(resultat["confiance"], 40)
        self.assertNotEqual(resultat["recommandation"], "Acheter")

    def test_12_ventilation_vide(self):
        entree = score_complet(80)
        entree["ventilation"] = []
        resultat = construire_decision(entree)
        self.assertEqual(resultat["recommandation"], "Attendre")
        self.assertEqual(resultat["confiance"], 0)
        self.assertEqual(resultat["facteurs_neutres"], [FACTEUR_REPLI])

    def test_13_champ_inconnu_supplementaire_ignore(self):
        entree = score_complet()
        attendu = construire_decision(entree)
        entree["nouveau_champ"] = {"libre": True}
        self.assertEqual(construire_decision(entree), attendu)

    def test_14_critere_inconnu_ignore(self):
        entree = score_complet()
        attendu = construire_decision(entree)
        entree["ventilation"].insert(2, {
            "critere": "Critère futur",
            "valeur": 1,
            "contribution": -100,
            "raison": "Doit être ignoré",
        })
        self.assertEqual(construire_decision(entree), attendu)

    def test_15_critere_duplique_premier_valide_conserve(self):
        entree = score_complet()
        entree["ventilation"].append({
            "critere": "RSI",
            "valeur": 2,
            "contribution": -10,
            "raison": "Doublon défavorable",
        })
        resultat = construire_decision(entree)
        self.assertEqual(resultat["confiance"], 85)
        self.assertIn("Raison RSI", resultat["facteurs_favorables"])
        self.assertNotIn("Doublon défavorable", resultat["facteurs_defavorables"])

    def test_16_raison_absente_utilise_critere(self):
        entree = score_complet()
        entree["ventilation"][1].pop("raison")
        resultat = construire_decision(entree)
        self.assertEqual(resultat["confiance"], 87)
        self.assertEqual(resultat["facteurs_favorables"][0], "Tendance EMA 20")

    def test_17_contribution_invalide(self):
        entree = score_complet()
        entree["ventilation"][1]["contribution"] = "invalide"
        resultat = construire_decision(entree)
        self.assertEqual(resultat["confiance"], 78)
        self.assertIn("Tendance EMA 20", resultat["donnees_manquantes"])
        self.assertNotIn("Raison Tendance EMA 20", resultat["facteurs_favorables"])

    def test_18_entree_et_structures_imbriquees_non_mutees(self):
        entree = score_complet()
        avant = copy.deepcopy(entree)
        construire_decision(entree)
        self.assertEqual(entree, avant)

    def test_19_determinisme_strict(self):
        entree = score_complet(60, (10, -10, 5, 0, -5))
        self.assertEqual(construire_decision(entree), construire_decision(entree))

    def test_20_serialisation_json_stricte(self):
        resultat = construire_decision(score_complet())
        texte = json.dumps(resultat, ensure_ascii=False, allow_nan=False)
        self.assertIsInstance(texte, str)

    def test_21_risques_permanents_dans_toutes_les_branches(self):
        entrees = [
            {},
            score_complet(60),
            score_complet(45),
            score_complet(30, (-10, -10, -10, -5, -10), "VENTE"),
        ]
        for entree in entrees:
            with self.subTest(entree=entree):
                resultat = construire_decision(entree)
                self.assertEqual(resultat["risques"][:2], list(RISQUES_PERMANENTS))
                self.verifier_invariants(resultat)

    def test_22_acheter_impossible_pour_tous_les_scores(self):
        for score in range(101):
            with self.subTest(score=score):
                resultat = construire_decision(score_complet(score))
                self.assertNotEqual(resultat["recommandation"], "Acheter")

    def test_23_signal_vente_jamais_repris_dans_la_sortie(self):
        resultat = construire_decision(
            score_complet(20, (-10, -10, -10, -5, -10), "VENTE")
        )
        sortie = " ".join(toutes_les_chaines(resultat)).lower()
        self.assertEqual(resultat["recommandation"], "Éviter")
        self.assertNotIn("vendre", sortie)
        self.assertNotIn("vente", sortie)

    def test_24_signal_manquant(self):
        entree = score_complet()
        entree.pop("signal")
        resultat = construire_decision(entree)
        self.assertEqual(resultat["recommandation"], "Surveiller")
        self.assertEqual(resultat["confiance"], 85)
        self.assertEqual(resultat["donnees_manquantes"][0], "signal")

    def test_25_scores_invalides(self):
        for score in (None, True, "80", float("nan"), float("inf"), -1, 101):
            with self.subTest(score=score):
                entree = score_complet()
                entree["score"] = score
                resultat = construire_decision(entree)
                self.assertEqual(resultat["recommandation"], "Attendre")
                self.assertLessEqual(resultat["confiance"], 20)
                self.assertIn("score", resultat["donnees_manquantes"])

    def test_26_ordre_des_facteurs_et_deduplication_textuelle(self):
        entree = score_complet(
            60,
            (10, -10, 0, 5, -5),
        )
        entree["ventilation"][1]["raison"] = "Texte partagé"
        entree["ventilation"][4]["raison"] = "Texte partagé"
        resultat = construire_decision(entree)
        self.assertEqual(
            resultat["facteurs_favorables"], ["Texte partagé"]
        )
        self.assertEqual(resultat["facteurs_defavorables"], [
            "Raison RSI", "Raison Volume",
        ])
        self.assertEqual(resultat["facteurs_neutres"], ["Raison MACD"])

    def test_27_premiere_entree_valide_apres_doublon_invalide(self):
        entree = score_complet()
        entree["ventilation"].insert(1, {
            "critere": "Tendance EMA 20",
            "contribution": None,
            "raison": "Invalide",
        })
        resultat = construire_decision(entree)
        self.assertIn("Raison Tendance EMA 20", resultat["facteurs_favorables"])
        self.assertNotIn("Invalide", resultat["facteurs_favorables"])
        self.assertEqual(resultat["confiance"], 80)

    def test_28_ventilation_incorrecte_toleree(self):
        for valeur in (None, "incorrecte", {}, 12):
            with self.subTest(valeur=valeur):
                entree = score_complet()
                entree["ventilation"] = valeur
                resultat = construire_decision(entree)
                self.assertEqual(resultat["recommandation"], "Attendre")
                self.assertEqual(resultat["confiance"], 0)
                self.assertEqual(resultat["facteurs_neutres"], [FACTEUR_REPLI])

    def test_29_dictionnaire_global_non_valide(self):
        for entree in (None, [], "invalide", 12, True):
            with self.subTest(entree=entree):
                resultat = construire_decision(entree)
                self.assertEqual(resultat["recommandation"], "Attendre")
                self.assertEqual(resultat["confiance"], 0)
                self.assertEqual(resultat["donnees_manquantes"], [
                    "score", "signal", "raisons", "ventilation",
                    *CRITERES_ATTENDUS,
                ])
                self.verifier_invariants(resultat)

    def test_30_ordre_des_cles_types_et_valeurs_fixes(self):
        resultat = construire_decision(score_complet())
        self.assertEqual(tuple(resultat.keys()), ORDRE_CLES_SORTIE)
        self.assertIs(type(resultat["confiance"]), int)
        self.assertIs(resultat["decision_finale_utilisateur"], True)
        self.assertEqual(resultat["risques"][:2], list(RISQUES_PERMANENTS))

    def test_31_resultats_frais_sans_reference_interne_exposee(self):
        entree = score_complet()
        premier = construire_decision(entree)
        premier["risques"].append("Mutation externe")
        premier["facteurs_favorables"].append("Mutation externe")
        premier["donnees_manquantes"].append("Mutation externe")
        second = construire_decision(entree)
        self.assertEqual(second["risques"][:2], list(RISQUES_PERMANENTS))
        self.assertNotIn("Mutation externe", toutes_les_chaines(second))
        self.assertIsNot(premier["risques"], second["risques"])

    def test_32_score_de_base_strictement_ignore(self):
        entree = score_complet()
        attendu = construire_decision(entree)
        entree["ventilation"][0] = {
            "critere": "Score de base",
            "valeur": object(),
            "contribution": -999999,
            "raison": "Ne doit jamais apparaître",
        }
        resultat = construire_decision(entree)
        self.assertEqual(resultat, attendu)

    def test_33_champs_partiels_et_entrees_mal_formees(self):
        entree = {
            "score": 80,
            "signal": "ACHAT",
            "raisons": [],
            "ventilation": [None, 1, "texte", {}, {"critere": "Inconnu"}],
        }
        resultat = construire_decision(entree)
        self.assertEqual(resultat["recommandation"], "Attendre")
        self.assertEqual(resultat["confiance"], 0)
        self.verifier_invariants(resultat)

    def test_34_import_isole_standard_library_uniquement(self):
        interdits = {
            "streamlit", "pandas", "market_data", "storage", "yfinance",
            "plotly", "openai", "scoring", "signals", "portfolio",
        }
        commande = (
            "import sys; import core.decision; "
            f"assert not ({interdits!r} & set(sys.modules))"
        )
        resultat = subprocess.run(
            [sys.executable, "-c", commande],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(resultat.returncode, 0, resultat.stderr)


if __name__ == "__main__":
    unittest.main()
