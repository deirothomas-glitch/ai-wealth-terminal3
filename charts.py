"""Graphiques Plotly partagés."""

import plotly.graph_objects as go


def create_candlestick_chart(dataframe, titre):
    figure = go.Figure(go.Candlestick(
        x=dataframe.index, open=dataframe["Open"], high=dataframe["High"],
        low=dataframe["Low"], close=dataframe["Close"], name=titre,
    ))
    figure.update_layout(
        title=titre, template="plotly_dark", height=600,
        xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=60, b=20),
    )
    return figure
