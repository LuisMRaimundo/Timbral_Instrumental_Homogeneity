"""Tests for H_fusion_acoustic_heuristic (acoustic-informed fusion, not audio)."""

from __future__ import annotations

import pytest

import json
from pathlib import Path

import numpy as np
from homogeneity_analyser.acoustic_profiles.features import resolve_acoustic_feature_row
from homogeneity_analyser.acoustic_profiles.similarity import weighted_normalized_feature_distance
from homogeneity_analyser.analyzers.fusion_acoustic_heuristic import (
    compute_fusion_acoustic_heuristic_window,
)
from homogeneity_analyser.models.results import FusionAcousticHeuristicSeriesResult
from homogeneity_analyser.services.analysis_service import run_fusion_acoustic_heuristic_analysis
from homogeneity_analyser.services.json_export import build_fusion_acoustic_heuristic_export

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"


def _slice(
    *,
    instrument: str,
    technique_state_id: str,
    pitch: float,
    overlap_ql: float = 1.0,
    onset: float = 0.0,
) -> dict:
    return {
        "instrument": instrument,
        "family": "strings",
        "instrument_source": "test",
        "pitch": float(pitch),
        "onset": float(onset),
        "note_end": float(onset) + 1.0,
        "overlap_ql": float(overlap_ql),
        "technique_state_id": technique_state_id,
        "technique_state": {},
    }


def test_compute_window_deterministic_json_roundtrip():
    slices = [
        _slice(instrument="Violin", technique_state_id="arco", pitch=60.0, onset=0.0),
        _slice(instrument="Violin", technique_state_id="arco", pitch=64.0, onset=0.1),
    ]
    reg = np.array([60.0, 64.0], dtype=float)
    a = compute_fusion_acoustic_heuristic_window(slices, reg)
    b = compute_fusion_acoustic_heuristic_window(slices, reg)
    assert a["H_fusion_acoustic_heuristic"] == pytest.approx(b["H_fusion_acoustic_heuristic"])
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    for k in (
        "model_version",
        "not_audio_analysis",
        "sources_used",
        "missing_features",
        "confidence_score",
        "confidence_label",
        "main_penalty_reason",
    ):
        assert k in a


def test_missing_unknown_instrument_does_not_crash():
    slices = [
        _slice(instrument="TotallyUnknownInstrumentXYZ", technique_state_id="t1", pitch=60.0),
    ]
    reg = np.array([60.0], dtype=float)
    out = compute_fusion_acoustic_heuristic_window(slices, reg)
    assert 0.0 <= out["H_fusion_acoustic_heuristic"] <= 1.0
    assert out["not_audio_analysis"] is True
    assert out["resolved_profile_match_rules"] == ["global_default"]


def test_same_instrument_same_technique_higher_than_mixed_technique():
    uniform = [
        _slice(instrument="Violin", technique_state_id="arco", pitch=60.0),
        _slice(instrument="Violin", technique_state_id="arco", pitch=63.0),
    ]
    mixed = [
        _slice(instrument="Violin", technique_state_id="arco", pitch=60.0),
        _slice(instrument="Violin", technique_state_id="pizz", pitch=63.0),
    ]
    reg_u = np.array([60.0, 63.0], dtype=float)
    hu = compute_fusion_acoustic_heuristic_window(uniform, reg_u)["H_fusion_acoustic_heuristic"]
    hm = compute_fusion_acoustic_heuristic_window(mixed, reg_u)["H_fusion_acoustic_heuristic"]
    assert hu > hm
    tu = compute_fusion_acoustic_heuristic_window(uniform, reg_u)["technique_similarity"]
    tm = compute_fusion_acoustic_heuristic_window(mixed, reg_u)["technique_similarity"]
    assert tu > tm


def test_horn_vs_violin_explained_by_profile_vectors_not_hidden_family_constant():
    rv = resolve_acoustic_feature_row("Violin", None)
    rh = resolve_acoustic_feature_row("Horn", None)
    assert rv["vector"]["spectral_centroid_class"] != rh["vector"]["spectral_centroid_class"]
    d, n_used, _ = weighted_normalized_feature_distance(rv["vector"], rh["vector"], None)
    assert n_used > 0 and d > 0.01
    v_slices = [
        _slice(instrument="Violin", technique_state_id="arco", pitch=60.0),
        _slice(instrument="Violin", technique_state_id="arco", pitch=64.0),
    ]
    h_slices = [
        _slice(instrument="Horn", technique_state_id="stopped", pitch=60.0),
        _slice(instrument="Horn", technique_state_id="stopped", pitch=64.0),
    ]
    reg = np.array([60.0, 64.0], dtype=float)
    dv = compute_fusion_acoustic_heuristic_window(v_slices, reg)["profile_explain"]["mean_pairwise_profile_distance"]
    dh = compute_fusion_acoustic_heuristic_window(h_slices, reg)["profile_explain"]["mean_pairwise_profile_distance"]
    assert dv == pytest.approx(0.0, abs=1e-9)
    assert dh == pytest.approx(0.0, abs=1e-9)
    cross = [
        _slice(instrument="Violin", technique_state_id="arco", pitch=60.0),
        _slice(instrument="Horn", technique_state_id="stopped", pitch=64.0),
    ]
    d_cross = compute_fusion_acoustic_heuristic_window(cross, reg)["profile_explain"]["mean_pairwise_profile_distance"]
    assert d_cross > max(dv, dh) + 1e-6


def test_partial_vector_lowers_confidence_vs_full_violin():
    base_slices = [
        _slice(instrument="Violin", technique_state_id="arco", pitch=60.0),
        _slice(instrument="Violin", technique_state_id="arco", pitch=62.0),
    ]
    partial_slices = [
        _slice(instrument="FusionTestPartial", technique_state_id="arco", pitch=60.0),
        _slice(instrument="FusionTestPartial", technique_state_id="arco", pitch=62.0),
    ]
    reg = np.array([60.0, 62.0], dtype=float)
    c_full = compute_fusion_acoustic_heuristic_window(base_slices, reg)["confidence_score"]
    c_part = compute_fusion_acoustic_heuristic_window(partial_slices, reg)["confidence_score"]
    assert c_full > c_part


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
def test_run_service_and_export_roundtrip():
    out = run_fusion_acoustic_heuristic_analysis(str(FIXTURE_XML), {"time_step": 0.5, "window_size": 4.0})
    assert not out.get("error"), out.get("error")
    doc = build_fusion_acoustic_heuristic_export(str(FIXTURE_XML), {"time_step": 0.5, "window_size": 4.0}, out)
    assert doc["kind"] == "fusion_acoustic_heuristic"
    assert doc["metric_kind"] == "fusion_acoustic_heuristic"
    assert doc["not_audio_analysis"] is True
    assert isinstance(doc.get("source_keys"), list) and doc["source_keys"]
    assert doc["results"]["fusion_model_header"]["not_audio_analysis"] is True
    raw = json.dumps(doc["results"], sort_keys=True)
    json.loads(raw)


def test_series_result_roundtrip():
    raw = {
        "t": [0.0, 1.0],
        "H_fusion_acoustic_heuristic": [0.55, 0.66],
        "fusion_model_header": {"model_version": "x", "not_audio_analysis": True},
        "H_fusion_acoustic_heuristic_diagnostics": [
            {"H_fusion_acoustic_heuristic": 0.55, "model_version": "x", "not_audio_analysis": True},
            {"H_fusion_acoustic_heuristic": 0.66, "model_version": "x", "not_audio_analysis": True},
        ],
    }
    s = FusionAcousticHeuristicSeriesResult.from_legacy(raw)
    back = s.as_legacy_dict()
    assert back["t"] == raw["t"]
    assert back["H_fusion_acoustic_heuristic"] == raw["H_fusion_acoustic_heuristic"]
