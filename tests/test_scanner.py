import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np
import pandas as pd

from scanner_core import CSV_COLUMNS, analyser_watchlist, generer_csv


def historique(prix):
    return pd.DataFrame({"Close": prix})


def score(valeur, rsi=55.4, signal="ACHAT", raisons=None):
    return {
        "score": valeur, "rsi": rsi, "signal": signal,
        "raisons": raisons or ["Raison test"],
    }


class ScannerCoreTests(unittest.TestCase):
    def test_resultats_legers_natifs_et_serialisables(self):
        resultat = analyser_watchlist(
            {"Actions": ["BBB"]},
            lambda symbole: historique([100, 102]),
            lambda info, donnees: score(
                pd.Series([75], dtype="int64").iloc[0],
                pd.Series([51.25], dtype="float64").iloc[0],
            ),
        )
        self.assertEqual(set(resultat[0]), {
            "Catégorie", "Actif", "Prix", "Variation %", "RSI", "Score",
            "Signal", "Raisons", "Ventilation",
        })
        self.assertIs(type(resultat[0]["Prix"]), float)
        self.assertIs(type(resultat[0]["RSI"]), float)
        self.assertIs(type(resultat[0]["Score"]), int)
        self.assertEqual(resultat[0]["Raisons"], ["Raison test"])
        self.assertEqual(resultat[0]["Ventilation"], [])
        json.dumps(resultat, ensure_ascii=False)

    def test_progression_exactement_une_fois_par_actif(self):
        appels_progression = []
        erreurs = []

        def charger(symbole):
            if symbole == "VIDE":
                return None
            if symbole == "ERREUR":
                raise RuntimeError("échec simulé")
            return historique([10, 11])

        resultat = analyser_watchlist(
            {"Actions": ["OK", "VIDE", "ERREUR"]}, charger,
            lambda info, donnees: score(60),
            progress_callback=lambda traites, total: appels_progression.append(
                (traites, total)
            ),
            error_callback=lambda categorie, symbole: erreurs.append(
                (categorie, symbole)
            ),
        )
        self.assertEqual([ligne["Actif"] for ligne in resultat], ["OK"])
        self.assertEqual(appels_progression, [(1, 3), (2, 3), (3, 3)])
        self.assertEqual(erreurs, [("Actions", "ERREUR")])

    def test_erreur_du_score_ignore_actif_et_continue(self):
        def calculer(info, donnees):
            if float(donnees["Close"].iloc[-1]) == 2:
                raise ValueError("score invalide")
            return score(50)

        erreurs = []
        resultat = analyser_watchlist(
            {"ETF": ["MAUVAIS", "BON"]},
            lambda symbole: historique(
                [1, 2] if symbole == "MAUVAIS" else [2, 3]
            ),
            calculer,
            error_callback=lambda categorie, symbole: erreurs.append(symbole),
        )
        self.assertEqual([ligne["Actif"] for ligne in resultat], ["BON"])
        self.assertEqual(erreurs, ["MAUVAIS"])

    def test_tri_deterministe_score_categorie_actif(self):
        scores = {"Z": 80, "A": 80, "M": 90, "B": 80}
        resultat = analyser_watchlist(
            {"ETF": ["Z", "A"], "Actions": ["M", "B"]},
            lambda symbole: pd.DataFrame({
                "Close": [10, 11], "ScoreTest": [scores[symbole]] * 2,
            }),
            lambda info, donnees: score(int(donnees["ScoreTest"].iloc[-1])),
        )
        self.assertEqual(
            [(ligne["Score"], ligne["Catégorie"], ligne["Actif"])
             for ligne in resultat],
            [(90, "Action", "M"), (80, "Action", "B"),
             (80, "ETF", "A"), (80, "ETF", "Z")],
        )

    def test_tri_conserve_ordre_pour_cles_identiques(self):
        appels = iter(("premier", "second"))

        resultat = analyser_watchlist(
            {"ETF": ["DUP", "DUP"]},
            lambda symbole: historique([10, 11]),
            lambda info, donnees: score(80, raisons=[next(appels)]),
        )

        self.assertEqual(
            [ligne["Raisons"] for ligne in resultat],
            [["premier"], ["second"]],
        )

    def test_watchlist_vide(self):
        appels = []
        self.assertEqual(
            analyser_watchlist(
                {}, lambda symbole: None, lambda info, donnees: score(0),
                progress_callback=lambda traites, total: appels.append(
                    (traites, total)
                ),
            ),
            [],
        )
        self.assertEqual(appels, [])

    def test_csv_schema_scalaire_et_bom(self):
        donnees = [{
            "Catégorie": "Action", "Actif": "ABC", "Prix": 12.5,
            "Variation %": 1.2, "RSI": 51.0, "Score": 70,
            "Signal": "ACHAT", "Raisons": ["ne doit pas apparaître"],
            "Historique": historique([1, 2]),
            "Ventilation": [{"critere": "RSI", "contribution": 10}],
        }]
        contenu = generer_csv(donnees)
        self.assertTrue(contenu.startswith(b"\xef\xbb\xbf"))
        texte = contenu.decode("utf-8-sig")
        lignes = list(csv.reader(io.StringIO(texte), delimiter=";"))
        self.assertEqual(lignes[0], list(CSV_COLUMNS))
        self.assertEqual(len(lignes[1]), len(CSV_COLUMNS))
        self.assertNotIn("Raisons", texte)
        self.assertNotIn("Historique", texte)
        self.assertNotIn("Ventilation", texte)
        self.assertNotIn("DataFrame", texte)

    def test_csv_vide_contient_entete_stable(self):
        texte = generer_csv([]).decode("utf-8-sig")
        lignes = list(csv.reader(io.StringIO(texte), delimiter=";"))
        self.assertEqual(lignes, [list(CSV_COLUMNS)])

    def test_module_metier_simporte_sans_streamlit(self):
        commande = (
            "import sys; import scanner_core; "
            "assert 'streamlit' not in sys.modules"
        )
        resultat = subprocess.run(
            [sys.executable, "-c", commande], capture_output=True, text=True,
            check=False,
        )
        self.assertEqual(resultat.returncode, 0, resultat.stderr)


    def test_ventilation_native_complete_ordonnee_et_independante(self):
        source = [
            {
                "critere": "RSI",
                "valeur": np.float64(51.25),
                "contribution": np.int64(10),
                "raison": "RSI équilibré",
                "actif": True,
                7: (np.int64(1), {"liste": [np.float64(2.5)]}),
                "non_finis": [float("nan"), float("inf"), -float("inf")],
            },
            "entrée ignorée",
            {"critere": "MACD", "contribution": -10, "inconnu": {"x": 1}},
        ]
        resultat_score = score(70)
        resultat_score["ventilation"] = source
        resultat = analyser_watchlist(
            {"Actions": ["ABC"]},
            lambda symbole: historique([10, 11]),
            lambda info, donnees: resultat_score,
        )
        ventilation = resultat[0]["Ventilation"]
        self.assertEqual([entree["critere"] for entree in ventilation], ["RSI", "MACD"])
        self.assertEqual(ventilation[0]["valeur"], 51.25)
        self.assertIs(type(ventilation[0]["valeur"]), float)
        self.assertIs(type(ventilation[0]["contribution"]), int)
        self.assertIs(ventilation[0]["actif"], True)
        self.assertEqual(ventilation[0]["7"], [1, {"liste": [2.5]}])
        self.assertEqual(ventilation[0]["non_finis"], [None, None, None])
        self.assertEqual(ventilation[1]["raison"] if "raison" in ventilation[1] else None, None)
        self.assertEqual(ventilation[1]["inconnu"], {"x": 1})
        json.dumps(resultat, ensure_ascii=False, allow_nan=False)

        ventilation[0]["7"][1]["liste"].append(3.5)
        self.assertEqual(source[0][7][1]["liste"], [np.float64(2.5)])
        source[0][7][1]["liste"].append(np.float64(4.5))
        self.assertEqual(ventilation[0]["7"][1]["liste"], [2.5, 3.5])

    def test_ventilation_absente_none_ou_non_liste_devient_vide(self):
        for ventilation in (None, "invalide", {}, ({} ,)):
            with self.subTest(ventilation=ventilation):
                resultat_score = score(50)
                resultat_score["ventilation"] = ventilation
                resultat = analyser_watchlist(
                    {"ETF": ["ABC"]}, lambda symbole: historique([1, 2]),
                    lambda info, donnees: resultat_score,
                )
                self.assertEqual(resultat[0]["Ventilation"], [])

    def test_un_seul_chargement_et_calcul_deterministe(self):
        appels = {"chargeur": 0, "calculateur": 0}
        source = [{"critere": "Volume", "contribution": 0, "raison": "Neutre"}]

        def charger(symbole):
            appels["chargeur"] += 1
            return historique([10, 11])

        def calculer(info, donnees):
            appels["calculateur"] += 1
            resultat = score(60)
            resultat["ventilation"] = source
            return resultat

        premier = analyser_watchlist({"ETF": ["ABC"]}, charger, calculer)
        self.assertEqual(appels, {"chargeur": 1, "calculateur": 1})
        appels = {"chargeur": 0, "calculateur": 0}
        second = analyser_watchlist({"ETF": ["ABC"]}, charger, calculer)
        self.assertEqual(premier, second)
        self.assertEqual(appels, {"chargeur": 1, "calculateur": 1})
        self.assertNotIn("Historique", premier[0])
        self.assertNotIn("EMA", premier[0])
        self.assertNotIn("Décision", premier[0])
        self.assertNotIn("Recommandation", premier[0])
        self.assertNotIn("Confiance", premier[0])

    def test_scanner_masque_ventilation_et_decision_limitee_a_interface(self):
        racine = Path(__file__).resolve().parents[1]
        source = (racine / "scanner.py").read_text(encoding="utf-8")
        source_core = (racine / "scanner_core.py").read_text(encoding="utf-8")
        self.assertIn('colonnes_masquees = ["Raisons", "Historique", "Ventilation"]', source)
        self.assertIn("from core.decision import construire_decision", source)
        self.assertIn("from ui.decision_card import afficher_decision_prudente", source)
        self.assertEqual(source.count("construire_decision("), 1)
        self.assertNotIn("core.decision", source_core)
        self.assertNotIn("ui.decision_card", source_core)
        self.assertNotIn("construire_decision", source_core)
        self.assertNotIn("calculer_score(", source)
        self.assertNotIn("charger_donnees(", source)
        self.assertIn('st.header("🔎 Scanner IA")', source)
        self.assertIn("🔎 Actif en tête du classement technique", source)
        self.assertIn('metric("📈 Score moyen"', source)

    def test_csv_schema_reste_strictement_inchange_avec_ventilation(self):
        self.assertEqual(CSV_COLUMNS, (
            "Catégorie", "Actif", "Prix", "Variation %", "RSI", "Score", "Signal",
        ))
        contenu = generer_csv([{
            "Catégorie": "Action", "Actif": "ABC", "Prix": 10.0,
            "Variation %": 1.0, "RSI": 50.0, "Score": 60,
            "Signal": "SURVEILLER", "Raisons": ["Raison"],
            "Ventilation": [{"critere": "RSI"}],
        }])
        self.assertTrue(contenu.startswith(b"\xef\xbb\xbf"))
        texte = contenu.decode("utf-8-sig")
        lignes = list(csv.reader(io.StringIO(texte), delimiter=";"))
        self.assertEqual(lignes[0], list(CSV_COLUMNS))
        self.assertEqual(len(lignes[1]), 7)
        self.assertNotIn("Ventilation", texte)
        self.assertNotIn("Raisons", texte)



if __name__ == "__main__":
    unittest.main()
