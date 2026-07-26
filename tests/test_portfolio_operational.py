"""Tests du portefeuille opérationnel Sprint 3.3."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, patch
from core.portfolio import *
from core.position_alerts import construire_alertes_position
from services.portfolio_prices import charger_prix_portefeuille
import storage
import services.portfolio_operations as operations

def position(**extra):
    p={"identifiant":"p1","symbole":"abc","nom":"ABC","type_actif":"action","quantite":2,"prix_entree":100,"stop_loss":90,"objectif":120,"date_ouverture":"2026-01-01","notes":"test"}; p.update(extra); return p
class PortfolioOperationalTests(unittest.TestCase):
    def test_normalisation_et_absence_mutation(self):
        p=position(); original=deepcopy(p); n=normaliser_position(p); self.assertEqual(p,original); self.assertEqual(n["symbole"],"ABC")
    def test_validation(self):
        self.assertEqual(valider_position(position()),[])
        self.assertTrue(valider_position(position(symbole="",quantite=0,prix_entree=-1)))
    def test_calculs_gain_perte_performance(self):
        self.assertEqual(calculer_montant_investi(position()),200); self.assertEqual(calculer_valeur_actuelle(position(),110),220); self.assertEqual(calculer_gain_perte_non_realise(position(),90),-20); self.assertEqual(calculer_performance_pourcentage(position(),110),10)
    def test_prix_absent(self):
        r=resumer_position(position(),None); self.assertIsNone(r["valeur_actuelle"]); self.assertIsNone(r["gain_perte"]); self.assertEqual(r["statut"],"prix indisponible")
    def test_resume_global_contrat(self):
        r=construire_resume_global([position()],{"ABC":110},[{"type_evenement":"cloture","gain_perte_realise":5}]); self.assertEqual(set(r),{"nombre_positions","capital_investi","valeur_actuelle","gain_perte_non_realise","gain_perte_realise","performance_globale_pourcentage","positions_sans_prix"}); self.assertEqual(r["gain_perte_realise"],5)
    def test_statistiques(self):
        s=construire_statistiques_journal([{"type_evenement":"cloture","gain_perte_realise":20},{"type_evenement":"cloture","gain_perte_realise":-10}]); self.assertEqual(s["taux_reussite"],50); self.assertEqual(s["gain_total_realise"],10)
    def test_json_strict(self): json.dumps(resumer_position(position(),None),allow_nan=False)
    def test_alertes_stop_atteint(self): self.assertEqual(construire_alertes_position(position(),90)[0]["niveau"],"attention")
    def test_alertes_stop_proche(self): self.assertEqual(construire_alertes_position(position(),92)[0]["titre"],"Prix proche du stop")
    def test_alertes_objectif(self): self.assertTrue(any(a["categorie"]=="objectif" for a in construire_alertes_position(position(),120)))
    def test_alertes_prix_indisponible(self): self.assertEqual(construire_alertes_position(position(),None)[0]["categorie"],"donnees")
    def test_alertes_stop_absent(self): self.assertEqual(construire_alertes_position(position(stop_loss=None),100)[0]["categorie"],"risque")
    def test_alertes_aucun_seuil(self): self.assertEqual(construire_alertes_position(position(stop_loss=80,objectif=120),100),[])
    def test_alertes_contrat_invalide(self): self.assertEqual(construire_alertes_position({},100),[])
    def test_alertes_deterministes_sans_mutation(self):
        p=position(); avant=deepcopy(p); self.assertEqual(construire_alertes_position(p,90),construire_alertes_position(p,90)); self.assertEqual(p,avant)
    def test_formulations_interdites(self):
        texte=str(construire_alertes_position(position(stop_loss=None),100)).lower(); self.assertFalse(any(x in texte for x in ("vendez immédiatement","achetez maintenant","gain garanti","perte impossible","ordre automatique","position sûre")))
    def test_stockage_absent_vide_invalide_et_atomique(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"p.json"; self.assertEqual(storage.charger_portefeuille(p),[]); p.write_text("",encoding="utf-8"); self.assertEqual(storage.charger_portefeuille(p),[]); p.write_text("{oops",encoding="utf-8"); data,err=storage.charger_portefeuille_avec_erreur(p); self.assertEqual(data,[]); self.assertIsNotNone(err); self.assertEqual(p.read_text(),"{oops"); storage.sauvegarder_portefeuille([position()],p); self.assertEqual(storage.charger_portefeuille(p)[0]["symbole"],"abc"); self.assertFalse(list(Path(d).glob("*.tmp")))
    def test_un_prix_par_symbole_et_erreur_isolee(self):
        class H: empty=False
        charge=Mock(side_effect=lambda s: (_ for _ in ()).throw(ValueError("panne")) if s=="BAD" else H())
        prix,erreurs=charger_prix_portefeuille([position(symbole="abc"),position(symbole="ABC"),position(symbole="bad")],charge,lambda h:123); self.assertEqual(charge.call_count,2); self.assertEqual(prix,{"ABC":123.0,"BAD":None}); self.assertEqual(len(erreurs),1)
    def test_journal_ouverture(self):
        with patch.object(operations,"sauvegarder_portefeuille"), patch.object(operations,"sauvegarder_journal"):
            positions,journal=operations.ajouter_position([],[],position(identifiant=""))
        self.assertEqual(journal[-1]["type_evenement"],"ouverture"); self.assertEqual(journal[-1]["position_id"],positions[0]["identifiant"])
    def test_journal_modification(self):
        with patch.object(operations,"sauvegarder_portefeuille"), patch.object(operations,"sauvegarder_journal"):
            positions,journal=operations.modifier_position([position()],[],"p1",{"quantite":3})
        self.assertEqual(positions[0]["quantite"],3); self.assertEqual(journal[-1]["type_evenement"],"modification")
    def test_journal_cloture_contrat(self):
        with patch.object(operations,"sauvegarder_portefeuille"), patch.object(operations,"sauvegarder_journal"):
            positions,journal=operations.cloturer_position([position()],[],"p1",120,"2026-02-01","sortie")
        e=journal[-1]; self.assertEqual(positions,[]); self.assertEqual(e["type_evenement"],"cloture"); self.assertEqual(e["gain_perte_realise"],40); self.assertEqual(e["performance_pourcentage"],20)
    def test_journal_suppression_conserve_autres_positions(self):
        autre=position(identifiant="p2",symbole="XYZ")
        with patch.object(operations,"sauvegarder_portefeuille"), patch.object(operations,"sauvegarder_journal"):
            positions,journal=operations.supprimer_position([position(),autre],[],"p1")
        self.assertEqual([x["identifiant"] for x in positions],["p2"]); self.assertEqual(journal[-1]["type_evenement"],"suppression")
if __name__=="__main__": unittest.main()
