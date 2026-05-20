"""Summary visuals (gauge / placeholder)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from homogeneity_analyser.plotting.common import GAUGE_COLORS


def make_gauge_figure(H_value: float, title="Homogeneity degree (static chord)", gauge_color="Green"):
    """Donut chart for a single homogeneity value in [0, 1]."""
    H_value = float(np.clip(H_value, 0.0, 1.0))
    wedge_hex, remainder_hex = GAUGE_COLORS.get(gauge_color, GAUGE_COLORS["Green"])
    fig = go.Figure(
        data=[
            go.Pie(
                values=[H_value, 1.0 - H_value],
                hole=0.68,
                marker=dict(colors=[wedge_hex, remainder_hex], line=dict(width=0, color="#ffffff")),
                text=[f"{H_value:.2f}", ""],
                textinfo="text",
                textposition="inside",
                hoverinfo="skip",
                direction="clockwise",
                rotation=0,
                textfont=dict(size=14, color="#374151", family="Segoe UI, system-ui, sans-serif"),
            )
        ],
        layout=go.Layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor="center",
                font=dict(size=14, color="#111827", family="Segoe UI, system-ui, sans-serif"),
                pad=dict(t=4, b=0),
            ),
            showlegend=False,
            margin=dict(l=24, r=24, t=44, b=24),
            paper_bgcolor="#fafafa",
            plot_bgcolor="#fafafa",
            height=300,
            annotations=[
                dict(
                    text=f"<b>{H_value:.2f}</b>",
                    x=0.5,
                    y=0.5,
                    font=dict(size=32, color="#111827", family="Segoe UI, system-ui, sans-serif"),
                    showarrow=False,
                )
            ],
            font=dict(family="Segoe UI, system-ui, sans-serif"),
        ),
    )
    return fig


def make_gauge_placeholder():
    """Placeholder when not in single-aggregate mode."""
    fig = go.Figure(
        layout=go.Layout(
            title=dict(
                text="Homogeneity gauge (static chord only)",
                x=0.5,
                xanchor="center",
                font=dict(size=14, color="#111827", family="Segoe UI, system-ui, sans-serif"),
            ),
            margin=dict(l=24, r=24, t=44, b=24),
            paper_bgcolor="#fafafa",
            plot_bgcolor="#fafafa",
            height=300,
            annotations=[
                dict(
                    text="Enable <b>Single aggregate mode</b><br>for gauge",
                    x=0.5,
                    y=0.5,
                    font=dict(size=14, color="#6b7280", family="Segoe UI, system-ui, sans-serif"),
                    showarrow=False,
                )
            ],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
    )
    return fig
