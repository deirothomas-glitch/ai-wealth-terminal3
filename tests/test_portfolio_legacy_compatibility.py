"""Régressions de compatibilité des positions historiques du portefeuille."""
import math
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

import portfolio
from core.portfolio import (
    calculer_gain_perte_non_realise,
    construire_resume_global,
    normaliser_position,
    resumer_position,
)
import services.portfolio_operations as operations
from services.portfolio_prices import charger_prix_portefeuille


class _Contexte:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class _StreamlitFormulaire:
    def __init__(self):
        self.session_state = SimpleNamespace(portfolio_prix={"MSFT": 420.0})
        self.valeurs_numeriques = []
        self.avertissements = []

    def expander(self, *_args, **_kwargs): return _Contexte()
    def tabs(self, labels): return [_Contexte() for _ in labels]
    def form(self, *_args, **_kwargs): return _Contexte()
    def number_input(self, _label, **kwargs):
        valeur = kwargs["value"]
        self.valeurs_numeriques.append(valeur)
        return valeur
    def text_area(self, *_args, **kwargs): return kwargs.get("value", "")
    def form_submit_button(self, *_args, **_kwargs): return False
    def date_input(self, *_args, **kwargs): return kwargs["value"]
    def checkbox(self, *_args, **_kwargs): return False
    def button(self, *_args, **_kwargs): return False
    def warning(self, message): self.avertissements.append(message)


def _position(**changements):
    base = {
        "identifiant": "historique-msft",
        "symbole": "MSFT",
        "quantite": 10,
        "prix_entree": None,
        "stop_loss": None,
        "objectif": None,
        "date_ouverture": "2024-01-01",
        "notes": "ancienne position",
    }
    base.update(changements)
    return base


class PortfolioLegacyCompatibilityTests(unittest.TestCase):
    def test_prix_entree_none_ou_absent_reste_indisponible(self):
        for position in (_position(), _position(prix_entree=None), {k: v for k, v in _position().items() if k != "prix_entree"}):
            resume = resumer_position(position, 420)
            self.assertIsNone(resume["prix_entree"])
            self.assertIsNone(resume["montant_investi"])
            self.assertIsNone(resume["gain_perte"])
            self.assertEqual(resume["statut"], "prix d’entrée indisponible")

    def test_anciennes_cles_sont_interpretees_sans_mutation(self):
        ancien = _position(prix_entree=None, prix_achat="100.5", objectif_prix="130", date_ouverture=None, date_ajout="2023-12-01")
        avant = deepcopy(ancien)
        normalise = normaliser_position(ancien)
        self.assertEqual(ancien, avant)
        self.assertEqual(normalise["prix_entree"], 100.5)
        self.assertEqual(normalise["objectif"], 130.0)
        self.assertEqual(normalise["date_ouverture"], "2023-12-01")

    def test_quantite_et_seuils_invalides_ne_provoquent_aucun_calcul_invente(self):
        for invalide in (None, "abc", float("nan"), float("inf"), float("-inf")):
            position = _position(quantite=invalide, prix_entree=invalide, stop_loss=invalide, objectif=invalide)
            normalise = normaliser_position(position)
            self.assertIsNone(normalise["quantite"])
            self.assertIsNone(normalise["prix_entree"])
            self.assertIsNone(normalise["stop_loss"])
            self.assertIsNone(normalise["objectif"])
            self.assertIsNone(calculer_gain_perte_non_realise(position, 420))

    def test_formulaire_historique_souvre_avec_des_valeurs_numeriques_finies(self):
        position = _position(quantite="incorrecte", prix_entree=None, stop_loss=None, objectif=float("inf"))
        avant = deepcopy(position)
        faux_st = _StreamlitFormulaire()
        with patch.object(portfolio, "st", faux_st):
            portfolio._actions(position)
        self.assertEqual(position, avant)
        self.assertEqual(len(faux_st.valeurs_numeriques), 5)
        self.assertTrue(all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in faux_st.valeurs_numeriques))
        self.assertIn(0.0, faux_st.valeurs_numeriques)
        self.assertTrue(any("Prix d’entrée indisponible" in message for message in faux_st.avertissements))

    def test_prix_invalide_ne_peut_pas_etre_sauvegarde_meme_avec_ancienne_cle(self):
        historique = _position(prix_achat=100)
        with patch.object(operations, "sauvegarder_portefeuille") as sauver_positions, patch.object(operations, "sauvegarder_journal") as sauver_journal:
            with self.assertRaisesRegex(ValueError, "prix d’entrée"):
                operations.modifier_position([historique], [], "historique-msft", {"prix_entree": 0})
        sauver_positions.assert_not_called()
        sauver_journal.assert_not_called()

    def test_cloture_refuse_quantite_ou_prix_entree_invalide_sans_ecriture(self):
        cas = [
            (_position(quantite="abc", prix_entree=100), "quantité valide"),
            (_position(quantite=10, prix_entree=None), "prix d’entrée valide"),
        ]
        for position, message in cas:
            with self.subTest(message=message), patch.object(operations, "sauvegarder_portefeuille") as sauver_positions, patch.object(operations, "sauvegarder_journal") as sauver_journal:
                with self.assertRaisesRegex(ValueError, message):
                    operations.cloturer_position([position], [], "historique-msft", 420, "2026-07-26")
                sauver_positions.assert_not_called()
                sauver_journal.assert_not_called()

    def test_suppression_reste_possible_pour_une_position_invalide(self):
        invalide = _position(quantite=None, prix_entree=None)
        autre = _position(identifiant="autre", symbole="AAPL", quantite=1, prix_entree=200)
        with patch.object(operations, "sauvegarder_portefeuille"), patch.object(operations, "sauvegarder_journal"):
            positions, journal = operations.supprimer_position([invalide, autre], [], "historique-msft")
        self.assertEqual([p["identifiant"] for p in positions], ["autre"])
        self.assertEqual(journal[-1]["type_evenement"], "suppression")

    def test_resume_global_reste_utilisable_et_ninvente_pas_de_capital(self):
        resume = construire_resume_global([_position()], {"MSFT": float("inf")})
        self.assertIsNone(resume["capital_investi"])
        self.assertIsNone(resume["valeur_actuelle"])
        self.assertIsNone(resume["gain_perte_non_realise"])
        self.assertEqual(resume["positions_sans_prix"], 1)
        self.assertEqual(portfolio._format(None, " €"), "Indisponible")
        self.assertEqual(portfolio._format(float("nan")), "Indisponible")

    def test_migration_en_memoire_preserve_source_et_champs_existants(self):
        ancien = {"symbole": "msft", "quantite": 10, "prix_achat": 100, "objectif_prix": 140, "date_ajout": "2020-01-01", "champ_historique": "conserver"}
        avant = deepcopy(ancien)
        migre = portfolio._migrer(ancien)
        self.assertEqual(ancien, avant)
        self.assertEqual(migre["prix_entree"], 100.0)
        self.assertEqual(migre["objectif"], 140.0)
        self.assertEqual(migre["date_ouverture"], "2020-01-01")
        self.assertEqual(migre["champ_historique"], "conserver")

    def test_prix_courant_infini_est_rejete(self):
        class Historique:
            empty = False
        prix, erreurs = charger_prix_portefeuille([_position()], lambda _symbole: Historique(), lambda _historique: float("inf"))
        self.assertEqual(prix, {"MSFT": None})
        self.assertEqual(erreurs, ["Prix indisponible pour MSFT."])


if __name__ == "__main__":
    unittest.main()
