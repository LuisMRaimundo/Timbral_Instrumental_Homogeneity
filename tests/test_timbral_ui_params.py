"""Tests for ``ui/timbral_ui_params.py``."""

from __future__ import annotations

import pytest

from homogeneity_analyser.ui.timbral_ui_params import (
    TIMBRAL_PARSE_ERROR_STUB,
    build_timbral_analysis_params_from_ui,
    timbral_config_from_optional,
    timbral_parse_error_summary,
    timbral_plot_title,
)


def test_timbral_config_none_when_empty() -> None:
    assert timbral_config_from_optional(None, None, None, None) is None


def test_timbral_params_defaults() -> None:
    p = build_timbral_analysis_params_from_ui()
    assert p["time_step"] == pytest.approx(0.25)
    assert p["return_components"] is False


def test_timbral_parse_error_stub_unchanged() -> None:
    assert TIMBRAL_PARSE_ERROR_STUB["H_timbral"] == [0.5]


def test_timbral_summary_mentions_legacy() -> None:
    s = timbral_parse_error_summary("bad value")
    assert "legacy h_timbral" in s.lower()
    assert "bad value" in s


def test_timbral_plot_title_format() -> None:
    assert timbral_plot_title(window_size=4.0, time_step=0.25).startswith("Legacy H_timbral")
