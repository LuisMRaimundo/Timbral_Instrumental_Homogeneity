"""
Shared validation for analysis parameters (service / API layer).

Direct calls to ``run_*_analysis`` must not bypass invalid ``window_size`` / ``sigma`` /
``pitch_bin_step`` / timbral overrides: validate here before score I/O.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, cast

import numpy as np

from homogeneity_analyser.models.timbral_semantics import assert_active_timbral_model_mode
from homogeneity_analyser.services.constants import (
    DEFAULT_HOMOGENEITY_PARAMS,
    DEFAULT_SAME_FAMILY_RELIEF_PROFILE,
    SAME_FAMILY_RELIEF_PROFILES,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import get_timbral_config


class AnalysisParameterError(ValueError):
    """Raised when analysis parameters are out of range or non-finite (API / service layer)."""


def same_family_relief_override_provided(ovr_raw: Any) -> bool:
    """
    True when ``same_family_relief_override`` (or legacy ``same_family_relief``) should be read as an explicit value.

    ``None``, blank strings, and whitespace-only strings mean **no** override (use the named profile). Numeric ``0.0``
    means an **explicit** zero override. ``bool`` is ignored so ``True``/``False`` are not mistaken for ``1``/``0``.
    """
    if ovr_raw is None:
        return False
    if isinstance(ovr_raw, bool):
        return False
    if isinstance(ovr_raw, str):
        return ovr_raw.strip() != ""
    if isinstance(ovr_raw, int | float):
        return math.isfinite(float(ovr_raw))
    return str(ovr_raw).strip() != ""


def safe_nan_summary(values: Sequence[float] | np.ndarray) -> dict[str, float | None]:
    """
    Min / mean / max over finite values; ignore NaN.

    Returns ``min``, ``mean``, ``max`` all ``None`` when ``values`` is empty or has no
    finite entries (including all-NaN), so summaries never emit misleading numeric stats.
    """
    a = np.asarray(values, dtype=float).ravel()
    if a.size == 0:
        return {"min": None, "mean": None, "max": None}
    mask = np.isfinite(a)
    if not np.any(mask):
        return {"min": None, "mean": None, "max": None}
    b = a[mask]
    return {"min": float(np.min(b)), "mean": float(np.mean(b)), "max": float(np.max(b))}


def _req_positive(name: str, x: float) -> None:
    if not math.isfinite(x) or x <= 0.0:
        raise AnalysisParameterError(f"{name} must be a finite number > 0; got {x!r}.")


def _req_finite_nonneg(name: str, x: float) -> None:
    if not math.isfinite(x) or x < 0.0:
        raise AnalysisParameterError(f"{name} must be finite and nonnegative; got {x!r}.")


def _req_unit_interval(name: str, x: float) -> None:
    if not math.isfinite(x) or x < 0.0 or x > 1.0:
        raise AnalysisParameterError(f"{name} must be finite and in [0, 1]; got {x!r}.")


def _float_field(p: Mapping[str, Any], key: str, *, default: float | None = None) -> float:
    v = p.get(key, default) if default is not None else p[key]
    try:
        return float(v)
    except (TypeError, ValueError) as e:
        raise AnalysisParameterError(f"{key} must be numeric; got {v!r}.") from e


def _req_hti_bool_scalar(key: str, raw: Any) -> None:
    """Reject non-boolean scalars for JSON/API callers (bool first; ``0``/``1`` allowed)."""
    if isinstance(raw, bool):
        return
    if isinstance(raw, int) and raw in (0, 1):
        return
    if isinstance(raw, float) and math.isfinite(raw) and raw in (0.0, 1.0):
        return
    raise AnalysisParameterError(f"{key} must be a boolean (or 0/1); got {raw!r}.")


def validate_homogeneity_params(p: Mapping[str, Any]) -> None:
    """Validate merged homogeneity parameter dict (mutates nothing)."""
    _req_positive("time_step", _float_field(p, "time_step"))
    _req_positive("window_size", _float_field(p, "window_size"))
    _req_positive("sigma", _float_field(p, "sigma"))
    _req_positive("pitch_bin_step", _float_field(p, "pitch_bin_step"))
    si = _float_field(
        p,
        "silence_intra_value",
        default=cast(float, DEFAULT_HOMOGENEITY_PARAMS["silence_intra_value"]),
    )
    st = _float_field(
        p,
        "silence_transition_value",
        default=cast(float, DEFAULT_HOMOGENEITY_PARAMS["silence_transition_value"]),
    )
    _req_unit_interval("silence_intra_value", si)
    _req_unit_interval("silence_transition_value", st)
    for key in ("weight_m1", "weight_m2", "weight_m3"):
        _req_finite_nonneg(key, _float_field(p, key))


def validate_timbral_params(p: Mapping[str, Any]) -> None:
    """Validate merged timbral parameter dict and optional ``timbral_config`` overrides."""
    _req_positive("time_step", _float_field(p, "time_step"))
    _req_positive("window_size", _float_field(p, "window_size"))
    try:
        assert_active_timbral_model_mode(p.get("timbral_model_mode"))
    except ValueError as exc:
        raise AnalysisParameterError(str(exc)) from exc
    cfg = p.get("timbral_config")
    if isinstance(cfg, Mapping):
        try:
            assert_active_timbral_model_mode(cfg.get("timbral_model_mode"))
        except ValueError as exc:
            raise AnalysisParameterError(str(exc)) from exc
        top_m, nest_m = p.get("timbral_model_mode"), cfg.get("timbral_model_mode")
        if top_m not in (None, "") and nest_m not in (None, "") and str(top_m) != str(nest_m):
            raise AnalysisParameterError(
                "timbral_model_mode must match between top-level params and timbral_config when both are set."
            )
    if cfg is None:
        return
    if not isinstance(cfg, Mapping):
        raise AnalysisParameterError("timbral_config must be a dict or None.")
    allowed = frozenset(get_timbral_config().keys())
    for k, v in cfg.items():
        if k not in allowed:
            continue
        if k == "register_ref_semitones":
            try:
                rv = float(v)
            except (TypeError, ValueError) as e:
                raise AnalysisParameterError(f"register_ref_semitones must be numeric; got {v!r}.") from e
            if not math.isfinite(rv) or rv <= 0.0:
                raise AnalysisParameterError(f"register_ref_semitones must be finite and > 0; got {v!r}.")
        elif k in ("weight_instrument", "weight_register"):
            try:
                wv = float(v)
            except (TypeError, ValueError) as e:
                raise AnalysisParameterError(f"{k} must be numeric; got {v!r}.") from e
            _req_finite_nonneg(k, wv)
        elif k == "family_bonus":
            try:
                fb = float(v)
            except (TypeError, ValueError) as e:
                raise AnalysisParameterError(f"family_bonus must be numeric; got {v!r}.") from e
            _req_unit_interval("family_bonus", fb)


def validate_hti_params(p: Mapping[str, Any]) -> None:
    """Validate merged H_TI (symbolic timbral–instrumental homogeneity) parameter dict."""
    from homogeneity_analyser.analyzers.hti_adaptive_windows import (
        HTI_EDGE_DROP,
        HTI_EDGE_INCLUDE,
        HTI_EDGE_MARK,
        HTI_WINDOW_MODE_AUTO_DURATION,
        HTI_WINDOW_MODE_AUTO_TARGET,
        HTI_WINDOW_MODE_MANUAL,
    )
    from homogeneity_analyser.services.constants import (
        DEFAULT_HTI_PARAMS,
        DEFAULT_REGISTER_REF_PROFILE,
        REGISTER_REF_PROFILE_SEMITONES,
    )

    mode = str(p.get("window_mode", HTI_WINDOW_MODE_MANUAL)).strip()
    if mode not in (HTI_WINDOW_MODE_MANUAL, HTI_WINDOW_MODE_AUTO_DURATION, HTI_WINDOW_MODE_AUTO_TARGET):
        raise AnalysisParameterError(
            "window_mode must be manual, auto_by_excerpt_duration, or auto_by_target_windows; "
            f"got {p.get('window_mode')!r}."
        )
    epol = str(p.get("edge_policy", HTI_EDGE_MARK)).strip()
    if epol not in (HTI_EDGE_INCLUDE, HTI_EDGE_DROP, HTI_EDGE_MARK):
        raise AnalysisParameterError(
            f"edge_policy must be include_partial_windows, drop_partial_windows, or mark_partial_windows; "
            f"got {p.get('edge_policy')!r}."
        )

    ts_in = _float_field(p, "time_step", default=cast(float, DEFAULT_HTI_PARAMS["time_step"]))
    ws_in = _float_field(p, "window_size", default=cast(float, DEFAULT_HTI_PARAMS["window_size"]))
    if mode == HTI_WINDOW_MODE_MANUAL:
        _req_positive("time_step", ts_in)
        _req_positive("window_size", ws_in)
    else:
        _req_finite_nonneg("time_step", ts_in)
        _req_finite_nonneg("window_size", ws_in)

    min_w = _float_field(p, "min_window_size", default=cast(float, DEFAULT_HTI_PARAMS["min_window_size"]))
    max_w = _float_field(p, "max_window_size", default=cast(float, DEFAULT_HTI_PARAMS["max_window_size"]))
    min_ts = _float_field(p, "min_time_step", default=cast(float, DEFAULT_HTI_PARAMS["min_time_step"]))
    max_ts = _float_field(p, "max_time_step", default=cast(float, DEFAULT_HTI_PARAMS["max_time_step"]))
    if min_w <= 0.0 or max_w <= 0.0 or min_ts <= 0.0 or max_ts <= 0.0:
        raise AnalysisParameterError("min/max window size and min/max time step must be positive.")
    if max_w + 1e-12 < min_w or max_ts + 1e-12 < min_ts:
        raise AnalysisParameterError(
            "max_window_size must be >= min_window_size; max_time_step must be >= min_time_step."
        )

    if mode == HTI_WINDOW_MODE_AUTO_DURATION:
        wr = _float_field(p, "window_ratio", default=cast(float, DEFAULT_HTI_PARAMS["window_ratio"]))
        sr = _float_field(p, "step_ratio", default=cast(float, DEFAULT_HTI_PARAMS["step_ratio"]))
        _req_finite_nonneg("window_ratio", wr)
        _req_finite_nonneg("step_ratio", sr)
    elif mode == HTI_WINDOW_MODE_AUTO_TARGET:
        twc = _float_field(p, "target_window_count", default=cast(float, DEFAULT_HTI_PARAMS["target_window_count"]))
        wsr = _float_field(p, "window_to_step_ratio", default=cast(float, DEFAULT_HTI_PARAMS["window_to_step_ratio"]))
        if twc <= 1e-12:
            raise AnalysisParameterError("target_window_count must be > 0.")
        _req_positive("window_to_step_ratio", wsr)

    prof = str(p.get("register_ref_profile", DEFAULT_REGISTER_REF_PROFILE)).strip().lower()
    if prof not in REGISTER_REF_PROFILE_SEMITONES:
        allowed = ", ".join(sorted(REGISTER_REF_PROFILE_SEMITONES))
        raise AnalysisParameterError(
            f"register_ref_profile must be one of {allowed}; got {p.get('register_ref_profile')!r}."
        )
    ovr = p.get("register_ref_semitones")
    if ovr is not None and str(ovr).strip() != "":
        try:
            rv = float(ovr)
        except (TypeError, ValueError) as e:
            raise AnalysisParameterError(f"register_ref_semitones must be numeric when set; got {ovr!r}.") from e
        if not math.isfinite(rv) or rv <= 0.0:
            raise AnalysisParameterError(f"register_ref_semitones must be finite and > 0 when set; got {rv!r}.")

    wi = _float_field(
        p,
        "weight_instrument_uniformity",
        default=cast(float, DEFAULT_HTI_PARAMS["weight_instrument_uniformity"]),
    )
    wf = _float_field(
        p,
        "weight_family_uniformity",
        default=cast(float, DEFAULT_HTI_PARAMS["weight_family_uniformity"]),
    )
    wt = _float_field(
        p,
        "weight_technique_uniformity",
        default=cast(float, DEFAULT_HTI_PARAMS["weight_technique_uniformity"]),
    )
    wr = _float_field(
        p,
        "weight_register_proximity",
        default=cast(float, DEFAULT_HTI_PARAMS["weight_register_proximity"]),
    )
    for name, wv in (
        ("weight_instrument_uniformity", wi),
        ("weight_family_uniformity", wf),
        ("weight_technique_uniformity", wt),
        ("weight_register_proximity", wr),
    ):
        _req_finite_nonneg(name, wv)
    if wi + wf + wt + wr <= 1e-15:
        raise AnalysisParameterError("H_TI component weights must have a positive sum.")

    from homogeneity_analyser.analyzers.pitch_interpretation import PITCH_INTERPRETATION_MODES

    pim = str(p.get("pitch_interpretation_mode", "musicxml_sounding")).strip()
    if pim not in PITCH_INTERPRETATION_MODES:
        allowed = ", ".join(PITCH_INTERPRETATION_MODES)
        raise AnalysisParameterError(
            f"pitch_interpretation_mode must be one of {allowed}; got {p.get('pitch_interpretation_mode')!r}."
        )

    from homogeneity_analyser.analyzers.harmonic_pitch import HARMONIC_PITCH_POLICIES

    hpp = str(p.get("harmonic_pitch_policy", DEFAULT_HTI_PARAMS["harmonic_pitch_policy"])).strip().lower()
    if hpp not in HARMONIC_PITCH_POLICIES:
        allowed_h = ", ".join(HARMONIC_PITCH_POLICIES)
        raise AnalysisParameterError(
            f"harmonic_pitch_policy must be one of {allowed_h}; got {p.get('harmonic_pitch_policy')!r}."
        )

    sfr = _float_field(
        p,
        "same_subfamily_relief_factor",
        default=cast(float, DEFAULT_HTI_PARAMS["same_subfamily_relief_factor"]),
    )
    _req_unit_interval("same_subfamily_relief_factor", sfr)

    tar = _float_field(
        p,
        "timbral_affinity_relief_factor",
        default=cast(float, DEFAULT_HTI_PARAMS["timbral_affinity_relief_factor"]),
    )
    _req_unit_interval("timbral_affinity_relief_factor", tar)
    tap = str(p.get("timbral_affinity_profile", "conservative")).strip().lower()
    if tap not in ("strict", "conservative", "moderate", "exploratory"):
        raise AnalysisParameterError(
            "timbral_affinity_profile must be one of strict, conservative, moderate, exploratory; "
            f"got {p.get('timbral_affinity_profile')!r}."
        )

    for bk in (
        "dynamic_affinity_enabled",
        "export_affinity_pairs",
        "include_symbolic_blend_potential",
        "include_acoustic_proxy",
        "acoustic_proxy_pairwise_export",
        "acoustic_proxy_include_interval_class",
    ):
        _req_hti_bool_scalar(bk, p.get(bk, DEFAULT_HTI_PARAMS[bk]))

    app = str(p.get("acoustic_proxy_profile", DEFAULT_HTI_PARAMS["acoustic_proxy_profile"])).strip().lower()
    if app not in ("strict", "conservative", "moderate", "exploratory"):
        raise AnalysisParameterError(
            "acoustic_proxy_profile must be one of strict, conservative, moderate, exploratory; "
            f"got {p.get('acoustic_proxy_profile')!r}."
        )
    mep = str(
        p.get("acoustic_proxy_min_evidence_policy", DEFAULT_HTI_PARAMS["acoustic_proxy_min_evidence_policy"])
    ).strip()
    if mep not in ("omit_missing_components", "strict"):
        raise AnalysisParameterError(
            "acoustic_proxy_min_evidence_policy must be omit_missing_components or strict; "
            f"got {p.get('acoustic_proxy_min_evidence_policy')!r}."
        )
    for wk in (
        "source_mechanism_weight",
        "family_similarity_weight",
        "technique_similarity_weight",
        "register_tessitura_weight",
        "dynamic_similarity_weight",
        "attack_similarity_weight",
    ):
        raw = p.get(wk, DEFAULT_HTI_PARAMS.get(wk))
        if raw is None or str(raw).strip() == "":
            continue
        wf = _float_field(p, wk, default=float(raw))
        if wf < 0.0:
            raise AnalysisParameterError(f"{wk} must be >= 0 when set.")


def validate_register_uniformity_params(p: Mapping[str, Any]) -> None:
    """Validate merged register-uniformity parameter dict."""
    _req_positive("time_step", _float_field(p, "time_step"))
    _req_positive("window_size", _float_field(p, "window_size"))


def validate_both_combine_time_window_sigma(time_step: float, window_size: float, sigma: float) -> None:
    """Shared bounds for ``run_both_and_combine``."""
    _req_positive("time_step", float(time_step))
    _req_positive("window_size", float(window_size))
    _req_positive("sigma", float(sigma))


def validate_orchestration_symbolic_params(p: Mapping[str, Any]) -> None:
    """Validate merged H_orchestration_symbolic parameter dict (shares timbral time/window + mode)."""
    tp = {
        "time_step": _float_field(p, "time_step"),
        "window_size": _float_field(p, "window_size"),
        "timbral_config": p.get("timbral_config"),
        "timbral_model_mode": p.get("timbral_model_mode", "legacy"),
    }
    validate_timbral_params(tp)
    from homogeneity_analyser.services.constants import DEFAULT_ORCHESTRATION_SYMBOLIC_PARAMS

    wi = _float_field(
        p,
        "weight_orchestration_instrument",
        default=cast(float, DEFAULT_ORCHESTRATION_SYMBOLIC_PARAMS["weight_orchestration_instrument"]),
    )
    wf = _float_field(
        p,
        "weight_orchestration_family",
        default=cast(float, DEFAULT_ORCHESTRATION_SYMBOLIC_PARAMS["weight_orchestration_family"]),
    )
    wt = _float_field(
        p,
        "weight_orchestration_technique",
        default=cast(float, DEFAULT_ORCHESTRATION_SYMBOLIC_PARAMS["weight_orchestration_technique"]),
    )
    _req_finite_nonneg("weight_orchestration_instrument", wi)
    _req_finite_nonneg("weight_orchestration_family", wf)
    _req_finite_nonneg("weight_orchestration_technique", wt)
    if wi + wf + wt <= 1e-15:
        raise AnalysisParameterError("Orchestration Herfindahl weights must have a positive sum.")


def resolve_notated_fusion_same_family_relief(p: Mapping[str, Any]) -> tuple[float, str, bool]:
    """
    Resolve ``same_family_relief`` from optional override, legacy ``same_family_relief`` key, or named profile.

    Returns ``(relief, canonical_profile, used_numeric_override)`` where ``used_numeric_override`` is True when
    ``same_family_relief_override`` or legacy ``same_family_relief`` supplied a numeric value.
    """
    prof = str(p.get("same_family_relief_profile", DEFAULT_SAME_FAMILY_RELIEF_PROFILE)).strip().lower()
    if prof not in SAME_FAMILY_RELIEF_PROFILES:
        allowed = ", ".join(sorted(SAME_FAMILY_RELIEF_PROFILES))
        raise AnalysisParameterError(f"same_family_relief_profile must be one of: {allowed}; got {prof!r}.")
    ovr_raw = p.get("same_family_relief_override")
    if same_family_relief_override_provided(ovr_raw):
        try:
            r = float(ovr_raw)  # type: ignore[arg-type]
        except (TypeError, ValueError) as e:
            raise AnalysisParameterError(f"same_family_relief_override must be numeric; got {ovr_raw!r}.") from e
        _req_unit_interval("same_family_relief_override", r)
        return float(np.clip(r, 0.0, 1.0)), prof, True
    leg = p.get("same_family_relief")
    if same_family_relief_override_provided(leg):
        try:
            r = float(leg)  # type: ignore[arg-type]
        except (TypeError, ValueError) as e:
            raise AnalysisParameterError(f"same_family_relief must be numeric when provided; got {leg!r}.") from e
        _req_unit_interval("same_family_relief", r)
        return float(np.clip(r, 0.0, 1.0)), prof, True
    return float(SAME_FAMILY_RELIEF_PROFILES[prof]), prof, False


def validate_notated_fusion_potential_params(p: Mapping[str, Any]) -> None:
    """Validate merged ``H_notated_fusion_potential`` parameter dict (shares timbral time/window + mode)."""
    tp = {
        "time_step": _float_field(p, "time_step"),
        "window_size": _float_field(p, "window_size"),
        "timbral_config": p.get("timbral_config"),
        "timbral_model_mode": p.get("timbral_model_mode", "legacy"),
    }
    validate_timbral_params(tp)
    from homogeneity_analyser.services.constants import DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS

    reg_ref = _float_field(
        p,
        "notated_fusion_register_ref_semitones",
        default=cast(float, DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS["notated_fusion_register_ref_semitones"]),
    )
    _req_positive("notated_fusion_register_ref_semitones", reg_ref)
    relief, _, _ = resolve_notated_fusion_same_family_relief(p)
    _req_unit_interval("same_family_relief", relief)
    wi = _float_field(
        p,
        "weight_notated_fusion_instrument",
        default=cast(float, DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS["weight_notated_fusion_instrument"]),
    )
    wf = _float_field(
        p,
        "weight_notated_fusion_family",
        default=cast(float, DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS["weight_notated_fusion_family"]),
    )
    wt = _float_field(
        p,
        "weight_notated_fusion_technique",
        default=cast(float, DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS["weight_notated_fusion_technique"]),
    )
    wr = _float_field(
        p,
        "weight_notated_fusion_register",
        default=cast(float, DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS["weight_notated_fusion_register"]),
    )
    _req_finite_nonneg("weight_notated_fusion_instrument", wi)
    _req_finite_nonneg("weight_notated_fusion_family", wf)
    _req_finite_nonneg("weight_notated_fusion_technique", wt)
    _req_finite_nonneg("weight_notated_fusion_register", wr)
    if wi + wf + wt + wr <= 1e-15:
        raise AnalysisParameterError("H_notated_fusion_potential weights must have a positive sum.")
    wd = _float_field(
        p,
        "weight_notated_fusion_dynamic",
        default=cast(float, DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS["weight_notated_fusion_dynamic"]),
    )
    _req_unit_interval("weight_notated_fusion_dynamic", wd)


def validate_fusion_acoustic_heuristic_params(p: Mapping[str, Any]) -> None:
    """Validate merged ``H_fusion_acoustic_heuristic`` parameter dict (shares timbral time/window + mode)."""
    tp = {
        "time_step": _float_field(p, "time_step"),
        "window_size": _float_field(p, "window_size"),
        "timbral_config": p.get("timbral_config"),
        "timbral_model_mode": p.get("timbral_model_mode", "legacy"),
    }
    validate_timbral_params(tp)
    from homogeneity_analyser.services.constants import DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS

    wp = _float_field(
        p,
        "weight_fusion_profile",
        default=cast(float, DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS["weight_fusion_profile"]),
    )
    ws = _float_field(
        p,
        "weight_fusion_spectral",
        default=cast(float, DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS["weight_fusion_spectral"]),
    )
    wt = _float_field(
        p,
        "weight_fusion_technique",
        default=cast(float, DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS["weight_fusion_technique"]),
    )
    wr = _float_field(
        p,
        "weight_fusion_register",
        default=cast(float, DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS["weight_fusion_register"]),
    )
    for name, val in (
        ("weight_fusion_profile", wp),
        ("weight_fusion_spectral", ws),
        ("weight_fusion_technique", wt),
        ("weight_fusion_register", wr),
    ):
        _req_finite_nonneg(name, val)
    if wp + ws + wt + wr <= 1e-15:
        raise AnalysisParameterError("Fusion heuristic blend weights must have a positive sum.")
    _nh_def = DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS["fusion_n_harmonics"]
    _nh_default_f = float(_nh_def) if isinstance(_nh_def, int | float) and not isinstance(_nh_def, bool) else 12.0
    nh = int(_float_field(p, "fusion_n_harmonics", default=_nh_default_f))
    if nh < 4 or nh > 32:
        raise AnalysisParameterError("fusion_n_harmonics must be between 4 and 32.")
    rs = _float_field(
        p,
        "fusion_roughness_scale",
        default=cast(float, DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS["fusion_roughness_scale"]),
    )
    _req_finite_nonneg("fusion_roughness_scale", rs)
    fr = _float_field(
        p,
        "fusion_register_ref_span_semitones",
        default=cast(float, DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS["fusion_register_ref_span_semitones"]),
    )
    _req_positive("fusion_register_ref_span_semitones", fr)
    pds = _float_field(
        p,
        "fusion_profile_distance_scale",
        default=cast(float, DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS["fusion_profile_distance_scale"]),
    )
    _req_positive("fusion_profile_distance_scale", pds)


def validate_cluster_params(p: Mapping[str, Any]) -> None:
    """Validate merged H_cluster parameter dict."""
    _req_positive("time_step", _float_field(p, "time_step"))
    _req_positive("window_size", _float_field(p, "window_size"))
    _req_positive("cluster_ref_span", _float_field(p, "cluster_ref_span"))
