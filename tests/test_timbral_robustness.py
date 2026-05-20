"""Robustness tests for ``H_timbral`` (weights, mass semantics, order-free family blend, bounds)."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest
from music21 import chord, instrument, meter, stream

from homogeneity_analyser.analyzers.brass_technique import BRASS_OPEN
from homogeneity_analyser.analyzers.clarinet_technique import CLARINET_ORDINARIO
from homogeneity_analyser.analyzers.saxophone_technique import SAX_ORDINARIO
from homogeneity_analyser.analyzers.string_technique import TECH_ARCO
from homogeneity_analyser.analyzers.timbral import (
    TimbralHomogeneityAnalyzer,
    _combine_family_pairwise_homogeneity,
    _normalized_instr_register_weights,
)
from homogeneity_analyser.analyzers.timbre_cross_relations import verified_cross_timbral_boost
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_SAXOPHONES,
    get_timbral_config,
)


def _analyzer_cfg(**overrides: float | str) -> TimbralHomogeneityAnalyzer:
    a = object.__new__(TimbralHomogeneityAnalyzer)
    cfg = dict(get_timbral_config())
    cfg.update(overrides)
    a._timbral_config = cfg
    return a


def _minimal_feats_no_segments() -> dict:
    """One instrument, two pitches; no specialist segment masses (pairwise blend = legacy)."""
    return {
        "n_notes": 2,
        "n_instruments": 1,
        "n_families": 1,
        "pitches": np.array([60.0, 64.0], dtype=float),
        "register_span_pitches": np.array([60.0, 64.0], dtype=float),
        "string_events": [],
        "string_overlap_mass": 0.0,
        "brass_events": [],
        "brass_overlap_mass": 0.0,
        "flute_events": [],
        "flute_overlap_mass": 0.0,
        "clarinet_events": [],
        "clarinet_overlap_mass": 0.0,
        "double_reed_events": [],
        "double_reed_overlap_mass": 0.0,
        "saxophone_events": [],
        "saxophone_overlap_mass": 0.0,
        "percussion_events": [],
        "percussion_overlap_mass": 0.0,
        "percussion_unpitched_overlap_mass": 0.0,
        "percussion_pitched_overlap_mass": 0.0,
        "total_overlap_mass": 8.0,
        "timbral_note_slices": [],
        "timbral_state_concentration": 1.0,
    }


def test_normalized_weights_equal_positive_sum_like_half_half() -> None:
    a, b = _normalized_instr_register_weights({"weight_instrument": 2.0, "weight_register": 2.0})
    assert abs(a - 0.5) < 1e-9
    assert abs(b - 0.5) < 1e-9


def test_normalized_weights_negative_clamped_then_renormalized() -> None:
    wi, wr = _normalized_instr_register_weights({"weight_instrument": -1.0, "weight_register": 2.0})
    assert wi == 0.0
    assert abs(wr - 1.0) < 1e-9


def test_normalized_weights_both_zero_falls_back_to_defaults() -> None:
    wi, wr = _normalized_instr_register_weights({"weight_instrument": 0.0, "weight_register": 0.0})
    d = get_timbral_config()
    assert abs(wi - float(d["weight_instrument"])) < 1e-9
    assert abs(wr - float(d["weight_register"])) < 1e-9


def test_equal_positive_weights_match_explicit_half_half_H() -> None:
    """(2, 2) must renormalise to (0.5, 0.5), not act like raw 2+2 on the convex combination."""
    feats = _minimal_feats_no_segments()
    ref = 3.0
    reg = 1.0 / (1.0 + 4.0 / ref)
    expected_half = 0.5 * 1.0 + 0.5 * reg

    h_half = _analyzer_cfg(weight_instrument=0.5, weight_register=0.5, register_ref_semitones=ref).compute_H_timbral(
        feats
    )
    h_two_two = _analyzer_cfg(weight_instrument=2.0, weight_register=2.0, register_ref_semitones=ref).compute_H_timbral(
        feats
    )
    assert abs(h_half - expected_half) < 1e-6
    assert abs(h_two_two - expected_half) < 1e-6
    assert h_two_two <= 1.0 + 1e-9


def test_negative_weight_config_stays_in_unit_interval() -> None:
    feats = _minimal_feats_no_segments()
    h = _analyzer_cfg(weight_instrument=-5.0, weight_register=1.0).compute_H_timbral(feats)
    assert 0.0 <= h <= 1.0


def test_combine_family_blend_symmetric_under_mass_swap() -> None:
    """
    Mass-weighted mean is commutative: permuting which family carries which mass while
    permuting the corresponding fixed pairwise scores the same way leaves ``h_bar`` unchanged
    (order-independent; not tied to string-then-brass source order).
    """
    legacy = 0.4

    def mk_feats(sm: float, bm: float) -> dict:
        return {
            "total_overlap_mass": sm + bm,
            "string_overlap_mass": sm,
            "string_events": [
                {"instrument": "violin", "pitch": 60.0, "technique": TECH_ARCO, "overlap_ql": 1.0},
                {"instrument": "violin", "pitch": 62.0, "technique": TECH_ARCO, "overlap_ql": 1.0},
            ],
            "brass_overlap_mass": bm,
            "brass_events": [
                {"instrument": "trumpet", "pitch": 65.0, "technique": BRASS_OPEN, "overlap_ql": 1.0},
                {"instrument": "trumpet", "pitch": 67.0, "technique": BRASS_OPEN, "overlap_ql": 1.0},
            ],
        }

    a = mk_feats(2.0, 4.0)
    b = mk_feats(4.0, 2.0)
    with (
        patch("homogeneity_analyser.analyzers.timbral.pairwise_string_homogeneity", return_value=0.25),
        patch("homogeneity_analyser.analyzers.timbral.pairwise_brass_homogeneity", return_value=0.85),
    ):
        ha = _combine_family_pairwise_homogeneity(legacy, a)
    with (
        patch("homogeneity_analyser.analyzers.timbral.pairwise_string_homogeneity", return_value=0.85),
        patch("homogeneity_analyser.analyzers.timbral.pairwise_brass_homogeneity", return_value=0.25),
    ):
        hb = _combine_family_pairwise_homogeneity(legacy, b)
    assert abs(ha - hb) < 1e-9
    f = min(1.0, 6.0 / 6.0)
    h_bar = (2.0 * 0.25 + 4.0 * 0.85) / 6.0
    assert abs(ha - ((1.0 - f) * legacy + f * h_bar)) < 1e-9


def test_piano_chord_one_instrument_pitch_mass_exceeds_event_mass() -> None:
    """A chord is one score event / one instrument; pitch-level overlap mass scales with notes."""
    sc = stream.Score()
    p = stream.Part()
    p.insert(0, instrument.Piano())
    p.insert(0, meter.TimeSignature("4/4"))
    p.append(chord.Chord(["C4", "E4", "G4", "B4"], quarterLength=4.0))
    sc.insert(0, p)
    an = TimbralHomogeneityAnalyzer(music21_score=sc)
    feats = an.extract_timbral_features(2.0, 4.0)
    assert feats is not None
    assert feats["n_instruments"] == 1
    assert feats["n_score_events"] == 1
    assert feats["n_notes"] == 4
    assert feats["pitch_overlap_mass"] > feats["event_overlap_mass"] + 1e-6
    h = an.compute_H_timbral(feats)
    assert 0.0 <= h <= 1.0


@pytest.mark.parametrize(
    "slices,tm",
    [
        (
            [
                {"instrument": "tenor saxophone", "family": FAMILY_SAXOPHONES, "pitch": 68.0, "overlap_ql": 1.0},
                {"instrument": "b flat clarinet", "family": FAMILY_CLARINETS, "pitch": 70.0, "overlap_ql": 1.0},
            ],
            2.0,
        ),
        (
            [
                {"instrument": "trumpet", "family": FAMILY_BRASS, "pitch": 72.0, "overlap_ql": 3.0},
                {"instrument": "oboe", "family": "oboes", "pitch": 74.0, "overlap_ql": 3.0},
            ],
            6.0,
        ),
    ],
)
def test_verified_cross_boost_nonnegative_and_capped(slices: list[dict], tm: float) -> None:
    b = verified_cross_timbral_boost(slices, tm)
    assert 0.0 <= b <= 0.068 + 1e-9


def _features_tenor_sax_clarinet_cross() -> dict:
    """Minimal ``extract_timbral_features``-shaped dict with a verified cross-family pair."""
    slices = [
        {"instrument": "tenor saxophone", "family": FAMILY_SAXOPHONES, "pitch": 68.0, "overlap_ql": 1.0},
        {"instrument": "b flat clarinet", "family": FAMILY_CLARINETS, "pitch": 70.0, "overlap_ql": 1.0},
    ]
    pitches = np.array([68.0, 70.0], dtype=float)
    return {
        "pitches": pitches,
        "register_span_pitches": pitches.copy(),
        "instruments": {"tenor saxophone", "b flat clarinet"},
        "families": {FAMILY_SAXOPHONES, FAMILY_CLARINETS},
        "n_notes": 2,
        "n_instruments": 2,
        "n_families": 2,
        "string_events": [],
        "string_overlap_mass": 0.0,
        "brass_events": [],
        "brass_overlap_mass": 0.0,
        "flute_events": [],
        "flute_overlap_mass": 0.0,
        "clarinet_events": [
            {
                "instrument": "b flat clarinet",
                "pitch": 70.0,
                "technique": CLARINET_ORDINARIO,
                "overlap_ql": 1.0,
            }
        ],
        "clarinet_overlap_mass": 1.0,
        "double_reed_events": [],
        "double_reed_overlap_mass": 0.0,
        "saxophone_events": [
            {
                "instrument": "tenor saxophone",
                "pitch": 68.0,
                "technique": SAX_ORDINARIO,
                "overlap_ql": 1.0,
            }
        ],
        "saxophone_overlap_mass": 1.0,
        "percussion_events": [],
        "percussion_overlap_mass": 0.0,
        "percussion_unpitched_overlap_mass": 0.0,
        "percussion_pitched_overlap_mass": 0.0,
        "total_overlap_mass": 2.0,
        "timbral_note_slices": list(slices),
        "timbral_state_concentration": 1.0,
    }


def test_compute_H_timbral_stays_in_unit_interval_with_cross_slices() -> None:
    """End-to-end: instrument term + bounded cross boost + convex register mix never exceeds 1."""
    an = _analyzer_cfg()
    h = an.compute_H_timbral(_features_tenor_sax_clarinet_cross())
    assert 0.0 <= h <= 1.0
