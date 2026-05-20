"""
Structured JSON export for analysis results (machine-readable, no live analyzer objects).

Documents use ``schema_version`` and a ``kind`` field so consumers can evolve safely.

**Schema 1.3** (additive): combined exports may include **H_orchestration_symbolic** (Herfindahl-only
symbolic orchestration uniformity) plus a nested ``orchestration_symbolic`` document, alongside
**H_cluster** and prior timbral/register fields.

**Schema 1.4** (additive): combined ``combined_series`` adds **H_fusion_acoustic_heuristic**,
``legacy_H_timbral`` (alias of ``H_timbral``), fusion confidence fields, and a nested
``fusion_acoustic_heuristic`` document; ``cluster_orch_fusion_diagnostics_csv`` holds the
per-window comparison table text.

**Schema 1.5** (additive): every export carries ``model_version``, ``metric_kind`` (same string as
``kind``), and ``not_audio_analysis: true``. Fusion exports include top-level ``source_keys`` (sorted
union of per-window ``sources_used``). Combined bundles copy that list to the root as ``source_keys``
when the nested fusion export is present.

**Schema 1.7** (additive): extends **1.6** with **same_family_relief** calibration profiles and enriched
``notated_fusion_potential`` / per-window diagnostics (``same_family_relief_profile``,
``literature_motivated_calibrated_proxy`` evidence where applicable).

**Schema 1.8** (additive): adds ``H_notated_fusion_potential_dynamic`` and per-window dynamic-coherence
diagnostics (``dynamic_coherence``, ``dynamic_coverage_status``, …) without changing the base
``H_notated_fusion_potential`` series.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.hti import HTI_EXPORT_TIME_SERIES_KEYS, TECHNIQUE_MODEL_VERSION
from homogeneity_analyser.analyzers.hti_dynamic_conditioning import FAMILY_RULES_VERSION
from homogeneity_analyser.analyzers.hti_dynamics import notated_dynamic_scale_export
from homogeneity_analyser.models.timbral_semantics import timbral_model_metadata_for_diagnostics
from homogeneity_analyser.services.constants import SYMBOLIC_HOMOGENEITY_SCOPE_DISCLAIMER
from homogeneity_analyser.services.window_pipeline import interpolate_onto_times

JSON_EXPORT_SCHEMA_VERSION = "1.8"

# Bundle identifier for all score-derived exports (bump when export semantics change materially).
JSON_EXPORT_MODEL_VERSION = "1.0"


def _standard_document_fields(metric_kind: str) -> dict[str, Any]:
    """Shared metadata: symbolic / heuristic score analysis only (no user audio waveforms)."""
    return {
        "model_version": JSON_EXPORT_MODEL_VERSION,
        "metric_kind": metric_kind,
        "not_audio_analysis": True,
    }


def _fusion_source_keys_union(results: dict[str, Any]) -> list[str]:
    """Sorted union of ``sources_used`` across ``H_fusion_acoustic_heuristic_diagnostics`` rows."""
    keys: set[str] = set()
    diags = results.get("H_fusion_acoustic_heuristic_diagnostics") or []
    if not isinstance(diags, list):
        return []
    for row in diags:
        if not isinstance(row, dict):
            continue
        su = row.get("sources_used")
        if isinstance(su, list):
            for x in su:
                if isinstance(x, str) and x.strip():
                    keys.add(x.strip())
    return sorted(keys)


TIMBRAL_HOMOGENEITY_NOTE = (
    "H_timbral is the backward-compatible legacy scalar: symbolic timbral-instrumental / "
    "orchestration-register homogeneity (instrument names, taxonomy family, register span, "
    "technique-state concentration), not acoustic timbre or measured audio."
)

CLUSTER_METRIC_NOTE = (
    "H_cluster measures vertical pitch-cluster compactness from sounding MIDI only "
    "(instrumentation-independent). It is not H_timbral and does not use instrument names or technique."
)

ORCHESTRATION_SYMBOLIC_NOTE = (
    "H_orchestration_symbolic is overlap-weighted Herfindahl concentration over canonical instruments, "
    "families, and technique_state_id. It does not use family-specific pairwise fusion kernels from H_timbral."
)

FUSION_ACOUSTIC_HEURISTIC_NOTE = (
    "H_fusion_acoustic_heuristic is a literature-tagged feature-vector distance blend plus an explicit "
    "harmonic roughness proxy. It is not measured audio analysis and is not legacy H_timbral. "
    "Per-window confidence_score / confidence_label in results diagnostics qualify how strongly "
    "to treat the scalar as an acoustic proxy (never substitute for waveform measurement)."
)

LEGACY_TIMBRAL_JSON_WARNING = (
    "Legacy H_timbral is retained for backward compatibility. It is not measured acoustic timbre and must "
    "not be interpreted as acoustically validated fusion."
)

COMBINED_INTERPRETATION_GUIDANCE = (
    "For timbral/orchestration-style interpretation, prefer **H_cluster** (pitch-object identity from sounding MIDI), "
    "**H_orchestration_symbolic** (symbolic scoring uniformity), **H_notated_fusion_potential** (single score-derived "
    "scalar blending orchestration uniformity and sounding register proximity; not measured audio; no legacy timbral "
    "pairwise kernels), then **H_fusion_acoustic_heuristic** (only with confidence / source diagnostics in JSON). "
    "**legacy_H_timbral** / **H_timbral** are backward-compatible diagnostics, not acoustically validated fusion."
)

NOTATED_FUSION_POTENTIAL_NOTE = (
    "H_notated_fusion_potential is a general notation-derived fusion-potential proxy across all taxonomy instruments: "
    "overlap-weighted Herfindahl uniformity over canonical instruments, families, and technique-only buckets, combined "
    "with sounding MIDI register proximity. Instrument concentration uses distribution-only same_family_relief on "
    "(family_uniformity - instrument_uniformity), with named calibration profiles (strict / conservative / balanced / "
    "permissive) and optional numeric override; default balanced relief is literature-motivated but project-calibrated "
    "(not a measured acoustic constant). No pairwise instrument tables or family-specific affinity rules. It is not "
    "measured audio, not FFT/spectral analysis, and does not use legacy H_timbral pairwise kernels. Unpitched material "
    "contributes to orchestration-style axes; register proximity uses pitched pairs only; diagnostics report register "
    "coverage and per-window evidence_status (including literature_motivated_calibrated_proxy when register coverage "
    "is ok and the profile is not strict). "
    "``H_notated_fusion_potential_dynamic`` multiplies the **unchanged** base scalar by "
    "``dynamic_coherence ** weight_dynamic`` (default weight 0.10): coherence rewards **shared** notated dynamic level "
    "or **shared** hairpin process and penalises only **cross-part divergence** (not absolute ``mf`` vs ``pp`` when "
    "uniform); not SPL."
)


def enrich_timbral_diagnostics_list(diags: list[Any] | None) -> list[Any] | None:
    """
    Return a shallow-copied list of diagnostic dicts with optional ``evidence_status`` per row.

    When ``source_keys_used`` is empty and ``provisional_constants_used`` is non-empty, sets
    ``evidence_status`` to ``\"unsupported_or_provisional\"`` (export / UI safety; does not change H_timbral).
    """
    if not diags:
        return diags
    out: list[Any] = []
    for d in diags:
        if not isinstance(d, dict):
            out.append(d)
            continue
        row = dict(d)
        sk = row.get("source_keys_used")
        pc = row.get("provisional_constants_used")
        sk_l = sk if isinstance(sk, list) else []
        pc_l = pc if isinstance(pc, list) else []
        if len(sk_l) == 0 and len(pc_l) > 0:
            row["evidence_status"] = "unsupported_or_provisional"
        out.append(row)
    return out


def to_json_serializable(obj: Any) -> Any:
    """
    Recursively convert numpy scalars/arrays, dataclasses, NaN/inf floats, and nested
    structures to JSON-safe values.
    """
    if obj is None:
        return None
    if isinstance(obj, str | bool | int):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if is_dataclass(obj) and not isinstance(obj, type):
        return to_json_serializable(asdict(obj))
    if isinstance(obj, np.ndarray):
        return to_json_serializable(obj.tolist())
    if isinstance(obj, np.generic):
        return to_json_serializable(obj.item())
    if isinstance(obj, dict):
        return {str(k): to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [to_json_serializable(v) for v in obj]
    return str(obj)


def _h_timbral_effective_parameters(analyzer: Any) -> dict[str, Any] | None:
    if analyzer is None:
        return None
    cfg = getattr(analyzer, "_timbral_config", None)
    if not isinstance(cfg, dict):
        return None
    return {
        "weight_instrument": cfg.get("weight_instrument"),
        "weight_register": cfg.get("weight_register"),
        "family_bonus": cfg.get("family_bonus"),
        "register_ref_semitones": cfg.get("register_ref_semitones"),
    }


def _align_u_onto_t_grid(
    t_target: list[float],
    t_u: list[float] | None,
    u_vals: list[float] | None,
) -> list[float | None] | None:
    """Map register ``U`` onto ``t_target`` (homogeneity combined grid); NaN/inf → ``None`` for JSON."""
    if not t_target or t_u is None or u_vals is None:
        return None
    tt = np.asarray(t_target, dtype=float)
    ts = np.asarray(t_u, dtype=float)
    uv = np.asarray(u_vals, dtype=float)
    if ts.size != uv.size or ts.size == 0:
        return None
    if tt.size == ts.size and np.allclose(tt, ts, rtol=0.0, atol=1e-9):
        y = uv.astype(float)
    else:
        u_clean = np.where(np.isfinite(uv), uv, np.nanmedian(uv) if np.any(np.isfinite(uv)) else 0.0)
        y = interpolate_onto_times(ts, u_clean, tt)
    out: list[float | None] = []
    for v in y:
        fv = float(v)
        out.append(None if (math.isnan(fv) or math.isinf(fv)) else fv)
    return out


def write_json_export(path: str | Path, document: dict[str, Any]) -> str:
    """Write ``document`` as UTF-8 JSON with indentation; return path as str."""
    p = Path(path)
    payload = to_json_serializable(document)
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_homogeneity_export(
    score_path: str | None,
    params: dict[str, Any],
    out: dict[str, Any],
) -> dict[str, Any]:
    """Full export document for ``run_homogeneity_analysis`` output."""
    base: dict[str, Any] = {
        "schema_version": JSON_EXPORT_SCHEMA_VERSION,
        "kind": "homogeneity",
        **_standard_document_fields("homogeneity"),
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "parameters": to_json_serializable(params),
        "error": out.get("error"),
    }
    if out.get("error"):
        return base
    an = out.get("analyzer")
    base["summary"] = out.get("summary")
    base["results"] = to_json_serializable(out.get("results", {}))
    base["plot_series"] = to_json_serializable(out.get("plot_results", out.get("results", {})))
    base["change_point_indices"] = list(out.get("change_points") or [])
    base["change_times"] = to_json_serializable(list(out.get("change_times") or []))
    sens = out.get("sensitivity") or []
    base["sensitivity"] = [
        {
            "window_size_quarterlength": float(ws),
            "correlation_with_baseline_H": to_json_serializable(corr),
            "mean_H": to_json_serializable(m),
            "std_H": to_json_serializable(s),
        }
        for ws, corr, m, s in sens
    ]
    if an is not None:
        base["score_metadata"] = {
            "duration_quarterlength": float(getattr(an, "end_time", 0.0) or 0.0),
            "n_notes_flat": len(getattr(an, "events", []) or []),
            "pitch_space": getattr(an, "pitch_space", None),
        }
    return base


def build_timbral_export(
    score_path: str | None,
    params: dict[str, Any],
    out: dict[str, Any],
) -> dict[str, Any]:
    """Full export document for ``run_timbral_analysis`` output."""
    base: dict[str, Any] = {
        "schema_version": JSON_EXPORT_SCHEMA_VERSION,
        "kind": "timbral",
        **_standard_document_fields("timbral"),
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "parameters": to_json_serializable(params),
        "error": out.get("error"),
        "timbral_homogeneity_note": TIMBRAL_HOMOGENEITY_NOTE,
    }
    if out.get("error"):
        return base
    an = out.get("analyzer")
    base["summary"] = out.get("summary")
    res: dict[str, Any] = {**(out.get("results") or {})}
    if res.get("H_timbral_diagnostics"):
        res["H_timbral_diagnostics"] = enrich_timbral_diagnostics_list(list(res["H_timbral_diagnostics"]))
    base["results"] = to_json_serializable(res)
    eff = _h_timbral_effective_parameters(an)
    if eff is not None:
        base["h_timbral_effective_parameters"] = to_json_serializable(eff)
    base["timbral_state_series"] = to_json_serializable(
        {
            "timbral_state_distribution": res.get("timbral_state_distribution"),
            "dominant_timbral_state": res.get("dominant_timbral_state"),
            "timbral_state_concentration": res.get("timbral_state_concentration"),
            "H_timbral_diagnostics": res.get("H_timbral_diagnostics"),
        }
    )
    base["primary_series"] = to_json_serializable({"t_quarterlength": res.get("t"), "H_timbral": res.get("H_timbral")})
    if an is not None:
        mode = getattr(an, "_timbral_model_mode", "legacy")
        mode_s = str(mode)
        base["timbral_model_mode"] = mode_s
        base["timbral_semantic_model"] = to_json_serializable(timbral_model_metadata_for_diagnostics(mode))
        if mode_s == "legacy":
            base["legacy_warning"] = LEGACY_TIMBRAL_JSON_WARNING
            base["interpretation_status"] = "legacy_diagnostic"
        base["score_metadata"] = {
            "duration_quarterlength": float(getattr(an, "end_time", 0.0) or 0.0),
            "n_timbral_events": len(getattr(an, "_events", []) or []),
        }
    return base


def build_register_export(
    score_path: str | None,
    params: dict[str, Any],
    out: dict[str, Any],
) -> dict[str, Any]:
    """Full export document for ``run_register_uniformity_analysis`` output."""
    base: dict[str, Any] = {
        "schema_version": JSON_EXPORT_SCHEMA_VERSION,
        "kind": "register_uniformity",
        **_standard_document_fields("register_uniformity"),
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "parameters": to_json_serializable(params),
        "error": out.get("error"),
    }
    if out.get("error"):
        return base
    an = out.get("analyzer")
    base["summary"] = out.get("summary")
    base["results"] = to_json_serializable(out.get("results", {}))
    params_out = dict(params)
    if an is not None:
        params_out["register_low_midi_ps"] = float(getattr(an, "register_low", 0.0))
        params_out["register_high_midi_ps"] = float(getattr(an, "register_high", 0.0))
    base["parameters"] = to_json_serializable(params_out)
    if an is not None:
        base["score_metadata"] = {
            "duration_quarterlength": float(getattr(an, "end_time", 0.0) or 0.0),
            "register_low_midi_ps": float(getattr(an, "register_low", 0.0)),
            "register_high_midi_ps": float(getattr(an, "register_high", 0.0)),
            "n_notes_flat": len(getattr(an, "events", []) or []),
        }
    return base


def build_cluster_export(score_path: str | None, params: dict[str, Any], out: dict[str, Any]) -> dict[str, Any]:
    """Full export document for ``run_cluster_analysis`` output."""
    base: dict[str, Any] = {
        "schema_version": JSON_EXPORT_SCHEMA_VERSION,
        "kind": "cluster",
        **_standard_document_fields("cluster"),
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "parameters": to_json_serializable(params),
        "error": out.get("error"),
        "cluster_metric_note": CLUSTER_METRIC_NOTE,
    }
    if out.get("error"):
        return base
    an = out.get("analyzer")
    base["summary"] = out.get("summary")
    base["results"] = to_json_serializable(out.get("results", {}))
    base["primary_series"] = to_json_serializable(
        {
            "t_quarterlength": (out.get("results") or {}).get("t"),
            "H_cluster": (out.get("results") or {}).get("H_cluster"),
        }
    )
    if an is not None:
        base["score_metadata"] = {
            "duration_quarterlength": float(getattr(an, "end_time", 0.0) or 0.0),
            "n_cluster_events": len(getattr(an, "_events", []) or []),
            "cluster_ref_span": float(getattr(an, "cluster_ref_span", 12.0) or 12.0),
        }
    return base


def build_orchestration_symbolic_export(
    score_path: str | None, params: dict[str, Any], out: dict[str, Any]
) -> dict[str, Any]:
    """Full export document for ``run_orchestration_symbolic_analysis`` output."""
    base: dict[str, Any] = {
        "schema_version": JSON_EXPORT_SCHEMA_VERSION,
        "kind": "orchestration_symbolic",
        **_standard_document_fields("orchestration_symbolic"),
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "parameters": to_json_serializable(params),
        "error": out.get("error"),
        "orchestration_symbolic_note": ORCHESTRATION_SYMBOLIC_NOTE,
    }
    if out.get("error"):
        return base
    an = out.get("analyzer")
    base["summary"] = out.get("summary")
    base["results"] = to_json_serializable(out.get("results", {}))
    base["primary_series"] = to_json_serializable(
        {
            "t_quarterlength": (out.get("results") or {}).get("t"),
            "H_orchestration_symbolic": (out.get("results") or {}).get("H_orchestration_symbolic"),
        }
    )
    if an is not None:
        base["score_metadata"] = {
            "duration_quarterlength": float(getattr(an, "end_time", 0.0) or 0.0),
            "n_timbral_source_events": len(getattr(getattr(an, "_timbral", None), "_events", []) or []),
            "weight_instrument": float(getattr(an, "w_i", 0.45)),
            "weight_family": float(getattr(an, "w_f", 0.25)),
            "weight_technique": float(getattr(an, "w_t", 0.30)),
        }
    return base


def build_notated_fusion_potential_export(
    score_path: str | None, params: dict[str, Any], out: dict[str, Any]
) -> dict[str, Any]:
    """Full export document for ``run_notated_fusion_potential_analysis`` output."""
    base: dict[str, Any] = {
        "schema_version": JSON_EXPORT_SCHEMA_VERSION,
        "kind": "notated_fusion_potential",
        **_standard_document_fields("notated_fusion_potential"),
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "parameters": to_json_serializable(params),
        "error": out.get("error"),
        "notated_fusion_potential_note": NOTATED_FUSION_POTENTIAL_NOTE,
    }
    if out.get("error"):
        return base
    an = out.get("analyzer")
    base["summary"] = out.get("summary")
    base["results"] = to_json_serializable(out.get("results", {}))
    base["primary_series"] = to_json_serializable(
        {
            "t_quarterlength": (out.get("results") or {}).get("t"),
            "H_notated_fusion_potential": (out.get("results") or {}).get("H_notated_fusion_potential"),
            "H_notated_fusion_potential_dynamic": (out.get("results") or {}).get("H_notated_fusion_potential_dynamic"),
        }
    )
    if an is not None:
        base["score_metadata"] = {
            "duration_quarterlength": float(getattr(an, "end_time", 0.0) or 0.0),
            "n_timbral_source_events": len(getattr(getattr(an, "_timbral", None), "_events", []) or []),
            "register_ref_semitones": float(getattr(an, "register_ref_semitones", 12.0)),
            "weight_instrument": float(getattr(an, "w_i", 0.30)),
            "weight_family": float(getattr(an, "w_f", 0.15)),
            "weight_technique": float(getattr(an, "w_t", 0.25)),
            "weight_register": float(getattr(an, "w_r", 0.30)),
            "weight_notated_fusion_dynamic": float(getattr(an, "w_dyn", 0.10)),
            "same_family_relief": float(getattr(an, "same_family_relief", 0.55)),
            "same_family_relief_profile": str(getattr(an, "same_family_relief_profile", "balanced")),
            "same_family_relief_from_override": bool(getattr(an, "same_family_relief_from_override", False)),
            "notated_fusion_evidence_status_note": (
                "Per-window ``evidence_status`` in ``H_notated_fusion_potential_diagnostics``: "
                "``literature_motivated_calibrated_proxy`` when register coverage is ``ok`` and the relief profile is "
                "not ``strict``; ``symbolic_no_register_evidence`` when no pitched pairs; otherwise "
                "``symbolic_register_proxy`` (strict profile with register coverage)."
            ),
        }
    return base


def build_fusion_acoustic_heuristic_export(
    score_path: str | None, params: dict[str, Any], out: dict[str, Any]
) -> dict[str, Any]:
    """Full export document for ``run_fusion_acoustic_heuristic_analysis`` output."""
    base: dict[str, Any] = {
        "schema_version": JSON_EXPORT_SCHEMA_VERSION,
        "kind": "fusion_acoustic_heuristic",
        **_standard_document_fields("fusion_acoustic_heuristic"),
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "parameters": to_json_serializable(params),
        "error": out.get("error"),
        "fusion_acoustic_heuristic_note": FUSION_ACOUSTIC_HEURISTIC_NOTE,
    }
    if out.get("error"):
        return base
    an = out.get("analyzer")
    base["summary"] = out.get("summary")
    res_raw = out.get("results") or {}
    base["results"] = to_json_serializable(res_raw)
    base["source_keys"] = to_json_serializable(_fusion_source_keys_union(res_raw if isinstance(res_raw, dict) else {}))
    base["primary_series"] = to_json_serializable(
        {
            "t_quarterlength": (out.get("results") or {}).get("t"),
            "H_fusion_acoustic_heuristic": (out.get("results") or {}).get("H_fusion_acoustic_heuristic"),
        }
    )
    if an is not None:
        base["score_metadata"] = {
            "duration_quarterlength": float(getattr(an, "end_time", 0.0) or 0.0),
            "n_timbral_source_events": len(getattr(getattr(an, "_timbral", None), "_events", []) or []),
            "fusion_weights": {
                "profile": float(getattr(an, "wp", 0.35)),
                "spectral": float(getattr(an, "ws", 0.35)),
                "technique": float(getattr(an, "wt", 0.15)),
                "register": float(getattr(an, "wr", 0.15)),
            },
        }
    return base


def build_combined_export(
    score_path: str | None,
    homogeneity_params: dict[str, Any],
    timbral_params: dict[str, Any],
    out: dict[str, Any],
    *,
    register_params: dict[str, Any] | None = None,
    register_out: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Export bundle for ``run_both_and_combine`` (homogeneity, timbral, cluster, orchestration,
    fusion, CSV, nested analyses).

    When ``register_out`` and ``register_params`` are provided, embeds register uniformity
    and adds ``U`` to ``combined_series`` aligned to the combined time grid.
    """
    base: dict[str, Any] = {
        "schema_version": JSON_EXPORT_SCHEMA_VERSION,
        "kind": "combined_homogeneity_timbral",
        **_standard_document_fields("combined_homogeneity_timbral"),
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "error": out.get("error"),
        "homogeneity_parameters": to_json_serializable(homogeneity_params),
        "timbral_parameters": to_json_serializable(timbral_params),
        "timbral_homogeneity_note": TIMBRAL_HOMOGENEITY_NOTE,
        "cluster_metric_note": CLUSTER_METRIC_NOTE,
        "orchestration_symbolic_note": ORCHESTRATION_SYMBOLIC_NOTE,
        "notated_fusion_potential_note": NOTATED_FUSION_POTENTIAL_NOTE,
        "fusion_acoustic_heuristic_note": FUSION_ACOUSTIC_HEURISTIC_NOTE,
        "interpretation_guidance": COMBINED_INTERPRETATION_GUIDANCE,
    }
    if register_params is not None and register_out is not None:
        base["register_parameters"] = to_json_serializable(register_params)
    if out.get("error"):
        oh_e = out.get("out_homogeneity") or {}
        ot_e = out.get("out_timbral") or {}
        oc_e = out.get("out_cluster") or {}
        oo_e = out.get("out_orchestration_symbolic") or {}
        base["out_homogeneity_error"] = oh_e.get("error")
        base["out_timbral_error"] = ot_e.get("error")
        base["out_cluster_error"] = oc_e.get("error")
        base["out_orchestration_symbolic_error"] = oo_e.get("error")
        base["out_fusion_acoustic_heuristic_error"] = (out.get("out_fusion_acoustic_heuristic") or {}).get("error")
        return base
    oh = out.get("out_homogeneity") or {}
    ot = out.get("out_timbral") or {}
    oc_ok = out.get("out_cluster") or {}
    cluster_summary = None if oc_ok.get("error") else oc_ok.get("summary")
    oo_ok = out.get("out_orchestration_symbolic") or {}
    orch_summary = None if oo_ok.get("error") else oo_ok.get("summary")
    of_ok = out.get("out_fusion_acoustic_heuristic") or {}
    fusion_summary = None if of_ok.get("error") else of_ok.get("summary")
    base["summaries"] = to_json_serializable(
        {
            "homogeneity": oh.get("summary"),
            "timbral": ot.get("summary"),
            **({"cluster": cluster_summary} if cluster_summary else {}),
            **({"orchestration_symbolic": orch_summary} if orch_summary else {}),
            **({"fusion_acoustic_heuristic": fusion_summary} if fusion_summary else {}),
            **(
                {"notated_fusion_potential": (out.get("out_notated_fusion_potential") or {}).get("summary")}
                if isinstance(out.get("out_notated_fusion_potential"), dict)
                and not (out.get("out_notated_fusion_potential") or {}).get("error")
                else {}
            ),
            **(
                {"register_uniformity": (register_out or {}).get("summary")}
                if register_out is not None and not register_out.get("error")
                else {}
            ),
        }
    )
    combined = dict(out.get("combined") or {})
    t_c = combined.get("t")
    if (
        register_out is not None
        and register_params is not None
        and not register_out.get("error")
        and isinstance(t_c, list)
    ):
        rr = register_out.get("results") or {}
        u_al = _align_u_onto_t_grid([float(x) for x in t_c], rr.get("t"), rr.get("U"))
        if u_al is not None:
            combined["U"] = u_al
    base["combined_series"] = to_json_serializable(combined)
    base["combined_csv"] = out.get("combined_csv_content") or ""
    base["cluster_orch_fusion_diagnostics_csv"] = out.get("cluster_orch_fusion_diagnostics_csv_content") or ""
    base["homogeneity"] = build_homogeneity_export(score_path, homogeneity_params, oh)
    base["timbral"] = build_timbral_export(score_path, timbral_params, ot)
    oc = out.get("out_cluster")
    cp = out.get("cluster_parameters")
    if isinstance(oc, dict) and not oc.get("error") and isinstance(cp, dict):
        base["cluster"] = build_cluster_export(score_path, cp, oc)
        base["cluster_parameters"] = to_json_serializable(cp)
    oo = out.get("out_orchestration_symbolic")
    op = out.get("orchestration_parameters")
    if isinstance(oo, dict) and not oo.get("error") and isinstance(op, dict):
        base["orchestration_symbolic"] = build_orchestration_symbolic_export(score_path, op, oo)
        base["orchestration_parameters"] = to_json_serializable(op)
    onf = out.get("out_notated_fusion_potential")
    nfp = out.get("notated_fusion_parameters")
    if isinstance(onf, dict) and not onf.get("error") and isinstance(nfp, dict):
        base["notated_fusion_potential"] = build_notated_fusion_potential_export(score_path, nfp, onf)
        base["notated_fusion_parameters"] = to_json_serializable(nfp)
    ofu = out.get("out_fusion_acoustic_heuristic")
    fp = out.get("fusion_parameters")
    if isinstance(ofu, dict) and not ofu.get("error") and isinstance(fp, dict):
        base["fusion_acoustic_heuristic"] = build_fusion_acoustic_heuristic_export(score_path, fp, ofu)
        base["fusion_parameters"] = to_json_serializable(fp)
    if register_out is not None and register_params is not None:
        base["register_uniformity"] = build_register_export(score_path, register_params, register_out)
    fu = base.get("fusion_acoustic_heuristic")
    if isinstance(fu, dict) and "source_keys" in fu:
        base["source_keys"] = to_json_serializable(list(fu["source_keys"]))
    return base


HTI_EXPORT_SCHEMA_VERSION = "3.0"


def _harmonic_pitch_warnings_from_analyzer(analyzer: Any) -> list[str]:
    msgs: list[str] = []
    any_unresolved = False
    for ev in getattr(analyzer, "score_events", ()) or ():
        for pm in ev.get("pitch_tone_metadata") or ():
            if not isinstance(pm, dict):
                continue
            w = str(pm.get("harmonic_warning") or "").strip()
            if w:
                tag = f"harmonic_pitch: {w}"
                if tag not in msgs:
                    msgs.append(tag)
            if str(pm.get("harmonic_sounding_status") or "") == "unresolved" and str(
                pm.get("harmonic_state") or ""
            ) not in (
                "",
                "none",
            ):
                any_unresolved = True
    if any_unresolved:
        msgs.append(
            "harmonic_pitch: unresolved harmonic sounding pitch for at least one notated event (see event audit)"
        )
    return msgs[:30]


def build_hti_export(score_path: str | None, out: dict[str, Any]) -> dict[str, Any]:
    """Structured JSON for ``run_symbolic_ti_homogeneity_analysis`` (H_TI only)."""
    res = out.get("results") or {}
    params = out.get("parameters") or {}
    warnings: list[str] = []
    if isinstance(res, dict):
        rcs = res.get("register_coverage_status") or []
        if isinstance(rcs, list) and any(str(x) == "unpitched_only" for x in rcs):
            warnings.append(
                "Some windows contain only unpitched material; register compactness "
                "(register_proximity / register_compactness) was omitted there and weights renormalised."
            )
        tcs = res.get("technique_coverage_status") or []
        if isinstance(tcs, list) and any(str(x) in ("unavailable", "ambiguous") for x in tcs):
            warnings.append(
                "Technique-state coverage was unavailable or ambiguous in at least one window; "
                "technique_uniformity was omitted there and weights renormalised."
            )
    an = out.get("analyzer")
    if an is not None:
        warnings.extend(_harmonic_pitch_warnings_from_analyzer(an))
    n = len(res.get("t") or [])
    series: list[dict[str, Any]] = []
    keys = HTI_EXPORT_TIME_SERIES_KEYS
    for i in range(n):
        row: dict[str, Any] = {}
        for k in keys:
            lst = res.get(k)
            if isinstance(lst, list) and i < len(lst):
                row[k] = lst[i]
            else:
                row[k] = None
        series.append(to_json_serializable(row))
    hs = out.get("summary")
    summary_text = hs if isinstance(hs, str) else ""
    dyn_series: list[dict[str, Any]] = []
    dyn_keys = (
        "t",
        "measure",
        "H_TI_core",
        "H_TI_strict",
        "H_TI_subfamily_relieved",
        "same_subfamily_relief_factor",
        "instrument_effective_uniformity",
        "active_weights",
        "notated_dynamic_level_distribution",
        "notated_dynamic_coherence",
        "dominant_dynamic",
        "dominant_dynamics",
        "dominant_dynamic_tie",
        "dominant_dynamic_share",
        "dominant_dynamic_margin",
        "dynamic_intensity_ordinal",
        "dynamic_softness",
        "dynamic_coverage_status",
        "crescendo_active",
        "diminuendo_active",
        "dynamic_divergence_detected",
        "soft_blend_potential",
        "intra_family_convergence_potential",
        "transparent_blend_potential",
        "bright_salience_risk",
        "projection_divergence_risk",
        "masked_tonal_mass_risk",
        "masking_context_weight",
        "family_specific_projection_weight",
        "dynamic_interpretation_label",
        "dynamic_interpretation_label_subfamily_relieved",
        "dynamic_evidence_status",
        "H_TI_affinity_literature_relieved",
        "timbral_affinity_uniformity",
        "instrument_affinity_effective_uniformity",
        "timbral_affinity_profile",
        "timbral_affinity_relief_factor",
        "timbral_affinity_dynamic_factor",
        "timbral_affinity_dynamic_status",
        "affinity_dynamic_interpretation_label",
        "H_TI_affinity_dynamic_conditioned",
        "timbral_affinity_evidence_status",
        "timbral_affinity_rule_summary",
        "timbral_affinity_literature_sources",
    )
    for i in range(n):
        drow: dict[str, Any] = {}
        for k in dyn_keys:
            lst = res.get(k)
            if isinstance(lst, list) and i < len(lst):
                drow[k] = lst[i]
            else:
                drow[k] = None
        dyn_series.append(to_json_serializable(drow))

    base: dict[str, Any] = {
        "schema_version": HTI_EXPORT_SCHEMA_VERSION,
        "kind": "symbolic_timbral_instrumental_homogeneity",
        **_standard_document_fields("symbolic_timbral_instrumental_homogeneity"),
        "symbolic_homogeneity_scope_disclaimer": SYMBOLIC_HOMOGENEITY_SCOPE_DISCLAIMER,
        "exported_at_utc": _utc_now_iso(),
        "score_path": score_path,
        "parameters": to_json_serializable(params),
        "active_weights_nominal": to_json_serializable(
            {
                "instrument_uniformity": params.get("weight_instrument_uniformity"),
                "family_uniformity": params.get("weight_family_uniformity"),
                "technique_uniformity": params.get("weight_technique_uniformity"),
                "register_proximity": params.get("weight_register_proximity"),
            }
        ),
        "time_series": series,
        "dynamic_conditioning": {
            "model_scope": "symbolic_notated_dynamic_conditioning",
            "not_audio_analysis": True,
            "warning": ("Written dynamics are ordinal symbolic evidence, not SPL or measured acoustic intensity."),
            "dynamic_scale": to_json_serializable(notated_dynamic_scale_export()),
            "family_rules_version": FAMILY_RULES_VERSION,
            "time_series": dyn_series,
        },
        "summary": summary_text,
        "warnings": warnings,
        "instrument_taxonomy_version": None,
        "technique_model_version": TECHNIQUE_MODEL_VERSION,
        "hti_homogeneity_semantics": {
            "H_TI_strict": (
                "Strict canonical-instrument homogeneity. Different instrument types are penalised "
                "even within the same subfamily."
            ),
            "H_TI_subfamily_relieved": (
                "Subfamily-aware homogeneity. Different instruments within the same instrumental subfamily "
                "receive partial relief, useful for interpreting related-instrument blending potential. "
                "Symbolic and score-derived, not measured acoustic fusion."
            ),
            "H_TI_core_note": (
                "H_TI_core remains the strict structural reference (same numeric series as H_TI_strict when "
                "dynamic conditioning does not alter the scalar); H_TI_subfamily_relieved is an interpretive "
                "variant, not a replacement."
            ),
            "H_TI_affinity_literature_relieved": (
                "Optional literature-governed symbolic timbral affinity relief: pairwise similarity over active "
                "events replaces only the instrument axis in the same weighted geometric mean as H_TI_core. "
                "Not measured acoustic or perceptual fusion; profiles gate rule confidence."
            ),
            "H_TA_acoustic_proxy": (
                "Score-derived acoustic-informed timbral-affinity proxy: event-level pairwise kernel average "
                "(timbral_acoustic_affinity). Orthogonal to H_TI_core Herfindahl concentration. "
                "Not measured audio, not FFT/SPL, not perceptually validated."
            ),
            "H_TI_core": (
                "Strict symbolic concentration metric (weighted geometric mean including instrument_uniformity "
                "Herfindahl). Unchanged when optional affinity proxies are enabled."
            ),
        },
        "acoustic_timbral_affinity_proxy": {
            "not_audio_analysis": True,
            "validation_status": "score_derived_unvalidated",
            "brass_woodwind_note": (
                "Brass ordinary mixtures share lip-reed excitation; woodwinds span air-jet, single-reed, and "
                "double-reed mechanisms — pairwise source-mechanism similarity is used instead of a single "
                "woodwind homogeneity bucket."
            ),
        },
        "error": out.get("error"),
    }
    ap_rows = res.get("affinity_pair_rows")
    if isinstance(ap_rows, list) and ap_rows:
        base["timbral_affinity_pairwise_rows"] = to_json_serializable(ap_rows)
    tap_rows = res.get("timbral_acoustic_pairwise_rows")
    if isinstance(tap_rows, list) and tap_rows:
        base["timbral_acoustic_pairwise_rows"] = to_json_serializable(tap_rows)
    return base
