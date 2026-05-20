"""Tests for European-style decimal comma parsing in the Gradio UI layer."""

from __future__ import annotations

import pytest

from pathlib import Path
from types import SimpleNamespace

from homogeneity_analyser.ui.callbacks import run_timbral_app
from homogeneity_analyser.ui.validation import parse_ui_float

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"


def test_parse_ui_float_comma_decimal():
    assert parse_ui_float("0,25", default=0.0, field_name="t") == 0.25


def test_parse_ui_float_dot_decimal():
    assert parse_ui_float("0.25", default=0.0, field_name="t") == 0.25


def test_parse_ui_float_integer_string():
    assert parse_ui_float("4", default=0.0, field_name="t") == 4.0


def test_parse_ui_float_whitespace():
    assert parse_ui_float("  0,5  ", default=0.0, field_name="t") == 0.5


def test_parse_ui_float_empty_returns_none_when_default_none():
    assert parse_ui_float("", default=None, field_name="t") is None
    assert parse_ui_float(None, default=None, field_name="t") is None


def test_parse_ui_float_empty_required_raises():
    with pytest.raises(ValueError, match="time step"):
        parse_ui_float("", field_name="time step")


def test_parse_ui_float_ambiguous_mixed_separators_raises():
    with pytest.raises(ValueError, match="ambiguous"):
        parse_ui_float("1,234.5", default=0.0, field_name="x")


def test_parse_ui_float_invalid_raises():
    with pytest.raises(ValueError, match="not_a_number"):
        parse_ui_float("not-a-number", default=0.0, field_name="not_a_number")


def test_run_timbral_app_accepts_comma_decimal_timestep():
    if not FIXTURE_XML.is_file():
        pytest.skip("Fixture not found")
    fake = SimpleNamespace(name=str(FIXTURE_XML))
    fig_t, summary_t, csv_path_t, plot_path_t, json_path_t, diag_up, diag_csv_up = run_timbral_app(
        file_obj=fake,
        time_step="0,25",
        window_size="4,0",
        interactive_plot=False,
        include_timbral_diagnostics=False,
    )
    assert "Could not run legacy H_timbral" not in summary_t
    assert csv_path_t is not None
    assert plot_path_t is not None
    assert json_path_t is not None
    assert fig_t is not None


def test_run_timbral_app_still_accepts_dot_decimal_timestep():
    if not FIXTURE_XML.is_file():
        pytest.skip("Fixture not found")
    fake = SimpleNamespace(name=str(FIXTURE_XML))
    _, summary_t, csv_path_t, *_ = run_timbral_app(
        file_obj=fake,
        time_step="0.25",
        window_size="4.0",
        interactive_plot=False,
        include_timbral_diagnostics=False,
    )
    assert "Could not run legacy H_timbral" not in summary_t
    assert csv_path_t is not None


def test_run_timbral_app_parse_error_returns_user_message():
    if not FIXTURE_XML.is_file():
        pytest.skip("Fixture not found")
    fake = SimpleNamespace(name=str(FIXTURE_XML))
    fig_t, summary_t, csv_path_t, plot_path_t, json_path_t, *_ = run_timbral_app(
        file_obj=fake,
        time_step="1,2.3",
        window_size="4.0",
        interactive_plot=False,
        include_timbral_diagnostics=False,
    )
    assert "Could not run legacy H_timbral" in summary_t
    assert "ambiguous" in summary_t.lower()
    assert csv_path_t is None
    assert json_path_t is None
    assert fig_t is not None
    assert plot_path_t is not None
