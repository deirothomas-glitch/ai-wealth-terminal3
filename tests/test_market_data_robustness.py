"""Tests défensifs des extractions de données de marché mises en cache."""

import unittest

import pandas as pd

from market_data import dernier_prix, dernier_volume, variation_journaliere


class MarketDataRobustnessTests(unittest.TestCase):
    def test_none_et_dataframe_vide(self):
        self.assertEqual(dernier_prix(None), 0.0)
        self.assertEqual(dernier_volume(pd.DataFrame()), 0)
        self.assertEqual(variation_journaliere(pd.DataFrame()), 0.0)

    def test_nan_infini_et_texte_ne_provoquent_pas_exception(self):
        for valeur in (None, float("nan"), float("inf"), "invalide"):
            donnees = pd.DataFrame({"Close": [100, valeur], "Volume": [10, valeur]})
            self.assertEqual(dernier_prix(donnees), 0.0)
            self.assertEqual(dernier_volume(donnees), 0)
            self.assertEqual(variation_journaliere(donnees), 0.0)

    def test_colonnes_absentes_ne_provoquent_pas_exception(self):
        donnees = pd.DataFrame({"Open": [1, 2]})
        self.assertEqual(dernier_prix(donnees), 0.0)
        self.assertEqual(dernier_volume(donnees), 0)
        self.assertEqual(variation_journaliere(donnees), 0.0)

    def test_valeurs_valides_conservent_le_comportement(self):
        donnees = pd.DataFrame({"Close": [100.0, 110.0], "Volume": [10, 25]})
        self.assertEqual(dernier_prix(donnees), 110.0)
        self.assertEqual(dernier_volume(donnees), 25)
        self.assertEqual(variation_journaliere(donnees), 10.0)


if __name__ == "__main__":
    unittest.main()
