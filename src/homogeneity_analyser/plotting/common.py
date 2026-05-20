"""Shared matplotlib / plotly styling for time-series figures."""

from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

MPL_FIGURE_KW = {"figsize": (12, 4.5), "facecolor": "#fafafa", "dpi": 100}
MPL_LINE_KW = {"linewidth": 2.2, "solid_capstyle": "round"}
MPL_COLORS = {
    "homogeneity": "#2563eb",
    "timbral": "#0d9488",
    "register": "#ca8a04",
    "cluster": "#9333ea",
    "orchestration_symbolic": "#155e75",
    "notated_fusion_potential": "#047857",
    "fusion": "#c2410c",
}

GAUGE_COLORS = {
    "Green": ("#2ecc71", "#ecf0f1"),
    "Blue": ("#3498db", "#ecf0f1"),
    "Teal": ("#1abc9c", "#ecf0f1"),
    "Orange": ("#e67e22", "#fef5e7"),
    "Purple": ("#9b59b6", "#f5eef8"),
    "Red": ("#e74c3c", "#fdedec"),
    "Slate": ("#34495e", "#ebedef"),
}


def apply_mpl_style(ax, ylabel: str, title: str):
    ax.set_facecolor("#ffffff")
    ax.set_ylim(0, 1)
    ax.set_ylabel(ylabel, fontsize=11, fontweight="500", color="#374151")
    ax.set_xlabel("Time (quarter length)", fontsize=11, fontweight="500", color="#374151")
    ax.set_title(title, fontsize=13, fontweight="600", color="#111827", pad=12)
    ax.tick_params(axis="both", which="major", labelsize=10, colors="#4b5563")
    ax.grid(True, axis="both", alpha=0.35, color="#9ca3af", linestyle="-", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#d1d5db")
        spine.set_linewidth(0.8)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
    ax.xaxis.set_major_formatter(mticker.ScalarFormatter())
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
    return ax


def plotly_layout(title: str, yaxis_title: str, _line_color: str):
    return dict(
        title=dict(
            text=title,
            font=dict(size=16, color="#111827", family="Segoe UI, system-ui, sans-serif"),
            x=0.5,
            xanchor="center",
            pad=dict(t=8, b=0),
        ),
        font=dict(family="Segoe UI, system-ui, sans-serif", size=12, color="#374151"),
        paper_bgcolor="#fafafa",
        plot_bgcolor="#ffffff",
        margin=dict(l=64, r=40, t=56, b=52),
        xaxis=dict(
            title=dict(text="Time (quarter length)", font=dict(size=12, color="#374151")),
            showgrid=True,
            gridcolor="rgba(156,163,175,0.35)",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="#e5e7eb",
            linewidth=1,
            tickfont=dict(size=11, color="#4b5563"),
            tickangle=0,
        ),
        yaxis=dict(
            title=dict(text=yaxis_title, font=dict(size=12, color="#374151")),
            range=[0, 1],
            dtick=0.2,
            showgrid=True,
            gridcolor="rgba(156,163,175,0.35)",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="#e5e7eb",
            linewidth=1,
            tickfont=dict(size=11, color="#4b5563"),
        ),
        showlegend=False,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#ffffff", font_size=11, font_family="Segoe UI, system-ui, sans-serif"),
    )
