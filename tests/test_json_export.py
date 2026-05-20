"""Tests for structured JSON export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from homogeneity_analyser.analyzers.hti import HTI_EXPORT_TIME_SERIES_KEYS
from homogeneity_analyser.models.results import TimbralSeriesResult
from homogeneity_analyser.services.analysis_service import (
    run_homogeneity_analysis,
    run_register_uniformity_analysis,
    run_timbral_analysis,
)
from homogeneity_analyser.services.json_export import (
    HTI_EXPORT_SCHEMA_VERSION,
    JSON_EXPORT_MODEL_VERSION,
    JSON_EXPORT_SCHEMA_VERSION,
    build_combined_export,
    build_homogeneity_export,
    build_hti_export,
    build_timbral_export,
    enrich_timbral_diagnostics_list,
    to_json_serializable,
    write_json_export,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"


def test_to_json_serializable_numpy_and_nan():
    import numpy as np

    d = {"a": np.array([1.0, 2.0]), "b": np.float64(3.0), "c": float("nan")}
    out = to_json_serializable(d)
    assert out["a"] == [1.0, 2.0]
    assert out["b"] == 3.0
    assert out["c"] is None


def test_to_json_serializable_nested_nan_and_inf():
    d = {"outer": {"x": float("nan"), "y": float("inf")}, "z": [1.0, float("-inf")]}
    out = to_json_serializable(d)
    assert out["outer"]["x"] is None and out["outer"]["y"] is None
    assert out["z"][1] is None
    json.loads(json.dumps(out))


def test_write_json_export_roundtrip(tmp_path: Path):
    p = tmp_path / "out.json"
    write_json_export(p, {"schema_version": JSON_EXPORT_SCHEMA_VERSION, "x": [1, 2]})
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["x"] == [1, 2]


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
@pytest.mark.legacy
def test_homogeneity_export_contains_series_and_metadata():
    params = {"time_step": 0.5, "window_size": 4.0, "sigma": 12.0, "single_aggregate": True}
    out = run_homogeneity_analysis(str(FIXTURE_XML), params)
    assert not out.get("error"), out.get("error")
    doc = build_homogeneity_export(str(FIXTURE_XML), params, out)
    assert doc["schema_version"] == JSON_EXPORT_SCHEMA_VERSION
    assert doc["kind"] == "homogeneity"
    assert doc["metric_kind"] == "homogeneity"
    assert doc["model_version"] == JSON_EXPORT_MODEL_VERSION
    assert doc["not_audio_analysis"] is True
    assert doc["results"]["t"]
    assert doc["results"]["H"]
    assert "score_metadata" in doc
    assert doc["score_metadata"]["duration_quarterlength"] > 0


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
@pytest.mark.legacy
def test_combined_export_nested_keys():
    from homogeneity_analyser.services.analysis_service import run_both_and_combine

    out = run_both_and_combine(
        str(FIXTURE_XML),
        time_step=0.5,
        window_size=4.0,
        sigma=12.0,
        homogeneity_params={"single_aggregate": True},
    )
    if out.get("error"):
        pytest.skip(out["error"])
    doc = build_combined_export(
        str(FIXTURE_XML),
        {"time_step": 0.5, "window_size": 4.0, "sigma": 12.0, "single_aggregate": True},
        {"time_step": 0.5, "window_size": 4.0, "timbral_config": None},
        out,
    )
    assert doc["kind"] == "combined_homogeneity_timbral"
    assert doc["schema_version"] == JSON_EXPORT_SCHEMA_VERSION
    assert doc["metric_kind"] == "combined_homogeneity_timbral"
    assert doc["model_version"] == JSON_EXPORT_MODEL_VERSION
    assert doc["not_audio_analysis"] is True
    assert isinstance(doc.get("source_keys"), list)
    assert doc["source_keys"], "fusion export should list at least one source key"
    assert "combined_series" in doc
    assert "homogeneity" in doc and doc["homogeneity"]["kind"] == "homogeneity"
    assert "timbral" in doc and doc["timbral"]["kind"] == "timbral"
    assert "combined_csv" in doc and len(doc["combined_csv"]) > 0
    assert "summaries" in doc and "homogeneity" in doc["summaries"]
    assert "timbral_homogeneity_note" in doc
    assert "H_cluster" in doc["combined_series"]
    assert "H_orchestration_symbolic" in doc["combined_series"]
    assert len(doc["combined_series"]["H_orchestration_symbolic"]) == len(doc["combined_series"]["t"])
    assert "H_fusion_acoustic_heuristic" in doc["combined_series"]
    assert "H_notated_fusion_potential" in doc["combined_series"]
    assert "H_notated_fusion_potential_dynamic" in doc["combined_series"]
    assert len(doc["combined_series"]["H_notated_fusion_potential"]) == len(doc["combined_series"]["t"])
    assert len(doc["combined_series"]["H_notated_fusion_potential_dynamic"]) == len(doc["combined_series"]["t"])
    assert "legacy_H_timbral" in doc["combined_series"]
    assert len(doc["combined_series"]["H_fusion_acoustic_heuristic"]) == len(doc["combined_series"]["t"])
    assert doc["combined_series"]["legacy_H_timbral"] == doc["combined_series"]["H_timbral"]
    assert "cluster" in doc and doc["cluster"]["kind"] == "cluster"
    assert doc.get("orchestration_symbolic", {}).get("kind") == "orchestration_symbolic"
    assert "orchestration_parameters" in doc
    assert doc.get("fusion_acoustic_heuristic", {}).get("kind") == "fusion_acoustic_heuristic"
    assert "fusion_parameters" in doc
    assert doc.get("notated_fusion_potential", {}).get("kind") == "notated_fusion_potential"
    assert "notated_fusion_parameters" in doc
    assert "notated_fusion_potential_note" in doc
    assert "cluster_orch_fusion_diagnostics_csv" in doc and len(doc["cluster_orch_fusion_diagnostics_csv"]) > 0
    assert "confidence_score" in doc["combined_series"]
    assert doc.get("interpretation_guidance")
    assert "H_cluster" in doc["interpretation_guidance"] and "legacy" in doc["interpretation_guidance"].lower()


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
@pytest.mark.legacy
def test_timbral_export_contains_state_distribution_and_effective_params():
    params = {"time_step": 0.5, "window_size": 4.0, "timbral_config": None}
    out = run_timbral_analysis(str(FIXTURE_XML), params)
    assert not out.get("error"), out.get("error")
    doc = build_timbral_export(str(FIXTURE_XML), params, out)
    assert doc["schema_version"] == JSON_EXPORT_SCHEMA_VERSION
    assert doc["metric_kind"] == "timbral"
    assert doc["model_version"] == JSON_EXPORT_MODEL_VERSION
    assert doc["not_audio_analysis"] is True
    assert "timbral_homogeneity_note" in doc
    assert "h_timbral_effective_parameters" in doc
    ep = doc["h_timbral_effective_parameters"]
    assert "weight_instrument" in ep and "register_ref_semitones" in ep
    assert "timbral_state_series" in doc
    assert doc["timbral_state_series"]["timbral_state_distribution"] is not None
    assert len(doc["results"]["timbral_state_distribution"]) == len(doc["results"]["t"])
    tsm = doc["timbral_semantic_model"]
    assert tsm["timbral_model_mode"] == "legacy"
    assert tsm["not_audio_analysis"] is True
    assert "model_description" in tsm and "model_version" in tsm
    assert doc.get("legacy_warning")
    assert "backward compatibility" in doc["legacy_warning"].lower()
    assert doc.get("interpretation_status") == "legacy_diagnostic"
    assert doc.get("timbral_model_mode") == "legacy"
    raw = json.dumps(to_json_serializable(doc), ensure_ascii=False)
    json.loads(raw)


@pytest.mark.legacy
def test_enrich_timbral_diagnostics_sets_evidence_status_when_provisional_without_sources():
    diags = enrich_timbral_diagnostics_list(
        [{"source_keys_used": [], "provisional_constants_used": ["x"], "H_timbral": 0.5}]
    )
    assert diags is not None
    assert diags[0].get("evidence_status") == "unsupported_or_provisional"
    diags2 = enrich_timbral_diagnostics_list([{"source_keys_used": ["lit:key"], "provisional_constants_used": []}])
    assert "evidence_status" not in diags2[0]


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
@pytest.mark.legacy
def test_write_json_export_timbral_is_valid_json(tmp_path: Path):
    params = {"time_step": 0.5, "window_size": 4.0, "timbral_config": None}
    out = run_timbral_analysis(str(FIXTURE_XML), params)
    assert not out.get("error"), out.get("error")
    doc = build_timbral_export(str(FIXTURE_XML), params, out)
    p = tmp_path / "timbral.json"
    write_json_export(p, doc)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["schema_version"] == JSON_EXPORT_SCHEMA_VERSION
    assert "timbral_state_distribution" in data["results"]


@pytest.mark.legacy
def test_to_json_serializable_dataclass_timbral_series():
    ts = TimbralSeriesResult(
        t=[0.0, 1.0],
        H_timbral=[0.5, float("nan")],
        timbral_state_distribution=[{"a": 1.0}, {"b": 1.0}],
        dominant_timbral_state=["x", None],
        timbral_state_concentration=[1.0, 0.9],
    )
    out = to_json_serializable(ts)
    assert isinstance(out, dict)
    assert out["H_timbral"][1] is None
    raw = json.dumps(out, ensure_ascii=False)
    json.loads(raw)


def _walk_no_dataclass(obj: object, seen: set[int]) -> None:
    if isinstance(obj, dict | list):
        i = id(obj)
        if i in seen:
            return
        seen.add(i)
    if hasattr(obj, "__dataclass_fields__") and not isinstance(obj, type):
        raise AssertionError(f"dataclass instance leaked into JSON tree: {type(obj)}")
    if isinstance(obj, dict):
        for v in obj.values():
            _walk_no_dataclass(v, seen)
    elif isinstance(obj, list):
        for v in obj:
            _walk_no_dataclass(v, seen)


@pytest.mark.skipif(not FIXTURE_XML.is_file(), reason="Fixture not found")
@pytest.mark.legacy
def test_combined_export_with_register_includes_u_and_summaries():
    from homogeneity_analyser.services.analysis_service import run_both_and_combine

    h_params = {"time_step": 0.5, "window_size": 4.0, "sigma": 12.0, "single_aggregate": True}
    t_params = {"time_step": 0.5, "window_size": 4.0, "timbral_config": None}
    r_params = {"time_step": 0.5, "window_size": 4.0, "register_low": "A1", "register_high": "E7"}
    out = run_both_and_combine(
        str(FIXTURE_XML),
        time_step=0.5,
        window_size=4.0,
        sigma=12.0,
        homogeneity_params=h_params,
    )
    if out.get("error"):
        pytest.skip(out["error"])
    reg = run_register_uniformity_analysis(str(FIXTURE_XML), r_params)
    assert not reg.get("error"), reg.get("error")
    doc = build_combined_export(
        str(FIXTURE_XML),
        h_params,
        t_params,
        out,
        register_params=r_params,
        register_out=reg,
    )
    assert "register_uniformity" in doc
    assert "U" in doc["combined_series"]
    assert len(doc["combined_series"]["U"]) == len(doc["combined_series"]["t"])
    assert doc["summaries"].get("register_uniformity") is not None
    payload = to_json_serializable(doc)
    raw = json.dumps(payload, ensure_ascii=False)
    data = json.loads(raw)
    _walk_no_dataclass(data, set())


def _minimal_hti_results_one_window() -> dict:
    res: dict = {"t": [0.0]}
    for k in HTI_EXPORT_TIME_SERIES_KEYS:
        if k == "t":
            continue
        if k in ("crescendo_active", "diminuendo_active", "dynamic_divergence_detected"):
            res[k] = [False]
        elif k.endswith("_distribution") or k == "notated_dynamic_level_distribution":
            res[k] = [{}]
        elif k == "active_weights":
            res[k] = [
                {
                    "instrument_uniformity": 0.25,
                    "family_uniformity": 0.25,
                    "technique_uniformity": 0.25,
                    "register_proximity": 0.25,
                }
            ]
        elif k == "edge_window":
            res[k] = [False]
        elif k in ("window_start",):
            res[k] = [0.0]
        elif k in ("window_end",):
            res[k] = [4.0]
        elif k == "window_coverage_ratio":
            res[k] = [1.0]
        elif k == "effective_window_overlap_duration":
            res[k] = [4.0]
        elif k in ("measure",):
            res[k] = [""]
        elif k in ("dominant_timbral_state", "dominant_dynamic"):
            res[k] = [None]
        elif k in (
            "dominant_instruments",
            "dominant_macrofamilies",
            "dominant_families",
            "dominant_timbral_states",
            "dominant_dynamics",
        ):
            res[k] = [[]]
        elif k in (
            "dominant_instrument_tie",
            "dominant_macrofamily_tie",
            "dominant_family_tie",
            "dominant_timbral_state_tie",
            "dominant_dynamic_tie",
        ):
            res[k] = [False]
        elif k in (
            "dominant_instrument_share",
            "dominant_instrument_margin",
            "dominant_macrofamily_share",
            "dominant_macrofamily_margin",
            "dominant_family_share",
            "dominant_family_margin",
            "dominant_timbral_state_share",
            "dominant_timbral_state_margin",
            "dominant_dynamic_share",
            "dominant_dynamic_margin",
        ):
            res[k] = [float("nan")]
        elif k in ("dominant_instrument", "dominant_family", "dominant_instrumental_subfamily", "dominant_macrofamily"):
            res[k] = [""]
        elif k in ("dynamic_interpretation_label", "dynamic_interpretation_label_subfamily_relieved"):
            res[k] = ["structural_homogeneity_dynamic_neutral"]
        elif k in ("timbral_affinity_rule_summary", "timbral_affinity_literature_sources"):
            res[k] = [""]
        elif k == "timbral_affinity_profile":
            res[k] = ["conservative"]
        elif k in ("timbral_affinity_dynamic_status", "timbral_affinity_evidence_status"):
            res[k] = ["insufficient"]
        elif k == "affinity_dynamic_interpretation_label":
            res[k] = ["affinity_dynamic_layer_disabled"]
        elif k == "dynamic_evidence_status":
            res[k] = ["moderate"]
        elif k in ("technique_coverage_status", "register_coverage_status", "dynamic_coverage_status"):
            res[k] = ["unavailable" if k == "dynamic_coverage_status" else "none"]
        elif k == "pairwise_interval_coverage_status":
            res[k] = ["insufficient_pairs"]
        else:
            res[k] = [float("nan")]
    return res


def test_build_hti_export_includes_dynamic_conditioning():
    doc = build_hti_export(
        str(FIXTURE_XML),
        {"results": _minimal_hti_results_one_window(), "parameters": {}, "summary": ""},
    )
    assert doc["schema_version"] == HTI_EXPORT_SCHEMA_VERSION
    dc = doc.get("dynamic_conditioning")
    assert isinstance(dc, dict)
    assert dc.get("model_scope") == "symbolic_notated_dynamic_conditioning"
    assert dc.get("not_audio_analysis") is True
    assert "dynamic_scale" in dc
    assert dc.get("family_rules_version") == "hti_dynamic_conditioning_v1"
    assert isinstance(dc.get("time_series"), list) and len(dc["time_series"]) == 1
    row0 = doc["time_series"][0]
    assert "H_TI_affinity_literature_relieved" in row0
    assert "timbral_affinity_uniformity" in row0
