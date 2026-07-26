import unittest
import pandas as pd
from scoring import SCORE_BASE, calculer_score
from signals import SIGNAL_DONNEES_INSUFFISANTES, determiner_signal


def historique(prix, volumes=None):
    close = pd.Series(prix, dtype=float)
    data = {"Close": close, "Open": close, "High": close + 1, "Low": close - 1}
    if volumes is not None:
        data["Volume"] = volumes
    return pd.DataFrame(data)


class ScoringTests(unittest.TestCase):
    def verifier_insuffisant(self, resultat):
        cles = {"score", "signal", "raisons", "prix", "ema20", "rsi", "ventilation"}
        self.assertTrue(cles.issubset(resultat))
        self.assertEqual(resultat["score"], 0)
        self.assertEqual(resultat["signal"], SIGNAL_DONNEES_INSUFFISANTES)
        self.assertEqual(sum(x["contribution"] for x in resultat["ventilation"]), 0)

    def test_none_deterministe(self):
        premier = calculer_score({}, None)
        self.verifier_insuffisant(premier)
        self.assertEqual(premier, calculer_score({"ignore": True}, None))

    def test_vide(self):
        self.verifier_insuffisant(calculer_score({}, pd.DataFrame()))

    def test_trop_court(self):
        self.verifier_insuffisant(calculer_score({}, historique(range(20))))

    def test_close_absent(self):
        self.verifier_insuffisant(calculer_score({}, pd.DataFrame({"Volume": [1] * 30})))

    def test_nan(self):
        self.verifier_insuffisant(calculer_score({}, historique(list(range(1, 30)) + [float("nan")])))

    def test_compatible_explicable(self):
        prix = [100 + i * 0.4 + (-1) ** i for i in range(40)]
        resultat = calculer_score({}, historique(prix, [100] * 39 + [500]))
        self.assertTrue({"score", "signal", "raisons", "prix", "ema20", "rsi"}.issubset(resultat))
        self.assertEqual(resultat["ventilation"][0]["contribution"], SCORE_BASE)
        brut = sum(x["contribution"] for x in resultat["ventilation"])
        self.assertEqual(resultat["score"], max(0, min(int(brut), 100)))
        self.assertEqual(resultat["signal"], determiner_signal(resultat["score"]))
        for element in resultat["ventilation"]:
            self.assertEqual({"critere", "valeur", "contribution", "raison"}, set(element))

    def test_volume_absent(self):
        resultat = calculer_score({}, historique([100 + i % 5 for i in range(40)]))
        self.assertNotEqual(resultat["signal"], SIGNAL_DONNEES_INSUFFISANTES)
        volume = next(x for x in resultat["ventilation"] if x["critere"] == "Volume")
        self.assertEqual(volume["contribution"], 0)

    def test_scores_bornes(self):
        for prix in (range(1, 41), range(41, 1, -1)):
            resultat = calculer_score({}, historique(prix, [100] * 40))
            self.assertTrue(0 <= resultat["score"] <= 100)


if __name__ == "__main__":
    unittest.main()
