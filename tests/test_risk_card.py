"""Tests du rendu Streamlit du plan de risque."""

import copy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from core.risk import construire_plan_risque
from ui.risk_card import (
    AVERTISSEMENT,
    PLAN_INDISPONIBLE,
    TAILLE_INDISPONIBLE,
    TITRE,
    afficher_plan_risque,
)


class _Colonne:
    def __init__(self, appels):
        self.appels = appels

    def metric(self, label, value):
        self.appels.append(("metric", label, value))


class _Streamlit:
    def __init__(self):
        self.appels = []

    def columns(self, nombre):
        return [_Colonne(self.appels) for _ in range(nombre)]

    def subheader(self, texte):
        self.appels.append(("subheader", texte))

    def caption(self, texte):
        self.appels.append(("caption", texte))

    def warning(self, texte):
        self.appels.append(("warning", texte))

    def info(self, texte):
        self.appels.append(("info", texte))

    def markdown(self, texte):
        self.appels.append(("markdown", texte))

    def write(self, texte):
        self.appels.append(("write", texte))


class RiskCardTests(unittest.TestCase):
    def _afficher(self, plan):
        faux = _Streamlit()
        with patch("ui.risk_card.st", faux):
            afficher_plan_risque(plan)
        return faux.appels

    def test_titre_et_avertissement_exacts(self):
        appels = self._afficher(construire_plan_risque(100, 5))
        self.assertEqual(appels[:2], [
            ("subheader", TITRE), ("caption", AVERTISSEMENT),
        ])

    def test_plan_partiel_affiche_metriques_et_absence_taille(self):
        appels = self._afficher(construire_plan_risque(100, 5))
        metriques = {
            appel[1]: appel[2] for appel in appels if appel[0] == "metric"
        }
        self.assertEqual(set(metriques), {
            "Prix d’entrée de référence", "ATR", "Stop-loss indicatif",
            "Objectif indicatif", "Risque par unité", "Ratio risque/rendement",
        })
        self.assertEqual(metriques["Ratio risque/rendement"], "1 : 2")
        self.assertIn(("info", TAILLE_INDISPONIBLE), appels)

    def test_plan_disponible_affiche_taille(self):
        appels = self._afficher(construire_plan_risque(100, 5, 10_000, 1))
        metriques = {
            appel[1]: appel[2] for appel in appels if appel[0] == "metric"
        }
        self.assertEqual(metriques["Capital de référence"], "10000.00 €")
        self.assertEqual(metriques["Risque maximal"], "1 %")
        self.assertEqual(metriques["Risque en euros"], "100.00 €")
        self.assertEqual(metriques["Taille de position indicative"], "10")
        self.assertNotIn(("info", TAILLE_INDISPONIBLE), appels)

    def test_plan_indisponible_sans_metrique_none(self):
        appels = self._afficher(construire_plan_risque(None, None))
        self.assertIn(("warning", PLAN_INDISPONIBLE), appels)
        self.assertFalse(any(appel[0] == "metric" for appel in appels))
        self.assertNotIn("None", str(appels))

    def test_risques_et_decision_finale_non_dupliques(self):
        plan = construire_plan_risque(100, 5)
        appels = self._afficher(plan)
        for risque in plan["risques"]:
            self.assertEqual(appels.count(("write", f"• {risque}")), 1)
        self.assertEqual(
            appels.count(("caption", plan["decision_finale_utilisateur"])), 1
        )

    def test_absence_mutation(self):
        plan = construire_plan_risque(100, 5, 1000, 1)
        copie = copy.deepcopy(plan)
        self._afficher(plan)
        self.assertEqual(plan, copie)

    def test_aucune_instruction_ou_promesse_interdite(self):
        texte = str(self._afficher(construire_plan_risque(100, 5))).lower()
        for interdit in (
            "gain garanti", "rendement garanti", "achetez", "vendez",
            "passez un ordre", "investissez maintenant",
        ):
            self.assertNotIn(interdit, texte)

    def test_import_isole_sans_dependances_interdites(self):
        interdits = {"pandas", "yfinance", "openai"}
        code = (
            "import sys; import ui.risk_card; "
            f"interdits={interdits!r}; "
            "charges=interdits.intersection(sys.modules); "
            "assert not charges, charges"
        )
        resultat = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(resultat.returncode, 0, resultat.stderr)

    def test_aucun_calcul_metier_ni_acces_donnees(self):
        source = (
            Path(__file__).resolve().parents[1] / "ui/risk_card.py"
        ).read_text(encoding="utf-8")
        for interdit in (
            "calculer_atr", "construire_plan_risque", "market_data",
            "pandas", "yfinance", "openai",
        ):
            self.assertNotIn(interdit, source)


if __name__ == "__main__":
    unittest.main()
