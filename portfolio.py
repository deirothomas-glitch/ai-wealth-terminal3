"""Interface Streamlit du portefeuille opérationnel."""
from datetime import date
from uuid import uuid4
import pandas as pd
import streamlit as st
from core.portfolio import (calculer_score_diversification,calculer_taille_position,construire_resume_global,construire_statistiques_journal,convertir_nombre_fini,convertir_nombre_positif,normaliser_position,resumer_position,valider_position)
from core.position_alerts import generer_alertes_positions
from core.portfolio_intelligence import analyser_portefeuille
from market_data import charger_donnees,dernier_prix
from services.portfolio_operations import ajouter_position,cloturer_position,modifier_position,supprimer_position
from services.portfolio_prices import charger_prix_portefeuille
from services.portfolio_service import collecter_valorisation
from services.news_aggregator import agreger_actualites
from services.news_sources import YahooNewsSource
from storage import charger_journal_avec_erreur,charger_portefeuille_avec_erreur
from ui.portfolio_stats import afficher_statistiques_portefeuille
from ui.portfolio_summary import afficher_resume_portefeuille
from ui.portfolio_intelligence_card import afficher_intelligence_portefeuille
from ui.position_alert_card import afficher_alerte_position
from ui.news_card import afficher_actualites_normalisees

def _score_diversification(n): return calculer_score_diversification(n)
def _taille_position_suggeree(a,b,c,d): return calculer_taille_position(a,b,c,d)
def _normaliser_position(position):
    # Wrapper historique volontairement mutable pour les tests et anciens appels.
    position.setdefault("stop_loss",0.0); position.setdefault("objectif_prix",0.0); position.setdefault("these_achat",""); position.setdefault("notes_suivi",""); position.setdefault("horizon","Non défini"); return position
def _collecter_valorisation(capital_reference,risque_max_position):
    return collecter_valorisation(st.session_state.portfolio,capital_reference,risque_max_position,charger_donnees,dernier_prix,_normaliser_position)

def _init():
    if "portfolio" not in st.session_state:
        p,e=charger_portefeuille_avec_erreur(); st.session_state.portfolio=[_migrer(x) for x in p]; st.session_state.portfolio_erreur=e
    if "trading_journal" not in st.session_state:
        j,e=charger_journal_avec_erreur(); st.session_state.trading_journal=j; st.session_state.journal_erreur=e
    st.session_state.setdefault("portfolio_prix",{})
def _migrer(x):
    source=dict(x) if isinstance(x,dict) else {}
    p={**source,**normaliser_position(source)}; p["identifiant"]=p["identifiant"] or str(uuid4()); return p
def _rafraichir():
    prix,erreurs=charger_prix_portefeuille(st.session_state.portfolio,charger_donnees,dernier_prix); st.session_state.portfolio_prix=prix; return erreurs
def _format(v,suffixe=""):
    nombre=convertir_nombre_fini(v)
    return "Indisponible" if nombre is None else f"{nombre:.2f}{suffixe}"
def _valeur_formulaire(v,defaut=0.0):
    nombre=convertir_nombre_positif(v)
    return nombre if nombre is not None else defaut
def _sync(retour): st.session_state.portfolio,st.session_state.trading_journal=retour

def _ajout():
    st.subheader("Ajouter une position")
    prefill=st.session_state.get("portfolio_prefill", {})
    with st.form("portfolio_ajout",clear_on_submit=True):
        c=st.columns(2); symbole=c[0].text_input("Symbole",value=str(prefill.get("symbole","")),placeholder="AAPL ou BTC-USD"); nom=c[1].text_input("Nom (facultatif)",value=str(prefill.get("nom","")))
        c=st.columns(3); types_actifs=["action","ETF","crypto","autre"]; type_prefill=prefill.get("type_actif","action"); typ=c[0].selectbox("Type d’actif",types_actifs,index=types_actifs.index(type_prefill) if type_prefill in types_actifs else 0); quantite=c[1].number_input("Quantité",min_value=0.000001,value=1.0); entree=c[2].number_input("Prix d’entrée",min_value=0.01,value=_valeur_formulaire(prefill.get("prix_entree"),1.0))
        c=st.columns(3); stop=c[0].number_input("Stop (0 = aucun)",min_value=0.0,value=_valeur_formulaire(prefill.get("stop_loss"))); objectif=c[1].number_input("Objectif (0 = aucun)",min_value=0.0,value=_valeur_formulaire(prefill.get("objectif"))); ouverture=c[2].date_input("Date d’ouverture",value=date.today())
        notes=st.text_area("Notes"); soumis=st.form_submit_button("Ajouter la position")
    if soumis:
        p={"symbole":symbole,"nom":nom,"type_actif":typ,"quantite":quantite,"prix_entree":entree,"stop_loss":stop or None,"objectif":objectif or None,"date_ouverture":ouverture.isoformat(),"notes":notes}
        erreurs=valider_position(p)
        if erreurs: st.error(" ".join(erreurs))
        else:
            try: _sync(ajouter_position(st.session_state.portfolio,st.session_state.trading_journal,p)); st.session_state.pop("portfolio_prefill",None); st.success("Position ajoutée."); st.rerun()
            except (OSError,ValueError) as e: st.error(f"Enregistrement impossible : {e}")

def _actions(position):
    p=normaliser_position(position); pid=p["identifiant"]; symbole=p["symbole"]
    with st.expander(f"Gérer {symbole} — {pid[:8]}"):
        onglets=st.tabs(["Modifier","Clôturer","Supprimer"])
        with onglets[0]:
            if p["quantite"] is None: st.warning("Quantité indisponible : renseignez une quantité valide avant d’enregistrer.")
            if p["prix_entree"] is None: st.warning("Prix d’entrée indisponible : renseignez un prix valide avant d’enregistrer.")
            with st.form(f"modifier_{pid}"):
                q=st.number_input("Quantité",min_value=0.0,value=_valeur_formulaire(p["quantite"]),key=f"mq_{pid}"); pe=st.number_input("Prix d’entrée",min_value=0.0,value=_valeur_formulaire(p["prix_entree"]),key=f"mp_{pid}"); s=st.number_input("Stop (0 = aucun)",min_value=0.0,value=_valeur_formulaire(p["stop_loss"]),key=f"ms_{pid}"); o=st.number_input("Objectif (0 = aucun)",min_value=0.0,value=_valeur_formulaire(p["objectif"]),key=f"mo_{pid}"); n=st.text_area("Notes",value=p["notes"],key=f"mn_{pid}"); ok=st.form_submit_button("Enregistrer")
            if ok:
                try: _sync(modifier_position(st.session_state.portfolio,st.session_state.trading_journal,pid,{"quantite":q,"prix_entree":pe,"stop_loss":s or None,"objectif":o or None,"notes":n})); st.success("Position modifiée."); st.rerun()
                except (OSError,ValueError,KeyError) as e: st.error(str(e))
        with onglets[1]:
            if p["quantite"] is None or p["prix_entree"] is None: st.warning("Renseignez une quantité et un prix d’entrée valides avant de clôturer cette position.")
            with st.form(f"cloturer_{pid}"):
                prix_courant=convertir_nombre_positif(st.session_state.portfolio_prix.get(symbole)); ps=st.number_input("Prix de sortie",min_value=0.0,value=prix_courant or _valeur_formulaire(p["prix_entree"]),key=f"cp_{pid}"); ds=st.date_input("Date de sortie",value=date.today(),key=f"cd_{pid}"); notes=st.text_area("Notes facultatives",key=f"cn_{pid}"); confirme=st.checkbox("Je confirme la clôture totale.",key=f"cc_{pid}"); ok=st.form_submit_button("Clôturer")
            if ok:
                if not confirme: st.warning("Confirmez la clôture totale.")
                else:
                    try: _sync(cloturer_position(st.session_state.portfolio,st.session_state.trading_journal,pid,ps,ds.isoformat(),notes)); st.success("Position clôturée et journalisée."); st.rerun()
                    except (OSError,ValueError,KeyError) as e: st.error(str(e))
        with onglets[2]:
            confirme=st.checkbox("Je confirme la suppression.",key=f"dc_{pid}")
            if st.button("Supprimer",key=f"db_{pid}"):
                if not confirme: st.warning("Confirmez la suppression.")
                else:
                    try: _sync(supprimer_position(st.session_state.portfolio,st.session_state.trading_journal,pid)); st.success("Position supprimée et journalisée."); st.rerun()
                    except (OSError,KeyError) as e: st.error(str(e))

def afficher_portefeuille():
    st.header("💼 Portefeuille opérationnel"); _init()
    for e in (st.session_state.get("portfolio_erreur"),st.session_state.get("journal_erreur")):
        if e: st.error(e)
    if st.button("🔄 Rafraîchir les prix",key="portfolio_refresh") or (st.session_state.portfolio and not st.session_state.portfolio_prix):
        for e in _rafraichir(): st.warning(e)
    resume=construire_resume_global(st.session_state.portfolio,st.session_state.portfolio_prix,st.session_state.trading_journal); afficher_resume_portefeuille(st,resume)
    if resume["positions_sans_prix"]: st.caption(f"{resume['positions_sans_prix']} position(s) sans prix : les totaux actuels restent indisponibles.")
    intelligence=analyser_portefeuille(st.session_state.portfolio,st.session_state.portfolio_prix)
    afficher_intelligence_portefeuille(st,intelligence)
    _ajout(); st.subheader("Positions ouvertes")
    lignes=[resumer_position(p,st.session_state.portfolio_prix.get(p["symbole"])) for p in st.session_state.portfolio]
    if not lignes: st.info("Votre portefeuille est vide. Ajoutez votre première position ci-dessus.")
    else:
        table=[{"Symbole":x["symbole"],"Quantité":x["quantite"],"Prix d’entrée":_format(x["prix_entree"]," €"),"Prix courant":_format(x["prix_courant"]," €"),"Investi":_format(x["montant_investi"]," €"),"Valeur":_format(x["valeur_actuelle"]," €"),"Gain/perte":_format(x["gain_perte"]," €"),"Performance":_format(x["performance_pourcentage"]," %"),"Stop":_format(x["stop_loss"]),"Objectif":_format(x["objectif"])} for x in lignes]
        st.dataframe(pd.DataFrame(table),use_container_width=True,hide_index=True)
        for p in st.session_state.portfolio: _actions(p)
    st.subheader("Alertes de positions"); alertes=generer_alertes_positions(st.session_state.portfolio,st.session_state.portfolio_prix); st.session_state.alertes_positions=alertes
    if not alertes: st.success("Aucune alerte de position active.")
    for a in alertes: afficher_alerte_position(st,a)
    st.subheader("Actualités des positions")
    if st.button("📰 Rafraîchir les actualités des positions",key="portfolio_news_refresh"):
        actualites_positions=[]
        for symbole in sorted({p["symbole"] for p in st.session_state.portfolio if p.get("symbole")}):
            articles,erreurs_news=agreger_actualites([YahooNewsSource()],symbole,limite=3)
            actualites_positions.extend(articles)
            for erreur_news in erreurs_news: st.warning(erreur_news)
        st.session_state.actualites_positions=actualites_positions
    afficher_actualites_normalisees(st.session_state.get("actualites_positions",[]),limite=10)
    clotures=[e for e in st.session_state.trading_journal if e.get("type_evenement")=="cloture"]; st.subheader("Positions clôturées"); st.dataframe(pd.DataFrame(clotures),use_container_width=True,hide_index=True) if clotures else st.info("Aucune position clôturée.")
    st.subheader("Statistiques"); afficher_statistiques_portefeuille(st,construire_statistiques_journal(st.session_state.trading_journal))
    st.subheader("Journal"); st.dataframe(pd.DataFrame(st.session_state.trading_journal),use_container_width=True,hide_index=True) if st.session_state.trading_journal else st.info("Le journal sera alimenté automatiquement.")
