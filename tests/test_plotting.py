"""Headless tests for matplotlib/plotly helpers (Agg backend)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from homogeneity_analyser.plotting import (
    GAUGE_COLORS,
    MPL_COLORS,
    make_cluster_figure,
    make_cluster_figure_plotly,
    make_cluster_orch_fusion_diagnostics_figure,
    make_cluster_orch_fusion_diagnostics_figure_plotly,
    make_fusion_acoustic_heuristic_figure,
    make_fusion_acoustic_heuristic_figure_plotly,
    make_gauge_figure,
    make_gauge_placeholder,
    make_homogeneity_figure,
    make_homogeneity_figure_plotly,
    make_hti_figure,
    make_hti_figure_plotly,
    make_notated_fusion_potential_figure,
    make_notated_fusion_potential_figure_plotly,
    make_orchestration_symbolic_figure,
    make_orchestration_symbolic_figure_plotly,
    make_register_figure,
    make_register_figure_plotly,
    make_timbral_figure,
    make_timbral_figure_plotly,
)
from homogeneity_analyser.plotting.common import apply_mpl_style, plotly_layout


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def test_apply_mpl_style_sets_limits_and_labels():
    fig, ax = plt.subplots()
    apply_mpl_style(ax, "Y label", "Title")
    assert ax.get_ylim() == (0, 1)
    assert ax.get_ylabel() == "Y label"
    assert ax.get_title() == "Title"
    plt.close(fig)


def test_plotly_layout_structure():
    layout = plotly_layout("T", "Yaxis", "#000000")
    assert layout["title"]["text"] == "T"
    assert layout["yaxis"]["title"]["text"] == "Yaxis"
    assert layout["yaxis"]["range"] == [0, 1]
    assert layout["showlegend"] is False


def test_constants_exported():
    assert "homogeneity" in MPL_COLORS
    assert "Green" in GAUGE_COLORS


def test_make_homogeneity_figure_mpl():
    fig = make_homogeneity_figure({"t": [0.0, 4.0], "H": [0.2, 0.9]})
    assert len(fig.axes) == 1
    line = fig.axes[0].lines[0]
    assert line.get_xdata().tolist() == [0.0, 4.0]
    plt.close(fig)


def test_make_homogeneity_figure_plotly():
    fig = make_homogeneity_figure_plotly({"t": [0.0, 1.0], "H": [0.5, 0.6]})
    assert len(fig.data) == 1
    assert np.allclose(fig.data[0].x, [0.0, 1.0])
    assert np.allclose(fig.data[0].y, [0.5, 0.6])


def test_make_timbral_figure_mpl_and_plotly():
    payload = {"t": [0.0, 2.0], "H_timbral": [0.7, 0.71]}
    fig_m = make_timbral_figure(payload)
    assert fig_m.axes[0].lines[0].get_ydata().tolist() == [0.7, 0.71]
    plt.close(fig_m)
    fig_p = make_timbral_figure_plotly(payload)
    assert len(fig_p.data) == 1


def test_make_hti_figure_mpl_and_plotly():
    payload = {"t": [0.0, 2.0], "H_TI": [0.55, 0.6]}
    fig_m = make_hti_figure(payload)
    assert fig_m.axes[0].lines[0].get_ydata().tolist() == [0.55, 0.6]
    plt.close(fig_m)
    fig_p = make_hti_figure_plotly(payload)
    assert len(fig_p.data) == 1


def test_make_hti_figure_plotly_hover_includes_edge_when_series_present():
    payload = {
        "t": [0.0, 2.0],
        "H_TI": [0.55, 0.6],
        "edge_window": [False, True],
        "window_coverage_ratio": [1.0, 0.4],
        "hti_comparability_class": ["full_4_component", "full_4_component"],
    }
    fig_p = make_hti_figure_plotly(payload)
    tr = fig_p.data[0]
    assert tr.hovertemplate is not None
    assert "edge_window" in tr.hovertemplate
    assert "hti_comparability_class" in tr.hovertemplate
    assert tr.customdata is not None
    assert len(fig_p.data) == 2


def test_make_hti_figure_excludes_edge_windows_when_requested():
    payload = {
        "t": [0.0, 2.0, 4.0],
        "H_TI": [0.5, 0.6, 0.7],
        "edge_window": [True, False, True],
        "window_coverage_ratio": [0.5, 1.0, 0.5],
    }
    fig_m = make_hti_figure(payload, exclude_edge_windows=True)
    y = fig_m.axes[0].lines[0].get_ydata()
    assert np.isnan(y[0])
    assert y[1] == pytest.approx(0.6)
    assert np.isnan(y[2])
    plt.close(fig_m)


def test_make_hti_figure_marks_edge_windows_mpl():
    payload = {
        "t": [0.0, 2.0],
        "H_TI": [0.55, 0.6],
        "edge_window": [True, False],
        "window_coverage_ratio": [0.4, 1.0],
    }
    fig_m = make_hti_figure(payload, mark_edge_windows=True)
    assert len(fig_m.axes[0].collections) >= 1
    plt.close(fig_m)


def test_make_register_figure_mpl_and_plotly():
    payload = {"t": [0.0, 1.0], "U": [0.3, float("nan")]}
    fig_m = make_register_figure(payload)
    assert len(fig_m.axes[0].lines[0].get_ydata()) == 2
    plt.close(fig_m)
    fig_p = make_register_figure_plotly(payload)
    assert len(fig_p.data) == 1


def test_make_gauge_figure_clips_and_unknown_color():
    fig = make_gauge_figure(1.5, gauge_color="UnknownPalette")
    assert len(fig.data) == 1
    vals = fig.data[0].values
    assert vals[0] == 1.0 and vals[1] == 0.0


def test_make_gauge_placeholder():
    fig = make_gauge_placeholder()
    assert fig.layout.annotations[0].text is not None


def test_legacy_multimetric_plot_smoke_mpl_and_plotly():
    """Headless smoke for legacy-series plot helpers (implementation still in plotting/time_series)."""
    t = [0.0, 4.0]
    fig_c = make_cluster_figure({"t": t, "H_cluster": [0.5, 0.6]})
    assert len(fig_c.axes) == 1
    plt.close(fig_c)
    assert len(make_cluster_figure_plotly({"t": t, "H_cluster": [0.5, 0.6]}).data) == 1
    fig_o = make_orchestration_symbolic_figure({"t": t, "H_orchestration_symbolic": [0.4, 0.5]})
    assert len(fig_o.axes) == 1
    plt.close(fig_o)
    assert len(
        make_orchestration_symbolic_figure_plotly({"t": t, "H_orchestration_symbolic": [0.4, 0.5]}).data
    ) == 1
    nf = {"t": t, "H_notated_fusion_potential": [0.3, 0.35]}
    fig_nf = make_notated_fusion_potential_figure(nf)
    assert len(fig_nf.axes) == 1
    plt.close(fig_nf)
    assert len(make_notated_fusion_potential_figure_plotly(nf).data) == 1
    fus = {"t": t, "H_fusion_acoustic_heuristic": [0.2, 0.25]}
    fig_fus = make_fusion_acoustic_heuristic_figure(fus)
    assert len(fig_fus.axes) == 1
    plt.close(fig_fus)
    assert len(make_fusion_acoustic_heuristic_figure_plotly(fus).data) == 1
    diag = {
        "t": t,
        "H_cluster": [0.5, 0.6],
        "H_orchestration_symbolic": [0.4, 0.5],
        "H_notated_fusion_potential": [0.3, 0.35],
        "H_fusion_acoustic_heuristic": [0.2, 0.25],
    }
    fig_d = make_cluster_orch_fusion_diagnostics_figure(diag)
    assert len(fig_d.axes) >= 1
    plt.close(fig_d)
    assert len(make_cluster_orch_fusion_diagnostics_figure_plotly(diag).data) >= 1
