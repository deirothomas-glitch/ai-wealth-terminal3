import plotly.graph_objects as go
from plotly.subplots import make_subplots

from indicators import ema, rsi


def create_candlestick(data, titre):
    # Calcul des indicateurs
    ema20 = ema(data, 20)
    ema50 = ema(data, 50)
    ema200 = ema(data, 200)
    rsi14 = rsi(data)

    # Figure avec 3 panneaux
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.65, 0.20, 0.15],
        subplot_titles=(
            titre,
            "Volume",
            "RSI"
        )
    )

    # ==========================
    # Chandeliers
    # ==========================
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Prix"
        ),
        row=1,
        col=1
    )

    # EMA 20
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=ema20,
            mode="lines",
            name="EMA 20"
        ),
        row=1,
        col=1
    )

    # EMA 50
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=ema50,
            mode="lines",
            name="EMA 50"
        ),
        row=1,
        col=1
    )

    # EMA 200
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=ema200,
            mode="lines",
            name="EMA 200"
        ),
        row=1,
        col=1
    )

    # ==========================
    # Volume
    # ==========================
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data["Volume"],
            name="Volume",
            opacity=0.35
        ),
        row=2,
        col=1
    )

    # ==========================
    # RSI
    # ==========================
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=rsi14,
            mode="lines",
            name="RSI 14"
        ),
        row=3,
        col=1
    )

    # Niveaux RSI
    fig.add_hline(
        y=70,
        row=3,
        col=1,
        line_dash="dash"
    )

    fig.add_hline(
        y=30,
        row=3,
        col=1,
        line_dash="dash"
    )

    # ==========================
    # Mise en page
    # ==========================
    fig.update_layout(
        template="plotly_dark",
        height=950,
        title=titre,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            y=1.03,
            x=1,
            xanchor="right"
        ),
        margin=dict(
            l=30,
            r=30,
            t=70,
            b=30
        )
    )

    fig.update_yaxes(title_text="Prix", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])

    return fig