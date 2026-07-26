"""Tests déterministes des calculs métier purs du portefeuille."""

import subprocess
import sys
import unittest

from core.portfolio import (
    calculer_allocation,
    calculer_score_diversification,
    calculer_taille_position,
    calculer_valorisation_position,
)


class PortfolioCoreTests(unittest.TestCase):
    def test_score_diversification_aux_frontieres(self):
        cas = {
            0: 2,
            2: 2,
            3: 4,
            4: 4,
            5: 6,
            7: 6,
            8: 8,
            9: 8,
            10: 10,
            25: 10,
        }
        for nombre_positions, attendu in cas.items():
            with self.subTest(nombre_positions=nombre_positions):
                self.assertEqual(
                    calculer_score_diversification(nombre_positions), attendu
                )

    def test_taille_position_nominale(self):
        self.assertEqual(calculer_taille_position(100, 90, 10_000, 1), 10.0)

    def test_taille_position_stop_egal_ou_superieur(self):
        self.assertIsNone(calculer_taille_position(100, 100, 10_000, 1))
        self.assertIsNone(calculer_taille_position(100, 110, 10_000, 1))

    def test_taille_position_capital_nul_ou_negatif(self):
        self.assertIsNone(calculer_taille_position(100, 90, 0, 1))
        self.assertIsNone(calculer_taille_position(100, 90, -1, 1))

    def test_taille_position_risque_nul_ou_negatif(self):
        self.assertEqual(calculer_taille_position(100, 90, 10_000, 0), 0.0)
        self.assertEqual(calculer_taille_position(100, 90, 10_000, -1), -10.0)

    def test_resultat_deterministe(self):
        arguments = ("ABC", 3.3333, 10.123, 9.111, 14.567,
                     12.345, 11.111, 10_000.0, 1.5)
        premier = calculer_valorisation_position(*arguments)
        second = calculer_valorisation_position(*arguments)
        self.assertEqual(premier, second)

    def test_valorisation_et_arrondis_historiques(self):
        resultat = calculer_valorisation_position(
            "ABC", 3.3333, 10.123, 9.111, 14.567,
            12.345, 11.111, 10_000.0, 1.5,
        )
        self.assertEqual(resultat, {
            "Actif": "ABC",
            "Quantité": 3.3333,
            "Prix achat": 10.12,
            "Cours actuel": 12.35,
            "Valeur": 41.15,
            "Gain (€)": 7.41,
            "Gain (%)": 21.95,
            "Variation jour (%)": 11.11,
            "Stop-loss": 9.11,
            "Objectif prix": 14.57,
            "Distance stop (%)": 10.0,
            "Risque potentiel (€)": 3.37,
            "Risque capital (%)": 0.03,
            "Taille suggérée": 148.2213,
        })

    def test_valorisation_sans_cout_stop_ou_cours_precedent(self):
        resultat = calculer_valorisation_position(
            "ZERO", 2.0, 0.0, 0.0, 0.0, 5.0, 0.0, 0.0, 0.0,
        )
        self.assertEqual(resultat["Gain (%)"], 0.0)
        self.assertEqual(resultat["Variation jour (%)"], 0.0)
        self.assertEqual(resultat["Distance stop (%)"], 0.0)
        self.assertEqual(resultat["Risque potentiel (€)"], 0.0)
        self.assertEqual(resultat["Risque capital (%)"], 0.0)
        self.assertEqual(resultat["Taille suggérée"], "—")

    def test_valorisation_preserve_taille_negative(self):
        resultat = calculer_valorisation_position(
            "NEG", 1.0, 100.0, 90.0, 0.0, 100.0, 100.0,
            10_000.0, -1.0,
        )
        self.assertEqual(resultat["Taille suggérée"], -10.0)

    def test_allocation_arrondie_et_total_nul(self):
        self.assertEqual(calculer_allocation(41.15, 123.45), 33.33)
        self.assertEqual(calculer_allocation(10.0, 0.0), 0.0)
        self.assertEqual(calculer_allocation(10.0, -5.0), 0.0)

    def test_wrappers_historiques(self):
        from portfolio import (
            _score_diversification,
            _taille_position_suggeree,
        )

        self.assertEqual(_score_diversification(8), 8)
        self.assertEqual(
            _taille_position_suggeree(100, 90, 10_000, -1), -10.0
        )
        self.assertIsNone(
            _taille_position_suggeree(100, 100, 10_000, 1)
        )

    def test_import_isole_sans_streamlit(self):
        commande = (
            "import sys; import core.portfolio; "
            "assert 'streamlit' not in sys.modules"
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
