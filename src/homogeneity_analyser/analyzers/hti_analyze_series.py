"""Series key registry and row helpers for ``SymbolicTIHomogeneityAnalyzer.analyze_hti``."""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.analyzers.hti_dynamic_conditioning import (
    attach_dynamic_conditioning_for_window,
    pick_dynamic_interpretation_label_subfamily_relieved,
)
from homogeneity_analyser.analyzers.symbolic_blend_layers import HTI_SYMBOLIC_BLEND_SERIES_KEYS
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
    HTI_ACOUSTIC_PROXY_SERIES_KEYS,
    compute_H_TA_acoustic_contextual,
    compute_timbral_acoustic_affinity,
)
from homogeneity_analyser.analyzers.timbral_affinity import (
    compute_timbral_affinity_bundle_for_window,
    finalize_timbral_affinity_dynamic,
)

HTI_ANALYZE_SERIES_KEYS: tuple[str, ...] = (
    "t",
    "window_start",
    "window_end",
    "edge_window",
    "window_coverage_ratio",
    "effective_window_overlap_duration",
    "measure",
    "pitch_interpretation_mode",
    "H_TI",
    "H_TI_core",
    "H_TI_strict",
    "H_TI_subfamily_relieved",
    "same_subfamily_relief_factor",
    "instrument_effective_uniformity",
    "instrument_uniformity",
    "instrumental_subfamily_uniformity",
    "macrofamily_uniformity",
    "family_uniformity",
    "technique_uniformity",
    "register_proximity",
    "register_compactness",
    "register_span_proximity",
    "register_span_factor",
    "pairwise_interval_proximity",
    "register_pair_distance_factor",
    "pairwise_interval_coverage_status",
    "n_instruments",
    "n_families",
    "n_macrofamilies",
    "register_span_semitones",
    "dominant_instrument",
    "dominant_instruments",
    "dominant_instrument_tie",
    "dominant_instrument_share",
    "dominant_instrument_margin",
    "dominant_instrumental_subfamily",
    "dominant_macrofamily",
    "dominant_macrofamilies",
    "dominant_macrofamily_tie",
    "dominant_macrofamily_share",
    "dominant_macrofamily_margin",
    "dominant_family",
    "dominant_families",
    "dominant_family_tie",
    "dominant_family_share",
    "dominant_family_margin",
    "dominant_timbral_state",
    "dominant_timbral_states",
    "dominant_timbral_state_tie",
    "dominant_timbral_state_share",
    "dominant_timbral_state_margin",
    "technique_state_distribution",
    "instrument_distribution",
    "family_distribution",
    "macrofamily_distribution",
    "technique_coverage_status",
    "register_coverage_status",
    "active_weights",
    "hti_comparability_class",
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
    "same_family_mixed_instrument_mass",
    "family_heterogeneity",
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
    "literature_affinity_unverified_rule_blocked",
    *HTI_SYMBOLIC_BLEND_SERIES_KEYS,
    *HTI_ACOUSTIC_PROXY_SERIES_KEYS,
)


def enrich_hti_window_optional_layers(
    analyzer: Any,
    feats: dict[str, Any],
    *,
    h_strict: float,
    h_relaxed: float,
    ieff: float,
    w_instr: float,
    w_fam: float,
    w_tech: float,
    w_reg: float,
    collect_affinity_pairs: bool,
    t: float,
    mnum: int | None,
    pair_accum: list[dict[str, Any]],
    acoustic_pair_accum: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], list[tuple[dict[str, Any], float]], str]:
    """
    Attach dynamic conditioning, timbral affinity, and optional acoustic proxy to ``feats``.

    Mutates ``feats`` (pops private ``__*__`` keys). Returns affinity bundle, acoustic bundle,
    overlap ``contrib`` list, and subfamily-relieved dynamic label.
    """
    contrib_pre = list(feats.get("__contrib__", []))
    aff_base = compute_timbral_affinity_bundle_for_window(
        contrib_pre,
        feats,
        profile=str(getattr(analyzer, "timbral_affinity_profile", "conservative")),
        relief_factor=float(getattr(analyzer, "timbral_affinity_relief_factor", 0.0)),
        instrument_uniformity=float(feats["instrument_uniformity"]),
        compute_h_ti=analyzer.compute_H_TI,
        feats_for_h_ti=feats,
        w_instr=w_instr,
        w_fam=w_fam,
        w_tech=w_tech,
        w_reg=w_reg,
        collect_pairs=collect_affinity_pairs,
    )
    contrib = list(feats.pop("__contrib__", []))
    inst_mass = dict(feats.pop("__inst_mass__", {}))
    fam_mass = dict(feats.pop("__fam_mass__", {}))
    macro_mass = dict(feats.pop("__macro_mass__", {}))
    reg_pitches = list(feats.pop("__register_pitches__", []))
    span_semi_priv = feats.pop("__span_semi__", float("nan"))
    span_semi_use = float(span_semi_priv) if isinstance(span_semi_priv, int | float) else float("nan")
    attach_dynamic_conditioning_for_window(
        feats,
        float(h_strict),
        contrib,
        inst_mass,
        fam_mass,
        macro_mass,
        reg_pitches,
        span_semi_use,
    )
    aff_full = finalize_timbral_affinity_dynamic(
        aff_base,
        feats,
        dynamic_affinity_enabled=bool(getattr(analyzer, "dynamic_affinity_enabled", True)),
    )
    acoustic_full: dict[str, Any] = {}
    if bool(getattr(analyzer, "include_acoustic_proxy", False)):
        acoustic_full = compute_timbral_acoustic_affinity(
            contrib_pre,
            feats,
            profile=str(getattr(analyzer, "acoustic_proxy_profile", "conservative")),
            kernel_weights=getattr(analyzer, "acoustic_proxy_kernel_weights", None),
            include_interval_class=bool(getattr(analyzer, "acoustic_proxy_include_interval_class", False)),
            collect_pairs=bool(getattr(analyzer, "acoustic_proxy_pairwise_export", False))
            or collect_affinity_pairs,
            min_evidence_policy=str(
                getattr(analyzer, "acoustic_proxy_min_evidence_policy", "omit_missing_components")
            ),
        )
        h_ctx = compute_H_TA_acoustic_contextual(acoustic_full, feats)
        acoustic_full["H_TA_acoustic_contextual"] = h_ctx
    prs = aff_full.pop("_pair_rows", [])
    if collect_affinity_pairs:
        mstr = int(mnum) if mnum is not None else ""
        for pr in prs:
            pair_accum.append({**pr, "t_quarterLength": float(t), "measure": mstr})
    if acoustic_full:
        aprs = acoustic_full.pop("_pair_rows", [])
        if bool(getattr(analyzer, "acoustic_proxy_pairwise_export", False)) or collect_affinity_pairs:
            mstr_a = int(mnum) if mnum is not None else ""
            for pr in aprs:
                acoustic_pair_accum.append({**pr, "t_quarterLength": float(t), "measure": mstr_a})
    lbl_r = pick_dynamic_interpretation_label_subfamily_relieved(
        feats, float(h_relaxed), float(ieff), contrib=contrib
    )
    return aff_full, acoustic_full, contrib, lbl_r
