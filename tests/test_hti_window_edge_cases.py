"""Localized H_TI window / edge-policy and empty-overlap behaviour."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from music21 import converter, stream

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.hti_adaptive_windows import (
    HTI_EDGE_DROP,
    HTI_EDGE_INCLUDE,
    HTI_EDGE_MARK,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"


def _load(name: str):
    path = FIXTURE_DIR / name
    if not path.is_file():
        pytest.skip(f"missing fixture {name}")
    return converter.parse(str(path))


def test_edge_include_marks_no_partial_edges_on_short_score() -> None:
    sc = _load("golden_two_violins_unison_c5.musicxml")
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    r = an.analyze_hti(4.0, edge_policy=HTI_EDGE_INCLUDE)
    assert all(not bool(x) for x in r["edge_window"])


def test_edge_drop_and_mark_flag_partial_centers() -> None:
    sc = _load("golden_two_violins_unison_c5.musicxml")
    for ep in (HTI_EDGE_DROP, HTI_EDGE_MARK):
        an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        r = an.analyze_hti(4.0, edge_policy=ep)
        assert r["edge_window"] == [True, True, False, True, True]
        assert r["window_coverage_ratio"][0] == pytest.approx(0.5, abs=1e-9)


def test_empty_window_compute_hti_returns_nan() -> None:
    sc = stream.Score()
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    an._events = [
        {
            "offset": 0.0,
            "end": 4.0,
            "instrument": "violin",
            "family": "strings",
            "technique_state_id": "ts",
            "technique_state": {},
            "pitches": [60.0],
            "dynamic_mark": "mf",
            "hairpin": "none",
        }
    ]
    assert an.extract_hti_window(20.0, 4.0) is None
    h, diag, aw = an.compute_H_TI(None)
    assert math.isnan(h)
    assert diag["reason"] == "no_active_events"
    assert sum(aw.values()) == pytest.approx(1.0, abs=1e-12)


def test_zero_overlap_contrib_returns_none() -> None:
    sc = stream.Score()
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    an._events = [
        {
            "offset": 10.0,
            "end": 12.0,
            "instrument": "violin",
            "family": "strings",
            "technique_state_id": "",
            "technique_state": {},
            "pitches": [60.0],
            "dynamic_mark": "",
            "hairpin": "none",
        }
    ]
    assert an.extract_hti_window(2.0, 4.0) is None
