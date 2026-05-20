"""Technique coverage branches via ``hti_technique_coverage`` and H_TI windows."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from music21 import converter, stream

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.hti_technique_coverage import resolve_technique_uniformity_and_coverage
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BRASS

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"


def test_resolve_unavailable_empty_technique_mass() -> None:
    tu, st = resolve_technique_uniformity_and_coverage({}, [])
    assert st == "unavailable"
    assert math.isnan(tu)


def test_golden_violins_ordinary_default_via_analyzer() -> None:
    path = FIXTURE_DIR / "golden_two_violins_unison_c5.musicxml"
    if not path.is_file():
        pytest.skip("fixture missing")
    sc = converter.parse(str(path))
    feats = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0).extract_hti_window(2.0, 4.0)
    assert feats is not None
    assert feats["technique_coverage_status"] == "ordinary_default_uniform"
    assert feats["technique_uniformity"] == pytest.approx(1.0)


def test_sul_pont_fixture_explicit_mixed() -> None:
    path = FIXTURE_DIR / "golden_two_violins_sul_pont_ordinario.musicxml"
    if not path.is_file():
        pytest.skip("fixture missing")
    sc = converter.parse(str(path))
    feats = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0).extract_hti_window(2.0, 4.0)
    assert feats is not None
    assert feats["technique_coverage_status"] == "explicit_mixed"
    assert feats["technique_uniformity"] == pytest.approx(0.5, abs=1e-9)


def test_no_technique_ids_unavailable() -> None:
    sc = stream.Score()
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    an._events = [
        {
            "offset": 0.0,
            "end": 4.0,
            "instrument": "horn",
            "family": FAMILY_BRASS,
            "technique_state_id": "",
            "technique_state": {},
            "pitches": [65.0],
            "dynamic_mark": "",
            "hairpin": "none",
        }
    ]
    feats = an.extract_hti_window(2.0, 4.0)
    assert feats is not None
    assert feats["technique_coverage_status"] == "unavailable"
