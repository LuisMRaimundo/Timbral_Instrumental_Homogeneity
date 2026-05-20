"""Tests for instrumentation-independent vertical cluster metric H_cluster."""

from __future__ import annotations

import math

import pytest
from pathlib import Path

from music21 import instrument as m21inst
from music21 import meter, note, stream

from homogeneity_analyser.analyzers.cluster import (
    ClusterHomogeneityAnalyzer,
    compute_cluster_diagnostics_from_midi_list,
)
from homogeneity_analyser.services.analysis_service import run_cluster_analysis
from homogeneity_analyser.services.param_validation import AnalysisParameterError, validate_cluster_params


def _score_chromatic_four(cls: type, written_names: list[str]) -> stream.Score:
    sc = stream.Score()
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, cls())
    for nm in written_names:
        p.append(note.Note(nm, quarterLength=1.0))
    sc.append(p)
    return sc


@pytest.mark.parametrize(
    ("ins", "written"),
    [
        (m21inst.Violin, ["B3", "C4", "C#4", "D4"]),
        (m21inst.Horn, ["F#4", "G4", "G#4", "A4"]),
        (m21inst.Clarinet, ["C#4", "D4", "D#4", "E4"]),
    ],
)
def test_h_cluster_identical_for_same_sounding_chromatic_cluster(ins, written) -> None:
    """B3–C4–C#4–D4 concert yields identical H_cluster regardless of transposing instrument."""
    sc = _score_chromatic_four(ins, written)
    an = ClusterHomogeneityAnalyzer(music21_score=sc, time_step=1.0, cluster_ref_span=12.0)
    d = an.compute_cluster_window(2.0, 4.0)
    assert d["n_unique_pitches"] == 4
    assert d["chromatic_density"] == pytest.approx(1.0)
    assert d["H_cluster"] == pytest.approx(math.sqrt(0.8))


def test_chromatic_density_one_for_b3_d4_tetrad() -> None:
    d = compute_cluster_diagnostics_from_midi_list([59.0, 60.0, 61.0, 62.0], cluster_ref_span=12.0)
    assert d["chromatic_density"] == pytest.approx(1.0)
    assert d["span_st"] == pytest.approx(3.0)


def test_duplicate_doubling_duplicate_count_not_unique() -> None:
    base = compute_cluster_diagnostics_from_midi_list([59.0, 60.0, 61.0, 62.0], cluster_ref_span=12.0)
    dup = compute_cluster_diagnostics_from_midi_list([59.0, 60.0, 61.0, 62.0, 62.0], cluster_ref_span=12.0)
    assert dup["duplicate_pitch_count"] == base["duplicate_pitch_count"] + 1
    assert dup["n_unique_pitches"] == base["n_unique_pitches"]
    assert dup["H_cluster"] == pytest.approx(base["H_cluster"])


def test_empty_window_h_cluster_one_and_zero_events() -> None:
    d = compute_cluster_diagnostics_from_midi_list([], cluster_ref_span=12.0)
    assert d["H_cluster"] == 1.0
    assert d["n_events"] == 0
    assert d["cluster_empty_window"] is True


def test_validate_cluster_rejects_nonpositive_ref_span() -> None:
    with pytest.raises(AnalysisParameterError):
        validate_cluster_params({"time_step": 0.25, "window_size": 4.0, "cluster_ref_span": 0.0})


def test_run_cluster_fixture_smoke() -> None:
    fx = Path(__file__).resolve().parents[1] / "validation" / "fixtures_musicxml" / "step_density.xml"
    if not fx.is_file():
        pytest.skip("fixture not found")
    out = run_cluster_analysis(str(fx), {"time_step": 0.5, "window_size": 4.0, "cluster_ref_span": 12.0})
    assert not out.get("error"), out.get("error")
    assert "H_cluster" in out["results"]
    assert len(out["results"]["H_cluster"]) == len(out["results"]["t"])


def test_analyzer_empty_window_same_as_no_pitches() -> None:
    sc = stream.Score()
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, m21inst.Violin())
    p.append(note.Note("C4", quarterLength=1.0))
    sc.append(p)
    an = ClusterHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    d = an.compute_cluster_window(50.0, 2.0)
    assert d["cluster_empty_window"] is True
    assert d["H_cluster"] == 1.0
    assert d["n_events"] == 0
