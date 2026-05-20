"""Tests for bowed-string refinement of H_timbral (symbolic, pairwise)."""

from __future__ import annotations

import numpy as np
import pytest
from music21 import articulations, expressions, note

from homogeneity_analyser.analyzers.string_pairwise_timbral import (
    BOWED_ORCHESTRAL_STRINGS,
    blend_string_and_legacy_instrument_component,
    pairwise_string_homogeneity,
    register_similarity_pitch,
    section_similarity,
    technique_similarity,
)
from homogeneity_analyser.analyzers.string_technique import (
    TECH_ARCO,
    TECH_HARMONIC,
    TECH_PIZZ,
    TECH_SUL_PONT,
    TECH_SUL_TASTO,
    TECH_TREMOLO,
    string_technique_from_note,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer


def _ev(inst: str, pitch: float, tech: str = TECH_ARCO, w: float = 1.0) -> dict:
    return {"instrument": inst, "pitch": pitch, "technique": tech, "overlap_ql": w}


def test_section_hierarchy_violin_viola_vs_violin_cello():
    a = pairwise_string_homogeneity([_ev("violin", 69), _ev("viola", 69)])
    b = pairwise_string_homogeneity([_ev("violin", 69), _ev("cello", 69)])
    assert a > b


def test_section_hierarchy_cello_bass_vs_violin_bass():
    a = pairwise_string_homogeneity([_ev("cello", 48), _ev("double bass", 36)])
    b = pairwise_string_homogeneity([_ev("violin", 69), _ev("double bass", 36)])
    assert a > b


def test_register_same_section_near_vs_far():
    close = pairwise_string_homogeneity([_ev("violin", 69), _ev("violin", 71)])
    mid = pairwise_string_homogeneity([_ev("violin", 60), _ev("violin", 72)])
    far = pairwise_string_homogeneity([_ev("violin", 55), _ev("violin", 79)])
    assert close >= mid >= far


def test_technique_hierarchy_arco_chain():
    base = (69.0, 69.0)
    pairs = [
        (TECH_ARCO, TECH_ARCO),
        (TECH_ARCO, TECH_TREMOLO),
        (TECH_ARCO, TECH_SUL_TASTO),
        (TECH_ARCO, TECH_SUL_PONT),
        (TECH_ARCO, TECH_HARMONIC),
        (TECH_ARCO, TECH_PIZZ),
    ]
    vals = []
    for t1, t2 in pairs:
        vals.append(pairwise_string_homogeneity([_ev("violin", base[0], t1), _ev("violin", base[1], t2)]))
    for i in range(len(vals) - 1):
        assert vals[i] > vals[i + 1], (pairs[i], pairs[i + 1], vals[i], vals[i + 1])


def test_arco_pizz_strongly_lower_than_arco_arco():
    aa = pairwise_string_homogeneity([_ev("violin", 60, TECH_ARCO), _ev("violin", 60, TECH_ARCO)])
    ap = pairwise_string_homogeneity([_ev("violin", 60, TECH_ARCO), _ev("violin", 60, TECH_PIZZ)])
    assert aa - ap > 0.35


def test_three_violins_vs_violins_plus_cello():
    vvv = pairwise_string_homogeneity([_ev("violin", 65), _ev("violin", 66), _ev("violin", 64)])
    vvc = pairwise_string_homogeneity([_ev("violin", 65), _ev("violin", 66), _ev("cello", 64)])
    assert vvv > vvc


def test_blend_preserves_non_string_mass():
    legacy = 0.4
    h_s = 0.95
    out = blend_string_and_legacy_instrument_component(h_s, legacy, string_overlap_mass=1.0, total_overlap_mass=4.0)
    assert abs(out - (0.25 * h_s + 0.75 * legacy)) < 1e-9


def test_string_technique_pizzicato_articulation():
    n = note.Note("G4")
    n.articulations = [articulations.Pizzicato()]
    assert string_technique_from_note(n) == TECH_PIZZ


def test_string_technique_tremolo_expression():
    n = note.Note("A4")
    n.expressions.append(expressions.Tremolo())
    assert string_technique_from_note(n) == TECH_TREMOLO


def test_string_technique_text_pizz():
    n = note.Note("B4")
    n.expressions.append(expressions.TextExpression("pizz."))
    assert string_technique_from_note(n) == TECH_PIZZ


def test_string_technique_text_sul_pont():
    n = note.Note("C5")
    n.expressions.append(expressions.TextExpression("sul pont."))
    assert string_technique_from_note(n) == TECH_SUL_PONT


def test_bowed_set_excludes_harp():
    assert "harp" not in BOWED_ORCHESTRAL_STRINGS


def test_timbral_compute_backward_compatible_dict():
    """Manual feature dicts without string_* keys still use legacy-only path."""
    ana = TimbralHomogeneityAnalyzer.__new__(TimbralHomogeneityAnalyzer)
    ana._timbral_config = {
        "weight_instrument": 0.65,
        "weight_register": 0.35,
        "family_bonus": 0.65,
        "register_ref_semitones": 3.0,
    }
    feats = {"n_notes": 4, "n_instruments": 1, "n_families": 1, "pitches": np.array([60, 62, 64, 65])}
    H = TimbralHomogeneityAnalyzer.compute_H_timbral(ana, feats)
    assert H > 0.7


def test_timbral_string_refinement_lowers_wide_register_two_violins():
    ana = TimbralHomogeneityAnalyzer.__new__(TimbralHomogeneityAnalyzer)
    ana._timbral_config = {
        "weight_instrument": 0.65,
        "weight_register": 0.35,
        "family_bonus": 0.65,
        "register_ref_semitones": 3.0,
    }
    wide = {
        "n_notes": 2,
        "n_instruments": 1,
        "n_families": 1,
        "pitches": np.array([55.0, 79.0]),
        "string_events": [
            {"instrument": "violin", "pitch": 55.0, "technique": TECH_ARCO, "overlap_ql": 1.0},
            {"instrument": "violin", "pitch": 79.0, "technique": TECH_ARCO, "overlap_ql": 1.0},
        ],
        "string_overlap_mass": 2.0,
        "total_overlap_mass": 2.0,
    }
    narrow = {
        "n_notes": 2,
        "n_instruments": 1,
        "n_families": 1,
        "pitches": np.array([69.0, 71.0]),
        "string_events": [
            {"instrument": "violin", "pitch": 69.0, "technique": TECH_ARCO, "overlap_ql": 1.0},
            {"instrument": "violin", "pitch": 71.0, "technique": TECH_ARCO, "overlap_ql": 1.0},
        ],
        "string_overlap_mass": 2.0,
        "total_overlap_mass": 2.0,
    }
    assert TimbralHomogeneityAnalyzer.compute_H_timbral(ana, narrow) > TimbralHomogeneityAnalyzer.compute_H_timbral(
        ana, wide
    )


@pytest.mark.parametrize(
    ("a", "b", "mn"),
    [
        ("violin", "viola", 0.9),
        ("violin", "cello", 0.6),
        ("cello", "double bass", 0.85),
        ("violin", "double bass", 0.45),
    ],
)
def test_section_similarity_magnitudes(a, b, mn):
    assert section_similarity(a, b) >= mn


def test_register_similarity_identity():
    assert register_similarity_pitch(60.0, 60.0) == pytest.approx(1.0)


def test_technique_similarity_symmetric():
    assert technique_similarity(TECH_ARCO, TECH_TREMOLO) == technique_similarity(TECH_TREMOLO, TECH_ARCO)
