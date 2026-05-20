"""H_timbral optional per-window decomposition (formula unchanged)."""

from __future__ import annotations

import pytest

from music21 import instrument as m21inst
from music21 import meter, note, stream

from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.services.analysis_service import run_timbral_analysis


def _score_four_bb_clarinets() -> stream.Score:
    sc = stream.Score()
    for _ in range(4):
        p = stream.Part()
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, m21inst.Clarinet())
        p.insert(0, note.Note("C4", quarterLength=4.0))
        sc.append(p)
    return sc


def _score_three_bb_one_bass_clarinet() -> stream.Score:
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


def test_h_timbral_series_identical_with_or_without_decomposition():
    sc = _score_four_bb_clarinets()
    an = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25)
    r0 = an.analyze_timbral(4.0, return_components=False)
    r1 = an.analyze_timbral(4.0, return_components=True)
    assert r0["H_timbral"] == r1["H_timbral"]
    assert len(r1["H_timbral_diagnostics"]) == len(r1["t"])
    _sem = {
        "timbral_model_mode",
        "model_description",
        "model_version",
        "not_audio_analysis",
        "config_profile_name",
        "config_model_version",
        "constants_used",
        "source_keys_used",
        "provisional_constants_used",
    }
    for d in r1["H_timbral_diagnostics"]:
        assert _sem.issubset(d.keys())
        assert d["timbral_model_mode"] == "legacy"
        assert d["not_audio_analysis"] is True
        assert d["config_profile_name"] == "legacy_default"
        assert isinstance(d["constants_used"], list)
        if d.get("n_notes", 0) > 0:
            assert len(d["constants_used"]) > 0
        assert set(d["provisional_constants_used"]).issubset(set(d["constants_used"]))
        if d.get("n_notes", 0) == 0 or d.get("instrument_component") is None:
            assert d["H_timbral"] == 0.5
            continue
        h_lin = d["weight_instrument"] * d["instrument_component"] + d["weight_register"] * d["register_component"]
        assert d["H_timbral"] == pytest.approx(max(0.0, min(1.0, float(h_lin))), abs=1e-11)


def test_compute_H_timbral_matches_decomposition_scalar():
    sc = _score_four_bb_clarinets()
    an = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=0.25)
    for t in (0.0, 1.0, 2.0, 3.0):
        feats = an.extract_timbral_features(float(t), 4.0)
        h_old = an.compute_H_timbral(feats)
        h_new, diag = an.compute_H_timbral_decomposition(feats)
        assert h_old == pytest.approx(h_new, abs=1e-12)
        assert h_new == pytest.approx(diag["H_timbral"], abs=1e-12)


def test_run_timbral_analysis_return_components_in_results(tmp_path):
    sc = _score_four_bb_clarinets()
    path = tmp_path / "cl4.musicxml"
    sc.write("musicxml", fp=str(path))
    out = run_timbral_analysis(str(path), {"time_step": 0.25, "window_size": 4.0, "return_components": True})
    assert not out.get("error"), out.get("error")
    assert "H_timbral_diagnostics" in out["results"]
    assert len(out["results"]["H_timbral_diagnostics"]) == len(out["results"]["t"])


def test_uniform_vs_mixed_clarinets_diagnostics_show_instrument_split():
    """Four identical Bb clarinets vs three Bb + one bass: diagnostics expose distinct instrument mass."""
    uniform = _score_four_bb_clarinets()
    mixed = _score_three_bb_one_bass_clarinet()
    an_u = TimbralHomogeneityAnalyzer(music21_score=uniform, time_step=1.0)
    an_m = TimbralHomogeneityAnalyzer(music21_score=mixed, time_step=1.0)
    fu = an_u.extract_timbral_features(2.0, 4.0)
    fm = an_m.extract_timbral_features(2.0, 4.0)
    assert fu is not None and fm is not None
    _, du = an_u.compute_H_timbral_decomposition(fu)
    _, dm = an_m.compute_H_timbral_decomposition(fm)
    assert du is not None and dm is not None
    inst_u = du["instrument_distribution"]
    inst_m = dm["instrument_distribution"]
    assert len(inst_u) == 1, "four identical canonical clarinets → one instrument bucket"
    assert len(inst_m) >= 2, "three Bb + bass clarinet → at least two canonical instrument ids"
    assert sum(inst_u.values()) > 0 and sum(inst_m.values()) > 0
    assert float(dm["instrument_pairwise_component"]) < float(du["instrument_pairwise_component"]) - 1e-6
