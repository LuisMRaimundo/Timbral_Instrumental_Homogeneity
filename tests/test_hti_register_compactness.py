"""H_TI register compactness: span + pairwise interval proximity (``hti.py``)."""

from __future__ import annotations

import math

import pytest
from music21 import instrument as m21inst
from music21 import note, stream

from homogeneity_analyser.analyzers.hti import (
    SymbolicTIHomogeneityAnalyzer,
    compute_register_compactness_fields,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_STRINGS

_TS_STOPPED = {
    "primary": "stopped",
    "mute": "none",
    "contact_point": "ordinary",
    "excitation": "ordinary",
    "articulation_effect": "none",
}


def test_pairwise_close_packed_higher_than_sparse_same_outer_span() -> None:
    ref = 12.0
    # Same outer span 12 semitones; chromatic cluster vs wide internal thirds.
    packed = [(60.0, 1.0), (61.0, 1.0), (62.0, 1.0), (72.0, 1.0)]
    sparse = [(60.0, 1.0), (64.0, 1.0), (68.0, 1.0), (72.0, 1.0)]
    da = compute_register_compactness_fields(packed, ref)
    db = compute_register_compactness_fields(sparse, ref)
    assert da["register_span_semitones"] == pytest.approx(12.0)
    assert db["register_span_semitones"] == pytest.approx(12.0)
    assert da["register_span_proximity"] == pytest.approx(db["register_span_proximity"])
    assert da["pairwise_interval_proximity"] > db["pairwise_interval_proximity"]
    assert da["register_compactness"] > db["register_compactness"]
    assert da["register_proximity"] == pytest.approx(da["register_compactness"])
    assert da["pairwise_interval_coverage_status"] == "sufficient_pairs"


def test_single_pitch_insufficient_pairs() -> None:
    out = compute_register_compactness_fields([(60.0, 2.5)], 7.0)
    assert out["pairwise_interval_coverage_status"] == "insufficient_pairs"
    assert out["pairwise_interval_proximity"] == pytest.approx(1.0)
    assert out["register_span_semitones"] == pytest.approx(0.0)
    assert out["register_span_proximity"] == pytest.approx(1.0)
    assert out["register_compactness"] == pytest.approx(1.0)


def test_unpitched_only_bundle() -> None:
    out = compute_register_compactness_fields([], 7.0)
    assert out["register_coverage_status"] == "unpitched_only"
    assert out["pairwise_interval_coverage_status"] == "unpitched_only"
    assert not math.isfinite(float(out["register_compactness"]))


def _violin_event(pitches: list[float]) -> dict:
    return {
        "offset": 0.0,
        "end": 4.0,
        "instrument": "violin",
        "family": FAMILY_STRINGS,
        "technique_state_id": "ts1",
        "technique_state": _TS_STOPPED,
        "pitches": list(pitches),
        "dynamic_mark": "mf",
        "hairpin": "none",
    }


def test_chord_multiple_pitches_one_event_all_enter_pairwise() -> None:
    sc = stream.Score()
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0, register_ref_semitones=12.0)
    an._events = [_violin_event([60.0, 64.0, 67.0])]
    feats = an.extract_hti_window(2.0, 4.0)
    assert feats is not None
    assert feats["pairwise_interval_coverage_status"] == "sufficient_pairs"
    # Three tones: manual check weighted mean of three pair proximities with equal masses (1*1 weights).
    ref = 12.0
    d01, d02, d12 = 4.0, 7.0, 3.0
    p01 = 1.0 / (1.0 + d01 / ref)
    p02 = 1.0 / (1.0 + d02 / ref)
    p12 = 1.0 / (1.0 + d12 / ref)
    expected_pair = (p01 + p02 + p12) / 3.0
    assert feats["pairwise_interval_proximity"] == pytest.approx(expected_pair, rel=1e-5)
    span = 7.0
    expected_span = 1.0 / (1.0 + span / ref)
    assert feats["register_span_proximity"] == pytest.approx(expected_span, rel=1e-5)


def test_close_packed_higher_H_TI_core_than_sparse_same_outer_span() -> None:
    sc = stream.Score()
    packed_an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0, register_ref_semitones=12.0)
    sparse_an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0, register_ref_semitones=12.0)
    packed_an._events = [_violin_event([60.0, 61.0, 62.0, 72.0])]
    sparse_an._events = [_violin_event([60.0, 64.0, 68.0, 72.0])]
    fp = packed_an.extract_hti_window(2.0, 4.0)
    fs = sparse_an.extract_hti_window(2.0, 4.0)
    assert fp is not None and fs is not None
    hp, _, _ = packed_an.compute_H_TI(fp)
    hs, _, _ = sparse_an.compute_H_TI(fs)
    assert fp["instrument_uniformity"] == pytest.approx(fs["instrument_uniformity"])
    assert fp["family_uniformity"] == pytest.approx(fs["family_uniformity"])
    assert hp > hs


def test_hti_register_uses_sounding_pitch_for_transposing_clarinet() -> None:
    """Pipeline ``pitches`` are concert MIDI (same as timbral); written C4 → B♭3 for B♭ clarinet."""
    p = stream.Part()
    p.insert(0, m21inst.Clarinet())
    p.insert(0, note.Note("C4", quarterLength=4.0))
    sc = stream.Score(p)
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    assert len(an._events) == 1
    assert an._events[0]["pitches"] == [58.0]


def test_unpitched_percussion_no_register_component() -> None:
    sc = stream.Score()
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    an._events = [
        {
            "offset": 0.0,
            "end": 4.0,
            "instrument": "snare drum",
            "family": "percussion",
            "technique_state_id": "",
            "technique_state": {},
            "pitches": [],
            "dynamic_mark": "",
            "hairpin": "none",
        }
    ]
    feats = an.extract_hti_window(2.0, 4.0)
    assert feats is not None
    assert feats["register_coverage_status"] == "unpitched_only"
    assert feats["pairwise_interval_coverage_status"] == "unpitched_only"
    assert not math.isfinite(float(feats["register_compactness"]))
    h, diag, renorm = an.compute_H_TI(feats)
    assert "register_proximity" not in renorm
    assert "register_proximity" not in diag["components"]
    assert math.isfinite(h)
