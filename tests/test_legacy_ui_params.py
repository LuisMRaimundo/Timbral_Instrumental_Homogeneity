"""Tests for ``ui/legacy_ui_params.py`` (H(t) UI mapping)."""

from __future__ import annotations

import numpy as np
import pytest

from homogeneity_analyser.ui.legacy_ui_params import (
    build_homogeneity_params_from_ui,
    homogeneity_csv_save_arrays,
    homogeneity_plot_title,
)


def test_homogeneity_params_defaults() -> None:
    p = build_homogeneity_params_from_ui()
    assert p["time_step"] == pytest.approx(0.25)
    assert p["sigma"] == pytest.approx(12.0)


def test_homogeneity_params_rejects_nonpositive_step() -> None:
    with pytest.raises(ValueError, match="Time step and window size"):
        build_homogeneity_params_from_ui(time_step=0, window_size=4)


def test_homogeneity_plot_title_unchanged_format() -> None:
    t = homogeneity_plot_title(window_size=4.0, time_step=0.25, sigma=12.0)
    assert "Homogeneity H(t)" in t
    assert "sigma=12.0" in t


def test_homogeneity_csv_header_with_components() -> None:
    results = {
        "t": [0.0, 1.0],
        "H": [0.5, 0.6],
        "m1": [0.1, 0.2],
        "m2": [0.2, 0.3],
        "m3": [0.3, 0.4],
    }
    data, header = homogeneity_csv_save_arrays(results)
    assert header == "t_quarterLength,H,m1,m2,m3"
    assert data.shape == (2, 5)


def test_homogeneity_csv_header_without_components() -> None:
    results = {"t": [0.0], "H": [0.5]}
    data, header = homogeneity_csv_save_arrays(results)
    assert header == "t_quarterLength,H"
    assert data.shape == (1, 2)
    assert np.isfinite(data).all()
