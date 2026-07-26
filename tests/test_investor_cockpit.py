"""Tests du rendu défensif du Cockpit Investisseur."""

import unittest

from core.cockpit import construire_cockpit
from ui.investor_cockpit import afficher_cockpit


class Contexte:
    def __enter__(self): return self
    def __exit__(self, *_): return False


class Colonne(Contexte):
    def __init__(self, appels): self.appels = appels
    def metric(self, *args, **kwargs): self.appels.append(("metric", args, kwargs))


class Streamlit:
    def __init__(self, cliquer=False): self.appels=[]; self.cliquer=cliquer
    def columns(self, valeur):
        nombre = valeur if isinstance(valeur, int) else len(valeur)
        return [Colonne(self.appels) for _ in range(nombre)]
    def container(self, **kwargs): return Contexte()
    def markdown(self, *args, **kwargs): self.appels.append(("markdown", args, kwargs))
    def subheader(self, *args, **kwargs): self.appels.append(("subheader", args, kwargs))
    def caption(self, *args, **kwargs): self.appels.append(("caption", args, kwargs))
    def info(self, *args, **kwargs): self.appels.append(("info", args, kwargs))
    def warning(self, *args, **kwargs): self.appels.append(("warning", args, kwargs))
    def success(self, *args, **kwargs): self.appels.append(("success", args, kwargs))
    def error(self, *args, **kwargs): self.appels.append(("error", args, kwargs))
    def write(self, *args, **kwargs): self.appels.append(("write", args, kwargs))
    def button(self, *args, **kwargs): self.appels.append(("button", args, kwargs)); return self.cliquer


class InvestorCockpitTests(unittest.TestCase):
    def test_rendu_vide_sans_exception_et_sans_promesse(self):
        st = Streamlit(); demande = afficher_cockpit(st, construire_cockpit())
        texte = str(st.appels).casefold()
        self.assertFalse(demande)
        for attendu in ("résumé marché", "résumé portefeuille", "top opportunités", "alertes prioritaires", "briefing ia", "évènements de marché"):
            self.assertIn(attendu, texte)
        self.assertIn("ne constituent ni une garantie de gain ni un ordre automatique", texte)

    def test_donnees_partielles_et_bouton_ia(self):
        st = Streamlit(cliquer=True)
        demande = afficher_cockpit(st, construire_cockpit(indices=[{"variation": 1.0}]))
        self.assertTrue(demande)
        self.assertIn("données partielles", str(st.appels))
        bouton = next(appel for appel in st.appels if appel[0] == "button")
        self.assertEqual(bouton[2]["key"], "cockpit_briefing_generate")
        self.assertNotEqual(bouton[2]["key"], "cockpit_briefing_ia")

    def test_analyse_ia_affiche_confiance_disponible(self):
        st = Streamlit()
        afficher_cockpit(st, construire_cockpit(), {"resume": "Synthèse prudente", "niveau_confiance": "faible"})
        texte = str(st.appels)
        self.assertIn("Synthèse prudente", texte)
        self.assertIn("Confiance déclarée : faible", texte)


if __name__ == "__main__":
    unittest.main()
