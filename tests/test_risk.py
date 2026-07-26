"""Tests du moteur pur de gestion du risque."""

import ast
import copy
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

from core.risk import (
    DECISION_FINALE,
    RISQUE_PLAN_INDISPONIBLE,
    RISQUES_PERMANENTS,
    calculer_atr,
    construire_plan_risque,
)


CLES_SORTIE = [
    "statut", "prix_entree", "atr", "multiplicateur_stop", "stop_loss",
    "objectif", "risque_par_unite", "ratio_risque_rendement",
    "capital_reference", "risque_max_pct", "risque_capital",
    "taille_position", "donnees_manquantes", "risques",
    "decision_finale_utilisateur",
]


class AtrTests(unittest.TestCase):
    def test_cas_nominal_sans_gap_et_type_natif(self):
        resultat = calculer_atr(
            [10, 11, 12, 13], [8, 9, 10, 11], [9, 10, 11, 12], 3
        )
        self.assertEqual(resultat, 2.0)
        self.assertIs(type(resultat), float)

    def test_gaps_haussier_et_baissier(self):
        self.assertEqual(
            calculer_atr([10, 15], [9, 14], [9.5, 14.5], 1), 5.5
        )
        self.assertEqual(
            calculer_atr([15, 11], [14, 9], [14.5, 10], 1), 5.5
        )

    def test_moyenne_des_derniers_true_range_et_periode_exacte(self):
        hauts = [10, 12, 15, 16]
        bas = [9, 10, 11, 15]
        clotures = [9.5, 11, 14, 15.5]
        self.assertEqual(calculer_atr(hauts, bas, clotures, 2), 3.0)
        self.assertEqual(calculer_atr(hauts[:3], bas[:3], clotures[:3], 2), 3.25)

    def test_donnees_trop_courtes_vides_et_longueurs_incoherentes(self):
        self.assertIsNone(calculer_atr([2], [1], [1.5], 1))
        self.assertIsNone(calculer_atr([], [], [], 1))
        self.assertIsNone(calculer_atr([2, 3], [1], [1.5, 2], 1))

    def test_series_invalides(self):
        for series in (
            ("texte", [1, 2], [1, 2]),
            ([1, 2], None, [1, 2]),
            ({1, 2}, [1, 2], [1, 2]),
        ):
            with self.subTest(series=series):
                self.assertIsNone(calculer_atr(*series, 1))

    def test_periodes_invalides(self):
        for periode in (0, -1, 1.0, True, False):
            with self.subTest(periode=periode):
                self.assertIsNone(calculer_atr(
                    [2, 3], [1, 2], [1.5, 2.5], periode
                ))

    def test_valeurs_invalides(self):
        invalides = (
            None, "2", True, float("nan"), float("inf"), -float("inf"), 0, -1,
        )
        for valeur in invalides:
            with self.subTest(valeur=valeur):
                self.assertIsNone(calculer_atr(
                    [2, valeur], [1, 1], [1.5, 1.5], 1
                ))

    def test_high_inferieur_a_low(self):
        self.assertIsNone(calculer_atr([2, 1], [1, 2], [1.5, 1.5], 1))

    def test_absence_mutation_et_determinisme(self):
        hauts, bas, clotures = [2, 3], [1, 2], [1.5, 2.5]
        original = copy.deepcopy((hauts, bas, clotures))
        premier = calculer_atr(hauts, bas, clotures, 1)
        second = calculer_atr(hauts, bas, clotures, 1)
        self.assertEqual((hauts, bas, clotures), original)
        self.assertEqual(premier, second)

    def test_aucune_moyenne_de_wilder(self):
        hauts = [10, 12, 15, 16, 20]
        bas = [9, 10, 11, 15, 17]
        clotures = [9.5, 11, 14, 15.5, 19]
        self.assertEqual(calculer_atr(hauts, bas, clotures, 2), 3.25)


class PlanRisqueTests(unittest.TestCase):
    def test_cas_nominal_complet_formules_et_statut(self):
        resultat = construire_plan_risque(100, 5, 10_000, 1, 2, 2)
        self.assertEqual(resultat["statut"], "disponible")
        self.assertEqual(resultat["stop_loss"], 90.0)
        self.assertEqual(resultat["risque_par_unite"], 10.0)
        self.assertEqual(resultat["objectif"], 120.0)
        self.assertEqual(resultat["risque_capital"], 100.0)
        self.assertEqual(resultat["taille_position"], 10.0)
        self.assertLess(resultat["stop_loss"], resultat["prix_entree"])
        self.assertGreater(resultat["objectif"], resultat["prix_entree"])

    def test_plans_partiels_sans_capital_ou_risque(self):
        cas = (
            ({}, ["capital_reference", "risque_max_pct"]),
            ({"capital_reference": 1000}, ["risque_max_pct"]),
            ({"risque_max_pct": 1}, ["capital_reference"]),
        )
        for kwargs, manquantes in cas:
            with self.subTest(kwargs=kwargs):
                resultat = construire_plan_risque(100, 5, **kwargs)
                self.assertEqual(resultat["statut"], "partiel")
                self.assertIsNone(resultat["risque_capital"])
                self.assertIsNone(resultat["taille_position"])
                self.assertEqual(resultat["donnees_manquantes"], manquantes)

    def test_parametres_principaux_invalides(self):
        cas = (
            ("prix_entree", {"prix_entree": 0}),
            ("prix_entree", {"prix_entree": -1}),
            ("prix_entree", {"prix_entree": True}),
            ("prix_entree", {"prix_entree": "100"}),
            ("atr", {"atr": None}),
            ("atr", {"atr": 0}),
            ("atr", {"atr": -1}),
            ("multiplicateur_stop", {"multiplicateur_stop": 0}),
            ("multiplicateur_stop", {"multiplicateur_stop": -1}),
            ("ratio_risque_rendement", {"ratio_risque_rendement": 0}),
            ("ratio_risque_rendement", {"ratio_risque_rendement": -1}),
        )
        base = {"prix_entree": 100, "atr": 5}
        for champ, changement in cas:
            with self.subTest(champ=champ, changement=changement):
                resultat = construire_plan_risque(**{**base, **changement})
                self.assertEqual(resultat["statut"], "indisponible")
                self.assertIn(champ, resultat["donnees_manquantes"])

    def test_stop_non_positif_rend_plan_indisponible(self):
        resultat = construire_plan_risque(10, 5, 1000, 1, 2)
        self.assertEqual(resultat["statut"], "indisponible")
        self.assertIn("stop_loss", resultat["donnees_manquantes"])
        self.assertIsNone(resultat["stop_loss"])
        self.assertIsNone(resultat["taille_position"])

    def test_capital_et_risque_invalides_rendent_plan_partiel(self):
        cas = (
            ("capital_reference", 0),
            ("capital_reference", -1),
            ("capital_reference", True),
            ("risque_max_pct", 0),
            ("risque_max_pct", -1),
            ("risque_max_pct", 101),
            ("risque_max_pct", True),
        )
        for champ, valeur in cas:
            with self.subTest(champ=champ, valeur=valeur):
                kwargs = {"capital_reference": 1000, "risque_max_pct": 1}
                kwargs[champ] = valeur
                resultat = construire_plan_risque(100, 5, **kwargs)
                self.assertEqual(resultat["statut"], "partiel")
                self.assertIn(champ, resultat["donnees_manquantes"])
                self.assertIsNone(resultat["taille_position"])

    def test_nan_et_infini_dans_chaque_parametre(self):
        champs = (
            "prix_entree", "atr", "capital_reference", "risque_max_pct",
            "multiplicateur_stop", "ratio_risque_rendement",
        )
        for champ in champs:
            for valeur in (float("nan"), float("inf"), -float("inf")):
                with self.subTest(champ=champ, valeur=valeur):
                    kwargs = {
                        "prix_entree": 100, "atr": 5,
                        "capital_reference": 1000, "risque_max_pct": 1,
                    }
                    kwargs[champ] = valeur
                    resultat = construire_plan_risque(**kwargs)
                    self.assertIn(champ, resultat["donnees_manquantes"])
                    json.dumps(resultat, allow_nan=False)

    def test_structure_ordre_statuts_et_donnees_manquantes(self):
        disponible = construire_plan_risque(100, 5, 1000, 1)
        partiel = construire_plan_risque(100, 5)
        indisponible = construire_plan_risque(None, None)
        self.assertEqual(list(disponible), CLES_SORTIE)
        self.assertEqual(disponible["statut"], "disponible")
        self.assertEqual(partiel["statut"], "partiel")
        self.assertEqual(indisponible["statut"], "indisponible")
        self.assertEqual(indisponible["donnees_manquantes"], [
            "prix_entree", "atr", "capital_reference", "risque_max_pct",
        ])
        self.assertEqual(
            len(indisponible["donnees_manquantes"]),
            len(set(indisponible["donnees_manquantes"])),
        )

    def test_risques_et_texte_final(self):
        for resultat in (
            construire_plan_risque(100, 5, 1000, 1),
            construire_plan_risque(100, 5),
        ):
            self.assertEqual(resultat["risques"], list(RISQUES_PERMANENTS))
            self.assertEqual(resultat["decision_finale_utilisateur"], DECISION_FINALE)
        indisponible = construire_plan_risque(None, None)
        self.assertEqual(
            indisponible["risques"],
            [*RISQUES_PERMANENTS, RISQUE_PLAN_INDISPONIBLE],
        )

    def test_arrondis_contractuels_et_calculs_non_arrondis(self):
        resultat = construire_plan_risque(
            100.123456789, 1.234567891, 12345.678, 1.234567,
            1.234567, 2.345678,
        )
        self.assertEqual(resultat["prix_entree"], round(100.123456789, 8))
        self.assertEqual(resultat["atr"], round(1.234567891, 8))
        self.assertEqual(resultat["multiplicateur_stop"], round(1.234567, 4))
        self.assertEqual(resultat["ratio_risque_rendement"], round(2.345678, 4))
        self.assertEqual(resultat["capital_reference"], round(12345.678, 2))
        self.assertEqual(resultat["risque_max_pct"], round(1.234567, 4))
        risque_brut = 1.234567891 * 1.234567
        self.assertEqual(resultat["risque_par_unite"], round(risque_brut, 8))
        self.assertEqual(
            resultat["taille_position"],
            round((12345.678 * 1.234567 / 100) / risque_brut, 8),
        )

    def test_fractionnaire_json_strict_sans_non_finis(self):
        cas = (
            construire_plan_risque(100, 3, 1000, 1),
            construire_plan_risque(100, 3),
            construire_plan_risque(0, None),
        )
        self.assertNotEqual(cas[0]["taille_position"] % 1, 0)
        for resultat in cas:
            json.dumps(resultat, ensure_ascii=False, allow_nan=False)
            for valeur in resultat.values():
                if isinstance(valeur, float):
                    self.assertTrue(math.isfinite(valeur))

    def test_absence_mutation_determinisme_et_listes_fraiches(self):
        arguments = {
            "prix_entree": 100, "atr": 5,
            "capital_reference": 1000, "risque_max_pct": 1,
        }
        copie = copy.deepcopy(arguments)
        premier = construire_plan_risque(**arguments)
        second = construire_plan_risque(**arguments)
        self.assertEqual(arguments, copie)
        self.assertEqual(premier, second)
        self.assertIsNot(premier["risques"], second["risques"])
        self.assertIsNot(
            premier["donnees_manquantes"], second["donnees_manquantes"]
        )

    def test_aucune_formulation_interdite(self):
        textes = json.dumps(
            construire_plan_risque(100, 5, 1000, 1),
            ensure_ascii=False,
        ).lower()
        for formulation in (
            "gain garanti", "rendement garanti",
            "ordre d’achat", "ordre d'achat", "ordre de vente",
        ):
            self.assertNotIn(formulation, textes)


class IsolationTests(unittest.TestCase):
    def test_bibliotheque_standard_uniquement(self):
        chemin = Path(__file__).resolve().parents[1] / "core/risk.py"
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        imports = []
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.Import):
                imports.extend(alias.name for alias in noeud.names)
            elif isinstance(noeud, ast.ImportFrom):
                imports.append(noeud.module)
        self.assertEqual(imports, ["math"])

    def test_import_isole_et_modules_interdits_absents(self):
        interdits = {
            "streamlit", "pandas", "numpy", "yfinance", "openai", "scoring",
            "scanner", "scanner_core", "portfolio", "signals",
        }
        code = (
            "import sys; import core.risk; "
            f"interdits={interdits!r}; "
            "charges=interdits.intersection(sys.modules); "
            "assert not charges, charges"
        )
        resultat = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(resultat.returncode, 0, resultat.stderr)


if __name__ == "__main__":
    unittest.main()
