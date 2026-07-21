import plotly.graph_objects as go


def create_candlestick_chart(df, symbol):
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=symbol,
        )
    )

    fig.update_layout(
        title=f"{symbol} - Graphique",
        template="plotly_dark",
        xaxis_title="Date",
        yaxis_title="Prix",
        height=650,
        xaxis_rangeslider_visible=False,
    )

    return fig