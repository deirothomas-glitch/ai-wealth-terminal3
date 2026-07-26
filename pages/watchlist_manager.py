import streamlit as st

from watchlist import (
    charger_watchlist,
    ajouter_actif,
    supprimer_actif,
)

st.set_page_config(
    page_title="Gestionnaire Watchlist",
    page_icon="⭐",
    layout="wide"
)

st.title("⭐ Gestionnaire de Watchlist")

watchlist = charger_watchlist()

st.subheader("📋 Watchlist actuelle")

for categorie, actifs in watchlist.items():

    st.markdown(f"### {categorie}")

    if actifs:
        st.write(", ".join(actifs))
    else:
        st.info("Aucun actif")

st.divider()

st.subheader("➕ Ajouter un actif")

categorie = st.selectbox(
    "Catégorie",
    list(watchlist.keys())
)

nouvel_actif = st.text_input(
    "Symbole",
    placeholder="Ex : PLTR ou BTC-USD"
)

if st.button("Ajouter"):

    if nouvel_actif.strip():

        ajouter_actif(
            categorie,
            nouvel_actif.strip().upper()
        )

        st.success("Actif ajouté.")

        st.rerun()

st.divider()

st.subheader("❌ Supprimer un actif")

categorie_suppr = st.selectbox(
    "Catégorie à modifier",
    list(watchlist.keys()),
    key="categorie_suppr"
)

if watchlist[categorie_suppr]:

    actif = st.selectbox(
        "Actif",
        watchlist[categorie_suppr]
    )

    if st.button("Supprimer"):

        supprimer_actif(
            categorie_suppr,
            actif
        )

        st.success("Actif supprimé.")

        st.rerun()
else:
    st.info("Aucun actif à supprimer.")
