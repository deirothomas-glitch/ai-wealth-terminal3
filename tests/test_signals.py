import unittest
from signals import (SIGNAL_ACHAT, SIGNAL_SURVEILLER, SIGNAL_VENTE,
                     SEUIL_ACHAT, SEUIL_SURVEILLER, determiner_signal, generer_signal)


class SignalTests(unittest.TestCase):
    def test_frontieres(self):
        self.assertEqual(determiner_signal(SEUIL_ACHAT), SIGNAL_ACHAT)
        self.assertEqual(determiner_signal(SEUIL_ACHAT - 1), SIGNAL_SURVEILLER)
        self.assertEqual(determiner_signal(SEUIL_SURVEILLER), SIGNAL_SURVEILLER)
        self.assertEqual(determiner_signal(SEUIL_SURVEILLER - 1), SIGNAL_VENTE)

    def test_contrat(self):
        resultat = generer_signal({"score": SEUIL_ACHAT, "prix": 100.0})
        self.assertEqual(set(resultat), {"signal", "confiance", "entree", "stop_loss",
                                        "objectif1", "objectif2", "ratio"})

    def test_ratio(self):
        self.assertEqual(generer_signal({"score": SEUIL_ACHAT, "prix": 100.0})["ratio"], 1.5)

    def test_libelles_canoniques(self):
        for score, attendu in ((SEUIL_ACHAT, SIGNAL_ACHAT),
                               (SEUIL_SURVEILLER, SIGNAL_SURVEILLER), (0, SIGNAL_VENTE)):
            self.assertEqual(generer_signal({"score": score, "prix": 100.0})["signal"], attendu)


if __name__ == "__main__":
    unittest.main()
