import streamlit as st


def metric_card(title, value, delta=None):
    """
    Affiche une carte de métrique avec un style uniforme.
    """

    with st.container(border=True):
        st.subheader(title)
        st.metric(
            label="",
            value=value,
            delta=delta
        )


def signal_card(signal, confidence):
    """
    Affiche le signal principal.
    """

    if signal.upper() == "ACHAT":
        st.success(f"🟢 {signal}")

    elif signal.upper() == "VENTE":
        st.error(f"🔴 {signal}")

    else:
        st.warning(f"🟡 {signal}")

    st.caption(f"Confiance : {confidence}")