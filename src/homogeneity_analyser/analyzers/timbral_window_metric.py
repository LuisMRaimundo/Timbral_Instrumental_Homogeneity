"""H_timbral scalar and diagnostic bundle from per-window feature dicts."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np

from homogeneity_analyser.acoustic_profiles.model_config import (
    build_timbral_window_diagnostics_bundle,
    timbral_float,
)
from homogeneity_analyser.acoustic_profiles.timbral_diag_constants import (
    CROSS_TIMBRAL_SEMANTIC_NAMES,
    GLOBAL_ALWAYS_SEMANTIC_NAMES,
    PAIRWISE_BRANCH_SEMANTIC_NAMES,
    PERCUSSION_REGISTER_BLEND_SEMANTIC_NAMES,
    PERCUSSION_UNPITCHED_REGISTER_PROXY_SEMANTIC_NAMES,
)
from homogeneity_analyser.analyzers.brass_pairwise_timbral import pairwise_brass_homogeneity
from homogeneity_analyser.analyzers.clarinet_pairwise_timbral import pairwise_clarinet_homogeneity
from homogeneity_analyser.analyzers.double_reed_pairwise_timbral import pairwise_double_reed_homogeneity
from homogeneity_analyser.analyzers.flute_pairwise_timbral import pairwise_flute_homogeneity
from homogeneity_analyser.analyzers.percussion_pairwise_timbral import (
    pairwise_percussion_homogeneity,
    unpitched_percussion_register_proxy,
)
from homogeneity_analyser.analyzers.saxophone_pairwise_timbral import pairwise_saxophone_homogeneity
from homogeneity_analyser.analyzers.string_pairwise_timbral import pairwise_string_homogeneity
from homogeneity_analyser.analyzers.technique_state import timbral_state_concentration_from_distribution
from homogeneity_analyser.analyzers.timbre_cross_relations import verified_cross_timbral_boost
from homogeneity_analyser.models.timbral_semantics import (
    TimbralModelMode,
    assert_active_timbral_model_mode,
    timbral_model_metadata_for_diagnostics,
)


def _numeric_feature_or(features: Mapping[str, Any], key: str, fallback: float) -> float:
    """Return ``features[key]`` as float when it is numeric; otherwise ``fallback``."""
    raw = features.get(key)
    if isinstance(raw, bool):
        return fallback
    if isinstance(raw, int | float):
        return float(raw)
    return fallback


_DEFAULT_WEIGHT_INSTRUMENT = timbral_float("timbral_default_weight_instrument")
_DEFAULT_WEIGHT_REGISTER = timbral_float("timbral_default_weight_register")
_DEFAULT_FAMILY_BONUS = timbral_float("timbral_default_family_bonus")
_DEFAULT_REGISTER_REF_SEMITONES = timbral_float("timbral_default_register_ref_semitones")
_REGISTER_GLOBAL_DAMPEN_FOR_PAIRWISE_COVERAGE = timbral_float("timbral_register_global_dampen_pairwise_coverage_max")
_TIMBRAL_PERC_REG_PM_TH = timbral_float("timbral_percussion_register_blend_pm_threshold")
_TIMBRAL_PERC_REG_PUN_TH = timbral_float("timbral_percussion_register_blend_pun_threshold")
_TIMBRAL_PERC_REG_BLEND_MULT = timbral_float("timbral_percussion_register_blend_multiplier")
_TIMBRAL_TECH_CONC_OFF = timbral_float("timbral_technique_component_offset")
_TIMBRAL_TECH_CONC_SCL = timbral_float("timbral_technique_component_concentration_scale")


def _semantic_defaults_from_cfg(cfg: dict[str, Any]) -> set[str]:
    out: set[str] = set()

    def _matches_default(raw: Any, default_val: float, semantic: str) -> None:
        if raw is None or raw == "":
            out.add(semantic)
            return
        try:
            if math.isclose(float(raw), float(default_val), rel_tol=0.0, abs_tol=1e-9):
                out.add(semantic)
        except (TypeError, ValueError):
            pass

    _matches_default(cfg.get("weight_instrument"), _DEFAULT_WEIGHT_INSTRUMENT, "timbral_default_weight_instrument")
    _matches_default(cfg.get("weight_register"), _DEFAULT_WEIGHT_REGISTER, "timbral_default_weight_register")
    _matches_default(cfg.get("family_bonus"), _DEFAULT_FAMILY_BONUS, "timbral_default_family_bonus")
    _matches_default(
        cfg.get("register_ref_semitones"), _DEFAULT_REGISTER_REF_SEMITONES, "timbral_default_register_ref_semitones"
    )
    return out


def _window_diag_semantic_names(
    cfg: dict[str, Any],
    active_pairwise_branches: set[str],
    *,
    register_percussion_blend: bool,
    cross_boost: float,
) -> set[str]:
    used: set[str] = set(GLOBAL_ALWAYS_SEMANTIC_NAMES)
    used |= _semantic_defaults_from_cfg(cfg)
    if register_percussion_blend:
        used |= PERCUSSION_REGISTER_BLEND_SEMANTIC_NAMES
        used |= PERCUSSION_UNPITCHED_REGISTER_PROXY_SEMANTIC_NAMES
    for br in active_pairwise_branches:
        used |= PAIRWISE_BRANCH_SEMANTIC_NAMES.get(br, frozenset())
    if float(cross_boost) > 1e-15:
        used |= CROSS_TIMBRAL_SEMANTIC_NAMES
    return used


def _normalized_instr_register_weights(cfg: dict[str, Any]) -> tuple[float, float]:
    try:
        wi = float(cfg.get("weight_instrument", _DEFAULT_WEIGHT_INSTRUMENT))
    except (TypeError, ValueError):
        wi = _DEFAULT_WEIGHT_INSTRUMENT
    try:
        wr = float(cfg.get("weight_register", _DEFAULT_WEIGHT_REGISTER))
    except (TypeError, ValueError):
        wr = _DEFAULT_WEIGHT_REGISTER
    wi = max(0.0, wi)
    wr = max(0.0, wr)
    s = wi + wr
    if not math.isfinite(s) or s <= 1e-15:
        return _DEFAULT_WEIGHT_INSTRUMENT, _DEFAULT_WEIGHT_REGISTER
    return wi / s, wr / s


def _combine_family_pairwise_homogeneity_detail(
    legacy_instr: float,
    features: dict[str, Any],
    *,
    active_pairwise_branches: set[str] | None = None,
) -> tuple[float, float, float]:
    total_m = float(features.get("total_overlap_mass", 0.0) or 0.0)
    segments: list[tuple[float, float]] = []

    def _add(branch: str, mass_key: str, events_key: str, pair_fn: Callable[[list[dict[str, Any]]], float]) -> None:
        m = float(features.get(mass_key) or 0.0)
        ev = features.get(events_key)
        if m <= 0.0 or not isinstance(ev, list) or len(ev) == 0:
            return
        if len(ev) < 2:
            h_k = float(legacy_instr)
        else:
            h_k = float(pair_fn(ev))
            if active_pairwise_branches is not None:
                active_pairwise_branches.add(branch)
        segments.append((m, h_k))

    _add("string", "string_overlap_mass", "string_events", pairwise_string_homogeneity)
    _add("brass", "brass_overlap_mass", "brass_events", pairwise_brass_homogeneity)
    _add("flute", "flute_overlap_mass", "flute_events", pairwise_flute_homogeneity)
    _add("clarinet", "clarinet_overlap_mass", "clarinet_events", pairwise_clarinet_homogeneity)
    _add("double_reed", "double_reed_overlap_mass", "double_reed_events", pairwise_double_reed_homogeneity)
    _add("saxophone", "saxophone_overlap_mass", "saxophone_events", pairwise_saxophone_homogeneity)
    _add("percussion", "percussion_overlap_mass", "percussion_events", pairwise_percussion_homogeneity)

    if not segments:
        return float(legacy_instr), 0.0, float(legacy_instr)
    sum_m = sum(m for m, _ in segments)
    if sum_m <= 1e-15:
        return float(legacy_instr), 0.0, float(legacy_instr)
    h_bar = sum(m * h for m, h in segments) / sum_m
    f_blend = min(1.0, sum_m / max(total_m, 1e-12))
    h_blended = float((1.0 - f_blend) * legacy_instr + f_blend * h_bar)
    return h_blended, float(f_blend), float(h_bar)


def _combine_family_pairwise_homogeneity(legacy_instr: float, features: dict[str, Any]) -> float:
    h, _, _ = _combine_family_pairwise_homogeneity_detail(legacy_instr, features, active_pairwise_branches=None)
    return h


def _timbral_overlap_mass_distributions(features: dict[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    inst_m: dict[str, float] = defaultdict(float)
    fam_m: dict[str, float] = defaultdict(float)
    for s in features.get("timbral_note_slices") or []:
        if not isinstance(s, dict):
            continue
        ol = float(s.get("overlap_ql", 0.0) or 0.0)
        inst_m[str(s.get("instrument") or "")] += ol
        fam_m[str(s.get("family") or "")] += ol
    inst_out = {k: float(v) for k, v in inst_m.items() if k}
    fam_out = {k: float(v) for k, v in fam_m.items() if k}
    return inst_out, fam_out


def compute_timbral_window_decomposition(
    features: dict[str, Any] | None,
    *,
    timbral_config: dict[str, Any],
    timbral_model_mode: TimbralModelMode | str | None = None,
) -> tuple[float, dict[str, Any]]:
    """Return ``(H_timbral, diagnostics)`` from a timbral window feature dict."""
    cfg = timbral_config
    w_instr, w_reg = _normalized_instr_register_weights(cfg)
    try:
        family_bonus = float(cfg.get("family_bonus", _DEFAULT_FAMILY_BONUS))
    except (TypeError, ValueError):
        family_bonus = _DEFAULT_FAMILY_BONUS
    family_bonus = max(0.0, min(1.0, family_bonus))

    timbral_mode_for_diag: TimbralModelMode = assert_active_timbral_model_mode(timbral_model_mode)

    def _empty_diag(h_val: float) -> dict[str, Any]:
        d: dict[str, Any] = {
            "H_timbral": float(h_val),
            "weight_instrument": float(w_instr),
            "weight_register": float(w_reg),
            "instrument_component": None,
            "instrument_pairwise_component": None,
            "register_component": None,
            "timbral_state_concentration": None,
            "technique_component": None,
            "cross_family_boost": None,
            "legacy_instrument_homogeneity": None,
            "pairwise_blend_weight": None,
            "pairwise_branch_mean": None,
            "family_component": None,
            "n_events": 0,
            "n_notes": 0,
            "n_instruments": 0,
            "n_families": 0,
            "instrument_distribution": {},
            "family_distribution": {},
            "technique_distribution": {},
            "dominant_timbral_state": None,
            "instrument_distribution_concentration": None,
            "family_distribution_concentration": None,
            "technique_only_concentration": None,
            "full_state_concentration": None,
            "legacy_concentration": None,
            "technique_only_distribution": {},
            "technique_state_distribution_full": {},
        }
        d.update(timbral_model_metadata_for_diagnostics(timbral_mode_for_diag))
        d.update(build_timbral_window_diagnostics_bundle(()))
        return d

    if features is None or features["n_notes"] == 0:
        return 0.5, _empty_diag(0.5)

    n_instr = int(features["n_instruments"])
    n_families = int(features["n_families"])
    n_score_events = int(features.get("n_score_events", 0) or 0)
    n_notes = int(features.get("n_notes", 0) or 0)

    if "register_span_pitches" in features:
        reg_arr = features["register_span_pitches"]
        if isinstance(reg_arr, np.ndarray) and reg_arr.size > 0:
            span_semi = float(np.ptp(reg_arr)) if reg_arr.size > 1 else 0.0
        else:
            span_semi = 0.0
    else:
        pitches = features["pitches"]
        span_semi = float(np.ptp(pitches)) if len(pitches) > 1 else 0.0

    try:
        ref_span = float(cfg.get("register_ref_semitones", _DEFAULT_REGISTER_REF_SEMITONES))
    except (TypeError, ValueError):
        ref_span = _DEFAULT_REGISTER_REF_SEMITONES
    if not math.isfinite(ref_span) or ref_span <= 0.0:
        ref_span = _DEFAULT_REGISTER_REF_SEMITONES

    if n_instr == 1:
        legacy_instr = 1.0
    elif n_families == 1:
        legacy_instr = family_bonus
    else:
        legacy_instr = 1.0 / (1.0 + (n_instr - 1))
    family_component: float | None = float(family_bonus) if n_families == 1 and n_instr > 1 else None

    register_component = 1.0 / (1.0 + span_semi / ref_span)

    pm_reg = float(features.get("percussion_overlap_mass", 0.0) or 0.0)
    tot_mass_reg = float(features.get("total_overlap_mass", 0.0) or 0.0)
    pun_reg = float(features.get("percussion_unpitched_overlap_mass", 0.0) or 0.0)
    register_percussion_blend = (
        tot_mass_reg > 1e-9
        and pm_reg / tot_mass_reg >= _TIMBRAL_PERC_REG_PM_TH
        and pun_reg / tot_mass_reg >= _TIMBRAL_PERC_REG_PUN_TH
    )
    if register_percussion_blend:
        pe = features.get("percussion_events") or []
        reg_proxy = unpitched_percussion_register_proxy(pe)
        w_blend = float(
            np.clip(
                (pun_reg / tot_mass_reg) * (pm_reg / tot_mass_reg) * _TIMBRAL_PERC_REG_BLEND_MULT,
                0.0,
                1.0,
            )
        )
        register_component = float((1.0 - w_blend) * register_component + w_blend * reg_proxy)

    specialist_mass_for_register_dampen = sum(
        float(features.get(k, 0.0) or 0.0)
        for k in (
            "string_overlap_mass",
            "brass_overlap_mass",
            "flute_overlap_mass",
            "clarinet_overlap_mass",
            "double_reed_overlap_mass",
            "saxophone_overlap_mass",
        )
    )
    coverage = min(1.0, specialist_mass_for_register_dampen / max(tot_mass_reg, 1e-12))
    register_component *= 1.0 - _REGISTER_GLOBAL_DAMPEN_FOR_PAIRWISE_COVERAGE * coverage

    active_pairwise_branches: set[str] = set()
    instr_pairwise, f_blend, h_bar = _combine_family_pairwise_homogeneity_detail(
        legacy_instr, features, active_pairwise_branches=active_pairwise_branches
    )

    conc_legacy = float(features.get("timbral_state_concentration", 1.0) or 1.0)
    conc_only = float(features.get("technique_only_concentration", conc_legacy) or conc_legacy)
    conc_for_technique_multiplier = conc_legacy if timbral_mode_for_diag == "legacy" else float(conc_only)
    technique_component = float(_TIMBRAL_TECH_CONC_OFF + _TIMBRAL_TECH_CONC_SCL * conc_for_technique_multiplier)
    instr_after_tech = float(np.clip(instr_pairwise * technique_component, 0.0, 1.0))

    slices = features.get("timbral_note_slices")
    cross_boost = verified_cross_timbral_boost(
        slices if isinstance(slices, list) else None,
        float(features.get("total_overlap_mass", 0.0) or 0.0),
    )
    instr_final = float(np.clip(instr_after_tech + cross_boost, 0.0, 1.0))

    h = w_instr * instr_final + w_reg * register_component
    if not math.isfinite(h):
        return 0.5, _empty_diag(0.5)
    h_out = float(max(0.0, min(1.0, h)))

    inst_dist, fam_dist = _timbral_overlap_mass_distributions(features)
    tech_dist = {str(k): float(v) for k, v in (features.get("timbral_state_distribution") or {}).items()}
    dom = features.get("dominant_timbral_state")
    dom_s = str(dom) if dom is not None else None

    diag: dict[str, Any] = {
        "H_timbral": h_out,
        "weight_instrument": float(w_instr),
        "weight_register": float(w_reg),
        "instrument_component": instr_final,
        "instrument_pairwise_component": float(instr_pairwise),
        "register_component": float(register_component),
        "timbral_state_concentration": float(conc_legacy),
        "technique_component": float(technique_component),
        "cross_family_boost": float(cross_boost),
        "legacy_instrument_homogeneity": float(legacy_instr),
        "pairwise_blend_weight": float(f_blend),
        "pairwise_branch_mean": float(h_bar),
        "family_component": family_component,
        "n_events": n_score_events,
        "n_notes": n_notes,
        "n_instruments": n_instr,
        "n_families": n_families,
        "instrument_distribution": inst_dist,
        "family_distribution": fam_dist,
        "technique_distribution": tech_dist,
        "dominant_timbral_state": dom_s,
        "instrument_distribution_concentration": float(
            _numeric_feature_or(
                features,
                "instrument_distribution_concentration",
                timbral_state_concentration_from_distribution({str(k): float(v) for k, v in inst_dist.items()}),
            )
        ),
        "family_distribution_concentration": float(
            _numeric_feature_or(
                features,
                "family_distribution_concentration",
                timbral_state_concentration_from_distribution({str(k): float(v) for k, v in fam_dist.items()}),
            )
        ),
        "technique_only_concentration": float(
            _numeric_feature_or(features, "technique_only_concentration", float(conc_only))
        ),
        "full_state_concentration": float(
            _numeric_feature_or(features, "full_state_concentration", float(conc_legacy))
        ),
        "legacy_concentration": float(conc_legacy),
        "technique_only_distribution": dict(features.get("technique_only_distribution") or {}),
        "technique_state_distribution_full": dict(features.get("technique_state_distribution_full") or {}),
    }
    diag.update(timbral_model_metadata_for_diagnostics(timbral_mode_for_diag))
    diag.update(
        build_timbral_window_diagnostics_bundle(
            _window_diag_semantic_names(
                cfg,
                active_pairwise_branches,
                register_percussion_blend=register_percussion_blend,
                cross_boost=float(cross_boost),
            )
        )
    )
    return h_out, diag


def compute_timbral_window_metric(
    features: dict[str, Any] | None,
    *,
    timbral_config: dict[str, Any],
    timbral_model_mode: TimbralModelMode | str | None = None,
) -> float:
    h, _diag = compute_timbral_window_decomposition(
        features,
        timbral_config=timbral_config,
        timbral_model_mode=timbral_model_mode,
    )
    return h
