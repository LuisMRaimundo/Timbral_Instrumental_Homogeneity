"""Timbral semantic model naming: diagnostics metadata and default numeric stability."""

from __future__ import annotations

import numpy as np
import pytest
from music21 import instrument as m21inst
from music21 import meter, note, stream

from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.models.timbral_semantics import timbral_model_metadata_for_diagnostics


def _score_four_bb_clarinets() -> stream.Score:
    sc = stream.Score()
    for _ in range(4):
        p = stream.Part()
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, m21inst.Clarinet())
        p.insert(0, note.Note("C4", quarterLength=4.0))
        sc.append(p)
    return sc


def test_timbral_model_metadata_for_diagnostics_legacy_shape() -> None:
    meta = timbral_model_metadata_for_diagnostics("legacy")
    assert meta["timbral_model_mode"] == "legacy"
    assert meta["not_audio_analysis"] is True
    assert "legacy" in meta["model_description"].lower()
    assert meta["model_version"]


def test_timbral_model_metadata_symbolic_shape() -> None:
    meta = timbral_model_metadata_for_diagnostics("symbolic")
    assert meta["timbral_model_mode"] == "symbolic"
    assert meta["not_audio_analysis"] is True
    assert "technique-only" in meta["model_description"].lower()


def test_default_h_timbral_series_unchanged_four_clarinets() -> None:
    """Golden pattern for fixed in-memory score (formula must not drift unintentionally)."""
    sc = _score_four_bb_clarinets()
    an = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25)
    r = an.analyze_timbral(4.0, return_components=False)
    h = r["H_timbral"]
    assert len(h) == 65
    for i in range(24):
        exp = 0.8604999999999998 if i in (5, 11) else 0.8605
        assert h[i] == pytest.approx(exp, abs=1e-12)
    for i in range(24, 65):
        assert h[i] == pytest.approx(0.5, abs=1e-12)


def test_explicit_legacy_matches_default_mode() -> None:
    sc = _score_four_bb_clarinets()
    a0 = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25)
    a1 = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25, timbral_model_mode="legacy")
    assert a0.analyze_timbral(4.0)["H_timbral"] == a1.analyze_timbral(4.0)["H_timbral"]


def test_symbolic_matches_legacy_on_uniform_four_clarinets() -> None:
    """Same score: technique-only concentration matches full-state here → identical H_timbral curve."""
    sc = _score_four_bb_clarinets()
    leg = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25, timbral_model_mode="legacy")
    sym = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25, timbral_model_mode="symbolic")
    assert leg.analyze_timbral(4.0)["H_timbral"] == sym.analyze_timbral(4.0)["H_timbral"]


def test_symbolic_at_least_legacy_on_clarinet_bass_clarinet_mix() -> None:
    """Synthetic window: same ordinary playing; symbolic should not double-penalize technique vs legacy."""
    slices = [
        {"instrument": "Clarinet", "family": "woodwinds", "technique_state_id": "Clarinet", "overlap_ql": 1.0}
    ] * 3 + [
        {
            "instrument": "Bass Clarinet",
            "family": "woodwinds",
            "technique_state_id": "Bass Clarinet",
            "overlap_ql": 1.0,
        }
    ]
    feats: dict = {
        "n_notes": 4,
        "n_score_events": 4,
        "n_instruments": 2,
        "n_families": 1,
        "pitches": np.array([60.0, 60.0, 60.0, 48.0]),
        "register_span_pitches": np.array([48.0, 60.0]),
        "instruments": {"Clarinet", "Bass Clarinet"},
        "families": {"woodwinds"},
        "total_overlap_mass": 4.0,
        "string_overlap_mass": 0.0,
        "brass_overlap_mass": 0.0,
        "flute_overlap_mass": 0.0,
        "clarinet_overlap_mass": 0.0,
        "double_reed_overlap_mass": 0.0,
        "saxophone_overlap_mass": 0.0,
        "percussion_overlap_mass": 0.0,
        "percussion_unpitched_overlap_mass": 0.0,
        "event_overlap_mass": 4.0,
        "timbral_note_slices": slices,
        "timbral_state_distribution": {"Clarinet": 3.0, "Bass Clarinet": 1.0},
        "timbral_state_concentration": 0.625,
        "dominant_timbral_state": "Clarinet",
        "instrument_distribution_concentration": 0.625,
        "family_distribution_concentration": 1.0,
        "technique_only_concentration": 1.0,
        "full_state_concentration": 0.625,
        "legacy_concentration": 0.625,
        "technique_only_distribution": {"__ordinary__": 4.0},
        "technique_state_distribution_full": {"Clarinet": 3.0, "Bass Clarinet": 1.0},
    }
    sc = _score_four_bb_clarinets()
    leg = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25, timbral_model_mode="legacy")
    sym = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25, timbral_model_mode="symbolic")
    h_leg, _ = leg.compute_H_timbral_decomposition(feats)
    h_sym, _ = sym.compute_H_timbral_decomposition(feats)
    assert h_sym >= h_leg - 1e-9
