import plotly.graph_objects as go


def create_candlestick_chart(df, titre):
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=titre,
        )
    )

    fig.update_layout(
        title=titre,
        template="plotly_dark",
        height=650,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig
