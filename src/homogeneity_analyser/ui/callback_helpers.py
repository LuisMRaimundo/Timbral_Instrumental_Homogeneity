"""Shared Gradio callback helpers (plot export, UI float parsing)."""

from __future__ import annotations

import logging
import warnings
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt

from homogeneity_analyser.plotting import make_timbral_figure, make_timbral_figure_plotly
from homogeneity_analyser.services.analysis_service import TIMBRAL_DIAGNOSTIC_TABLE_HEADERS
from homogeneity_analyser.ui.timbral_ui_params import (
    TIMBRAL_PARSE_ERROR_STUB,
    timbral_config_from_optional,
    timbral_parse_error_plot_title,
    timbral_parse_error_summary,
)
from homogeneity_analyser.ui.validation import parse_ui_float
from homogeneity_analyser.utils.output_paths import new_export_path

_LOG = logging.getLogger(__name__)

def ui_float_gradio(value: Any, default: float, field_name: str) -> float:
    """Parse a UI number; on failure raise ``gr.Error`` with a clear message."""
    try:
        parsed = parse_ui_float(value, default=default, field_name=field_name)
        if parsed is None:
            return float(default)
        return float(parsed)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc


# Backward-compatible alias for tests importing ``callbacks._timbral_config_from_optional``.
_timbral_config_from_optional = timbral_config_from_optional


def timbral_parse_error_return(interactive_plot: bool | None, message: str) -> tuple[Any, ...]:
    """Seven Gradio outputs when H_timbral numeric parsing fails (no generic Gradio crash)."""
    stub = TIMBRAL_PARSE_ERROR_STUB
    title = timbral_parse_error_plot_title(message)
    if interactive_plot:
        fig_t = make_timbral_figure_plotly(stub, title=title)
        plot_path_t = export_plotly_figure_static(fig_t, "timbral_error_plot_")
    else:
        fig_t = make_timbral_figure(stub, title=title)
        plot_path_t = new_export_path("timbral_error_plot_", ".png")
        fig_t.savefig(plot_path_t, dpi=200)
        plt.close(fig_t)
    summary = timbral_parse_error_summary(message)
    return (
        fig_t,
        summary,
        None,
        str(plot_path_t),
        None,
        gr.update(value=[], headers=TIMBRAL_DIAGNOSTIC_TABLE_HEADERS),
        gr.update(value=None),
    )


def export_plotly_figure_static(fig, stem: str) -> str:
    """
    Save an interactive Plotly figure for the file download.

    Prefer PNG via Kaleido. If that fails (missing/incompatible kaleido), write standalone HTML.
    """
    png_path = new_export_path(stem, ".png")
    try:
        fig.write_image(str(png_path))
        return str(png_path)
    except Exception as exc:  # pragma: no cover - environment-dependent
        _LOG.warning("Plotly write_image failed (%s); falling back to HTML export.", exc)
        warnings.warn(
            "Plot static PNG export failed (install compatible plotly+kaleido, see pyproject.toml). "
            "Saved interactive HTML instead.",
            UserWarning,
            stacklevel=2,
        )
        html_path = new_export_path(stem, ".html")
        fig.write_html(str(html_path), include_plotlyjs="cdn", full_html=True)
        return str(html_path)
