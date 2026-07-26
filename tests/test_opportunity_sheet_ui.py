"""Tests du rendu ordonné de la fiche d’opportunité."""

import unittest
from core.opportunity_sheet import construire_fiche_opportunite
from ui.opportunity_sheet import afficher_fiche_opportunite


class Colonne:
    def __init__(self, appels): self.appels=appels
    def metric(self,*args,**kwargs): self.appels.append(("metric",args,kwargs))


class UI:
    def __init__(self): self.appels=[]
    def columns(self,n): return [Colonne(self.appels) for _ in range(n)]
    def __getattr__(self,nom):
        def appel(*args,**kwargs): self.appels.append((nom,args,kwargs))
        return appel


class OpportunitySheetUITests(unittest.TestCase):
    def test_sections_un_a_huit_dans_ordre(self):
        fiche=construire_fiche_opportunite({"Actif":"AAPL","Score":70},{},{"recommandation":"Attendre","confiance":50},{},{})
        ui=UI(); afficher_fiche_opportunite(ui,fiche,lambda data,interface: interface.caption("scenarios"),lambda data,limite: None)
        texte=str(ui.appels)
        positions=[texte.index(f"{n}.") for n in range(1,9)]
        self.assertEqual(positions,sorted(positions))
        self.assertIn("ne représente pas une probabilité de gain",texte)

    def test_rendu_invalide_sans_traceback(self):
        ui=UI(); afficher_fiche_opportunite(ui,None)
        self.assertIn("Fiche d’opportunité",str(ui.appels))


if __name__ == "__main__": unittest.main()
