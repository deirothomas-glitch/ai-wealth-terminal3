"""Tests du modèle et du rendu de la recommandation prudente."""

import copy
import inspect
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import ui.decision_card as decision_card
from ui.decision_card import (
    DECISION_FINALE,
    FACTEURS_DEFAVORABLES_VIDES,
    FACTEURS_FAVORABLES_VIDES,
    QUALITE_EXPLICATION,
    QUALITE_LABEL,
    afficher_decision_prudente,
    construire_modele_affichage,
)


ORDRE_MODELE = (
    "titre",
    "recommandation_label",
    "recommandation",
    "qualite_label",
    "qualite",
    "qualite_explication",
    "resume",
    "facteurs_favorables_titre",
    "facteurs_favorables",
    "facteurs_defavorables_titre",
    "facteurs_defavorables",
    "facteurs_neutres_titre",
    "facteurs_neutres",
    "risques_titre",
    "risques",
    "donnees_manquantes_titre",
    "donnees_manquantes",
    "action_titre",
    "action_suggeree",
    "decision_finale",
)


def decision(recommandation="Surveiller", confiance=90,
             favorables=None, defavorables=None, neutres=None,
             risques=None, manquantes=None):
    return {
        "recommandation": recommandation,
        "confiance": confiance,
        "resume": f"Résumé {recommandation}",
        "facteurs_favorables": (
            ["Facteur favorable 1", "Facteur favorable 2"]
            if favorables is None else favorables
        ),
        "facteurs_defavorables": (
            ["Facteur défavorable 1", "Facteur défavorable 2"]
            if defavorables is None else defavorables
        ),
        "facteurs_neutres": [] if neutres is None else neutres,
        "risques": (
            ["Risque permanent 1", "Risque permanent 2"]
            if risques is None else risques
        ),
        "donnees_manquantes": [] if manquantes is None else manquantes,
        "action_suggeree": f"Action {recommandation}",
        "decision_finale_utilisateur": True,
    }


class FausseColonne:
    def __init__(self, appels):
        self.appels = appels

    def metric(self, label, value):
        self.appels.append(("metric", label, value))


class FauxStreamlit:
    def __init__(self):
        self.appels = []

    def columns(self, nombre):
        self.appels.append(("columns", nombre))
        return [FausseColonne(self.appels) for _ in range(nombre)]

    def subheader(self, texte):
        self.appels.append(("subheader", texte))

    def caption(self, texte):
        self.appels.append(("caption", texte))

    def write(self, texte):
        self.appels.append(("write", texte))

    def markdown(self, texte):
        self.appels.append(("markdown", texte))


class DecisionCardTests(unittest.TestCase):
    def test_modeles_surveille_attendre_eviter_et_insuffisant(self):
        cas = (
            ("Surveiller", 90),
            ("Attendre", 35),
            ("Éviter", 90),
            ("Attendre", 0),
        )
        for recommandation, confiance in cas:
            with self.subTest(recommandation=recommandation, confiance=confiance):
                modele = construire_modele_affichage(
                    decision(recommandation, confiance)
                )
                self.assertEqual(modele["recommandation"], recommandation)
                self.assertEqual(modele["qualite"], f"{confiance}/100")

    def test_ordre_exact_des_cles(self):
        self.assertEqual(
            tuple(construire_modele_affichage(decision())), ORDRE_MODELE
        )

    def test_format_et_libelle_qualite(self):
        modele = construire_modele_affichage(decision(confiance=90))
        self.assertEqual(modele["qualite"], "90/100")
        self.assertNotIn("%", modele["qualite"])
        self.assertEqual(modele["qualite_label"], QUALITE_LABEL)
        self.assertEqual(QUALITE_LABEL, "Couverture et cohérence techniques")
        self.assertIn("pas une probabilité de gain", modele["qualite_explication"])

    def test_facteurs_conserves_dans_leur_ordre(self):
        entree = decision(
            favorables=["F2", "F1"],
            defavorables=["D2", "D1"],
            neutres=["N2", "N1"],
        )
        modele = construire_modele_affichage(entree)
        self.assertEqual(modele["facteurs_favorables"], ["F2", "F1"])
        self.assertEqual(modele["facteurs_defavorables"], ["D2", "D1"])
        self.assertEqual(modele["facteurs_neutres"], ["N2", "N1"])

    def test_replis_exacts_facteurs_vides(self):
        modele = construire_modele_affichage(
            decision(favorables=[], defavorables=[])
        )
        self.assertEqual(
            modele["facteurs_favorables"], [FACTEURS_FAVORABLES_VIDES]
        )
        self.assertEqual(
            modele["facteurs_defavorables"], [FACTEURS_DEFAVORABLES_VIDES]
        )

    def test_facteurs_neutres_vides_sans_ajout(self):
        modele = construire_modele_affichage(decision(neutres=[]))
        self.assertEqual(modele["facteurs_neutres"], [])

    def test_risques_et_donnees_manquantes_conservent_ordre(self):
        modele = construire_modele_affichage(
            decision(risques=["R2", "R1"], manquantes=["M2", "M1"])
        )
        self.assertEqual(modele["risques"], ["R2", "R1"])
        self.assertTrue(modele["risques"])
        self.assertEqual(modele["donnees_manquantes"], ["M2", "M1"])

    def test_rappel_final_exact(self):
        modele = construire_modele_affichage(decision())
        self.assertEqual(
            modele["decision_finale"],
            "Décision finale : elle vous appartient.",
        )
        self.assertEqual(modele["decision_finale"], DECISION_FINALE)

    def test_signal_technique_absent_du_modele(self):
        entree = decision()
        entree["signal"] = "ACHAT"
        modele = construire_modele_affichage(entree)
        self.assertNotIn("signal", modele)
        self.assertNotIn("ACHAT", json.dumps(modele, ensure_ascii=False))

    def test_decision_non_mutee(self):
        entree = decision(favorables=[], defavorables=[], neutres=["N"])
        avant = copy.deepcopy(entree)
        construire_modele_affichage(entree)
        self.assertEqual(entree, avant)

    def test_determinisme_et_json_strict(self):
        entree = decision(manquantes=["Volume"])
        premier = construire_modele_affichage(entree)
        second = construire_modele_affichage(entree)
        self.assertEqual(premier, second)
        json.dumps(premier, ensure_ascii=False, allow_nan=False)

    def test_modele_frais_a_chaque_appel(self):
        entree = decision()
        premier = construire_modele_affichage(entree)
        premier["facteurs_favorables"].append("Mutation")
        premier["risques"].append("Mutation")
        second = construire_modele_affichage(entree)
        self.assertNotIn("Mutation", second["facteurs_favorables"])
        self.assertNotIn("Mutation", second["risques"])

    def test_rendu_affiche_contrat_complet(self):
        faux_st = FauxStreamlit()
        entree = decision(
            favorables=["F"], defavorables=["D"], neutres=["N"],
            risques=["R"], manquantes=["M"],
        )
        with patch.object(decision_card, "st", faux_st):
            afficher_decision_prudente(entree)

        self.assertIn(("subheader", "🧭 Recommandation prudente"), faux_st.appels)
        self.assertIn(("metric", "Recommandation prudente", "Surveiller"), faux_st.appels)
        self.assertIn(("metric", QUALITE_LABEL, "90/100"), faux_st.appels)
        self.assertIn(("caption", QUALITE_EXPLICATION), faux_st.appels)
        self.assertIn(("write", "• D"), faux_st.appels)
        self.assertIn(("write", "• R"), faux_st.appels)
        self.assertIn(("write", "Action Surveiller"), faux_st.appels)
        self.assertIn(("caption", DECISION_FINALE), faux_st.appels)

    def test_rendu_masque_neutres_et_manquantes_vides_seulement(self):
        faux_st = FauxStreamlit()
        with patch.object(decision_card, "st", faux_st):
            afficher_decision_prudente(decision(neutres=[], manquantes=[]))
        textes_markdown = [
            appel[1] for appel in faux_st.appels if appel[0] == "markdown"
        ]
        self.assertNotIn("**Facteurs neutres**", textes_markdown)
        self.assertNotIn("**Données manquantes**", textes_markdown)
        self.assertIn("**Facteurs défavorables**", textes_markdown)
        self.assertIn("**Risques et limites**", textes_markdown)

    def test_import_isole_sans_reseau_ni_openai(self):
        interdits = {
            "yfinance", "openai", "market_data", "news", "ai_analysis",
        }
        commande = (
            "import sys; import ui.decision_card; "
            f"assert not ({interdits!r} & set(sys.modules))"
        )
        resultat = subprocess.run(
            [sys.executable, "-c", commande],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(resultat.returncode, 0, resultat.stderr)

    def test_integration_marche_un_scoring_et_repli_exact(self):
        import market

        source = inspect.getsource(market.afficher_marche)
        self.assertEqual(source.count("calculer_score("), 1)
        self.assertIn('metric("Score technique"', source)
        self.assertIn('metric("Signal technique"', source)
        self.assertIn("construire_decision(resultat_score)", source)
        self.assertIn("afficher_decision_prudente(decision)", source)
        self.assertIn(
            "La recommandation prudente est indisponible. Le score et le ",
            source,
        )
        self.assertIn("signal techniques restent consultables.", source)


if __name__ == "__main__":
    unittest.main()
