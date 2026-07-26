import unittest
import pandas as pd
from indicators import rsi


def historique(prix):
    return pd.DataFrame({"Close": prix})


class RsiTests(unittest.TestCase):
    def test_hausse(self):
        self.assertEqual(rsi(historique(range(1, 22))).iloc[-1], 100.0)

    def test_baisse(self):
        self.assertEqual(rsi(historique(range(22, 1, -1))).iloc[-1], 0.0)

    def test_stable(self):
        self.assertEqual(rsi(historique([10.0] * 21)).iloc[-1], 50.0)

    def test_insuffisant(self):
        self.assertTrue(rsi(historique(range(10))).isna().all())

    def test_index_et_longueur(self):
        index = pd.date_range("2026-01-01", periods=20)
        resultat = rsi(pd.DataFrame({"Close": range(20)}, index=index))
        self.assertEqual(len(resultat), 20)
        self.assertTrue(resultat.index.equals(index))

    def test_mixte_borne(self):
        resultat = rsi(historique([100, 102, 101, 104, 103, 105, 102, 106] * 4))
        self.assertTrue(resultat.dropna().between(0, 100).all())


if __name__ == "__main__":
    unittest.main()
