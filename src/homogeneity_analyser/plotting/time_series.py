"""Matplotlib / Plotly time-series plots for H, H_timbral, U."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

from homogeneity_analyser.plotting.common import (
    MPL_COLORS,
    MPL_FIGURE_KW,
    MPL_LINE_KW,
    apply_mpl_style,
    plotly_layout,
)


def make_homogeneity_figure(results, title="Homogeneity H(t)"):
    t = np.array(results["t"], dtype=float)
    H = np.array(results["H"], dtype=float)
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    ax.plot(t, H, color=MPL_COLORS["homogeneity"], **MPL_LINE_KW)
    apply_mpl_style(ax, "Homogeneity [0–1]", title)
    fig.tight_layout(pad=2.0)
    return fig


def make_homogeneity_figure_plotly(results, title="Homogeneity H(t)"):
    t = np.array(results["t"], dtype=float)
    H = np.array(results["H"], dtype=float)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=H, mode="lines", line=dict(color=MPL_COLORS["homogeneity"], width=2.2)))
    fig.update_layout(**plotly_layout(title, "Homogeneity [0–1]", MPL_COLORS["homogeneity"]))
    return fig


def make_timbral_figure(results_t, title="Part-name homogeneity H_timbral(t)"):
    t = np.array(results_t["t"], dtype=float)
    H = np.array(results_t["H_timbral"], dtype=float)
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    ax.plot(t, H, color=MPL_COLORS["timbral"], **MPL_LINE_KW)
    apply_mpl_style(ax, "Part-name homogeneity [0–1]", title)
    fig.tight_layout(pad=2.0)
    return fig


def make_timbral_figure_plotly(results_t, title="Part-name homogeneity H_timbral(t)"):
    t = np.array(results_t["t"], dtype=float)
    H = np.array(results_t["H_timbral"], dtype=float)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=H, mode="lines", line=dict(color=MPL_COLORS["timbral"], width=2.2)))
    fig.update_layout(**plotly_layout(title, "Part-name homogeneity [0–1]", MPL_COLORS["timbral"]))
    return fig


def make_hti_figure(results_hti, title="Symbolic timbral–instrumental homogeneity H_TI(t)"):
    t = np.array(results_hti["t"], dtype=float)
    h = np.array(results_hti["H_TI"], dtype=float)
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    ax.plot(t, h, color=MPL_COLORS["timbral"], label="H_TI (strict / primary)", **MPL_LINE_KW)
    sfr0 = 0.0
    sfr_raw = results_hti.get("same_subfamily_relief_factor")
    if isinstance(sfr_raw, list | tuple) and len(sfr_raw) > 0:
        try:
            sfr0 = float(sfr_raw[0])
        except (TypeError, ValueError):
            sfr0 = 0.0
    hr_list = results_hti.get("H_TI_subfamily_relieved")
    if sfr0 > 1e-12 and hr_list is not None:
        hr = np.asarray(hr_list, dtype=float)
        if hr.shape == h.shape and np.any(np.isfinite(hr)):
            diff = np.abs(np.where(np.isfinite(h) & np.isfinite(hr), hr - h, np.nan))
            if np.isfinite(diff).any() and float(np.nanmax(diff)) > 1e-6:
                ax.plot(
                    t,
                    hr,
                    color="#64748b",
                    linewidth=1.6,
                    linestyle="--",
                    label="H_TI (subfamily relieved)",
                )
    tar0 = 0.0
    tar_raw = results_hti.get("timbral_affinity_relief_factor")
    if isinstance(tar_raw, list | tuple) and len(tar_raw) > 0:
        try:
            tar0 = float(tar_raw[0])
        except (TypeError, ValueError):
            tar0 = 0.0
    ha_list = results_hti.get("H_TI_affinity_literature_relieved")
    if tar0 > 1e-12 and ha_list is not None:
        ha = np.asarray(ha_list, dtype=float)
        if ha.shape == h.shape and np.any(np.isfinite(ha)):
            diff2 = np.abs(np.where(np.isfinite(h) & np.isfinite(ha), ha - h, np.nan))
            if np.isfinite(diff2).any() and float(np.nanmax(diff2)) > 1e-6:
                ax.plot(
                    t,
                    ha,
                    color="#b45309",
                    linewidth=1.5,
                    linestyle=":",
                    label="H_TI (literature affinity relieved)",
                )
    apply_mpl_style(ax, "H_TI [0–1]", title)
    if len(ax.lines) > 1:
        ax.legend(loc="lower right", fontsize=9, framealpha=0.92)
    fig.tight_layout(pad=2.0)
    return fig


def make_hti_figure_plotly(results_hti, title="Symbolic timbral–instrumental homogeneity H_TI(t)"):
    t = np.array(results_hti["t"], dtype=float)
    h = np.array(results_hti["H_TI"], dtype=float)
    fig = go.Figure()
    primary_kw: dict = {}
    ew_raw = results_hti.get("edge_window")
    cov_raw = results_hti.get("window_coverage_ratio")
    if (
        isinstance(ew_raw, list | tuple)
        and len(ew_raw) == len(t)
        and isinstance(cov_raw, list | tuple)
        and len(cov_raw) == len(t)
    ):
        cd0 = [bool(x) for x in ew_raw]
        cd1 = []
        for x in cov_raw:
            try:
                fv = float(x)
            except (TypeError, ValueError):
                cd1.append(float("nan"))
            else:
                cd1.append(fv if np.isfinite(fv) else float("nan"))
        primary_kw["customdata"] = np.column_stack([cd0, cd1])
        primary_kw["hovertemplate"] = (
            "t=%{x:.4f}<br>H_TI=%{y:.4f}<br>edge_window=%{customdata[0]}"
            "<br>window_coverage_ratio=%{customdata[1]:.4f}<extra></extra>"
        )
    fig.add_trace(
        go.Scatter(
            x=t,
            y=h,
            mode="lines",
            name="H_TI (strict / primary)",
            line=dict(color=MPL_COLORS["timbral"], width=2.2),
            **primary_kw,
        )
    )
    sfr0 = 0.0
    sfr_raw = results_hti.get("same_subfamily_relief_factor")
    if isinstance(sfr_raw, list | tuple) and len(sfr_raw) > 0:
        try:
            sfr0 = float(sfr_raw[0])
        except (TypeError, ValueError):
            sfr0 = 0.0
    hr_list = results_hti.get("H_TI_subfamily_relieved")
    if sfr0 > 1e-12 and hr_list is not None:
        hr = np.asarray(hr_list, dtype=float)
        if hr.shape == h.shape and np.any(np.isfinite(hr)):
            diff = np.abs(np.where(np.isfinite(h) & np.isfinite(hr), hr - h, np.nan))
            if np.isfinite(diff).any() and float(np.nanmax(diff)) > 1e-6:
                fig.add_trace(
                    go.Scatter(
                        x=t,
                        y=hr,
                        mode="lines",
                        name="H_TI (subfamily relieved)",
                        line=dict(color="#94a3b8", width=1.6, dash="dash"),
                    )
                )
    tar0 = 0.0
    tar_raw = results_hti.get("timbral_affinity_relief_factor")
    if isinstance(tar_raw, list | tuple) and len(tar_raw) > 0:
        try:
            tar0 = float(tar_raw[0])
        except (TypeError, ValueError):
            tar0 = 0.0
    ha_list = results_hti.get("H_TI_affinity_literature_relieved")
    if tar0 > 1e-12 and ha_list is not None:
        ha = np.asarray(ha_list, dtype=float)
        if ha.shape == h.shape and np.any(np.isfinite(ha)):
            diff2 = np.abs(np.where(np.isfinite(h) & np.isfinite(ha), ha - h, np.nan))
            if np.isfinite(diff2).any() and float(np.nanmax(diff2)) > 1e-6:
                fig.add_trace(
                    go.Scatter(
                        x=t,
                        y=ha,
                        mode="lines",
                        name="H_TI (literature affinity relieved)",
                        line=dict(color="#b45309", width=1.5, dash="dot"),
                    )
                )
    layout = plotly_layout(title, "H_TI [0–1]", MPL_COLORS["timbral"])
    if len(fig.data) > 1:
        layout = {
            **layout,
            "showlegend": True,
            "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        }
    fig.update_layout(**layout)
    return fig


def make_register_figure(results_u, title="Register uniformity U(t)"):
    t = np.array(results_u["t"], dtype=float)
    U = np.array(results_u["U"], dtype=float)
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    ax.plot(t, U, color=MPL_COLORS["register"], **MPL_LINE_KW)
    apply_mpl_style(ax, "Register uniformity [0–1]", title)
    fig.tight_layout(pad=2.0)
    return fig


def make_register_figure_plotly(results_u, title="Register uniformity U(t)"):
    t = np.array(results_u["t"], dtype=float)
    U = np.array(results_u["U"], dtype=float)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=U, mode="lines", line=dict(color=MPL_COLORS["register"], width=2.2)))
    fig.update_layout(**plotly_layout(title, "Register uniformity [0–1]", MPL_COLORS["register"]))
    return fig


def make_cluster_figure(results_c, title="Vertical cluster H_cluster(t)"):
    t = np.array(results_c["t"], dtype=float)
    H = np.array(results_c["H_cluster"], dtype=float)
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    ax.plot(t, H, color=MPL_COLORS["cluster"], **MPL_LINE_KW)
    apply_mpl_style(ax, "H_cluster [0–1]", title)
    fig.tight_layout(pad=2.0)
    return fig


def make_orchestration_symbolic_figure(results_o, title="Symbolic orchestration H_orchestration_symbolic(t)"):
    t = np.array(results_o["t"], dtype=float)
    H = np.array(results_o["H_orchestration_symbolic"], dtype=float)
    c = MPL_COLORS["orchestration_symbolic"]
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    ax.plot(t, H, color=c, **MPL_LINE_KW)
    apply_mpl_style(ax, "H_orchestration_symbolic [0–1]", title)
    fig.tight_layout(pad=2.0)
    return fig


def make_orchestration_symbolic_figure_plotly(results_o, title="Symbolic orchestration H_orchestration_symbolic(t)"):
    t = np.array(results_o["t"], dtype=float)
    H = np.array(results_o["H_orchestration_symbolic"], dtype=float)
    c = MPL_COLORS["orchestration_symbolic"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=H, mode="lines", line=dict(color=c, width=2.2)))
    fig.update_layout(**plotly_layout(title, "H_orchestration_symbolic [0–1]", c))
    return fig


def make_notated_fusion_potential_figure(results_nf, title="H_notated_fusion_potential(t)"):
    t = np.array(results_nf["t"], dtype=float)
    H = np.array(results_nf["H_notated_fusion_potential"], dtype=float)
    c = MPL_COLORS["notated_fusion_potential"]
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    ax.plot(t, H, color=c, **MPL_LINE_KW)
    apply_mpl_style(ax, "H_notated_fusion_potential [0–1]", title)
    fig.tight_layout(pad=2.0)
    return fig


def make_notated_fusion_potential_figure_plotly(results_nf, title="H_notated_fusion_potential(t)"):
    t = np.array(results_nf["t"], dtype=float)
    H = np.array(results_nf["H_notated_fusion_potential"], dtype=float)
    c = MPL_COLORS["notated_fusion_potential"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=H, mode="lines", line=dict(color=c, width=2.2)))
    fig.update_layout(**plotly_layout(title, "H_notated_fusion_potential [0–1]", c))
    return fig


def make_cluster_figure_plotly(results_c, title="Vertical cluster H_cluster(t)"):
    t = np.array(results_c["t"], dtype=float)
    H = np.array(results_c["H_cluster"], dtype=float)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=H, mode="lines", line=dict(color=MPL_COLORS["cluster"], width=2.2)))
    fig.update_layout(**plotly_layout(title, "H_cluster [0–1]", MPL_COLORS["cluster"]))
    return fig


def make_fusion_acoustic_heuristic_figure(results_f, title="H_fusion_acoustic_heuristic(t)"):
    t = np.array(results_f["t"], dtype=float)
    H = np.array(results_f["H_fusion_acoustic_heuristic"], dtype=float)
    c = MPL_COLORS["fusion"]
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    ax.plot(t, H, color=c, **MPL_LINE_KW)
    apply_mpl_style(ax, "H_fusion_acoustic_heuristic [0–1]", title)
    fig.tight_layout(pad=2.0)
    return fig


def make_fusion_acoustic_heuristic_figure_plotly(results_f, title="H_fusion_acoustic_heuristic(t)"):
    t = np.array(results_f["t"], dtype=float)
    H = np.array(results_f["H_fusion_acoustic_heuristic"], dtype=float)
    c = MPL_COLORS["fusion"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=H, mode="lines", line=dict(color=c, width=2.2)))
    fig.update_layout(**plotly_layout(title, "H_fusion_acoustic_heuristic [0–1]", c))
    return fig


def make_cluster_orch_fusion_diagnostics_figure(
    bundle: dict,
    title="Cluster / orchestration / fusion / legacy timbral",
):
    """
    Matplotlib overlay of H_cluster, H_orchestration_symbolic, H_fusion_acoustic_heuristic,
    and legacy_H_timbral.

    ``bundle`` keys: ``t``, ``H_cluster``, ``H_orchestration_symbolic``,
    ``H_fusion_acoustic_heuristic``, ``legacy_H_timbral`` (homogeneity time grid).
    """
    t = np.array(bundle["t"], dtype=float)
    fig, ax = plt.subplots(facecolor=MPL_FIGURE_KW["facecolor"])
    specs = [
        ("H_cluster", MPL_COLORS["cluster"]),
        ("H_orchestration_symbolic", MPL_COLORS["orchestration_symbolic"]),
        ("H_notated_fusion_potential", MPL_COLORS["notated_fusion_potential"]),
        ("H_fusion_acoustic_heuristic", MPL_COLORS["fusion"]),
        ("legacy_H_timbral", MPL_COLORS["timbral"]),
    ]
    for key, color in specs:
        if key not in bundle:
            continue
        y = np.array(bundle[key], dtype=float)
        if y.size != t.size:
            continue
        ax.plot(t, y, color=color, label=key, **MPL_LINE_KW)
    apply_mpl_style(ax, "Metric [0–1]", title)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.92)
    fig.tight_layout(pad=2.0)
    return fig


def make_cluster_orch_fusion_diagnostics_figure_plotly(
    bundle: dict,
    title="Cluster / orchestration / fusion / legacy timbral",
):
    """Plotly overlay; click legend entries to show or hide each curve."""
    t = np.array(bundle["t"], dtype=float)
    fig = go.Figure()
    specs = [
        ("H_cluster", MPL_COLORS["cluster"]),
        ("H_orchestration_symbolic", MPL_COLORS["orchestration_symbolic"]),
        ("H_notated_fusion_potential", MPL_COLORS["notated_fusion_potential"]),
        ("H_fusion_acoustic_heuristic", MPL_COLORS["fusion"]),
        ("legacy_H_timbral", MPL_COLORS["timbral"]),
    ]
    for key, color in specs:
        if key not in bundle:
            continue
        y = np.array(bundle[key], dtype=float)
        if y.size != t.size:
            continue
        vis = "legendonly" if key == "legacy_H_timbral" else True
        fig.add_trace(
            go.Scatter(
                x=t,
                y=y,
                mode="lines",
                name=key,
                line=dict(color=color, width=2.0),
                visible=vis,
            )
        )
    lay = plotly_layout(title, "Metric [0–1]", MPL_COLORS["cluster"])
    lay["showlegend"] = True
    lay["legend"] = dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=11),
    )
    fig.update_layout(**lay)
    return fig
