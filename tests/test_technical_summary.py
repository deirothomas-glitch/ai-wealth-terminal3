import copy
import json
import math
import unittest
from unittest.mock import patch

from ui.technical_summary import afficher_resume_technique, construire_modele_resume_technique


class Colonne:
    def __init__(self, appels): self.appels = appels
    def metric(self, label, value): self.appels.append(("metric", label, value))


class FauxStreamlit:
    def __init__(self): self.appels = []
    def columns(self, nombre): return [Colonne(self.appels) for _ in range(nombre)]
    def markdown(self, texte): self.appels.append(("markdown", texte))
    def write(self, texte): self.appels.append(("write", texte))


class TechnicalSummaryTests(unittest.TestCase):
    def test_ordre_et_libelles_exacts(self):
        modele = construire_modele_resume_technique({})
        self.assertEqual(list(modele), ["score_label", "score", "signal_label", "signal", "raisons_titre", "raisons"])
        self.assertEqual((modele["score_label"], modele["signal_label"], modele["raisons_titre"]),
                         ("Score technique", "Signal technique", "Raisons techniques"))

    def test_scores_valides(self):
        for score, attendu in ((75, "75/100"), (75.5, "75.5/100"), (0, "0/100"), (100.0, "100.0/100")):
            with self.subTest(score=score):
                self.assertEqual(construire_modele_resume_technique({"score": score})["score"], attendu)

    def test_scores_invalides(self):
        for score in (None, True, False, "75", math.nan, math.inf, -math.inf, -1, 101, 10 ** 1000):
            with self.subTest(score=score):
                entree = {} if score is None else {"score": score}
                self.assertEqual(construire_modele_resume_technique(entree)["score"], "Indisponible")

    def test_signaux_valides_et_nettoyage_externe(self):
        for signal in ("ACHAT", "SURVEILLER", "VENTE", "DONNÉES INSUFFISANTES"):
            self.assertEqual(construire_modele_resume_technique({"signal": f"  {signal}  "})["signal"], signal)

    def test_signaux_invalides(self):
        for entree in ({}, {"signal": ""}, {"signal": "  "}, {"signal": 1}, {"signal": None}):
            self.assertEqual(construire_modele_resume_technique(entree)["signal"], "INDISPONIBLE")

    def test_raisons_filtrees_ordre_et_doublons(self):
        resultat = construire_modele_resume_technique({"raisons": [" Une ", 2, "", "Deux", None, "Une"]})
        self.assertEqual(resultat["raisons"], ["Une", "Deux", "Une"])

    def test_raisons_absentes_vides_ou_non_liste(self):
        for entree in ({}, {"raisons": []}, {"raisons": "Une"}, {"raisons": None}, {"raisons": ("Une",)}):
            self.assertEqual(construire_modele_resume_technique(entree)["raisons"], [])

    def test_entree_non_dict_et_champ_inconnu(self):
        for entree in (None, [], "x", 4):
            self.assertEqual(construire_modele_resume_technique(entree)["score"], "Indisponible")
        self.assertEqual(construire_modele_resume_technique({"inconnu": object()})["raisons"], [])

    def test_non_mutation_determinisme_listes_fraiches_et_json(self):
        entree = {"score": 50, "signal": " ACHAT ", "raisons": [" Une "], "extra": {"x": [1]}}
        copie = copy.deepcopy(entree)
        un = construire_modele_resume_technique(entree)
        deux = construire_modele_resume_technique(entree)
        self.assertEqual(entree, copie)
        self.assertEqual(un, deux)
        self.assertIsNot(un["raisons"], deux["raisons"])
        un["raisons"].append("x")
        self.assertNotIn("x", deux["raisons"])
        json.dumps(deux, ensure_ascii=False, allow_nan=False)

    def test_aucun_vocabulaire_interdit_dans_les_libelles(self):
        modele = construire_modele_resume_technique({})
        texte = " ".join(modele[cle] for cle in ("score_label", "signal_label", "raisons_titre")).lower()
        for terme in ("confiance", "recommandation", "probabilité"):
            self.assertNotIn(terme, texte)

    def test_rendu_metriques_et_raisons(self):
        faux = FauxStreamlit()
        with patch("ui.technical_summary.st", faux):
            afficher_resume_technique({"score": 75, "signal": "ACHAT", "raisons": ["Une", "Deux"]})
        self.assertEqual(faux.appels, [("metric", "Score technique", "75/100"),
                                      ("metric", "Signal technique", "ACHAT"),
                                      ("markdown", "**Raisons techniques**"),
                                      ("write", "• Une"), ("write", "• Deux")])

    def test_rendu_repli_raisons_vides(self):
        faux = FauxStreamlit()
        with patch("ui.technical_summary.st", faux):
            afficher_resume_technique({})
        self.assertIn(("write", "Aucune raison technique exploitable."), faux.appels)

    def test_rendu_raisons_masquees(self):
        faux = FauxStreamlit()
        with patch("ui.technical_summary.st", faux):
            afficher_resume_technique({"raisons": ["Masquée"]}, afficher_raisons=False)
        self.assertEqual(len(faux.appels), 2)


if __name__ == "__main__": unittest.main()
