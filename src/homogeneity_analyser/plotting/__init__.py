"""Plotting (matplotlib + plotly) for the Gradio UI."""

from homogeneity_analyser.plotting.common import GAUGE_COLORS, MPL_COLORS
from homogeneity_analyser.plotting.summaries import make_gauge_figure, make_gauge_placeholder
from homogeneity_analyser.plotting.time_series import (
    make_cluster_figure,
    make_cluster_figure_plotly,
    make_cluster_orch_fusion_diagnostics_figure,
    make_cluster_orch_fusion_diagnostics_figure_plotly,
    make_fusion_acoustic_heuristic_figure,
    make_fusion_acoustic_heuristic_figure_plotly,
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

__all__ = [
    "GAUGE_COLORS",
    "MPL_COLORS",
    "make_cluster_figure",
    "make_cluster_figure_plotly",
    "make_cluster_orch_fusion_diagnostics_figure",
    "make_cluster_orch_fusion_diagnostics_figure_plotly",
    "make_fusion_acoustic_heuristic_figure",
    "make_fusion_acoustic_heuristic_figure_plotly",
    "make_gauge_figure",
    "make_gauge_placeholder",
    "make_homogeneity_figure",
    "make_homogeneity_figure_plotly",
    "make_hti_figure",
    "make_hti_figure_plotly",
    "make_notated_fusion_potential_figure",
    "make_notated_fusion_potential_figure_plotly",
    "make_orchestration_symbolic_figure",
    "make_orchestration_symbolic_figure_plotly",
    "make_register_figure",
    "make_register_figure_plotly",
    "make_timbral_figure",
    "make_timbral_figure_plotly",
]
