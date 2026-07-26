"""Tests du moteur descriptif d’intelligence du portefeuille."""

import copy
import json
import unittest

from core.portfolio_intelligence import analyser_portefeuille


class PortfolioIntelligenceTests(unittest.TestCase):
    def test_portefeuille_vide_produit_un_repli_json(self):
        resultat = analyser_portefeuille([], {})
        self.assertTrue(resultat["portefeuille_vide"])
        self.assertEqual(resultat["valeur_totale"], 0.0)
        self.assertEqual(resultat["diversification"]["niveau"], "Faible")
        self.assertEqual(resultat["qualite_analyse"], "Faible")
        json.dumps(resultat, ensure_ascii=False, allow_nan=False)

    def test_portefeuille_non_charge_ne_devient_pas_un_portefeuille_vide(self):
        resultat = analyser_portefeuille(None, None)
        self.assertFalse(resultat["donnees_chargees"])
        self.assertFalse(resultat["portefeuille_vide"])
        self.assertIsNone(resultat["valeur_totale"])

    def test_une_position_mesure_concentration_et_exposition(self):
        resultat = analyser_portefeuille(
            [{"symbole": "AAPL", "type_actif": "action", "quantite": 2}],
            {"AAPL": 100},
        )
        self.assertEqual(resultat["valeur_totale"], 200.0)
        self.assertEqual(resultat["expositions"], {"actions": 100.0, "crypto": 0.0})
        self.assertEqual(resultat["concentration"]["poids_principal"], 100.0)
        self.assertEqual(resultat["diversification"]["niveau"], "Faible")
        self.assertIn("Concentration élevée", resultat["constats"][0])

    def test_plusieurs_positions_calculent_repartition_top_cinq_et_bonne_diversification(self):
        positions = [
            {"symbole": symbole, "type_actif": "crypto" if symbole == "BTC-USD" else "action", "quantite": 1}
            for symbole in ("AAPL", "MSFT", "NVDA", "OR.PA", "BTC-USD", "AIR.PA")
        ]
        resultat = analyser_portefeuille(positions, {x["symbole"]: 100 for x in positions})
        self.assertEqual(resultat["valeur_totale"], 600.0)
        self.assertEqual(resultat["positions_valorisees"], 6)
        self.assertEqual(resultat["concentration"]["poids_top_5"], 83.33)
        self.assertEqual(resultat["diversification"]["niveau"], "Bonne")
        self.assertEqual(len(resultat["principales_positions"]), 5)
        self.assertEqual(resultat["expositions"]["crypto"], 16.67)

    def test_donnees_partielles_listent_prix_absent_et_valeur_impossible(self):
        resultat = analyser_portefeuille(
            [
                {"symbole": "AAPL", "type_actif": "action", "quantite": 1},
                {"symbole": "MSFT", "type_actif": "action", "quantite": 2},
            ],
            {"AAPL": 100},
        )
        self.assertEqual(resultat["valeur_totale"], 100.0)
        self.assertEqual(resultat["qualite_analyse"], "Moyenne")
        self.assertEqual(resultat["donnees_manquantes"]["prix_absents"], ["MSFT"])
        self.assertIn("MSFT : valorisation impossible.", resultat["donnees_manquantes"]["valeurs_impossibles"])

    def test_valeurs_invalides_sont_ignorees_sans_traceback(self):
        resultat = analyser_portefeuille(
            [None, {"symbole": "BAD", "type_actif": "action", "quantite": "invalide"}],
            {"BAD": float("nan")},
        )
        self.assertIsNone(resultat["valeur_totale"])
        self.assertEqual(resultat["positions_valorisees"], 0)
        self.assertEqual(resultat["qualite_analyse"], "Faible")
        self.assertTrue(resultat["donnees_manquantes"]["positions_incompletes"])
        json.dumps(resultat, ensure_ascii=False, allow_nan=False)

    def test_position_historique_est_preservee_et_valorisee(self):
        positions = [{
            "symbole": "msft", "quantite": "10", "prix_achat": 0,
            "objectif_prix": None, "date_ajout": "2024-01-01",
        }]
        avant = copy.deepcopy(positions)
        premier = analyser_portefeuille(positions, {"MSFT": "25"})
        second = analyser_portefeuille(positions, {"MSFT": "25"})
        self.assertEqual(premier, second)
        self.assertEqual(positions, avant)
        self.assertEqual(premier["valeur_totale"], 250.0)
        self.assertEqual(premier["principales_positions"][0]["type_actif"], "autre")
        self.assertIn("type d’actif absent", premier["donnees_manquantes"]["positions_incompletes"][0])

    def test_tous_les_types_et_niveau_modere_sont_documentes(self):
        positions = [
            {"symbole": "A", "type_actif": "action", "quantite": 1},
            {"symbole": "E", "type_actif": "ETF", "quantite": 1},
            {"symbole": "C", "type_actif": "crypto", "quantite": 1},
            {"symbole": "X", "type_actif": "inconnu", "quantite": 1},
        ]
        resultat = analyser_portefeuille(positions, {"A": 10, "E": 20, "C": 30, "X": 40})
        self.assertEqual([x["type_actif"] for x in resultat["repartition_types"]], ["Actions", "ETF", "Crypto", "Autres"])
        self.assertEqual(resultat["diversification"]["niveau"], "Modérée")
        self.assertIn("intermédiaire", resultat["diversification"]["justification"])

    def test_prix_nul_nan_infini_et_invalide_sont_rejetes(self):
        positions = [
            {"symbole": symbole, "type_actif": "action", "quantite": 1}
            for symbole in ("ZERO", "NAN", "INF", "TXT")
        ]
        resultat = analyser_portefeuille(
            positions,
            {"ZERO": 0, "NAN": float("nan"), "INF": float("inf"), "TXT": "invalide"},
        )
        self.assertIsNone(resultat["valeur_totale"])
        self.assertEqual(resultat["donnees_manquantes"]["prix_absents"], ["INF", "NAN", "TXT", "ZERO"])
        self.assertEqual(len(resultat["donnees_manquantes"]["valeurs_impossibles"]), 4)

    def test_exposition_crypto_forte_reste_un_constat_sans_injonction(self):
        resultat = analyser_portefeuille(
            [
                {"symbole": "BTC-USD", "type_actif": "crypto", "quantite": 3},
                {"symbole": "AAPL", "type_actif": "action", "quantite": 1},
            ],
            {"BTC-USD": 100, "AAPL": 100},
        )
        texte = " ".join(resultat["constats"]).casefold()
        self.assertIn("forte exposition crypto constatée", texte)
        for interdit in ("achetez", "vendez", "réduisez", "vous devriez"):
            self.assertNotIn(interdit, str(resultat).casefold())


if __name__ == "__main__":
    unittest.main()
