"""Tests de la carte partagée d’intelligence du portefeuille."""

import unittest

from core.portfolio_intelligence import analyser_portefeuille
from ui.portfolio_intelligence_card import afficher_intelligence_portefeuille


class Colonne:
    def __init__(self, appels): self.appels = appels
    def metric(self, *args, **kwargs): self.appels.append(("metric", args, kwargs))


class Interface:
    def __init__(self): self.appels = []
    def columns(self, nombre): return [Colonne(self.appels) for _ in range(nombre)]
    def __getattr__(self, nom):
        def appel(*args, **kwargs): self.appels.append((nom, args, kwargs))
        return appel


class PortfolioIntelligenceCardTests(unittest.TestCase):
    def test_repli_portefeuille_vide_est_elegant(self):
        ui = Interface()
        afficher_intelligence_portefeuille(ui, analyser_portefeuille([], {}))
        texte = str(ui.appels)
        self.assertIn("portefeuille est vide", texte)
        self.assertNotIn("metric", [x[0] for x in ui.appels])

    def test_rendu_complet_affiche_expositions_diversification_et_manquantes(self):
        ui = Interface()
        analyse = analyser_portefeuille(
            [
                {"symbole": "AAPL", "type_actif": "action", "quantite": 2},
                {"symbole": "BTC-USD", "type_actif": "crypto", "quantite": 1},
                {"symbole": "MSFT", "type_actif": "action", "quantite": 1},
            ],
            {"AAPL": 100, "BTC-USD": 100},
        )
        afficher_intelligence_portefeuille(ui, analyse)
        texte = str(ui.appels)
        for attendu in ("Intelligence du portefeuille", "Diversification", "Exposition actions", "Exposition crypto", "Prix absents ou invalides", "MSFT"):
            self.assertIn(attendu, texte)
        self.assertEqual(sum(x[0] == "metric" for x in ui.appels), 4)
        for interdit in ("achetez", "vendez", "réduisez"):
            self.assertNotIn(interdit, texte.casefold())

    def test_mode_compact_evite_de_repeter_la_valeur_du_resume_cockpit(self):
        ui = Interface()
        analyse = analyser_portefeuille(
            [{"symbole": "AAPL", "type_actif": "action", "quantite": 1}],
            {"AAPL": 100},
        )
        afficher_intelligence_portefeuille(ui, analyse, compact=True)
        texte = str(ui.appels)
        self.assertNotIn("Valeur calculée", texte)
        self.assertEqual(sum(x[0] == "metric" for x in ui.appels), 3)

    def test_entree_invalide_ne_provoque_pas_exception(self):
        ui = Interface()
        afficher_intelligence_portefeuille(ui, None)
        texte = str(ui.appels)
        self.assertIn("Intelligence du portefeuille", texte)
        self.assertIn("pas encore disponibles", texte)


if __name__ == "__main__":
    unittest.main()
