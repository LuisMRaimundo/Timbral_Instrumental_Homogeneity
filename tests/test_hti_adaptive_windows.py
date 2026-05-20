"""Adaptive H_TI windowing (orchestration only; H_TI formula unchanged)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from homogeneity_analyser.analyzers.hti import HTI_CSV_COLUMNS, SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.hti_adaptive_windows import (
    HTI_EDGE_DROP,
    HTI_EDGE_INCLUDE,
    HTI_EDGE_MARK,
    build_hti_window_centers,
    hti_window_row_geometry,
    resolve_hti_windowing,
)
from homogeneity_analyser.services.analysis_service import run_symbolic_ti_homogeneity_analysis
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS, resolve_register_ref_semitones
from homogeneity_analyser.services.json_export import build_hti_export

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"


def test_resolve_auto_by_excerpt_duration_example() -> None:
    p = {
        **DEFAULT_HTI_PARAMS,
        "window_mode": "auto_by_excerpt_duration",
        "window_ratio": 0.15,
        "step_ratio": 0.01,
    }
    r = resolve_hti_windowing(p, excerpt_duration_quarter_length=20.0)
    assert r["window_size_effective"] == pytest.approx(3.0)
    assert r["time_step_effective"] == pytest.approx(0.2)


def test_resolve_clamp_minimum_window() -> None:
    p = {**DEFAULT_HTI_PARAMS, "window_mode": "auto_by_excerpt_duration", "window_ratio": 0.15, "step_ratio": 0.01}
    r = resolve_hti_windowing(p, excerpt_duration_quarter_length=2.0)
    assert r["window_size_effective"] >= float(DEFAULT_HTI_PARAMS["min_window_size"])


def test_resolve_clamp_maximum_window() -> None:
    p = {**DEFAULT_HTI_PARAMS, "window_mode": "auto_by_excerpt_duration", "window_ratio": 0.15, "step_ratio": 0.01}
    r = resolve_hti_windowing(p, excerpt_duration_quarter_length=200.0)
    assert r["window_size_effective"] <= float(DEFAULT_HTI_PARAMS["max_window_size"]) + 1e-9


def test_resolve_auto_by_target_windows_example() -> None:
    p = {
        **DEFAULT_HTI_PARAMS,
        "window_mode": "auto_by_target_windows",
        "target_window_count": 100.0,
        "window_to_step_ratio": 10.0,
    }
    r = resolve_hti_windowing(p, excerpt_duration_quarter_length=25.0)
    assert r["time_step_effective"] == pytest.approx(0.25)
    assert r["window_size_effective"] == pytest.approx(2.5)


def test_drop_partial_windows_shortens_centers() -> None:
    inc = build_hti_window_centers(10.0, 1.0, 6.0, HTI_EDGE_INCLUDE)
    drp = build_hti_window_centers(10.0, 1.0, 6.0, HTI_EDGE_DROP)
    assert len(drp) < len(inc)
    for t in drp:
        assert t + 0.5 * 6.0 <= 10.0 + 1e-9


def test_mark_partial_flags_edge_geometry() -> None:
    g = hti_window_row_geometry(9.0, 6.0, 0.0, 10.0, HTI_EDGE_MARK)
    assert g["edge_window"] is True
    assert float(g["window_coverage_ratio"]) < 1.0


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
def test_json_parameters_include_adaptive_keys() -> None:
    p = {
        **DEFAULT_HTI_PARAMS,
        "window_mode": "auto_by_excerpt_duration",
        "time_step": 0.25,
        "window_size": 4.0,
    }
    out = run_symbolic_ti_homogeneity_analysis(str(FIXTURE_XML), p)
    assert not out.get("error"), out.get("error")
    doc = build_hti_export(str(FIXTURE_XML), out)
    par = doc["parameters"]
    required = {
        "window_mode",
        "window_size_input",
        "time_step_input",
        "window_size_effective",
        "time_step_effective",
        "excerpt_duration_quarterLength",
        "window_ratio",
        "step_ratio",
        "target_window_count",
        "window_to_step_ratio",
        "min_window_size",
        "max_window_size",
        "min_time_step",
        "max_time_step",
        "edge_policy",
    }
    for k in required:
        assert k in par, f"missing parameter {k!r}"


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
def test_csv_columns_include_edge_fields() -> None:
    for col in ("window_start", "window_end", "edge_window", "window_coverage_ratio"):
        assert col in HTI_CSV_COLUMNS


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
def test_manual_hti_matches_direct_analyzer() -> None:
    p = {
        **DEFAULT_HTI_PARAMS,
        "window_mode": "manual",
        "time_step": 0.5,
        "window_size": 4.0,
        "edge_policy": "mark_partial_windows",
    }
    out = run_symbolic_ti_homogeneity_analysis(str(FIXTURE_XML), p)
    assert not out.get("error"), out.get("error")
    ref_ql = resolve_register_ref_semitones(p)
    an = SymbolicTIHomogeneityAnalyzer(
        str(FIXTURE_XML),
        time_step=float(p["time_step"]),
        register_ref_semitones=ref_ql,
        pitch_interpretation_mode=str(p.get("pitch_interpretation_mode")),
        same_subfamily_relief_factor=float(p.get("same_subfamily_relief_factor", 0.0) or 0.0),
        timbral_affinity_relief_factor=float(p.get("timbral_affinity_relief_factor", 0.0) or 0.0),
        timbral_affinity_profile=str(p.get("timbral_affinity_profile") or "conservative"),
        dynamic_affinity_enabled=bool(p.get("dynamic_affinity_enabled", True)),
        harmonic_pitch_policy=str(p.get("harmonic_pitch_policy") or "conservative"),
    )
    direct = an.analyze_hti(
        float(p["window_size"]),
        excerpt_end_ql=float(an.end_time),
        edge_policy=str(p.get("edge_policy") or HTI_EDGE_MARK),
    )
    np.testing.assert_allclose(
        np.asarray(out["results"]["H_TI"], dtype=float),
        np.asarray(direct["H_TI"], dtype=float),
        rtol=0.0,
        atol=0.0,
        equal_nan=True,
    )
