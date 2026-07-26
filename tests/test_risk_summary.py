"""Tests du résumé Streamlit léger du risque."""

import copy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from core.risk import construire_plan_risque
from ui.risk_summary import AVERTISSEMENT, RAPPEL_PRUDENCE, RESUME_INDISPONIBLE, TITRE, afficher_resume_risque


class _Colonne:
    def __init__(self, appels): self.appels = appels
    def metric(self, label, value): self.appels.append(("metric", label, value))


class _Streamlit:
    def __init__(self): self.appels = []
    def columns(self, nombre): return [_Colonne(self.appels) for _ in range(nombre)]
    def subheader(self, texte): self.appels.append(("subheader", texte))
    def caption(self, texte): self.appels.append(("caption", texte))
    def warning(self, texte): self.appels.append(("warning", texte))


class RiskSummaryTests(unittest.TestCase):
    def _afficher(self, plan):
        faux = _Streamlit()
        with patch("ui.risk_summary.st", faux): afficher_resume_risque(plan)
        return faux.appels

    def test_import_titre_et_avertissement_exacts(self):
        self.assertTrue(callable(afficher_resume_risque))
        self.assertEqual(self._afficher(construire_plan_risque(100, 5))[:2], [("subheader", TITRE), ("caption", AVERTISSEMENT)])

    def test_plans_partiel_et_disponible_restent_synthetiques(self):
        for plan in (construire_plan_risque(100, 5), construire_plan_risque(100, 5, 10_000, 1)):
            appels = self._afficher(plan)
            metriques = {a[1]: a[2] for a in appels if a[0] == "metric"}
            self.assertEqual(metriques, {"ATR": "5", "Stop-loss indicatif": "90", "Objectif indicatif": "120", "Ratio risque/rendement": "1 : 2"})
            texte = str(appels)
            for absent in ("Prix d’entrée", "Risque par unité", "Capital", "Risque maximal", "Risque en euros", "Taille de position"):
                self.assertNotIn(absent, texte)

    def test_format_huit_decimales_utiles_sans_monnaie(self):
        appels = self._afficher(construire_plan_risque(100.123456789, 1.234567891))
        metriques = {a[1]: a[2] for a in appels if a[0] == "metric"}
        self.assertEqual(metriques["ATR"], "1.23456789")
        self.assertNotIn("€", str(metriques))

    def test_prudence_decision_sans_liste_complete_des_risques(self):
        plan = construire_plan_risque(100, 5)
        appels = self._afficher(plan)
        self.assertIn(("caption", RAPPEL_PRUDENCE), appels)
        self.assertIn(("caption", plan["decision_finale_utilisateur"]), appels)
        for risque in plan["risques"]: self.assertNotIn(risque, str(appels))

    def test_plan_indisponible_sans_metrique_none(self):
        plan = construire_plan_risque(None, None)
        appels = self._afficher(plan)
        self.assertIn(("warning", RESUME_INDISPONIBLE), appels)
        self.assertFalse(any(a[0] == "metric" for a in appels))
        self.assertNotIn("None", str(appels))
        self.assertIn(("caption", plan["decision_finale_utilisateur"]), appels)

    def test_none_nan_et_infinis_non_affiches(self):
        plan = {"statut": "partiel", "atr": None, "stop_loss": float("nan"), "objectif": float("inf"), "ratio_risque_rendement": float("-inf"), "decision_finale_utilisateur": "Décision utilisateur."}
        appels = self._afficher(plan)
        self.assertFalse(any(a[0] == "metric" for a in appels))
        for absent in ("none", "nan", "inf"): self.assertNotIn(absent, str(appels).lower())

    def test_aucune_mutation(self):
        plan = construire_plan_risque(100, 5, 1000, 1)
        copie = copy.deepcopy(plan)
        self._afficher(plan)
        self.assertEqual(plan, copie)

    def test_aucune_instruction_achat_vente_ou_promesse(self):
        texte = str(self._afficher(construire_plan_risque(100, 5))).lower()
        for interdit in ("achetez", "vendez", "investissez maintenant", "gain garanti", "rendement garanti", "promesse de gain"):
            self.assertNotIn(interdit, texte)

    def test_import_isole_sans_dependances_interdites(self):
        interdits = {"pandas", "numpy", "yfinance", "openai"}
        code = "import sys; import ui.risk_summary; interdits=" + repr(interdits) + "; charges=interdits.intersection(sys.modules); assert not charges, charges"
        resultat = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)

    def test_aucun_calcul_metier_ni_acces_donnees(self):
        source = (Path(__file__).resolve().parents[1] / "ui/risk_summary.py").read_text(encoding="utf-8").lower()
        for interdit in ("calculer_atr", "construire_plan_risque", "market_data", "pandas", "numpy", "yfinance", "openai"):
            self.assertNotIn(interdit, source)


if __name__ == "__main__": unittest.main()
