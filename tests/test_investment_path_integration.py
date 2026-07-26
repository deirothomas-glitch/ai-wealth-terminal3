"""Garanties du parcours Cockpit → Scanner → fiche → actions."""

from pathlib import Path
import math
import unittest

from scanner import _champs_fiables_position, _valeur_numerique_session

ROOT=Path(__file__).resolve().parents[1]


class InvestmentPathIntegrationTests(unittest.TestCase):
    def test_navigation_partagee_et_cockpit_ouvre_scanner(self):
        app=(ROOT/"app.py").read_text(encoding="utf-8")
        cockpit=(ROOT/"ui/investor_cockpit.py").read_text(encoding="utf-8")
        self.assertIn('key="navigation"',app)
        self.assertIn('st.session_state.navigation = "🔎 Scanner"',cockpit)
        self.assertIn("selected_asset",cockpit)

    def test_scanner_transmet_selection_aux_autres_ecrans(self):
        scanner=(ROOT/"scanner.py").read_text(encoding="utf-8")
        assistant=(ROOT/"pages/assistant_page.py").read_text(encoding="utf-8")
        app=(ROOT/"app.py").read_text(encoding="utf-8")
        self.assertIn("st.session_state.selected_asset = symbole_selectionne",scanner)
        self.assertIn("selection_parcours",assistant)
        self.assertIn("selection_parcours",app)

    def test_dashboard_ne_duplique_aucune_analyse_detaillee(self):
        source=(ROOT/"dashboard.py").read_text(encoding="utf-8")
        self.assertIn("afficher_cockpit",source)
        for interdit in ("calculer_score","construire_decision","construire_plan_risque","charger_donnees"):
            self.assertNotIn(interdit,source)

    def test_actions_sont_sans_ordre_automatique(self):
        source=(ROOT/"scanner.py").read_text(encoding="utf-8")
        for texte in ("Surveiller","Préparer une position","Ajouter au portefeuille","Documenter","Aucune action ne passe d’ordre"):
            self.assertIn(texte,source)


    def test_capital_absent_devient_valeur_widget_sure(self):
        self.assertEqual(_valeur_numerique_session(None), 0.0)

    def test_capital_invalide_ou_non_fini_est_rejete(self):
        for valeur in ("1000", float("nan"), float("inf"), -1):
            with self.subTest(valeur=valeur):
                self.assertEqual(_valeur_numerique_session(valeur), 0.0)

    def test_risque_superieur_au_plafond_est_rejete(self):
        self.assertEqual(_valeur_numerique_session(101, maximum=100), 0.0)
        self.assertEqual(_valeur_numerique_session(2.0, maximum=100), 2.0)

    def test_preparation_ne_conserve_que_les_valeurs_fiables(self):
        plan = {"prix_entree": 100, "stop_loss": 95, "objectif": 110, "taille_position": 2.5}
        self.assertEqual(
            _champs_fiables_position("AAPL", plan),
            {"symbole": "AAPL", "prix_entree": 100.0, "stop_loss": 95.0, "objectif": 110.0, "taille_position": 2.5},
        )

    def test_preparation_n_invente_pas_de_prix(self):
        plan = {"prix_entree": None, "stop_loss": float("nan"), "objectif": -1}
        self.assertEqual(_champs_fiables_position("MSFT", plan), {"symbole": "MSFT"})

    def test_identite_de_selection_inclut_rang_categorie_et_symbole(self):
        source = (ROOT / "scanner.py").read_text(encoding="utf-8")
        self.assertIn("identifiants = [", source)
        self.assertIn("x.get('categorie'", source)
        self.assertIn("opportunite_selectionnee = classement[index_actif]", source)

    def test_echec_ia_conserve_la_fiche_deterministe(self):
        source = (ROOT / "scanner.py").read_text(encoding="utf-8")
        self.assertIn("except Exception:", source)
        self.assertIn("La fiche ", source)
        self.assertIn("déterministe et le plan de risque restent accessibles.", source.replace('"\n                "', ""))

    def test_ajout_portefeuille_est_bloque_sans_prix_valide(self):
        source = (ROOT / "scanner.py").read_text(encoding="utf-8")
        self.assertIn('disabled=plan_risque.get("prix_entree") is None', source)
        self.assertIn("on_click=ouvrir_portefeuille", source)


    def test_tableau_ne_melange_pas_texte_et_nombre_dans_le_score(self):
        source = (ROOT / "ui" / "opportunity_table.py").read_text(encoding="utf-8")
        self.assertIn('"Indisponible"', source)
        self.assertIn('TextColumn(width="small")', source)
        self.assertNotIn("ProgressColumn", source)


if __name__ == "__main__": unittest.main()
