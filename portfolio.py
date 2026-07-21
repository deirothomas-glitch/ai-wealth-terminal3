import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder
from charts import create_candlestick_chart
from data import get_stock_history
from ai_analysis import analyse_marche
from datetime import datetime
from storage import charger_portefeuille, sauvegarder_portefeuille

def afficher_portefeuille():

    st.header("💼 Mon Portefeuille")

    if "portfolio" not in st.session_state:
        st.session_state.portfolio = charger_portefeuille()

    if "historique_portefeuille" not in st.session_state:
        st.session_state.historique_portefeuille = []

    quantite = st.number_input(
        "Quantité",
        min_value=0.01,
        value=1.0,
        step=0.01
    )

    prix_achat = st.number_input(
        "Prix d'achat",
        min_value=0.0,
        value=0.0,
        step=0.01
    )
     

    symbole = st.text_input(
        "Ajouter une action ou une crypto",
        placeholder="Exemple : AAPL ou BTC-USD"
    ).upper()

    if st.button("➕ Ajouter"):

        if symbole:

            st.session_state.portfolio.append({
                "symbole": symbole,
                "quantite": quantite,
                "prix_achat": prix_achat
            })

            sauvegarder_portefeuille(st.session_state.portfolio)
            st.success(f"{symbole} ajouté au portefeuille.")


    st.divider()

    total_portefeuille = 0
    total_gain = 0

    if not st.session_state.portfolio:
        st.info("Votre portefeuille est vide.")
        return
    
    resume = st.container()

    lignes = []

    for position in st.session_state.portfolio:
        symbole = position["symbole"]
        quantite = position["quantite"]
        prix_achat = position["prix_achat"]

        try:
            data = yf.Ticker(symbole).history(period="2d")

            prix = data["Close"].iloc[-1]
            ancien = data["Close"].iloc[-2]
            valeur_actuelle = prix * quantite
            cout_total = prix_achat * quantite
            gain_perte = valeur_actuelle - cout_total
            total_portefeuille += valeur_actuelle
            total_gain += gain_perte

            if cout_total > 0:
                gain_perte_pct = (gain_perte / cout_total) * 100
            else:
                gain_perte_pct = 0

                lignes.append({
                    "Actif": symbole,
                    "Quantité": quantite,
                    "Prix achat": prix_achat,
                    "Cours actuel": round(prix, 2),
                    "Valeur": round(valeur_actuelle, 2),
                    "Gain (€)": round(gain_perte, 2),
                    "Gain (%)": round(gain_perte_pct, 2)
                })

                variation = ((prix - ancien) / ancien) * 100

            st.markdown(f"### 📈 {symbole}")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Cours actuel",
                f"{prix:.2f} €"
            )

            col2.metric(
                "Valeur",
                f"{valeur_actuelle:.2f} €"
            )

            col3.metric(
                "Gain / Perte",
                f"{gain_perte:.2f} €",
                f"{gain_perte_pct:.2f}%"
            )

            st.divider()


        except Exception as e:
            st.error(f"Erreur pour {symbole} : {e}")

        with resume:

            st.subheader("📊 Résumé du portefeuille")

            if lignes :
                df_resume = pd.DataFrame(lignes)

                gb = GridOptionsBuilder.from_dataframe(df_resume)

                gb.configure_default_column(
                    sortable=True,
                    filter=True,
                    resizable=True
                )

                gb.configure_pagination(
                    paginationAutoPageSize=True
                )       

                grid_options = gb.build()

                AgGrid(
                    df_resume,
                    gridOptions=grid_options,
                    fit_columns_on_grid_load=True,
                    height=300
                )

                st.divider()
                maintenant = datetime.now()

                st.session_state.historique_portefeuille.append({
                    "date": maintenant,
                    "valeur": total_portefeuille
            })

            # Conserver uniquement les 200 dernières mesures
            st.session_state.historique_portefeuille = (
            st.session_state.historique_portefeuille[-200:]
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "💼 Valeur totale",
                f"{total_portefeuille:.2f} €"
            )

            col2.metric(
                "📈 Gain / Perte total",
                f"{total_gain:.2f} €"
            )   
            st.divider()

            st.subheader("📈 Analyse d'une position")

            liste_actifs = [p["symbole"] for p in st.session_state.portfolio]

            actif = st.selectbox(
                "Choisissez un actif",
                liste_actifs
            )

            historique = get_stock_history(actif)

            fig = create_candlestick_chart(historique, actif)

            st.plotly_chart(
                fig,
                use_container_width=True
            )
            st.divider()

            st.subheader("🤖 Analyse IA")

            if st.button("Analyser avec l'IA"):

                prix = historique["Close"].iloc[-1]

                with st.spinner("Analyse en cours..."):

                    resultat = analyse_marche(
                        actif,
                        prix
                    )

                st.success("Analyse terminée")
                st.markdown(resultat)

                st.divider()
                st.subheader("📈 Historique du portefeuille")

                df_historique = pd.DataFrame(
                    st.session_state.historique_portefeuille
                )

                if not df_historique.empty:

                    fig = go.Figure()

                    fig.add_trace(
                        go.Scatter(
                            x=df_historique["date"],
                            y=df_historique["valeur"],
                            mode="lines",
                            name="Portefeuille"
                        )
                    )

                    fig.update_layout(
                        template="plotly_dark",
                        height=400,
                        xaxis_title="Date",
                        yaxis_title="Valeur (€)"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )
