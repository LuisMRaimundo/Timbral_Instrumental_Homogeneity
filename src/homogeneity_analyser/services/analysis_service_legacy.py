"""
Legacy multimetric orchestration (H(t), H_timbral metric, H_cluster, fusion, U(t), combined JSON 1.8).

Uses the same symbolic score pipeline as H_TI (``analyzers/timbral.py`` — event/taxonomy base class),
but runs **separate metrics** from ``homogeneity_analyser.legacy``.
Not required for ``run_symbolic_ti_homogeneity_analysis``.

Import via ``homogeneity_analyser.services.analysis_service`` (facade) for backward compatibility.
"""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers import (
    TimbralHomogeneityAnalyzer,
    combine_weighted_geometric,
    normalize_homogeneity_weights,
    normalize_pitch_space,
    note_name_to_midi_ps,
)
from homogeneity_analyser.analyzers.notated_fusion_potential import NotatedFusionPotentialAnalyzer
from homogeneity_analyser.io.score_validation import ScoreValidationError
from homogeneity_analyser.legacy import (
    ClusterHomogeneityAnalyzer,
    FusionAcousticHeuristicAnalyzer,
    HomogeneityAnalyzer,
    OrchestrationSymbolicAnalyzer,
    RegisterUniformityAnalyzer,
)
from homogeneity_analyser.models.results import (
    ClusterSeriesResult,
    FusionAcousticHeuristicSeriesResult,
    HomogeneitySeriesResult,
    NotatedFusionPotentialSeriesResult,
    OrchestrationSymbolicSeriesResult,
    RegisterSeriesResult,
    TimbralSeriesResult,
)
from homogeneity_analyser.services.constants import (
    DEFAULT_CLUSTER_PARAMS,
    DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS,
    DEFAULT_HOMOGENEITY_PARAMS,
    DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS,
    DEFAULT_ORCHESTRATION_SYMBOLIC_PARAMS,
    DEFAULT_REGISTER_UNIFORMITY_PARAMS,
    DEFAULT_TIMBRAL_PARAMS,
)
from homogeneity_analyser.services.param_validation import (
    AnalysisParameterError,
    resolve_notated_fusion_same_family_relief,
    safe_nan_summary,
    validate_both_combine_time_window_sigma,
    validate_cluster_params,
    validate_fusion_acoustic_heuristic_params,
    validate_homogeneity_params,
    validate_notated_fusion_potential_params,
    validate_orchestration_symbolic_params,
    validate_register_uniformity_params,
    validate_timbral_params,
)
from homogeneity_analyser.services.result_assembly import (
    build_cluster_orch_fusion_diagnostics_csv,
    build_cluster_orch_fusion_diagnostics_rows,
    build_combined_csv,
    format_homogeneity_summary,
)
from homogeneity_analyser.services.window_pipeline import align_series_nearest, interpolate_onto_times

# Column order for optional H_timbral per-window diagnostics CSV (nested dicts JSON-encoded).
_TIMBRAL_DIAGNOSTIC_CSV_KEYS: tuple[str, ...] = (
    "H_timbral",
    "weight_instrument",
    "weight_register",
    "instrument_component",
    "instrument_pairwise_component",
    "register_component",
    "timbral_state_concentration",
    "technique_component",
    "cross_family_boost",
    "legacy_instrument_homogeneity",
    "pairwise_blend_weight",
    "pairwise_branch_mean",
    "family_component",
    "n_events",
    "n_notes",
    "n_instruments",
    "n_families",
    "instrument_distribution",
    "family_distribution",
    "technique_distribution",
    "dominant_timbral_state",
    "instrument_distribution_concentration",
    "family_distribution_concentration",
    "technique_only_concentration",
    "full_state_concentration",
    "legacy_concentration",
    "technique_only_distribution",
    "technique_state_distribution_full",
    "timbral_model_mode",
    "model_description",
    "model_version",
    "not_audio_analysis",
    "config_profile_name",
    "config_model_version",
    "constants_used",
    "source_keys_used",
    "provisional_constants_used",
    "evidence_status",
)

TIMBRAL_DIAGNOSTIC_TABLE_HEADERS = ["t_quarterLength", *_TIMBRAL_DIAGNOSTIC_CSV_KEYS]

LEGACY_TIMBRAL_SUMMARY_WARNING = "WARNING: legacy diagnostic only — not an acoustically validated fusion metric.\n\n"

PROVISIONAL_NO_SOURCE_GOVERNANCE_MSG = (
    "This result is based on provisional/project-specific constants and has no source-governed acoustic "
    "support in the current export.\n"
)


def _timbral_diagnostics_need_provisional_warning(diags: list[Any] | None) -> bool:
    if not diags:
        return False
    for d in diags:
        if not isinstance(d, dict):
            continue
        sk = d.get("source_keys_used")
        pc = d.get("provisional_constants_used")
        sk_l = sk if isinstance(sk, list) else []
        pc_l = pc if isinstance(pc, list) else []
        if len(sk_l) == 0 and len(pc_l) > 0:
            return True
    return False


def flatten_timbral_diagnostic_row(t: float, diag: dict[str, Any]) -> dict[str, Any]:
    """Flatten one window diagnostic dict for CSV (JSON for nested mappings)."""
    row: dict[str, Any] = {"t_quarterLength": float(t)}
    for k in _TIMBRAL_DIAGNOSTIC_CSV_KEYS:
        v = diag.get(k)
        if isinstance(v, dict):
            row[k] = json.dumps(v, sort_keys=True, ensure_ascii=False)
        elif isinstance(v, list | tuple):
            row[k] = json.dumps(v, ensure_ascii=False)
        elif v is None:
            row[k] = ""
        elif isinstance(v, bool | int | float | str):
            row[k] = v
        else:
            row[k] = str(v)
    return row


def write_timbral_diagnostics_csv(path: str | Path, t_list: list[float], diagnostics: list[dict[str, Any]]) -> None:
    """Write per-window H_timbral diagnostics to CSV (UTF-8)."""
    p = Path(path)
    rows = [flatten_timbral_diagnostic_row(t, d) for t, d in zip(t_list, diagnostics, strict=True)]
    fieldnames = ["t_quarterLength", *_TIMBRAL_DIAGNOSTIC_CSV_KEYS]
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def run_homogeneity_analysis(
    score_path: str,
    params: dict[str, Any] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Run distribution homogeneity analysis on a score.
    :param score_path: Path to MusicXML or MIDI file.
    :param params: Optional dict with keys as in DEFAULT_HOMOGENEITY_PARAMS.
    :param progress_callback: Optional (frac, desc) -> None with frac in [0, 1].
    :return: Dict with keys: results (t, H), plot_results, analyzer, change_points, change_times, summary, sensitivity.
    """
    p = {**DEFAULT_HOMOGENEITY_PARAMS, **(params or {})}
    p["pitch_space"] = normalize_pitch_space(p.get("pitch_space"))
    try:
        validate_homogeneity_params(p)
    except AnalysisParameterError as e:
        return {"error": str(e), "analyzer": None}
    wm1, wm2, wm3 = normalize_homogeneity_weights(
        p.get("weight_m1"),
        p.get("weight_m2"),
        p.get("weight_m3"),
    )
    p["weight_m1"], p["weight_m2"], p["weight_m3"] = wm1, wm2, wm3
    if progress_callback:
        progress_callback(0.0, "A carregar partitura…")
    try:
        analyzer = HomogeneityAnalyzer(
            score_path=score_path,
            time_step=float(p["time_step"]),
            pitch_space=p["pitch_space"],
            pitch_bin_step=float(p["pitch_bin_step"]),
            silence_intra_value=float(p["silence_intra_value"]),
            silence_transition_value=float(p["silence_transition_value"]),
            allow_partial_scales=bool(p["allow_partial_scales"]),
        )
    except ScoreValidationError as e:
        return {"error": str(e), "analyzer": None}
    except Exception as e:
        msg = (
            "Could not parse the score. Ensure the file is valid MusicXML "
            "(Sibelius/Dorico/MuseScore) or MIDI. Details: "
        )
        return {"error": msg + str(e), "analyzer": None}
    if analyzer.end_time <= 0 or len(analyzer.events) == 0:
        return {
            "error": "Score has no notes or no duration. Use a file that contains at least one note.",
            "analyzer": analyzer,
        }

    single_aggregate = bool(p["single_aggregate"])
    window_size = float(p["window_size"])
    sigma = float(p["sigma"])

    if single_aggregate:
        if progress_callback:
            progress_callback(0.5, "Modo agregado…")
        center = analyzer.end_time / 2.0
        curr_feat = analyzer.extract_features(center, window_size)
        m1 = analyzer.compute_metric_intra(curr_feat)
        m3 = analyzer.compute_metric_scale(center, window_size)
        H_single = combine_weighted_geometric(m1, 1.0, m3, wm1, wm2, wm3)
        results_raw = {
            "t": [center],
            "H": [float(H_single)],
            "m1": [float(m1)],
            "m2": [1.0],
            "m3": [float(m3)],
        }
        plot_results = {"t": [0.0, float(analyzer.end_time)], "H": [float(H_single), float(H_single)]}
        if progress_callback:
            progress_callback(1.0, "Concluído")
    else:

        def _cb(frac: float, desc: str) -> None:
            if progress_callback:
                progress_callback(frac * 0.25, desc)

        results_raw = analyzer.analyze_score(
            window_size=window_size,
            sigma=sigma,
            weight_m1=wm1,
            weight_m2=wm2,
            weight_m3=wm3,
            progress_callback=_cb,
        )
        plot_results = results_raw

    results = HomogeneitySeriesResult.from_legacy(results_raw).as_legacy_dict()
    change_points = [] if single_aggregate else analyzer.segment_homogeneity_pelt(results)
    change_times = [results["t"][i] for i in change_points] if change_points else []

    sensitivity = []
    if not single_aggregate and len(results["H"]) > 1:
        base = np.array(results["H"], dtype=float)
        for k, factor in enumerate((0.75, 1.0, 1.25)):
            if progress_callback:
                progress_callback(0.25 + 0.75 * (k / 3), f"Sensitivity (janela {factor:.2f}×)…")
            ws = window_size * factor
            alt = analyzer.analyze_score(
                window_size=ws,
                sigma=sigma,
                weight_m1=wm1,
                weight_m2=wm2,
                weight_m3=wm3,
            )
            alt_h = np.array(alt["H"], dtype=float)
            if alt_h.size != base.size:
                alt_h = interpolate_onto_times(np.array(alt["t"]), alt_h, np.array(results["t"]))
            sb, sa = np.nanstd(base), np.nanstd(alt_h)
            if alt_h.size > 1 and sb > 1e-12 and sa > 1e-12:
                corr = float(np.corrcoef(base, alt_h)[0, 1])
            else:
                corr = float("nan")
            sensitivity.append((ws, corr, float(np.nanmean(alt_h)), float(np.nanstd(alt_h))))
        if progress_callback:
            progress_callback(1.0, "Concluído")

    summary = format_homogeneity_summary(
        results=results,
        analyzer=analyzer,
        change_times=change_times,
        sensitivity=sensitivity,
        params=p,
    )
    return {
        "results": results,
        "plot_results": plot_results,
        "analyzer": analyzer,
        "change_points": change_points,
        "change_times": change_times,
        "summary": summary,
        "sensitivity": sensitivity,
        "error": None,
    }


def run_timbral_analysis(
    score_path: str,
    params: dict[str, Any] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Run timbral (instrumental) homogeneity analysis.
    :param score_path: Path to MusicXML or MIDI file (MusicXML preferred).
    :param params: Optional dict with time_step, window_size, timbral_config (optional override for weights/bonus),
        and optional ``return_components`` (bool): when True, ``results`` includes per-window
        ``H_timbral_diagnostics`` (does not change ``H_timbral`` values).
    :param progress_callback: Optional (frac, desc) -> None with frac in [0, 1].
    :return: Dict with keys: results (t, H_timbral), analyzer, summary, error.
    """
    p = {**DEFAULT_TIMBRAL_PARAMS, **(params or {})}
    return_components = bool(p.get("return_components", False))
    try:
        validate_timbral_params(p)
    except AnalysisParameterError as e:
        return {"error": str(e), "analyzer": None}
    if progress_callback:
        progress_callback(0.0, "A carregar partitura…")
    timbral_config = p.get("timbral_config")
    tc_copy = dict(timbral_config) if isinstance(timbral_config, dict) else None
    top_mode = p.get("timbral_model_mode")
    if tc_copy is not None and "timbral_model_mode" in tc_copy:
        nested_mode = tc_copy.pop("timbral_model_mode")
        if top_mode not in (None, "") and nested_mode not in (None, "") and str(top_mode) != str(nested_mode):
            return {
                "error": (
                    "timbral_model_mode must match between top-level params and timbral_config when both are set."
                ),
                "analyzer": None,
            }
        if top_mode in (None, "") and nested_mode not in (None, ""):
            top_mode = nested_mode
    try:
        analyzer = TimbralHomogeneityAnalyzer(
            score_path=score_path,
            time_step=float(p["time_step"]),
            timbral_config=tc_copy,
            timbral_model_mode=top_mode,
        )
    except ScoreValidationError as e:
        return {"error": str(e), "analyzer": None}
    except Exception as e:
        msg = (
            "Could not parse the score. Ensure the file is valid MusicXML "
            "(Sibelius/Dorico/MuseScore) or MIDI. Details: "
        )
        return {"error": msg + str(e), "analyzer": None}
    if analyzer.end_time <= 0 or len(analyzer._events) == 0:
        return {
            "error": "Score has no notes or no duration. Use a file that contains at least one note.",
            "analyzer": analyzer,
        }

    results_raw = analyzer.analyze_timbral(
        window_size=float(p["window_size"]),
        progress_callback=progress_callback,
        return_components=return_components,
    )
    if progress_callback:
        progress_callback(1.0, "Concluído")
    results = TimbralSeriesResult.from_legacy(results_raw).as_legacy_dict()
    Ht = np.array(results["H_timbral"], dtype=float)
    hs = safe_nan_summary(Ht)

    def _fmt(v: float | None) -> str:
        return "n/a" if v is None else f"{v:.4f}"

    summary = (
        f"Part-name / orchestration homogeneity H_timbral — **legacy** model mode "
        f"(notation-derived; not acoustic measurement or audio analysis)\n"
        f"Windows: {len(Ht)}\n"
        f"Score duration (quarterLength): {analyzer.end_time:.3f}\n"
        f"H_timbral min: {_fmt(hs['min'])}\n"
        f"H_timbral mean: {_fmt(hs['mean'])}\n"
        f"H_timbral max: {_fmt(hs['max'])}\n"
        f"Window size: {p['window_size']}, Time step: {p['time_step']}\n"
    )
    if str(getattr(analyzer, "_timbral_model_mode", "legacy")) == "legacy":
        summary = LEGACY_TIMBRAL_SUMMARY_WARNING + summary
    if _timbral_diagnostics_need_provisional_warning(results.get("H_timbral_diagnostics")):
        summary = summary + "\n" + PROVISIONAL_NO_SOURCE_GOVERNANCE_MSG
    return {
        "results": results,
        "analyzer": analyzer,
        "summary": summary,
        "error": None,
    }


def run_cluster_analysis(
    score_path: str,
    params: dict[str, Any] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Run vertical pitch-cluster compactness **H_cluster** (sounding MIDI only).

    :param params: Optional ``time_step``, ``window_size``, ``cluster_ref_span`` (default 12).
    :return: Dict with ``results`` (``t``, ``H_cluster``, optional ``H_cluster_diagnostics``),
        ``analyzer``, ``summary``, ``error``.
    """
    p = {**DEFAULT_CLUSTER_PARAMS, **(params or {})}
    try:
        validate_cluster_params(p)
    except AnalysisParameterError as e:
        return {"error": str(e), "analyzer": None}
    if progress_callback:
        progress_callback(0.0, "A carregar partitura…")
    try:
        analyzer = ClusterHomogeneityAnalyzer(
            score_path=score_path,
            time_step=float(p["time_step"]),
            cluster_ref_span=float(p["cluster_ref_span"]),
        )
    except ScoreValidationError as e:
        return {"error": str(e), "analyzer": None}
    except Exception as e:
        msg = "Could not parse the score. Ensure it is valid MusicXML or MIDI. Details: "
        return {"error": msg + str(e), "analyzer": None}
    if analyzer.end_time <= 0 or len(analyzer._events) == 0:
        return {
            "error": "Score has no notes or no duration. Use a file that contains at least one note.",
            "analyzer": analyzer,
        }

    results_raw = analyzer.analyze_cluster(
        window_size=float(p["window_size"]),
        progress_callback=progress_callback,
        return_diagnostics=True,
    )
    if progress_callback:
        progress_callback(1.0, "Concluído")
    results = ClusterSeriesResult.from_legacy(results_raw).as_legacy_dict()
    Hc = np.array(results["H_cluster"], dtype=float)
    cs = safe_nan_summary(Hc)

    def _fmt(v: float | None) -> str:
        return "n/a" if v is None else f"{v:.4f}"

    summary = (
        "Vertical pitch-cluster compactness H_cluster — **sounding MIDI only** "
        "(instrumentation-independent; not H_timbral).\n"
        f"Windows: {len(Hc)}\n"
        f"Score duration (quarterLength): {analyzer.end_time:.3f}\n"
        f"H_cluster min: {_fmt(cs['min'])}\n"
        f"H_cluster mean: {_fmt(cs['mean'])}\n"
        f"H_cluster max: {_fmt(cs['max'])}\n"
        f"Window size: {p['window_size']}, Time step: {p['time_step']}, cluster_ref_span: {p['cluster_ref_span']}\n"
    )
    return {
        "results": results,
        "analyzer": analyzer,
        "summary": summary,
        "error": None,
    }


def run_orchestration_symbolic_analysis(
    score_path: str,
    params: dict[str, Any] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Run **H_orchestration_symbolic**: Herfindahl concentration over instruments, families, and
    technique-state ids from timbral-style slices (no pairwise fusion kernels).
    """
    p = {**DEFAULT_ORCHESTRATION_SYMBOLIC_PARAMS, **(params or {})}
    try:
        validate_orchestration_symbolic_params(p)
    except AnalysisParameterError as e:
        return {"error": str(e), "analyzer": None}
    if progress_callback:
        progress_callback(0.0, "A carregar partitura…")
    tc = p.get("timbral_config")
    tc_copy = dict(tc) if isinstance(tc, dict) else None
    top_mode = p.get("timbral_model_mode")
    if tc_copy is not None and "timbral_model_mode" in tc_copy:
        nested_mode = tc_copy.pop("timbral_model_mode")
        if top_mode not in (None, "") and nested_mode not in (None, "") and str(top_mode) != str(nested_mode):
            return {
                "error": (
                    "timbral_model_mode must match between top-level params and timbral_config when both are set."
                ),
                "analyzer": None,
            }
        if top_mode in (None, "") and nested_mode not in (None, ""):
            top_mode = nested_mode
    try:
        analyzer = OrchestrationSymbolicAnalyzer(
            score_path=score_path,
            time_step=float(p["time_step"]),
            timbral_config=tc_copy,
            timbral_model_mode=top_mode,
            weight_orchestration_instrument=float(p["weight_orchestration_instrument"]),
            weight_orchestration_family=float(p["weight_orchestration_family"]),
            weight_orchestration_technique=float(p["weight_orchestration_technique"]),
        )
    except ScoreValidationError as e:
        return {"error": str(e), "analyzer": None}
    except Exception as e:
        msg = "Could not parse the score. Ensure it is valid MusicXML or MIDI. Details: "
        return {"error": msg + str(e), "analyzer": None}
    if analyzer.end_time <= 0 or len(analyzer._timbral._events) == 0:
        return {
            "error": "Score has no notes or no duration. Use a file that contains at least one note.",
            "analyzer": analyzer,
        }

    results_raw = analyzer.analyze_orchestration_symbolic(
        window_size=float(p["window_size"]),
        progress_callback=progress_callback,
        return_diagnostics=True,
    )
    if progress_callback:
        progress_callback(1.0, "Concluído")
    results = OrchestrationSymbolicSeriesResult.from_legacy(results_raw).as_legacy_dict()
    Ho = np.array(results["H_orchestration_symbolic"], dtype=float)
    osum = safe_nan_summary(Ho)

    def _fmt(v: float | None) -> str:
        return "n/a" if v is None else f"{v:.4f}"

    summary = (
        "Symbolic orchestration H_orchestration_symbolic — **Herfindahl** over instrument / family / "
        "technique_state_id (overlap-weighted; no family-specific fusion kernels; not H_timbral).\n"
        f"Windows: {len(Ho)}\n"
        f"Score duration (quarterLength): {analyzer.end_time:.3f}\n"
        f"H_orchestration_symbolic min: {_fmt(osum['min'])}\n"
        f"H_orchestration_symbolic mean: {_fmt(osum['mean'])}\n"
        f"H_orchestration_symbolic max: {_fmt(osum['max'])}\n"
        f"Weights (instr/family/tech): {analyzer.w_i:.3f} / {analyzer.w_f:.3f} / {analyzer.w_t:.3f}\n"
        f"Window size: {p['window_size']}, Time step: {p['time_step']}\n"
    )
    return {
        "results": results,
        "analyzer": analyzer,
        "summary": summary,
        "error": None,
    }


def run_notated_fusion_potential_analysis(
    score_path: str,
    params: dict[str, Any] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Run **H_notated_fusion_potential**: overlap-weighted Herfindahl uniformity over instruments,
    families, and technique-only buckets, combined with sounding-MIDI register proximity via a
    weighted geometric mean. **Not** measured audio; **not** legacy ``H_timbral`` pairwise kernels.
    """
    p = {**DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS, **(params or {})}
    try:
        validate_notated_fusion_potential_params(p)
    except AnalysisParameterError as e:
        return {"error": str(e), "analyzer": None}
    relief_r, prof_r, ovr_used = resolve_notated_fusion_same_family_relief(p)
    p = {
        **p,
        "same_family_relief": relief_r,
        "same_family_relief_profile": prof_r,
        "same_family_relief_from_override": ovr_used,
    }
    if progress_callback:
        progress_callback(0.0, "A carregar partitura…")
    tc = p.get("timbral_config")
    tc_copy = dict(tc) if isinstance(tc, dict) else None
    top_mode = p.get("timbral_model_mode")
    if tc_copy is not None and "timbral_model_mode" in tc_copy:
        nested_mode = tc_copy.pop("timbral_model_mode")
        if top_mode not in (None, "") and nested_mode not in (None, "") and str(top_mode) != str(nested_mode):
            return {
                "error": (
                    "timbral_model_mode must match between top-level params and timbral_config when both are set."
                ),
                "analyzer": None,
            }
        if top_mode in (None, "") and nested_mode not in (None, ""):
            top_mode = nested_mode
    try:
        analyzer = NotatedFusionPotentialAnalyzer(
            score_path=score_path,
            time_step=float(p["time_step"]),
            timbral_config=tc_copy,
            timbral_model_mode=top_mode,
            register_ref_semitones=float(p["notated_fusion_register_ref_semitones"]),
            same_family_relief=float(p["same_family_relief"]),
            same_family_relief_profile=str(p["same_family_relief_profile"]),
            same_family_relief_from_override=bool(p["same_family_relief_from_override"]),
            weight_notated_fusion_instrument=float(p["weight_notated_fusion_instrument"]),
            weight_notated_fusion_family=float(p["weight_notated_fusion_family"]),
            weight_notated_fusion_technique=float(p["weight_notated_fusion_technique"]),
            weight_notated_fusion_register=float(p["weight_notated_fusion_register"]),
            weight_notated_fusion_dynamic=float(p["weight_notated_fusion_dynamic"]),
        )
    except ScoreValidationError as e:
        return {"error": str(e), "analyzer": None}
    except Exception as e:
        msg = "Could not parse the score. Ensure it is valid MusicXML or MIDI. Details: "
        return {"error": msg + str(e), "analyzer": None}
    if analyzer.end_time <= 0 or len(analyzer._timbral._events) == 0:
        return {
            "error": "Score has no notes or no duration. Use a file that contains at least one note.",
            "analyzer": analyzer,
        }

    results_raw = analyzer.analyze_notated_fusion_potential(
        window_size=float(p["window_size"]),
        progress_callback=progress_callback,
        return_diagnostics=True,
    )
    if progress_callback:
        progress_callback(1.0, "Concluído")
    results = NotatedFusionPotentialSeriesResult.from_legacy(results_raw).as_legacy_dict()
    Hn = np.array(results["H_notated_fusion_potential"], dtype=float)
    nsum = safe_nan_summary(Hn)

    def _fmt(v: float | None) -> str:
        return "n/a" if v is None else f"{v:.4f}"

    summary = (
        "H_notated_fusion_potential — **notation-derived** fusion-potential proxy (Herfindahl over "
        "instrument / family / technique-only + sounding MIDI register proximity). **General across** "
        "taxonomy instruments; **not** measured audio; **does not** use legacy H_timbral family kernels.\n"
        f"Windows: {len(Hn)}\n"
        f"Score duration (quarterLength): {analyzer.end_time:.3f}\n"
        f"H_notated_fusion_potential min: {_fmt(nsum['min'])}\n"
        f"H_notated_fusion_potential mean: {_fmt(nsum['mean'])}\n"
        f"H_notated_fusion_potential max: {_fmt(nsum['max'])}\n"
        f"Weights (instr/family/tech/register): {analyzer.w_i:.3f} / {analyzer.w_f:.3f} / "
        f"{analyzer.w_t:.3f} / {analyzer.w_r:.3f}; register_ref_semitones={analyzer.register_ref_semitones:.3f}; "
        f"same_family_relief_profile={analyzer.same_family_relief_profile}, "
        f"same_family_relief={analyzer.same_family_relief:.3f}\n"
        f"Window size: {p['window_size']}, Time step: {p['time_step']}\n"
    )
    return {
        "results": results,
        "analyzer": analyzer,
        "summary": summary,
        "error": None,
        "notated_fusion_parameters": p,
    }


def run_fusion_acoustic_heuristic_analysis(
    score_path: str,
    params: dict[str, Any] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Run **H_fusion_acoustic_heuristic**: registry-linked feature vectors, explicit harmonic
    roughness proxy, technique concentration, and register compactness. **Not** waveform
    analysis and **not** legacy ``H_timbral``.
    """
    p = {**DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS, **(params or {})}
    try:
        validate_fusion_acoustic_heuristic_params(p)
    except AnalysisParameterError as e:
        return {"error": str(e), "analyzer": None}
    if progress_callback:
        progress_callback(0.0, "A carregar partitura…")
    tc = p.get("timbral_config")
    tc_copy = dict(tc) if isinstance(tc, dict) else None
    top_mode = p.get("timbral_model_mode")
    if tc_copy is not None and "timbral_model_mode" in tc_copy:
        nested_mode = tc_copy.pop("timbral_model_mode")
        if top_mode not in (None, "") and nested_mode not in (None, "") and str(top_mode) != str(nested_mode):
            return {
                "error": (
                    "timbral_model_mode must match between top-level params and timbral_config when both are set."
                ),
                "analyzer": None,
            }
        if top_mode in (None, "") and nested_mode not in (None, ""):
            top_mode = nested_mode
    try:
        analyzer = FusionAcousticHeuristicAnalyzer(
            score_path=score_path,
            time_step=float(p["time_step"]),
            timbral_config=tc_copy,
            timbral_model_mode=top_mode,
            weight_profile=float(p["weight_fusion_profile"]),
            weight_spectral=float(p["weight_fusion_spectral"]),
            weight_technique=float(p["weight_fusion_technique"]),
            weight_register=float(p["weight_fusion_register"]),
            n_harmonics=int(p["fusion_n_harmonics"]),
            roughness_scale=float(p["fusion_roughness_scale"]),
            register_ref_span_semitones=float(p["fusion_register_ref_span_semitones"]),
            profile_distance_scale=float(p["fusion_profile_distance_scale"]),
        )
    except ScoreValidationError as e:
        return {"error": str(e), "analyzer": None}
    except Exception as e:
        msg = "Could not parse the score. Ensure it is valid MusicXML or MIDI. Details: "
        return {"error": msg + str(e), "analyzer": None}
    if analyzer.end_time <= 0 or len(analyzer._timbral._events) == 0:
        return {
            "error": "Score has no notes or no duration. Use a file that contains at least one note.",
            "analyzer": analyzer,
        }

    results_raw = analyzer.analyze_fusion_acoustic_heuristic(
        window_size=float(p["window_size"]),
        progress_callback=progress_callback,
        return_diagnostics=True,
    )
    if progress_callback:
        progress_callback(1.0, "Concluído")
    results = FusionAcousticHeuristicSeriesResult.from_legacy(results_raw).as_legacy_dict()
    Hf = np.array(results["H_fusion_acoustic_heuristic"], dtype=float)
    fsum = safe_nan_summary(Hf)

    def _fmt(v: float | None) -> str:
        return "n/a" if v is None else f"{v:.4f}"

    summary = (
        "Acoustic-informed fusion heuristic H_fusion_acoustic_heuristic — **not** measured audio; "
        "separate from legacy H_timbral. Uses source-tagged feature vectors + harmonic roughness proxy.\n"
        f"Windows: {len(Hf)}\n"
        f"Score duration (quarterLength): {analyzer.end_time:.3f}\n"
        f"H_fusion_acoustic_heuristic min: {_fmt(fsum['min'])}\n"
        f"H_fusion_acoustic_heuristic mean: {_fmt(fsum['mean'])}\n"
        f"H_fusion_acoustic_heuristic max: {_fmt(fsum['max'])}\n"
        f"Weights (profile/spectral/technique/register): {analyzer.wp:.3f} / {analyzer.ws:.3f} / "
        f"{analyzer.wt:.3f} / {analyzer.wr:.3f}\n"
        f"Window size: {p['window_size']}, Time step: {p['time_step']}\n"
    )
    return {
        "results": results,
        "analyzer": analyzer,
        "summary": summary,
        "error": None,
    }


def _parse_register_bound(value) -> float:
    """Convert register bound from string (note name) or number (MIDI) to float MIDI ps."""
    if value is None or value == "":
        raise ValueError("Register bound is required.")
    if isinstance(value, int | float):
        return float(value)
    s = str(value).strip()
    if not s:
        raise ValueError("Register bound is required.")
    try:
        return float(s)
    except ValueError:
        pass
    return note_name_to_midi_ps(s)


def run_register_uniformity_analysis(
    score_path: str,
    params: dict[str, Any] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Run register uniformity analysis: how evenly pitches are distributed within
    a user-defined register [register_low, register_high]. Low = cluster in one
    region; high = spread across the range (e.g. large chord A1–E7).
    """
    p = {**DEFAULT_REGISTER_UNIFORMITY_PARAMS, **(params or {})}
    try:
        validate_register_uniformity_params(p)
    except AnalysisParameterError as e:
        return {"error": str(e), "analyzer": None}
    if progress_callback:
        progress_callback(0.0, "A carregar partitura…")
    try:
        reg_low = _parse_register_bound(p.get("register_low"))
        reg_high = _parse_register_bound(p.get("register_high"))
    except ValueError as e:
        return {"error": str(e), "analyzer": None}
    try:
        analyzer = RegisterUniformityAnalyzer(
            score_path=score_path,
            register_low_ps=reg_low,
            register_high_ps=reg_high,
            time_step=float(p["time_step"]),
        )
    except ScoreValidationError as e:
        return {"error": str(e), "analyzer": None}
    except Exception as e:
        msg = "Could not parse the score. Ensure the file is valid MusicXML or MIDI. Details: "
        return {"error": msg + str(e), "analyzer": None}
    if analyzer.end_time <= 0 or len(analyzer.events) == 0:
        return {"error": "Score has no notes or no duration.", "analyzer": analyzer}

    results_raw = analyzer.analyze_score(
        window_size=float(p["window_size"]),
        progress_callback=progress_callback,
    )
    if progress_callback:
        progress_callback(1.0, "Concluído")
    results = RegisterSeriesResult.from_legacy(results_raw).as_legacy_dict()
    U = np.array(results["U"], dtype=float)
    us = safe_nan_summary(U)

    def _fmt_u(v: float | None) -> str:
        return "n/a" if v is None else f"{v:.4f}"

    summary = (
        f"Register uniformity U(t) — evenness of pitch occupancy across bins in range "
        f"[{p.get('register_low')}, {p.get('register_high')}] (MIDI {reg_low:.0f}–{reg_high:.0f})\n"
        f"Windows: {len(U)}\n"
        f"Score duration (quarterLength): {analyzer.end_time:.3f}\n"
        f"U min: {_fmt_u(us['min'])}\n"
        f"U mean: {_fmt_u(us['mean'])}\n"
        f"U max: {_fmt_u(us['max'])}\n"
        f"Window size: {p['window_size']}, Time step: {p['time_step']}\n"
    )
    return {
        "results": results,
        "analyzer": analyzer,
        "summary": summary,
        "error": None,
    }


def _fusion_native_confidence_triples(results_f: dict[str, Any]) -> tuple[np.ndarray, list[Any], list[Any]]:
    """Per-window fusion confidence / labels on the fusion analyzer's native time grid."""
    t_list = results_f.get("t") or []
    n = len(t_list)
    nan_scores = np.full(n, np.nan, dtype=float)
    blanks = [None] * n
    if n == 0:
        return nan_scores, list(blanks), list(blanks)
    dlist = results_f.get("H_fusion_acoustic_heuristic_diagnostics")
    if not isinstance(dlist, list) or len(dlist) != n:
        return nan_scores, list(blanks), list(blanks)
    scores: list[float] = []
    labels: list[Any] = []
    reasons: list[Any] = []
    for d in dlist:
        if not isinstance(d, dict):
            scores.append(float("nan"))
            labels.append(None)
            reasons.append(None)
            continue
        raw = d.get("confidence_score")
        try:
            scores.append(float(raw) if raw is not None else float("nan"))
        except (TypeError, ValueError):
            scores.append(float("nan"))
        labels.append(d.get("confidence_label"))
        reasons.append(d.get("main_penalty_reason"))
    return np.asarray(scores, dtype=float), labels, reasons


def run_both_and_combine(
    score_path: str,
    time_step: float = 0.25,
    window_size: float = 4.0,
    sigma: float = 12.0,
    homogeneity_params: dict[str, Any] | None = None,
    timbral_params: dict[str, Any] | None = None,
    orchestration_params: dict[str, Any] | None = None,
    notated_fusion_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run homogeneity, timbral, cluster, symbolic orchestration, and fusion-heuristic analyses
    on a common time grid.
    :return: Dict with combined series (``t``, ``H``, ``H_timbral``, ``H_cluster``,
        ``H_orchestration_symbolic``, ``H_fusion_acoustic_heuristic``, ``legacy_H_timbral``, …),
        legacy combined CSV text, cluster/orchestration/fusion diagnostics rows + CSV, and nested ``out_*``.
    """
    try:
        validate_both_combine_time_window_sigma(time_step, window_size, sigma)
    except AnalysisParameterError as e:
        return {
            "error": str(e),
            "out_homogeneity": None,
            "out_timbral": None,
            "out_cluster": None,
            "out_orchestration_symbolic": None,
            "combined": None,
            "combined_csv_content": None,
        }
    h_params = {
        "time_step": time_step,
        "window_size": window_size,
        "sigma": sigma,
        "single_aggregate": False,
        **(homogeneity_params or {}),
    }
    t_params = {
        "time_step": time_step,
        "window_size": window_size,
        **(timbral_params or {}),
    }
    out_h = run_homogeneity_analysis(score_path, h_params)
    out_t = run_timbral_analysis(score_path, t_params)
    if out_h.get("error"):
        return {
            "error": out_h["error"],
            "out_homogeneity": out_h,
            "out_timbral": out_t,
            "out_cluster": None,
            "out_orchestration_symbolic": None,
        }
    if out_t.get("error"):
        return {
            "error": out_t["error"],
            "out_homogeneity": out_h,
            "out_timbral": out_t,
            "out_cluster": None,
            "out_orchestration_symbolic": None,
        }
    cluster_p = {
        **DEFAULT_CLUSTER_PARAMS,
        "time_step": float(time_step),
        "window_size": float(window_size),
    }
    out_c = run_cluster_analysis(score_path, cluster_p)
    if out_c.get("error"):
        return {
            "error": out_c["error"],
            "out_homogeneity": out_h,
            "out_timbral": out_t,
            "out_cluster": out_c,
            "out_orchestration_symbolic": None,
        }

    oextra = orchestration_params or {}
    orch_p = {
        **DEFAULT_ORCHESTRATION_SYMBOLIC_PARAMS,
        "time_step": float(time_step),
        "window_size": float(window_size),
        "timbral_config": t_params.get("timbral_config"),
        "timbral_model_mode": t_params.get("timbral_model_mode", DEFAULT_TIMBRAL_PARAMS["timbral_model_mode"]),
    }
    for k in ("weight_orchestration_instrument", "weight_orchestration_family", "weight_orchestration_technique"):
        if k in oextra:
            orch_p[k] = oextra[k]
    out_o = run_orchestration_symbolic_analysis(score_path, orch_p)
    if out_o.get("error"):
        return {
            "error": out_o["error"],
            "out_homogeneity": out_h,
            "out_timbral": out_t,
            "out_cluster": out_c,
            "out_orchestration_symbolic": out_o,
        }

    nf_p = {
        **DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS,
        "time_step": float(time_step),
        "window_size": float(window_size),
        "timbral_config": t_params.get("timbral_config"),
        "timbral_model_mode": t_params.get("timbral_model_mode", DEFAULT_TIMBRAL_PARAMS["timbral_model_mode"]),
        **(notated_fusion_params or {}),
    }
    out_nf = run_notated_fusion_potential_analysis(score_path, nf_p)
    nf_p = out_nf.get("notated_fusion_parameters") or nf_p
    if out_nf.get("error"):
        return {
            "error": out_nf["error"],
            "out_homogeneity": out_h,
            "out_timbral": out_t,
            "out_cluster": out_c,
            "out_orchestration_symbolic": out_o,
            "out_notated_fusion_potential": out_nf,
            "notated_fusion_parameters": nf_p,
        }

    fusion_p = {
        **DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS,
        "time_step": float(time_step),
        "window_size": float(window_size),
        "timbral_config": t_params.get("timbral_config"),
        "timbral_model_mode": t_params.get("timbral_model_mode", DEFAULT_TIMBRAL_PARAMS["timbral_model_mode"]),
    }
    out_f = run_fusion_acoustic_heuristic_analysis(score_path, fusion_p)
    if out_f.get("error"):
        return {
            "error": out_f["error"],
            "out_homogeneity": out_h,
            "out_timbral": out_t,
            "out_cluster": out_c,
            "out_orchestration_symbolic": out_o,
            "out_notated_fusion_potential": out_nf,
            "notated_fusion_parameters": nf_p,
            "out_fusion_acoustic_heuristic": out_f,
            "fusion_parameters": fusion_p,
        }

    t_h = np.array(out_h["results"]["t"])
    H = np.array(out_h["results"]["H"])
    t_t = np.array(out_t["results"]["t"])
    H_timbral = np.array(out_t["results"]["H_timbral"])
    H_timbral_aligned = H_timbral if np.array_equal(t_h, t_t) else interpolate_onto_times(t_t, H_timbral, t_h)
    t_cl = np.array(out_c["results"]["t"])
    H_cluster = np.array(out_c["results"]["H_cluster"])
    H_cluster_aligned = H_cluster if np.array_equal(t_h, t_cl) else interpolate_onto_times(t_cl, H_cluster, t_h)
    t_orch = np.array(out_o["results"]["t"])
    H_orch = np.array(out_o["results"]["H_orchestration_symbolic"])
    H_orch_aligned = H_orch if np.array_equal(t_h, t_orch) else interpolate_onto_times(t_orch, H_orch, t_h)
    t_nf = np.array(out_nf["results"]["t"])
    H_nf = np.array(out_nf["results"]["H_notated_fusion_potential"])
    H_nf_aligned = H_nf if np.array_equal(t_h, t_nf) else interpolate_onto_times(t_nf, H_nf, t_h)
    H_nfd = np.array(out_nf["results"].get("H_notated_fusion_potential_dynamic", H_nf), dtype=float)
    H_nfd_aligned = H_nfd if np.array_equal(t_h, t_nf) else interpolate_onto_times(t_nf, H_nfd, t_h)
    res_f = out_f["results"]
    t_f = np.array(res_f["t"], dtype=float)
    H_f = np.array(res_f["H_fusion_acoustic_heuristic"], dtype=float)
    H_f_aligned = H_f if np.array_equal(t_h, t_f) else interpolate_onto_times(t_f, H_f, t_h)
    sc_f, lab_f, rea_f = _fusion_native_confidence_triples(res_f)
    sc_use = np.where(np.isfinite(sc_f), sc_f, np.nanmedian(sc_f) if np.any(np.isfinite(sc_f)) else 0.5)
    sc_aligned = sc_use if np.array_equal(t_h, t_f) else interpolate_onto_times(t_f, sc_use, t_h)
    sc_list: list[float | None] = []
    for v in np.asarray(sc_aligned, dtype=float).ravel():
        fv = float(v)
        if math.isnan(fv) or math.isinf(fv):
            sc_list.append(None)
        else:
            sc_list.append(fv)
    lab_a = align_series_nearest(t_f, lab_f, t_h)
    rea_a = align_series_nearest(t_f, rea_f, t_h)
    combined = {
        "t": t_h.tolist(),
        "H": H.tolist(),
        "H_timbral": H_timbral_aligned.tolist(),
        "legacy_H_timbral": H_timbral_aligned.tolist(),
        "H_cluster": H_cluster_aligned.tolist(),
        "H_orchestration_symbolic": H_orch_aligned.tolist(),
        "H_notated_fusion_potential": H_nf_aligned.tolist(),
        "H_notated_fusion_potential_dynamic": H_nfd_aligned.tolist(),
        "H_fusion_acoustic_heuristic": H_f_aligned.tolist(),
        "confidence_score": sc_list,
        "confidence_label": lab_a,
        "main_penalty_reason": rea_a,
    }
    rh = out_h["results"]
    rt = out_t["results"]
    dom = rt.get("dominant_timbral_state")
    dominant_aligned = None
    if isinstance(dom, list) and len(dom) == len(t_t):
        dominant_aligned = align_series_nearest(t_t, dom, t_h)
    combined["dominant_timbral_state"] = dominant_aligned if dominant_aligned is not None else [None] * int(t_h.size)
    combined_csv_content = build_combined_csv(
        t_h,
        H,
        H_timbral_aligned,
        rh,
        dominant_timbral_aligned=dominant_aligned,
        H_cluster_aligned=H_cluster_aligned,
        H_orchestration_symbolic_aligned=H_orch_aligned,
        H_notated_fusion_potential_aligned=H_nf_aligned,
        H_notated_fusion_potential_dynamic_aligned=H_nfd_aligned,
    )
    n_h = int(t_h.size)
    dom_for_rows = dominant_aligned if dominant_aligned is not None and len(dominant_aligned) == n_h else [None] * n_h
    cof_rows = build_cluster_orch_fusion_diagnostics_rows(
        t_h,
        H_cluster_aligned,
        H_orch_aligned,
        H_nf_aligned,
        H_nfd_aligned,
        H_f_aligned,
        H_timbral_aligned,
        sc_list,
        lab_a,
        dom_for_rows,
        rea_a,
    )
    cof_csv_content = build_cluster_orch_fusion_diagnostics_csv(cof_rows)
    return {
        "combined": combined,
        "combined_csv_content": combined_csv_content,
        "cluster_orch_fusion_diagnostics_rows": cof_rows,
        "cluster_orch_fusion_diagnostics_csv_content": cof_csv_content,
        "out_homogeneity": out_h,
        "out_timbral": out_t,
        "out_cluster": out_c,
        "cluster_parameters": cluster_p,
        "out_orchestration_symbolic": out_o,
        "orchestration_parameters": orch_p,
        "out_notated_fusion_potential": out_nf,
        "notated_fusion_parameters": nf_p,
        "out_fusion_acoustic_heuristic": out_f,
        "fusion_parameters": fusion_p,
        "error": None,
    }


