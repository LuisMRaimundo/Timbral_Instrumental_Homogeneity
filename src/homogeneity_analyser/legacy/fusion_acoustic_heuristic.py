"""
Acoustic-informed **fusion heuristic** ``H_fusion_acoustic_heuristic`` (not measured audio).

Uses literature-tagged feature vectors (:mod:`homogeneity_analyser.acoustic_profiles.features`),
a harmonic roughness **proxy** (:mod:`homogeneity_analyser.acoustic_profiles.spectral_proxy`),
technique concentration, and register compactness. This path is **separate** from legacy
``H_timbral`` and from ``H_orchestration_symbolic``.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

from homogeneity_analyser.acoustic_profiles.features import (
    FUSION_FEATURE_FIELDS,
    get_fusion_feature_document,
    resolve_acoustic_feature_row,
)
from homogeneity_analyser.acoustic_profiles.similarity import (
    DEFAULT_FEATURE_WEIGHTS,
    mean_pairwise_profile_similarity,
    weighted_normalized_feature_distance,
)
from homogeneity_analyser.acoustic_profiles.spectral_proxy import (
    SPECTRAL_PROXY_FORMULA_SOURCE_KEY,
    spectral_proxy_model_note,
    window_spectral_roughness_proxy,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.analyzers.timbral_concentration_splits import concentration_bundle_from_timbral_slices

FUSION_MODEL_VERSION = "H_fusion_acoustic_heuristic_v0.1.0"


def _normalize_quadruplet(a: float, b: float, c: float, d: float) -> tuple[float, float, float, float]:
    x, y, z, w = float(a), float(b), float(c), float(d)
    if not all(math.isfinite(v) and v >= 0.0 for v in (x, y, z, w)):
        raise ValueError("Fusion blend weights must be finite and nonnegative.")
    s = x + y + z + w
    if s <= 1e-15 or not math.isfinite(s):
        raise ValueError("Fusion blend weights must sum to a finite value > 0.")
    return x / s, y / s, z / s, w / s


def _slice_sort_key(s: dict[str, Any]) -> tuple:
    return (
        str(s.get("instrument") or ""),
        str(s.get("technique_state_id") or ""),
        float(s.get("pitch", 0.0) or 0.0),
        float(s.get("onset", 0.0) or 0.0),
    )


def technique_similarity_from_slices(slices: list[dict[str, Any]]) -> float:
    """Herfindahl concentration on **technique-only** buckets (overlap weighted)."""
    return float(concentration_bundle_from_timbral_slices(slices)["technique_only_concentration"])


def register_compactness_from_register_array(
    register_span_pitches: np.ndarray,
    *,
    ref_span_semitones: float = 36.0,
) -> float:
    """``1 - span/ref`` clipped, or ``0.5`` when no pitches."""
    if register_span_pitches.size == 0:
        return 0.5
    span = float(np.max(register_span_pitches) - np.min(register_span_pitches))
    ref = max(1e-6, float(ref_span_semitones))
    return float(np.clip(1.0 - span / ref, 0.0, 1.0))


def _collect_sources_used(resolved: Sequence[dict[str, Any]]) -> list[str]:
    keys: set[str] = {SPECTRAL_PROXY_FORMULA_SOURCE_KEY}
    for row in resolved:
        fs = row.get("field_sources") or {}
        if isinstance(fs, dict):
            for v in fs.values():
                if isinstance(v, str) and v.strip():
                    keys.add(v.strip())
    return sorted(keys)


def _collect_missing_features(resolved: Sequence[dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for row in resolved:
        mf = row.get("missing_features") or []
        if isinstance(mf, list):
            for x in mf:
                if isinstance(x, str):
                    out.add(x)
    return sorted(out)


def _count_unknown_profiles(resolved: Sequence[dict[str, Any]]) -> int:
    n = 0
    for row in resolved:
        if str(row.get("match_rule") or "") == "global_default" and str(row.get("instrument_query") or "") not in (
            "",
            "__default__",
        ):
            n += 1
    return n


def _fusion_confidence(
    *,
    n_slices: int,
    missing_feature_tally: int,
    unknown_profile_rows: int,
    mean_dims_used: float,
    spectral_roughness: float,
    roughness_soft_cap: float,
) -> tuple[float, str, str]:
    """
    Return ``(score, label, main_penalty_reason)`` in ``[0,1]``.

    Heuristic v1: penalize missing vector components, defaulted profiles, thin feature
    overlap basis, and very high roughness proxies.
    """
    if n_slices <= 0:
        return 0.5, "low", "empty_window"

    miss_pen = min(0.35, 0.02 * float(missing_feature_tally))
    unk_pen = min(0.35, 0.12 * float(unknown_profile_rows) / max(1, n_slices))
    basis_pen = 0.25 if mean_dims_used <= 1e-9 else min(0.2, 0.04 * max(0.0, 7.0 - mean_dims_used))

    rough_pen = 0.0
    cap = max(1e-9, float(roughness_soft_cap))
    if spectral_roughness > cap:
        rough_pen = min(0.25, 0.25 * float(math.log1p(spectral_roughness - cap) / math.log1p(cap)))

    score = float(np.clip(1.0 - miss_pen - unk_pen - basis_pen - rough_pen, 0.0, 1.0))

    parts = [
        ("missing_feature_values", miss_pen),
        ("unknown_or_defaulted_profile", unk_pen),
        ("sparse_feature_basis", basis_pen),
        ("high_spectral_roughness_proxy", rough_pen),
    ]
    parts.sort(key=lambda x: x[1], reverse=True)
    main = "none"
    if parts[0][1] >= 1e-4:
        main = str(parts[0][0])

    if score >= 0.85:
        label = "high"
    elif score >= 0.6:
        label = "medium"
    else:
        label = "low"
    return score, label, main


def _main_outcome_penalty_reason(
    *,
    acoustic_profile_similarity: float,
    spectral_proxy_similarity: float,
    technique_similarity: float,
    register_compactness: float,
    roughness_raw: float,
    technique_entropy_proxy: float,
) -> str:
    """Pick a human-readable primary *fusion* limitation (orthogonal to confidence)."""
    comps = [
        ("spectral_proxy_similarity", float(spectral_proxy_similarity)),
        ("acoustic_profile_similarity", float(acoustic_profile_similarity)),
        ("technique_similarity", float(technique_similarity)),
        ("register_compactness", float(register_compactness)),
    ]
    comps.sort(key=lambda x: x[1])
    weakest = comps[0][0]
    if roughness_raw > 0.35 and weakest == "spectral_proxy_similarity":
        return "high_spectral_roughness_proxy"
    if weakest == "technique_similarity" and technique_entropy_proxy < 0.75:
        return "mixed_technique"
    if weakest == "acoustic_profile_similarity":
        return "heterogeneous_acoustic_profiles"
    if weakest == "register_compactness":
        return "wide_register_span"
    return "none"


def compute_fusion_acoustic_heuristic_window(
    slices: list[dict[str, Any]],
    register_span_pitches: np.ndarray,
    *,
    weight_profile: float = 0.35,
    weight_spectral: float = 0.35,
    weight_technique: float = 0.15,
    weight_register: float = 0.15,
    n_harmonics: int = 12,
    roughness_scale: float = 14.0,
    register_ref_span_semitones: float = 36.0,
    feature_weights: dict[str, float] | None = None,
    profile_distance_scale: float = 0.55,
) -> dict[str, Any]:
    """
    Compute scalar + component diagnostics for one window.

    Always includes ``model_version``, ``not_audio_analysis``, ``sources_used``,
    ``missing_features``, ``confidence_score``, ``confidence_label``, ``main_penalty_reason``.
    """
    wp, ws, wt, wr = _normalize_quadruplet(weight_profile, weight_spectral, weight_technique, weight_register)
    doc = get_fusion_feature_document()
    data_version = str(doc.get("config_model_version", ""))

    if not slices:
        meta = _neutral_meta(
            "empty_window",
            data_version=data_version,
            sources_used=sorted({SPECTRAL_PROXY_FORMULA_SOURCE_KEY}),
            missing_features=list(FUSION_FEATURE_FIELDS),
            confidence=0.5,
            confidence_label="low",
        )
        return {
            "H_fusion_acoustic_heuristic": 0.5,
            "acoustic_profile_similarity": 0.5,
            "spectral_proxy_similarity": 0.5,
            "technique_similarity": 0.5,
            "register_compactness": 0.5,
            "fusion_weights": {"profile": wp, "spectral": ws, "technique": wt, "register": wr},
            **meta,
        }

    ordered = sorted(slices, key=_slice_sort_key)
    resolved = [
        resolve_acoustic_feature_row(str(s.get("instrument") or ""), str(s.get("technique_state_id") or "") or None)
        for s in ordered
    ]
    vectors = [dict(x["vector"]) for x in resolved]
    masses = [max(0.0, float(s.get("overlap_ql", 0.0) or 0.0)) for s in ordered]

    prof_sim, mean_dist, n_pairs = mean_pairwise_profile_similarity(
        vectors,
        masses,
        feature_weights or DEFAULT_FEATURE_WEIGHTS,
        distance_scale=profile_distance_scale,
    )
    mean_dims = 0.0
    if n_pairs > 0:
        dim_sum = 0
        fw = feature_weights or DEFAULT_FEATURE_WEIGHTS
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                _, n_used, _ = weighted_normalized_feature_distance(vectors[i], vectors[j], fw)
                dim_sum += n_used
        mean_dims = float(dim_sum) / float(n_pairs)

    rough = window_spectral_roughness_proxy(ordered, resolved, n_harmonics=int(n_harmonics))
    spec_sim = float(1.0 / (1.0 + float(roughness_scale) * rough))

    tech_sim = technique_similarity_from_slices(ordered)
    reg_sim = register_compactness_from_register_array(
        register_span_pitches, ref_span_semitones=register_ref_span_semitones
    )

    h = float(np.clip(wp * prof_sim + ws * spec_sim + wt * tech_sim + wr * reg_sim, 0.0, 1.0))

    missing_tally = sum(len(x.get("missing_features") or []) for x in resolved)
    unknown_prof = _count_unknown_profiles(resolved)
    sources_used = _collect_sources_used(resolved)
    missing_feats = _collect_missing_features(resolved)

    conf, conf_label, conf_penalty = _fusion_confidence(
        n_slices=len(ordered),
        missing_feature_tally=missing_tally,
        unknown_profile_rows=unknown_prof,
        mean_dims_used=mean_dims,
        spectral_roughness=rough,
        roughness_soft_cap=0.45,
    )
    main_out = _main_outcome_penalty_reason(
        acoustic_profile_similarity=prof_sim,
        spectral_proxy_similarity=spec_sim,
        technique_similarity=tech_sim,
        register_compactness=reg_sim,
        roughness_raw=rough,
        technique_entropy_proxy=tech_sim,
    )

    diag_profile_explain = {
        "mean_pairwise_profile_distance": float(mean_dist),
        "mean_active_feature_dims_per_pair": float(mean_dims),
        "n_profile_pairs": int(n_pairs),
        "horn_vs_violin_note": (
            "Differences between brass and strings are explained only via resolved feature vectors "
            "and pairwise distances; there is no hidden family boost constant in this metric."
        ),
    }

    return {
        "H_fusion_acoustic_heuristic": h,
        "acoustic_profile_similarity": float(prof_sim),
        "spectral_proxy_similarity": float(spec_sim),
        "technique_similarity": float(tech_sim),
        "register_compactness": float(reg_sim),
        "spectral_roughness_proxy_raw": float(rough),
        "fusion_weights": {"profile": wp, "spectral": ws, "technique": wt, "register": wr},
        "model_version": FUSION_MODEL_VERSION,
        "fusion_feature_data_version": data_version,
        "not_audio_analysis": True,
        "sources_used": sources_used,
        "missing_features": missing_feats,
        "confidence_score": float(conf),
        "confidence_label": conf_label,
        "main_penalty_reason": main_out,
        "confidence_main_penalty_reason": conf_penalty,
        "spectral_proxy_model": spectral_proxy_model_note(),
        "profile_explain": diag_profile_explain,
        "resolved_profile_match_rules": [str(r.get("match_rule")) for r in resolved],
    }


def _neutral_meta(
    reason: str,
    *,
    data_version: str,
    sources_used: list[str],
    missing_features: list[str],
    confidence: float,
    confidence_label: str,
) -> dict[str, Any]:
    return {
        "model_version": FUSION_MODEL_VERSION,
        "fusion_feature_data_version": data_version,
        "not_audio_analysis": True,
        "sources_used": sources_used,
        "missing_features": missing_features,
        "confidence_score": float(confidence),
        "confidence_label": confidence_label,
        "main_penalty_reason": reason,
        "confidence_main_penalty_reason": reason,
        "spectral_proxy_model": spectral_proxy_model_note(),
    }


class FusionAcousticHeuristicAnalyzer:
    """Sliding-window ``H_fusion_acoustic_heuristic`` using timbral slice construction only."""

    def __init__(
        self,
        score_path: str | None = None,
        time_step: float = 0.25,
        timbral_config: dict[str, Any] | None = None,
        *,
        timbral_model_mode: str | None = None,
        weight_profile: float = 0.35,
        weight_spectral: float = 0.35,
        weight_technique: float = 0.15,
        weight_register: float = 0.15,
        n_harmonics: int = 12,
        roughness_scale: float = 14.0,
        register_ref_span_semitones: float = 36.0,
        feature_weights: dict[str, float] | None = None,
        profile_distance_scale: float = 0.55,
        music21_score: Any | None = None,
    ):
        self._timbral = TimbralHomogeneityAnalyzer(
            score_path=score_path,
            time_step=float(time_step),
            timbral_config=timbral_config,
            timbral_model_mode=timbral_model_mode,
            music21_score=music21_score,
        )
        self.wp, self.ws, self.wt, self.wr = _normalize_quadruplet(
            weight_profile, weight_spectral, weight_technique, weight_register
        )
        self.n_harmonics = int(n_harmonics)
        self.roughness_scale = float(roughness_scale)
        self.register_ref_span_semitones = float(register_ref_span_semitones)
        self.feature_weights = feature_weights
        self.profile_distance_scale = float(profile_distance_scale)
        self.time_axis = self._timbral.time_axis
        self.end_time = self._timbral.end_time

    def compute_fusion_window(self, window_center: float, window_size: float) -> dict[str, Any]:
        feats = self._timbral.extract_timbral_features(float(window_center), float(window_size))
        if feats is None:
            doc = get_fusion_feature_document()
            dv = str(doc.get("config_model_version", ""))
            meta = _neutral_meta(
                "empty_window",
                data_version=dv,
                sources_used=sorted({SPECTRAL_PROXY_FORMULA_SOURCE_KEY}),
                missing_features=list(FUSION_FEATURE_FIELDS),
                confidence=0.5,
                confidence_label="low",
            )
            return {
                "H_fusion_acoustic_heuristic": 0.5,
                "acoustic_profile_similarity": 0.5,
                "spectral_proxy_similarity": 0.5,
                "technique_similarity": 0.5,
                "register_compactness": 0.5,
                "fusion_weights": {"profile": self.wp, "spectral": self.ws, "technique": self.wt, "register": self.wr},
                **meta,
            }
        slices = feats.get("timbral_note_slices") or []
        if not isinstance(slices, list):
            slices = []
        reg = feats.get("register_span_pitches")
        reg_arr = np.asarray(reg, dtype=float).ravel() if reg is not None else np.array([], dtype=float)

        out = compute_fusion_acoustic_heuristic_window(
            list(slices),
            reg_arr,
            weight_profile=self.wp,
            weight_spectral=self.ws,
            weight_technique=self.wt,
            weight_register=self.wr,
            n_harmonics=self.n_harmonics,
            roughness_scale=self.roughness_scale,
            register_ref_span_semitones=self.register_ref_span_semitones,
            feature_weights=self.feature_weights,
            profile_distance_scale=self.profile_distance_scale,
        )
        out["fusion_weights"] = {"profile": self.wp, "spectral": self.ws, "technique": self.wt, "register": self.wr}
        return out

    def analyze_fusion_acoustic_heuristic(
        self,
        window_size: float,
        progress_callback: Callable[[float, str], None] | None = None,
        *,
        return_diagnostics: bool = True,
    ) -> dict[str, Any]:
        t_list: list[float] = []
        h_list: list[float] = []
        diag_list: list[dict[str, Any]] = []
        n = len(self.time_axis)
        for i, t in enumerate(self.time_axis):
            d = self.compute_fusion_window(float(t), float(window_size))
            t_list.append(float(t))
            h_list.append(float(d["H_fusion_acoustic_heuristic"]))
            if return_diagnostics:
                diag_list.append(d)
            if progress_callback is not None and n > 0:
                progress_callback((i + 1) / n, "H_fusion_acoustic_heuristic(t)")
        out: dict[str, Any] = {
            "t": t_list,
            "H_fusion_acoustic_heuristic": h_list,
            "fusion_model_header": {
                "model_version": FUSION_MODEL_VERSION,
                "fusion_feature_data_version": str(get_fusion_feature_document().get("config_model_version", "")),
                "not_audio_analysis": True,
                "description": (
                    "Literature- and registry-linked feature vectors + explicit harmonic roughness proxy; "
                    "no waveform analysis of user audio."
                ),
            },
        }
        if return_diagnostics:
            out["H_fusion_acoustic_heuristic_diagnostics"] = diag_list
        return out
