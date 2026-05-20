"""Tests for pure H_TI UI parameter mapping (``ui/hti_ui_params.py``)."""

from __future__ import annotations

import pytest

from homogeneity_analyser.analyzers.hti_export_rows import HTI_CSV_COLUMNS
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS
from homogeneity_analyser.ui.hti_ui_params import (
    build_hti_analysis_params_from_ui,
    build_hti_csv_rows_from_results,
    hti_results_plot_title,
)


def test_build_hti_params_manual_defaults() -> None:
    p = build_hti_analysis_params_from_ui()
    assert p["window_mode"] == DEFAULT_HTI_PARAMS["window_mode"]
    assert p["edge_policy"] == DEFAULT_HTI_PARAMS["edge_policy"]
    assert p["time_step"] == pytest.approx(float(DEFAULT_HTI_PARAMS["time_step"]))


def test_build_hti_params_manual_requires_positive_step_and_window() -> None:
    with pytest.raises(ValueError, match="Time step and window size"):
        build_hti_analysis_params_from_ui(window_mode="manual", time_step=0, window_size=4)


def test_build_hti_params_relief_out_of_range() -> None:
    with pytest.raises(ValueError, match="Same-subfamily relief"):
        build_hti_analysis_params_from_ui(same_subfamily_relief_factor=1.5)


def test_hti_plot_title_includes_mode() -> None:
    t = hti_results_plot_title(window_size_effective=4.0, time_step_effective=1.0, window_mode="manual")
    assert "manual" in t
    assert "4.0" in t


def test_build_hti_csv_rows_all_columns_same_length() -> None:
    from pathlib import Path

    from homogeneity_analyser.services.analysis_service_hti import run_symbolic_ti_homogeneity_analysis

    fx = Path("tests/fixtures/musicxml/golden_two_violins_unison_c5.musicxml")
    p = build_hti_analysis_params_from_ui(include_symbolic_blend_potential=True)
    out = run_symbolic_ti_homogeneity_analysis(str(fx), p)
    assert out.get("error") is None
    results = out["results"]
    n = len(results["t"])
    for col in HTI_CSV_COLUMNS:
        key = "t" if col == "t_quarterLength" else col
        assert len(results[key]) == n, f"{col}: {len(results[key])} != {n}"
    rows = build_hti_csv_rows_from_results(results)
    assert len(rows) == n


def test_build_hti_csv_rows_minimal_results() -> None:
    results: dict = {"t": [0.0]}
    for col in HTI_CSV_COLUMNS:
        if col == "t_quarterLength":
            continue
        results[col] = ["" if "dominant" in col and col.endswith("s") else float("nan")]
    rows = build_hti_csv_rows_from_results(results)
    assert len(rows) == 1
    assert rows[0]["t_quarterLength"] == pytest.approx(0.0)
