"""
H_TI product orchestration — ``run_symbolic_ti_homogeneity_analysis`` only.

Built on ``SymbolicTIHomogeneityAnalyzer`` (extends the symbolic event pipeline in ``timbral.py``).
Taxonomy, families, and register compactness logic live in ``analyzers/hti.py`` and helpers.

Import via ``homogeneity_analyser.services.analysis_service`` (facade) for backward compatibility.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.hti_adaptive_windows import (
    HTI_WINDOW_MODE_MANUAL,
    build_hti_window_centers,
    resolve_hti_windowing,
)
from homogeneity_analyser.io.score_validation import ScoreValidationError
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS, resolve_register_ref_semitones
from homogeneity_analyser.services.param_validation import (
    AnalysisParameterError,
    safe_nan_summary,
    validate_hti_params,
)


def _acoustic_proxy_kernel_weights_from_params(p: dict[str, Any]) -> dict[str, float] | None:
    """Map UI/service weight keys to timbral_acoustic_proxy kernel component names."""
    mapping = (
        ("source_mechanism_weight", "source_mechanism"),
        ("family_similarity_weight", "instrument_family"),
        ("technique_similarity_weight", "technique"),
        ("register_tessitura_weight", "register_tessitura"),
        ("dynamic_similarity_weight", "dynamic"),
        ("attack_similarity_weight", "attack_envelope"),
    )
    out: dict[str, float] = {}
    for pk, ck in mapping:
        raw = p.get(pk)
        if raw is None or str(raw).strip() == "":
            continue
        try:
            out[ck] = float(raw)
        except (TypeError, ValueError):
            continue
    return out or None


def run_symbolic_ti_homogeneity_analysis(
    score_path: str,
    params: dict[str, Any] | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict[str, Any]:
    """
    Symbolic timbral–instrumental homogeneity **H_TI(t)** — score-derived only (MusicXML / MIDI).

    :return: Dict with ``results`` (time series), ``analyzer``, ``summary``, ``error``.
    """
    p = {**DEFAULT_HTI_PARAMS, **(params or {})}
    try:
        validate_hti_params(p)
    except AnalysisParameterError as e:
        return {"error": str(e), "analyzer": None}
    if progress_callback:
        progress_callback(0.0, "Loading score…")
    ref_ql = resolve_register_ref_semitones(p)
    try:
        analyzer = SymbolicTIHomogeneityAnalyzer(
            score_path=score_path,
            time_step=float(p["time_step"]),
            register_ref_semitones=ref_ql,
            pitch_interpretation_mode=str(p.get("pitch_interpretation_mode") or "musicxml_sounding"),
            same_subfamily_relief_factor=float(p.get("same_subfamily_relief_factor", 0.0) or 0.0),
            timbral_affinity_relief_factor=float(p.get("timbral_affinity_relief_factor", 0.0) or 0.0),
            timbral_affinity_profile=str(p.get("timbral_affinity_profile") or "conservative"),
            dynamic_affinity_enabled=bool(p.get("dynamic_affinity_enabled", True)),
            harmonic_pitch_policy=str(p.get("harmonic_pitch_policy") or "conservative"),
            include_symbolic_blend_potential=bool(p.get("include_symbolic_blend_potential", False)),
            include_acoustic_proxy=bool(p.get("include_acoustic_proxy", False)),
            acoustic_proxy_profile=str(p.get("acoustic_proxy_profile") or "conservative"),
            acoustic_proxy_pairwise_export=bool(p.get("acoustic_proxy_pairwise_export", False)),
            acoustic_proxy_kernel_weights=_acoustic_proxy_kernel_weights_from_params(p),
            acoustic_proxy_include_interval_class=bool(
                p.get("acoustic_proxy_include_interval_class", False)
            ),
            acoustic_proxy_min_evidence_policy=str(
                p.get("acoustic_proxy_min_evidence_policy") or "omit_missing_components"
            ),
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
    wi = float(p["weight_instrument_uniformity"])
    wf = float(p["weight_family_uniformity"])
    wt = float(p["weight_technique_uniformity"])
    wr = float(p["weight_register_proximity"])
    excerpt_ql = float(analyzer.end_time)
    win_res = resolve_hti_windowing(p, excerpt_duration_quarter_length=excerpt_ql)
    w_eff = float(win_res["window_size_effective"])
    edge_pol = str(win_res["edge_policy"])
    if str(win_res["window_mode"]) == HTI_WINDOW_MODE_MANUAL:
        hti_centers: list[float] | None = None
    else:
        hti_centers = build_hti_window_centers(
            excerpt_ql,
            float(win_res["time_step_effective"]),
            w_eff,
            edge_pol,
        )
    results = analyzer.analyze_hti(
        w_eff,
        time_centers=hti_centers,
        excerpt_start_ql=0.0,
        excerpt_end_ql=excerpt_ql,
        edge_policy=edge_pol,
        w_instr=wi,
        w_fam=wf,
        w_tech=wt,
        w_reg=wr,
        progress_callback=progress_callback,
        collect_affinity_pairs=bool(p.get("export_affinity_pairs", False))
        or bool(p.get("acoustic_proxy_pairwise_export", False)),
    )
    if progress_callback:
        progress_callback(1.0, "Done")
    h_arr = np.asarray(results["H_TI"], dtype=float)
    hs = safe_nan_summary(h_arr)

    def _fmt(v: float | None) -> str:
        return "n/a" if v is None else f"{v:.4f}"

    prof = str(p.get("register_ref_profile", "")).strip() or str(DEFAULT_HTI_PARAMS["register_ref_profile"])
    summary = (
        "**Symbolic timbral–instrumental homogeneity** **H_TI(t)** — notation-derived; "
        "**not** measured audio, **not** spectral or waveform analysis.\n\n"
        f"Windows: {len(h_arr)}\n"
        f"Score duration (quarterLength): {analyzer.end_time:.3f}\n"
        f"H_TI min: {_fmt(hs['min'])}\n"
        f"H_TI mean: {_fmt(hs['mean'])}\n"
        f"H_TI max: {_fmt(hs['max'])}\n"
        f"Window size (effective): {win_res['window_size_effective']}, "
        f"time step (effective): {win_res['time_step_effective']}; "
        f"inputs — window: {p['window_size']}, step: {p['time_step']}; "
        f"window_mode: **{win_res['window_mode']}**, edge_policy: **{win_res['edge_policy']}**. "
        f"Register reference profile: **{prof}** → effective ref.: **{ref_ql:g}** semitones "
        f"(override when `register_ref_semitones` is set).\n"
        f"Nominal weights: instrument {wi:.3f}, family {wf:.3f}, technique {wt:.3f}, register {wr:.3f} "
        "(technique/register omitted per window when coverage is unavailable/ambiguous; "
        "remaining weights renormalised).\n"
        "Register term **register_compactness** (exported also as **register_proximity**): geometric mean of outer "
        "**register_span_proximity** and overlap-weighted **pairwise_interval_proximity** over chord tones / "
        "sounding MIDI (unpitched percussion excluded). Wide registral spacing can support transparency in the "
        "dynamic-conditioning layer; it is **not** treated as higher homogeneity.\n"
    )
    sfr = float(p.get("same_subfamily_relief_factor", 0.0) or 0.0)
    if math.isfinite(sfr) and sfr > 1e-12:
        summary += (
            f"**Same-subfamily relief** ``same_subfamily_relief_factor`` = **{sfr:g}**: interpretive "
            "**H_TI_subfamily_relieved** and **instrument_effective_uniformity** are exported alongside the strict "
            "**H_TI_core** / **H_TI_strict** reference (not a replacement; score-derived only).\n"
        )
    tar = float(p.get("timbral_affinity_relief_factor", 0.0) or 0.0)
    tap = str(p.get("timbral_affinity_profile") or "conservative").strip()
    if math.isfinite(tar) and tar > 1e-12:
        summary += (
            f"**Literature-governed timbral affinity** — profile **{tap}**, ``timbral_affinity_relief_factor`` = "
            f"**{tar:g}**: optional **H_TI_affinity_literature_relieved** and pairwise **timbral_affinity_uniformity** "
            "are exported; **H_TI_core** is unchanged. Symbolic / score-derived only — not measured fusion.\n"
        )
    if bool(p.get("include_acoustic_proxy", False)):
        app = str(p.get("acoustic_proxy_profile") or "conservative").strip()
        summary += (
            f"**Acoustic-aligned symbolic timbral-affinity proxy** — profile **{app}**: "
            "**H_TA_acoustic_proxy** / **timbral_acoustic_affinity** exported alongside **H_TI_core**. "
            "Score-derived organology kernel; **not** audio, **not** FFT/SPL, **not** perceptually validated.\n"
        )
    n_win = len(h_arr)
    if n_win > 0:
        dmf = results.get("dominant_macrofamilies")
        dmt = results.get("dominant_macrofamily_tie")
        if isinstance(dmf, list) and isinstance(dmt, list) and dmf and bool(dmt[0]):
            labels = [str(x) for x in (dmf[0] or [])]
            if len(labels) > 1:
                summary += "\n**Dominant macrofamily** (window 0): " + " / ".join(labels) + " **(tie)**\n"
        dfm = results.get("dominant_families")
        dft = results.get("dominant_family_tie")
        if isinstance(dfm, list) and isinstance(dft, list) and dfm and bool(dft[0]):
            flabels = [str(x) for x in (dfm[0] or [])]
            if len(flabels) > 1:
                summary += "**Dominant family** (window 0): " + " / ".join(flabels) + " **(tie)**\n"
        dim = results.get("dominant_instruments")
        dit = results.get("dominant_instrument_tie")
        if isinstance(dim, list) and isinstance(dit, list) and dim and bool(dit[0]):
            ilabels = [str(x) for x in (dim[0] or [])]
            if len(ilabels) > 1:
                summary += "**Dominant instrument** (window 0): " + " / ".join(ilabels) + " **(tie)**\n"
        dts = results.get("dominant_timbral_states")
        dst = results.get("dominant_timbral_state_tie")
        if isinstance(dts, list) and isinstance(dst, list) and dts and bool(dst[0]):
            tlabels = [str(x) for x in (dts[0] or [])]
            if len(tlabels) > 1:
                summary += "**Dominant timbral state** (window 0): " + " / ".join(tlabels) + " **(tie)**\n"
        ddy = results.get("dominant_dynamics")
        ddt = results.get("dominant_dynamic_tie")
        if isinstance(ddy, list) and isinstance(ddt, list) and ddy and bool(ddt[0]):
            dynlabels = [str(x) for x in (ddy[0] or [])]
            if len(dynlabels) > 1:
                summary += "**Dominant dynamic** (window 0): " + " / ".join(dynlabels) + " **(tie)**\n"
    params_out = dict(DEFAULT_HTI_PARAMS)
    for k in DEFAULT_HTI_PARAMS:
        if k in p:
            params_out[k] = p[k]
    params_out["register_ref_effective_semitones"] = float(ref_ql)
    params_out.update(win_res)
    return {
        "results": results,
        "analyzer": analyzer,
        "summary": summary,
        "error": None,
        "parameters": params_out,
    }
