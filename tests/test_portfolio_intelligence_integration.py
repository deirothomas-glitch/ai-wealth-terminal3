"""Garanties d’intégration sans chargement supplémentaire."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PortfolioIntelligenceIntegrationTests(unittest.TestCase):
    def test_page_portefeuille_reutilise_positions_et_prix_de_session(self):
        source = (ROOT / "portfolio.py").read_text(encoding="utf-8")
        self.assertIn("analyser_portefeuille(st.session_state.portfolio,st.session_state.portfolio_prix)", source)
        self.assertEqual(source.count("afficher_intelligence_portefeuille(st,intelligence)"), 1)

    def test_cockpit_reutilise_le_meme_composant(self):
        source = (ROOT / "ui/investor_cockpit.py").read_text(encoding="utf-8")
        self.assertIn("afficher_intelligence_portefeuille", source)
        self.assertEqual(source.count("afficher_intelligence_portefeuille("), 1)

    def test_page_et_cockpit_utilisent_strictement_le_meme_resultat_metier(self):
        from core.cockpit import construire_cockpit
        from core.portfolio_intelligence import analyser_portefeuille

        positions = [None, {"symbole": "AAPL", "type_actif": "action", "quantite": 1}]
        prix = {"AAPL": 100}
        direct = analyser_portefeuille(positions, prix)
        cockpit = construire_cockpit(
            positions=positions,
            prix_portefeuille=prix,
            portefeuille_charge=True,
        )["intelligence_portefeuille"]
        self.assertEqual(cockpit, direct)

    def test_moteur_ne_depend_ni_du_reseau_ni_de_linterface(self):
        source = (ROOT / "core/portfolio_intelligence.py").read_text(encoding="utf-8").casefold()
        for interdit in ("streamlit", "openai", "yfinance", "market_data", "charger_donnees", "storage"):
            self.assertNotIn(interdit, source)


if __name__ == "__main__":
    unittest.main()
