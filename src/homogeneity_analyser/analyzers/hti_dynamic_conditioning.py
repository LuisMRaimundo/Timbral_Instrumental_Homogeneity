"""
Literature-informed **notated dynamic conditioning** for H_TI.

This layer **never** modifies ``H_TI_core`` (structural symbolic homogeneity). It adds
interpretive scalars and labels that qualify how written dynamics *might* relate to blend,
projection, and masking narratives — **not** measured acoustic fusion or SPL.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.analyzers.technique_state import compute_technique_uniformity_key_from_event
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OBOES,
    FAMILY_PERCUSSION,
    FAMILY_STRINGS,
)

_EPS = 1e-12

FAMILY_RULES_VERSION = "hti_dynamic_conditioning_v1"

# Canonical instrument keys (taxonomy ``instrument`` field).
_BRIGHT_BRASS_HIGH_PROJECTION: frozenset[str] = frozenset(
    {
        "trumpet",
        "piccolo trumpet",
        "bass trumpet",
        "trombone",
        "alto trombone",
        "bass trombone",
        "contrabass trombone",
    }
)
_MELLOW_OR_CONICAL_BRASS: frozenset[str] = frozenset(
    {
        "flugelhorn",
        "euphonium",
        "tuba",
        "wagner tuba",
    }
)
_INTERMEDIATE_BRASS: frozenset[str] = frozenset(
    {
        "horn",
        "natural horn",
        "cornet",
        "cornett",
    }
)


def _tot_overlap(contrib: list[tuple[dict[str, Any], float]]) -> float:
    return float(sum(max(0.0, float(ol)) for _, ol in contrib))


def _overlap_frac_instruments(contrib: list[tuple[dict[str, Any], float]], inst_set: frozenset[str]) -> float:
    tot = _tot_overlap(contrib)
    if tot <= 1e-15:
        return 0.0
    s = 0.0
    for e, ol in contrib:
        if str(e.get("instrument") or "") in inst_set:
            s += float(ol)
    return float(np.clip(s / tot, 0.0, 1.0))


def _family_overlap_fraction(contrib: list[tuple[dict[str, Any], float]], family: str) -> float:
    tot = _tot_overlap(contrib)
    if tot <= 1e-15:
        return 0.0
    s = 0.0
    for e, ol in contrib:
        if str(e.get("family") or "") == family:
            s += float(ol)
    return float(np.clip(s / tot, 0.0, 1.0))


def same_family_mixed_instrument_mass_from_herfindahl(
    instrument_uniformity: float,
    family_uniformity: float,
) -> float:
    """``max(0, family_uniformity - instrument_uniformity)`` (notation-symbolic layout)."""
    return float(max(0.0, float(family_uniformity) - float(instrument_uniformity)))


def compute_masking_context_weight(
    contrib: list[tuple[dict[str, Any], float]],
    inst_mass: dict[str, float],
    fam_mass: dict[str, float],
    macro_mass: dict[str, float],
    register_span_pitches: list[float],
    span_semi: float,
    dynamic_intensity_ordinal: float,
) -> float:
    """
    Symbolic masking / density proxy: span, brass presence, cross-macrofamily overlap,
    low-register mass, and notated intensity — **not** SPL thresholds.
    """
    tot_ol = float(sum(inst_mass.values()))
    if tot_ol <= 1e-15:
        return 0.0

    span_term = 0.0
    if register_span_pitches and math.isfinite(float(span_semi)):
        span_term = float(min(1.0, max(0.0, float(span_semi) / 48.0)))

    brass_frac = _family_overlap_fraction(contrib, FAMILY_BRASS)
    n_macro = len([k for k, v in macro_mass.items() if float(v) > 1e-12])
    cross = float(min(1.0, max(0.0, (n_macro - 1) / 3.0))) if n_macro >= 2 else 0.0

    low_reg = 0.0
    if register_span_pitches:
        arr = np.asarray(register_span_pitches, dtype=float)
        m = float(np.median(arr))
        if m < 56.0:
            low_reg = float(min(1.0, (56.0 - m) / 28.0))

    di = float(dynamic_intensity_ordinal) if math.isfinite(float(dynamic_intensity_ordinal)) else 0.0
    di_term = 0.32 * di

    w = 0.30 * span_term + 0.26 * brass_frac + 0.20 * cross + 0.16 * low_reg + di_term
    return float(min(1.0, max(0.0, w)))


def compute_family_specific_projection_weight(
    contrib: list[tuple[dict[str, Any], float]],
    inst_mass: dict[str, float],
    dynamic_intensity_ordinal: float,
) -> float:
    """
    Down-weights trumpet-like **sharp** projection narratives when only mellow brass carries ff mass.
    """
    tot = float(sum(inst_mass.values())) or 1.0
    bright = sum(float(inst_mass.get(i, 0.0)) for i in _BRIGHT_BRASS_HIGH_PROJECTION)
    mellow = sum(float(inst_mass.get(i, 0.0)) for i in _MELLOW_OR_CONICAL_BRASS)
    inter = sum(float(inst_mass.get(i, 0.0)) for i in _INTERMEDIATE_BRASS)
    bf, mel, intr = bright / tot, mellow / tot, inter / tot

    di = float(dynamic_intensity_ordinal) if math.isfinite(float(dynamic_intensity_ordinal)) else 0.0
    hi = max(0.0, min(1.0, (di - 0.58) / 0.38))

    w = 0.42 + 0.58 * bf * (0.38 + hi) + 0.22 * intr * hi
    if mel > 0.42 and bf < 0.08 and hi > 0.45:
        w *= 0.62
    elif mel > 0.28 and bf < 0.15 and hi > 0.35:
        w *= 0.78
    if bf < 1e-6 and mel > 0.55 and hi > 0.4:
        w = min(w, 0.70)
    return float(min(1.0, max(0.12, w)))


def _bright_brass_simultaneous_trumpet_trombone(contrib: list[tuple[dict[str, Any], float]]) -> bool:
    has_t, has_tb = False, False
    for e, ol in contrib:
        if ol <= 0:
            continue
        ins = str(e.get("instrument") or "")
        if ins in ("trumpet", "piccolo trumpet", "bass trumpet"):
            has_t = True
        if "trombone" in ins:
            has_tb = True
    return has_t and has_tb


def compute_string_technique_state_mixed(contrib: list[tuple[dict[str, Any], float]]) -> bool:
    """True when string-family overlap mass splits across ≥2 distinct ``technique_state_id`` buckets."""
    mass_by_id: dict[str, float] = defaultdict(float)
    str_mass = 0.0
    for e, ol in contrib:
        if ol <= 1e-15:
            continue
        if str(e.get("family") or "") != FAMILY_STRINGS:
            continue
        str_mass += float(ol)
        tid = str(e.get("technique_uniformity_key") or "").strip()
        if not tid:
            tid = compute_technique_uniformity_key_from_event(e)
        if tid:
            mass_by_id[tid] += float(ol)
    if str_mass <= 1e-12 or len(mass_by_id) < 2:
        return False
    rels = sorted((float(v) / str_mass for v in mass_by_id.values()), reverse=True)
    if len(rels) < 2:
        return False
    return rels[0] >= 0.22 and rels[1] >= 0.18


def _dominant_low_dynamic(dom: str | None, dyn_int: float) -> bool:
    if dom is not None and str(dom).lower() in ("pppp", "ppp", "pp", "p"):
        return True
    return math.isfinite(dyn_int) and float(dyn_int) < 0.34


def _dominant_high_dynamic(dom: str | None, dyn_int: float) -> bool:
    if dom is not None and str(dom).lower() in ("f", "ff", "fff", "ffff"):
        return True
    return math.isfinite(dyn_int) and float(dyn_int) > 0.66


def _dominant_mid_low_dynamic(dom: str | None, dyn_int: float) -> bool:
    if dom is not None and str(dom).lower() in ("mp", "mf"):
        return True
    v = float(dyn_int) if math.isfinite(dyn_int) else 0.5
    return 0.38 <= v <= 0.58


def _resolve_dynamic_evidence_status(feats: dict[str, Any]) -> str:
    perc = float(feats.get("percussion_overlap_fraction") or 0.0)
    if str(feats.get("dynamic_coverage_status") or "") == "unavailable":
        return "insufficient"
    if perc >= 0.88 and float(feats.get("non_percussion_sustained_overlap_fraction") or 0.0) < 0.15:
        return "insufficient"
    if feats.get("double_reed_family_active") and not feats.get("brass_family_active"):
        return "moderate"
    if feats.get("brass_family_active") or feats.get("clarinet_family_active") or feats.get("flute_family_active"):
        return "strong"
    if feats.get("string_family_active"):
        return "strong"
    return "moderate"


def pick_dynamic_interpretation_label(feats: dict[str, Any]) -> str:
    """Single label per window following the product priority list (symbolic only)."""
    cov = str(feats.get("dynamic_coverage_status") or "")
    if cov == "unavailable":
        return "insufficient_dynamic_evidence"

    if feats.get("string_technique_state_mixed"):
        return "string_mixed_technique_heterogeneity"

    di = (
        float(feats["dynamic_intensity_ordinal"])
        if math.isfinite(float(feats.get("dynamic_intensity_ordinal", float("nan"))))
        else float("nan")
    )
    mk = float(feats.get("masking_context_weight") or 0.0)
    mtm = (
        float(feats.get("masked_tonal_mass_risk") or 0.0)
        if math.isfinite(float(feats.get("masked_tonal_mass_risk", float("nan"))))
        else float("nan")
    )
    n_macro = int(feats.get("n_macrofamilies") or 0)
    brass_on = bool(feats.get("brass_family_active"))
    dom = feats.get("dominant_dynamic")
    if (
        n_macro >= 2
        and brass_on
        and math.isfinite(di)
        and di > 0.66
        and mk > 0.44
        and math.isfinite(mtm)
        and mtm > 0.36
    ):
        return "cross_family_masked_tonal_mass_risk"

    pdr = (
        float(feats.get("projection_divergence_risk") or 0.0)
        if math.isfinite(float(feats.get("projection_divergence_risk", float("nan"))))
        else 0.0
    )
    bright_f = float(feats.get("bright_brass_overlap_fraction") or 0.0)
    if brass_on and _dominant_high_dynamic(dom, di) and (pdr > 0.38 or (bright_f > 0.18 and di > 0.72)):
        return "brass_projection_divergence_risk"

    if feats.get("clarinet_family_active") and _dominant_high_dynamic(dom, di):
        return "clarinet_bright_projection_salience"

    tbp = float(feats.get("transparent_blend_potential") or 0.0)
    if (
        n_macro >= 2
        and (_dominant_mid_low_dynamic(dom, di) or _dominant_low_dynamic(dom, di))
        and mk < 0.38
        and tbp > 0.28
    ):
        return "cross_family_transparent_blend_potential"

    sfm = float(feats.get("same_family_mixed_instrument_mass") or 0.0)
    if brass_on and _dominant_low_dynamic(dom, di) and sfm > 0.06:
        return "soft_brass_intra_family_convergence_potential"

    if feats.get("clarinet_family_active") and _dominant_low_dynamic(dom, di):
        return "clarinet_soft_blend_potential"

    if feats.get("flute_family_active") and _dominant_low_dynamic(dom, di):
        return "flute_soft_blend_potential"

    if feats.get("flute_family_active") and _dominant_high_dynamic(dom, di):
        return "flute_moderate_projection_salience"

    if feats.get("double_reed_family_active") and _dominant_low_dynamic(dom, di):
        return "double_reed_soft_blend_potential"

    if feats.get("double_reed_family_active") and _dominant_high_dynamic(dom, di):
        return "double_reed_projection_salience"

    if (
        feats.get("string_family_active")
        and _dominant_low_dynamic(dom, di)
        and not feats.get("string_technique_state_mixed")
    ):
        return "string_sectional_soft_blend"

    if (
        feats.get("string_family_active")
        and _dominant_high_dynamic(dom, di)
        and not feats.get("string_technique_state_mixed")
    ):
        return "string_sectional_mass"

    perc = float(feats.get("percussion_overlap_fraction") or 0.0)
    if perc >= 0.75 and float(feats.get("non_percussion_sustained_overlap_fraction") or 0.0) < 0.2:
        return "percussion_dynamic_salience_insufficient_fusion_evidence"

    return "structural_homogeneity_dynamic_neutral"


def enrich_window_masking_and_family_flags(
    feats: dict[str, Any],
    contrib: list[tuple[dict[str, Any], float]],
    inst_mass: dict[str, float],
    fam_mass: dict[str, float],
    macro_mass: dict[str, float],
    register_span_pitches: list[float],
    span_semi: float,
) -> None:
    """Populate overlap fractions, string-technique mix, and refined ``masking_context_weight``."""
    tot_ol = float(sum(inst_mass.values())) or 1.0
    di_raw = feats.get("dynamic_intensity_ordinal")
    di = float(di_raw) if isinstance(di_raw, int | float) and math.isfinite(float(di_raw)) else float("nan")

    inst_u = float(feats.get("instrument_uniformity") or 0.0)
    fam_u = float(feats.get("family_uniformity") or feats.get("instrumental_subfamily_uniformity") or 0.0)
    feats["same_family_mixed_instrument_mass"] = same_family_mixed_instrument_mass_from_herfindahl(inst_u, fam_u)

    feats["masking_context_weight"] = compute_masking_context_weight(
        contrib,
        inst_mass,
        fam_mass,
        macro_mass,
        register_span_pitches,
        span_semi,
        di if math.isfinite(di) else 0.0,
    )

    feats["string_technique_state_mixed"] = compute_string_technique_state_mixed(contrib)
    feats["brass_overlap_fraction"] = _family_overlap_fraction(contrib, FAMILY_BRASS)
    feats["percussion_overlap_fraction"] = _family_overlap_fraction(contrib, FAMILY_PERCUSSION)
    feats["clarinet_overlap_fraction"] = _family_overlap_fraction(contrib, FAMILY_CLARINETS)
    feats["flute_overlap_fraction"] = _family_overlap_fraction(contrib, FAMILY_FLUTES)
    feats["oboe_overlap_fraction"] = _family_overlap_fraction(contrib, FAMILY_OBOES)
    feats["string_overlap_fraction"] = _family_overlap_fraction(contrib, FAMILY_STRINGS)

    np_sus = 0.0
    for e, ol in contrib:
        fam = str(e.get("family") or "")
        if fam != FAMILY_PERCUSSION and macrofamily_from_instrumental_subfamily(fam) != "percussion":
            np_sus += float(ol)
    feats["non_percussion_sustained_overlap_fraction"] = float(np.clip(np_sus / tot_ol, 0.0, 1.0))

    feats["brass_family_active"] = feats["brass_overlap_fraction"] > 0.08
    feats["clarinet_family_active"] = feats["clarinet_overlap_fraction"] > 0.08
    feats["flute_family_active"] = feats["flute_overlap_fraction"] > 0.08
    feats["double_reed_family_active"] = feats["oboe_overlap_fraction"] > 0.08
    feats["string_family_active"] = feats["string_overlap_fraction"] > 0.08

    feats["bright_brass_overlap_fraction"] = _overlap_frac_instruments(contrib, _BRIGHT_BRASS_HIGH_PROJECTION)
    feats["mellow_brass_overlap_fraction"] = _overlap_frac_instruments(contrib, _MELLOW_OR_CONICAL_BRASS)

    feats["family_specific_projection_weight"] = compute_family_specific_projection_weight(contrib, inst_mass, di)

    if _bright_brass_simultaneous_trumpet_trombone(contrib) and math.isfinite(di) and di > 0.72:
        feats["family_specific_projection_weight"] = float(
            min(1.0, float(feats["family_specific_projection_weight"]) * 1.18)
        )


def apply_notated_dynamic_conditioning(feats: dict[str, Any], h_core: float) -> None:
    """
    Attach ``H_TI_core`` and all interpretive diagnostics. **Does not** alter structural inputs
    used to compute ``h_core``.
    """
    feats["H_TI_core"] = float(h_core)

    ndc_raw = feats.get("notated_dynamic_coherence")
    ndc = float(ndc_raw) if isinstance(ndc_raw, int | float) and math.isfinite(float(ndc_raw)) else float("nan")
    ds_raw = feats.get("dynamic_softness")
    ds = float(ds_raw) if isinstance(ds_raw, int | float) and math.isfinite(float(ds_raw)) else float("nan")
    di_raw = feats.get("dynamic_intensity_ordinal")
    di = float(di_raw) if isinstance(di_raw, int | float) and math.isfinite(float(di_raw)) else float("nan")

    ndc_use = max(_EPS, ndc) if math.isfinite(ndc) else _EPS
    ds_use = max(_EPS, ds) if math.isfinite(ds) else _EPS
    feats["soft_blend_potential"] = float(h_core) * ndc_use * ds_use

    sfm = float(feats.get("same_family_mixed_instrument_mass") or 0.0)
    fspw = float(feats.get("family_specific_projection_weight") or 0.55)
    bright_boost = 1.0
    if _bright_brass_simultaneous_trumpet_trombone(feats.get("_contrib") or []) and math.isfinite(di) and di > 0.70:
        bright_boost = 1.22

    feats["projection_divergence_risk"] = float(di * sfm * fspw * bright_boost) if math.isfinite(di) else float("nan")

    sub_u = float(feats.get("instrumental_subfamily_uniformity") or feats.get("family_uniformity") or 0.0)
    fam_het = float(np.clip(1.0 - sub_u, 0.0, 1.0))
    feats["family_heterogeneity"] = fam_het
    mk = float(feats.get("masking_context_weight") or 0.0)
    feats["masked_tonal_mass_risk"] = float(di * fam_het * mk) if math.isfinite(di) else float("nan")

    brass_frac = float(feats.get("brass_overlap_fraction") or 0.0)
    brass_soft_bonus = 0.45 * brass_frac * ds_use * min(1.0, sfm * 4.0) if math.isfinite(ds_use) else 0.0
    feats["intra_family_convergence_potential"] = (
        float(h_core) * ndc_use * ds_use * max(_EPS, sfm) * (1.0 + brass_soft_bonus)
    )

    n_macro = int(feats.get("n_macrofamilies") or 0)
    cross = max(0.0, min(1.0, (n_macro - 1) / 3.0)) if n_macro >= 2 else 0.0
    soft_cross = (1.0 - mk) * (1.0 - di) if math.isfinite(di) else (1.0 - mk) * 0.5
    feats["transparent_blend_potential"] = float(h_core) * ndc_use * max(0.0, soft_cross) * cross * ds_use

    clar_f = float(feats.get("clarinet_overlap_fraction") or 0.0)
    feats["bright_salience_risk"] = (
        float(di * clar_f * (1.0 - ds_use)) if math.isfinite(di) and math.isfinite(ds_use) else float("nan")
    )

    feats["dynamic_evidence_status"] = _resolve_dynamic_evidence_status(feats)
    feats["dynamic_interpretation_label"] = pick_dynamic_interpretation_label(feats)


def pick_dynamic_interpretation_label_subfamily_relieved(
    feats: dict[str, Any],
    h_relaxed: float,
    instrument_effective_uniformity: float,
    *,
    contrib: list[tuple[dict[str, Any], float]] | None = None,
) -> str:
    """
    Optional **interpretive** dynamic label using ``h_relaxed`` and mixed-instrument mass derived from
    ``instrument_effective_uniformity`` (same formula family as strict SFM, not measured fusion).
    """
    fam_u = float(feats.get("family_uniformity") or feats.get("instrumental_subfamily_uniformity") or 0.0)
    ieff = float(instrument_effective_uniformity)
    sfm_r = same_family_mixed_instrument_mass_from_herfindahl(ieff, fam_u)

    ndc_raw = feats.get("notated_dynamic_coherence")
    ndc = float(ndc_raw) if isinstance(ndc_raw, int | float) and math.isfinite(float(ndc_raw)) else float("nan")
    ds_raw = feats.get("dynamic_softness")
    ds = float(ds_raw) if isinstance(ds_raw, int | float) and math.isfinite(float(ds_raw)) else float("nan")
    di_raw = feats.get("dynamic_intensity_ordinal")
    di = float(di_raw) if isinstance(di_raw, int | float) and math.isfinite(float(di_raw)) else float("nan")

    ndc_use = max(_EPS, ndc) if math.isfinite(ndc) else _EPS
    ds_use = max(_EPS, ds) if math.isfinite(ds) else _EPS
    h_r = float(h_relaxed) if isinstance(h_relaxed, int | float) and math.isfinite(float(h_relaxed)) else float("nan")
    if not math.isfinite(h_r):
        h_r = 0.0

    fspw = float(feats.get("family_specific_projection_weight") or 0.55)
    bright_boost = 1.0
    c_list = contrib if contrib is not None else (feats.get("_contrib") or [])
    if _bright_brass_simultaneous_trumpet_trombone(c_list) and math.isfinite(di) and di > 0.70:
        bright_boost = 1.22
    pdr_r = float(di * sfm_r * fspw * bright_boost) if math.isfinite(di) else float("nan")

    brass_frac = float(feats.get("brass_overlap_fraction") or 0.0)
    brass_soft_bonus = 0.45 * brass_frac * ds_use * min(1.0, sfm_r * 4.0) if math.isfinite(ds_use) else 0.0
    intra_r = float(h_r) * ndc_use * ds_use * max(_EPS, sfm_r) * (1.0 + brass_soft_bonus)

    n_macro = int(feats.get("n_macrofamilies") or 0)
    cross = max(0.0, min(1.0, (n_macro - 1) / 3.0)) if n_macro >= 2 else 0.0
    mk = float(feats.get("masking_context_weight") or 0.0)
    soft_cross = (1.0 - mk) * (1.0 - di) if math.isfinite(di) else (1.0 - mk) * 0.5
    tbp_r = float(h_r) * ndc_use * max(0.0, soft_cross) * cross * ds_use

    nf = dict(feats)
    nf["same_family_mixed_instrument_mass"] = sfm_r
    nf["soft_blend_potential"] = float(h_r) * ndc_use * ds_use
    nf["projection_divergence_risk"] = pdr_r
    nf["intra_family_convergence_potential"] = intra_r
    nf["transparent_blend_potential"] = tbp_r
    return pick_dynamic_interpretation_label(nf)


def attach_dynamic_conditioning_for_window(
    feats: dict[str, Any],
    h_core: float,
    contrib: list[tuple[dict[str, Any], float]],
    inst_mass: dict[str, float],
    fam_mass: dict[str, float],
    macro_mass: dict[str, float],
    register_span_pitches: list[float],
    span_semi: float,
) -> None:
    """Structural enrichment + interpretive layer for one window (``contrib`` kept only for internal boosts)."""
    enrich_window_masking_and_family_flags(
        feats, contrib, inst_mass, fam_mass, macro_mass, register_span_pitches, span_semi
    )
    feats["_contrib"] = contrib
    apply_notated_dynamic_conditioning(feats, h_core)
    feats.pop("_contrib", None)
