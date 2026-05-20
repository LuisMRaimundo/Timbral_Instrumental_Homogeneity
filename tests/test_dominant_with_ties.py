"""Dominant category reporting with ties (H_TI export diagnostics only)."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from music21 import converter

from homogeneity_analyser.analyzers.dominant_distribution import dominant_with_ties
from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.services.analysis_service import run_symbolic_ti_homogeneity_analysis
from homogeneity_analyser.services.json_export import HTI_EXPORT_SCHEMA_VERSION, build_hti_export


def test_exact_macrofamily_style_tie() -> None:
    dist = {
        "woodwinds": 0.48148148148148145,
        "brass": 0.48148148148148145,
        "strings": 0.037037037037037035,
    }
    r = dominant_with_ties(dist)
    assert r["dominant_primary"] in ("brass", "woodwinds")
    assert r["dominant_all"] == ["brass", "woodwinds"]
    assert r["tie"] is True
    assert r["max_share"] == pytest.approx(0.48148148148148145)
    assert r["margin_to_second"] == 0.0


def test_no_tie_margin_to_second() -> None:
    r = dominant_with_ties({"strings": 0.8, "woodwinds": 0.2})
    assert r["dominant_all"] == ["strings"]
    assert r["tie"] is False
    assert r["dominant_primary"] == "strings"
    assert r["max_share"] == pytest.approx(0.8)
    assert r["margin_to_second"] == pytest.approx(0.6)


def test_near_tie_within_tolerance() -> None:
    r = dominant_with_ties({"woodwinds": 0.5000000001, "brass": 0.5}, tolerance=1e-9)
    assert r["tie"] is True
    assert set(r["dominant_all"]) == {"brass", "woodwinds"}
    assert r["margin_to_second"] == 0.0


def test_empty_distribution() -> None:
    r = dominant_with_ties({})
    assert r["dominant_primary"] is None
    assert r["dominant_all"] == []
    assert r["tie"] is False
    assert r["max_share"] is None
    assert r["margin_to_second"] is None


def test_hti_core_unchanged_by_dominant_reporting_keys() -> None:
    feats: dict = {
        "instrument_uniformity": 0.5,
        "family_uniformity": 0.5,
        "technique_uniformity": 0.5,
        "register_proximity": 0.5,
        "technique_coverage_status": "explicit_uniform",
        "register_coverage_status": "pitched",
        "dominant_macrofamilies": ["a", "b"],
        "dominant_macrofamily_tie": True,
    }
    an = SymbolicTIHomogeneityAnalyzer.__new__(SymbolicTIHomogeneityAnalyzer)
    h1, _, _ = SymbolicTIHomogeneityAnalyzer.compute_H_TI(an, feats)
    h2, _, _ = SymbolicTIHomogeneityAnalyzer.compute_H_TI(
        an, {k: v for k, v in feats.items() if not str(k).startswith("dominant_")}
    )
    assert h1 == h2
    assert math.isfinite(float(h1))


def test_penderecki_fixture_json_macrofamily_tie() -> None:
    path = Path(__file__).resolve().parent / "fixtures" / "musicxml" / "penderecki_style_macrofamily_tie.musicxml"
    sc = converter.parse(str(path))
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    res = an.analyze_hti(4.0)
    out = {"results": res, "parameters": {}, "analyzer": an}
    doc = build_hti_export(str(path), out)
    assert doc["schema_version"] == HTI_EXPORT_SCHEMA_VERSION
    row0 = doc["time_series"][0]
    assert row0.get("dominant_macrofamily_tie") is True
    dmall = row0.get("dominant_macrofamilies") or []
    assert set(dmall) == {"brass", "woodwinds"}


def test_run_symbolic_ti_summary_notes_macrofamily_tie() -> None:
    path = Path(__file__).resolve().parent / "fixtures" / "musicxml" / "penderecki_style_macrofamily_tie.musicxml"
    out = run_symbolic_ti_homogeneity_analysis(
        str(path),
        {"time_step": 1.0, "window_size": 4.0},
    )
    assert out.get("error") is None
    summary = str(out.get("summary") or "")
    assert "Dominant macrofamily" in summary
    assert "(tie)" in summary
    assert "brass" in summary.lower() and "woodwinds" in summary.lower()
