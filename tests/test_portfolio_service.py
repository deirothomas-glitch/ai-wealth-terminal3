"""Tests du service d'orchestration de la valorisation."""

import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from services.portfolio_service import collecter_valorisation


class FauxIloc:
    def __init__(self, valeurs, evenements=None):
        self.valeurs = valeurs
        self.evenements = evenements

    def __getitem__(self, index):
        if self.evenements is not None:
            self.evenements.append(f"historique:iloc:{index}")
        return self.valeurs[index]


class FausseSerie:
    def __init__(self, valeurs, evenements=None):
        self.iloc = FauxIloc(valeurs, evenements)


class FauxHistorique:
    def __init__(self, clotures=(10.0, 12.0), vide=False, evenements=None):
        self.clotures = list(clotures)
        self.empty = vide
        self.evenements = evenements

    def __len__(self):
        return len(self.clotures)

    def __getitem__(self, cle):
        if self.evenements is not None:
            self.evenements.append(f"historique:{cle}")
        if cle != "Close":
            raise KeyError(cle)
        return FausseSerie(self.clotures, self.evenements)


def position(symbole="ABC", quantite=2.0, prix_achat=10.0,
             stop_loss=8.0, objectif_prix=15.0):
    return {
        "symbole": symbole,
        "quantite": quantite,
        "prix_achat": prix_achat,
        "stop_loss": stop_loss,
        "objectif_prix": objectif_prix,
    }


def normaliser_identite(valeur):
    return valeur


class PortfolioServiceTests(unittest.TestCase):
    def test_position_valide_produit_structure_exacte(self):
        historique = FauxHistorique((11.0, 12.0))
        lignes, erreurs = collecter_valorisation(
            [position()], 10_000.0, 1.0,
            lambda symbole: historique,
            lambda donnees: 12.0,
            normaliser_identite,
        )

        self.assertEqual(erreurs, [])
        self.assertEqual(lignes, [{
            "Actif": "ABC",
            "Quantité": 2.0,
            "Prix achat": 10.0,
            "Cours actuel": 12.0,
            "Valeur": 24.0,
            "Gain (€)": 4.0,
            "Gain (%)": 20.0,
            "Variation jour (%)": 9.09,
            "Stop-loss": 8.0,
            "Objectif prix": 15.0,
            "Distance stop (%)": 20.0,
            "Risque potentiel (€)": 4.0,
            "Risque capital (%)": 0.04,
            "Taille suggérée": 50.0,
            "Allocation (%)": 100.0,
        }])

    def test_positions_dupliquees_conservent_ordre_et_multiplicite(self):
        positions = [position(" dup ", 1), position("dup", 2)]
        lignes, erreurs = collecter_valorisation(
            positions, 10_000, 1,
            lambda symbole: FauxHistorique(),
            lambda historique: 12,
            normaliser_identite,
        )
        self.assertEqual(erreurs, [])
        self.assertEqual([ligne["Actif"] for ligne in lignes], ["DUP", "DUP"])
        self.assertEqual([ligne["Quantité"] for ligne in lignes], [1.0, 2.0])

    def test_allocation_utilise_valeurs_deja_arrondies(self):
        historiques = {
            "A": FauxHistorique((0.01, 0.014)),
            "B": FauxHistorique((0.01, 0.016)),
        }
        prix = {"A": 0.014, "B": 0.016}
        lignes, _ = collecter_valorisation(
            [position("A", 1, 0, 0, 0), position("B", 1, 0, 0, 0)],
            10_000, 1,
            lambda symbole: historiques[symbole],
            lambda historique: historique.clotures[-1],
            normaliser_identite,
        )
        self.assertEqual([ligne["Valeur"] for ligne in lignes], [0.01, 0.02])
        self.assertEqual(
            [ligne["Allocation (%)"] for ligne in lignes], [33.33, 66.67]
        )

    def test_total_nul_produit_allocations_nulles(self):
        lignes, erreurs = collecter_valorisation(
            [position("A", 0), position("B", 0)], 10_000, 1,
            lambda symbole: FauxHistorique(),
            lambda historique: 12,
            normaliser_identite,
        )
        self.assertEqual(erreurs, [])
        self.assertEqual([ligne["Allocation (%)"] for ligne in lignes], [0.0, 0.0])

    def test_historique_absent_ou_vide_messages_exacts(self):
        for historique in (None, FauxHistorique(vide=True)):
            with self.subTest(historique=historique):
                extracteur = Mock(return_value=12)
                lignes, erreurs = collecter_valorisation(
                    [position("abc")], 10_000, 1,
                    lambda symbole: historique,
                    extracteur,
                    normaliser_identite,
                )
                self.assertEqual(lignes, [])
                self.assertEqual(
                    erreurs, ["Aucune donnée de marché disponible pour ABC."]
                )
                extracteur.assert_not_called()

    def test_exception_chargeur_message_exact_et_traitement_continue(self):
        def charger(symbole):
            if symbole == "ERREUR":
                raise RuntimeError("panne simulée")
            return FauxHistorique()

        lignes, erreurs = collecter_valorisation(
            [position("ERREUR"), position("OK")], 10_000, 1,
            charger, lambda historique: 12, normaliser_identite,
        )
        self.assertEqual([ligne["Actif"] for ligne in lignes], ["OK"])
        self.assertEqual(erreurs, ["Erreur pour ERREUR : panne simulée"])

    def test_exception_conversion_arrive_avant_chargement(self):
        class Inconvertible:
            def __float__(self):
                raise ValueError("quantité invalide")

        chargeur = Mock(return_value=FauxHistorique())
        lignes, erreurs = collecter_valorisation(
            [position("ABC", Inconvertible())], 10_000, 1,
            chargeur, lambda historique: 12, normaliser_identite,
        )
        self.assertEqual(lignes, [])
        self.assertEqual(erreurs, ["Erreur pour ABC : quantité invalide"])
        chargeur.assert_not_called()

    def test_exception_extracteur_prix_message_exact(self):
        def extraire(historique):
            raise ValueError("prix invalide")

        lignes, erreurs = collecter_valorisation(
            [position("ABC")], 10_000, 1,
            lambda symbole: FauxHistorique(), extraire, normaliser_identite,
        )
        self.assertEqual(lignes, [])
        self.assertEqual(erreurs, ["Erreur pour ABC : prix invalide"])

    def test_symbole_vide_utilise_message_historique(self):
        lignes, erreurs = collecter_valorisation(
            [position("")], 10_000, 1,
            lambda symbole: (_ for _ in ()).throw(RuntimeError("indisponible")),
            lambda historique: 12,
            normaliser_identite,
        )
        self.assertEqual(lignes, [])
        self.assertEqual(erreurs, ["Erreur pour la position : indisponible"])

    def test_normalisateur_recoit_dictionnaire_original(self):
        originale = {"symbole": "OLD", "quantite": 1, "prix_achat": 10}
        identifiants = []

        def normaliser(valeur):
            identifiants.append(id(valeur))
            valeur.setdefault("stop_loss", 0.0)
            valeur.setdefault("objectif_prix", 0.0)
            return valeur

        lignes, erreurs = collecter_valorisation(
            [originale], 10_000, 1,
            lambda symbole: FauxHistorique(), lambda historique: 12,
            normaliser,
        )
        self.assertEqual(erreurs, [])
        self.assertEqual(identifiants, [id(originale)])
        self.assertIn("stop_loss", originale)
        self.assertEqual(lignes[0]["Actif"], "OLD")

    def test_exception_normalisateur_reste_hors_du_try(self):
        def normaliser(position_originale):
            raise RuntimeError("normalisation impossible")

        with self.assertRaisesRegex(RuntimeError, "normalisation impossible"):
            collecter_valorisation(
                [position()], 10_000, 1,
                lambda symbole: FauxHistorique(), lambda historique: 12,
                normaliser,
            )

    def test_ordre_observable_des_operations(self):
        evenements = []

        class PositionTracee(dict):
            def get(self, cle, defaut=None):
                evenements.append(f"get:{cle}")
                return super().get(cle, defaut)

        originale = PositionTracee(position())
        historique = FauxHistorique((11, 12), evenements=evenements)

        def normaliser(valeur):
            evenements.append("normaliser")
            return valeur

        def charger(symbole):
            evenements.append(f"charger:{symbole}")
            return historique

        def dernier_prix(donnees):
            evenements.append("dernier_prix")
            return 12

        collecter_valorisation(
            [originale], 10_000, 1, charger, dernier_prix, normaliser
        )
        self.assertEqual(evenements, [
            "normaliser",
            "get:symbole",
            "get:quantite",
            "get:prix_achat",
            "get:stop_loss",
            "get:objectif_prix",
            "charger:ABC",
            "dernier_prix",
            "historique:Close",
            "historique:iloc:-2",
        ])

    def test_liste_vide(self):
        self.assertEqual(
            collecter_valorisation(
                [], 10_000, 1, Mock(), Mock(), Mock()
            ),
            ([], []),
        )

    def test_wrapper_transmet_exactement_dependances_et_positions(self):
        import portfolio

        positions = [position()]
        retour = ([{"Actif": "ABC"}], [])
        service = Mock(return_value=retour)
        faux_st = SimpleNamespace(
            session_state=SimpleNamespace(portfolio=positions)
        )
        with patch.object(portfolio, "collecter_valorisation", service), \
                patch.object(portfolio, "st", faux_st):
            resultat = portfolio._collecter_valorisation(10_000.0, 1.0)

        self.assertIs(resultat, retour)
        service.assert_called_once_with(
            positions,
            10_000.0,
            1.0,
            portfolio.charger_donnees,
            portfolio.dernier_prix,
            portfolio._normaliser_position,
        )

    def test_import_isole_sans_dependances_interdites(self):
        interdits = {
            "streamlit", "pandas", "market_data", "storage", "yfinance",
            "plotly", "openai",
        }
        commande = (
            "import sys; import services.portfolio_service; "
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
