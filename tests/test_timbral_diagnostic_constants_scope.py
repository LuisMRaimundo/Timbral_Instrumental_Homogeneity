"""H_timbral diagnostics: constants_used / source_keys reflect the active computation path only."""

from __future__ import annotations

import pytest
from music21 import instrument as m21inst
from music21 import meter, note, stream

from homogeneity_analyser.acoustic_profiles.model_config import (
    build_timbral_window_diagnostics_bundle,
    get_timbral_acoustic_profile_document,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer


def _two_violins_score() -> stream.Score:
    sc = stream.Score()
    for _ in range(2):
        p = stream.Part()
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, m21inst.Violin())
        p.insert(0, note.Note("C4", quarterLength=4.0))
        sc.append(p)
    return sc


def _two_horns_score() -> stream.Score:
    sc = stream.Score()
    for _ in range(2):
        p = stream.Part()
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, m21inst.Horn())
        p.insert(0, note.Note("G4", quarterLength=4.0))
        sc.append(p)
    return sc


def _three_bb_one_bass_clarinet_score() -> stream.Score:
    sc = stream.Score()
    for _ in range(3):
        p = stream.Part()
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, m21inst.Clarinet())
        p.insert(0, note.Note("C4", quarterLength=4.0))
        sc.append(p)
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, m21inst.BassClarinet())
    p.insert(0, note.Note("C4", quarterLength=4.0))
    sc.append(p)
    return sc


def _diag_at(an: TimbralHomogeneityAnalyzer, t: float, w: float) -> dict:
    f = an.extract_timbral_features(float(t), float(w))
    assert f is not None
    _, d = an.compute_H_timbral_decomposition(f)
    return d


@pytest.mark.parametrize("window", (4.0, 8.0))
def test_h_timbral_scalar_unchanged_with_diagnostics(window: float) -> None:
    sc = _two_violins_score()
    an = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25)
    r0 = an.analyze_timbral(window, return_components=False)
    r1 = an.analyze_timbral(window, return_components=True)
    assert r0["H_timbral"] == r1["H_timbral"]


def test_violin_only_diagnostics_exclude_brass_clarinet_percussion() -> None:
    an = TimbralHomogeneityAnalyzer(music21_score=_two_violins_score(), time_step=1.0)
    d = _diag_at(an, 2.0, 4.0)
    cu = set(d["constants_used"])
    assert "string_section_similarity_matrix" in cu
    assert "brass_section_similarity_matrix" not in cu
    assert "clarinet_subtype_similarity_matrix" not in cu
    assert "percussion_macro_cross_similarity_matrix" not in cu


def test_horn_only_diagnostics_exclude_string_clarinet_percussion() -> None:
    an = TimbralHomogeneityAnalyzer(music21_score=_two_horns_score(), time_step=1.0)
    d = _diag_at(an, 2.0, 4.0)
    cu = set(d["constants_used"])
    assert "brass_section_similarity_matrix" in cu
    assert "string_section_similarity_matrix" not in cu
    assert "clarinet_subtype_similarity_matrix" not in cu
    assert "percussion_macro_cross_similarity_matrix" not in cu


def test_clarinet_plus_bass_clarinet_includes_clarinet_constants() -> None:
    an = TimbralHomogeneityAnalyzer(music21_score=_three_bb_one_bass_clarinet_score(), time_step=1.0)
    d = _diag_at(an, 2.0, 4.0)
    cu = set(d["constants_used"])
    assert "clarinet_subtype_similarity_matrix" in cu
    assert "brass_section_similarity_matrix" not in cu


def test_source_keys_and_provisional_are_derived_from_constants_used() -> None:
    doc = get_timbral_acoustic_profile_document()
    index = {c["semantic_name"]: c for c in doc["constants"]}
    sample = sorted(index.keys())[:12]
    b = build_timbral_window_diagnostics_bundle(sample)
    for sk in b["source_keys_used"]:
        assert any(
            str(index[n].get("source_key") or "") == sk
            for n in b["constants_used"]
            if n in index and str(index[n].get("source_key") or "") not in ("", "project_specific")
        )
    for name in b["provisional_constants_used"]:
        assert name in b["constants_used"]
