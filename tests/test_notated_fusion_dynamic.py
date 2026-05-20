"""Dynamic coherence for ``H_notated_fusion_potential_dynamic`` (notation-symbolic, not SPL)."""

from __future__ import annotations

import os

import pytest
import tempfile
from pathlib import Path

from music21 import dynamics, instrument, note, stream

from homogeneity_analyser.analyzers.notated_fusion_dynamic import compute_dynamic_coherence_bundle
from homogeneity_analyser.analyzers.notated_fusion_potential import NotatedFusionPotentialAnalyzer
from homogeneity_analyser.services.analysis_service import (
    run_notated_fusion_potential_analysis,
    run_orchestration_symbolic_analysis,
)


def _four_trombones_pp_crescendo_score() -> stream.Score:
    s = stream.Score()
    for i in range(4):
        p = stream.Part(id=f"P{i + 1}")
        p.partName = "Trombone"
        p.insert(0, instrument.Trombone())
        m = stream.Measure()
        m.insert(0, dynamics.Dynamic("pp"))
        m.insert(0, dynamics.Crescendo())
        m.insert(1, note.Note(60 + i, quarterLength=4.0))
        p.append(m)
        s.insert(0, p)
    return s


def test_compute_dynamic_coherence_uniform_levels_and_process() -> None:
    t0, t1 = 0.0, 4.0
    ev = [
        {"offset": 0.0, "end": 4.0, "dynamic_mark": "mf", "hairpin": "none", "salient_articulation": False},
        {"offset": 0.0, "end": 4.0, "dynamic_mark": "mf", "hairpin": "none", "salient_articulation": False},
    ]
    b = compute_dynamic_coherence_bundle(ev, t0, t1, h_base=0.8, weight_dynamic=0.1)
    assert b["dynamic_coherence"] == pytest.approx(1.0)
    assert b["H_notated_fusion_potential_dynamic"] == pytest.approx(0.8)


def test_compute_dynamic_coherence_level_divergence() -> None:
    t0, t1 = 0.0, 4.0
    ev = [
        {"offset": 0.0, "end": 4.0, "dynamic_mark": "pp", "hairpin": "none", "salient_articulation": False},
        {"offset": 0.0, "end": 4.0, "dynamic_mark": "mf", "hairpin": "none", "salient_articulation": False},
    ]
    b = compute_dynamic_coherence_bundle(ev, t0, t1, h_base=0.9, weight_dynamic=0.1)
    assert b["dynamic_coherence"] < 1.0
    assert b["dynamic_divergence_detected"] is True
    assert b["H_notated_fusion_potential_dynamic"] < 0.9


def test_compute_dynamic_crescendo_vs_static() -> None:
    t0, t1 = 0.0, 4.0
    ev = [
        {"offset": 0.0, "end": 4.0, "dynamic_mark": "pp", "hairpin": "crescendo", "salient_articulation": False},
        {"offset": 0.0, "end": 4.0, "dynamic_mark": "pp", "hairpin": "none", "salient_articulation": False},
    ]
    b = compute_dynamic_coherence_bundle(ev, t0, t1, h_base=0.85, weight_dynamic=0.1)
    assert b["dynamic_coherence"] < 1.0
    assert b["H_notated_fusion_potential_dynamic"] < 0.85


def test_trbvlc_four_trombones_pp_shared_crescendo_programmatic() -> None:
    """Shared pp + crescendo: base H_nf unchanged scaling; dynamic coherence high; H_nfd ≈ H_nf."""
    sc = _four_trombones_pp_crescendo_score()
    an = NotatedFusionPotentialAnalyzer(music21_score=sc, time_step=1.0, weight_notated_fusion_dynamic=0.1)
    res = an.analyze_notated_fusion_potential(window_size=8.0, return_diagnostics=True)
    d0 = res["H_notated_fusion_potential_diagnostics"][0]
    h0 = float(res["H_notated_fusion_potential"][0])
    hd0 = float(res["H_notated_fusion_potential_dynamic"][0])
    assert h0 > 0.5
    assert d0["dynamic_coherence"] == pytest.approx(1.0)
    assert d0["crescendo_active"] is True
    assert d0["dynamic_divergence_detected"] is False
    assert hd0 == pytest.approx(h0 * (1.0**0.1))
    assert hd0 == pytest.approx(h0)

    fd, tmp = tempfile.mkstemp(suffix=".musicxml")
    os.close(fd)
    try:
        sc.write("musicxml", fp=tmp)
        oo = run_orchestration_symbolic_analysis(tmp, {"time_step": 1.0, "window_size": 8.0})
        assert oo.get("error") is None
        assert float(oo["results"]["H_orchestration_symbolic"][0]) > 0.5
    finally:
        os.unlink(tmp)


def test_negative_four_trombones_three_pp_one_mf_fixture() -> None:
    repo = Path(__file__).resolve().parents[1]
    xml = repo / "tests" / "fixtures" / "musicxml" / "four_trombones_three_pp_one_mf.musicxml"
    if not xml.is_file():
        pytest.skip("fixture missing")
    out = run_notated_fusion_potential_analysis(str(xml), {"time_step": 1.0, "window_size": 8.0})
    assert out.get("error") is None
    d0 = out["results"]["H_notated_fusion_potential_diagnostics"][0]
    hb = float(out["results"]["H_notated_fusion_potential"][0])
    hd = float(out["results"]["H_notated_fusion_potential_dynamic"][0])
    assert d0["dynamic_coherence"] < 1.0
    assert hd < hb - 1e-6
    assert d0["dynamic_divergence_detected"] is True
