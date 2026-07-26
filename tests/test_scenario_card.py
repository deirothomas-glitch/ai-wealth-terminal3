"""Tests du rendu UI multi-scénarios."""

import unittest
from core.scenario_engine import construire_scenarios
from ui.scenario_card import afficher_scenario_principal, afficher_scenarios


class Contexte:
    def __enter__(self): return self
    def __exit__(self, *_): return False


class St:
    def __init__(self): self.appels=[]
    def __getattr__(self, nom):
        def appel(*args, **kwargs):
            self.appels.append((nom, args, kwargs))
            if nom == "tabs": return [Contexte(), Contexte(), Contexte()]
            return Contexte()
        return appel


class ScenarioCardTests(unittest.TestCase):
    def test_rendu_des_trois_scenarios_et_confiance(self):
        st=St(); resultat=construire_scenarios({"facteurs_favorables":["EMA"],"donnees_manquantes":["volume"]})
        afficher_scenarios(resultat, st)
        texte=str(st.appels)
        for attendu in ("Scénario haussier", "Scénario neutre", "Scénario baissier", "Confiance", "Données manquantes"):
            self.assertIn(attendu, texte)
        self.assertIn("données partielles", texte)
        self.assertIn("awt-badge--bad", texte)

    def test_rendu_principal_uniquement(self):
        st=St(); resultat=construire_scenarios({"facteurs_defavorables":["MACD"]})
        afficher_scenario_principal(resultat, st)
        texte=str(st.appels)
        self.assertIn("Scénario principal", texte)
        self.assertIn("Scénario baissier", texte)
        self.assertNotIn("Scénario haussier", texte)
        self.assertIn("Vigilance principale", texte)
        self.assertNotIn("Facteurs favorables", texte)

    def test_repli_entree_invalide_sans_exception(self):
        st=St()
        afficher_scenarios(None, st)
        self.assertIn("Analyse multi-scénarios", str(st.appels))


if __name__ == "__main__": unittest.main()
