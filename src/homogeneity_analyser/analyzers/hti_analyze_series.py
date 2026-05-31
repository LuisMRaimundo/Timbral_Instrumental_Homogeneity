"""Series key registry and row helpers for ``SymbolicTIHomogeneityAnalyzer.analyze_hti``."""

from __future__ import annotations

import math
from typing import Any

from homogeneity_analyser.analyzers.hti_concentration import finite_share_float
from homogeneity_analyser.analyzers.hti_dynamic_conditioning import (
    attach_dynamic_conditioning_for_window,
    pick_dynamic_interpretation_label_subfamily_relieved,
)
from homogeneity_analyser.analyzers.percussion_ontology import PitchStatus, get_percussion_meta
from homogeneity_analyser.analyzers.percussion_pairwise_timbral import is_percussion_family
from homogeneity_analyser.analyzers.symbolic_blend_layers import (
    HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS,
    HTI_SYMBOLIC_BLEND_SERIES_KEYS,
    append_hti_symbolic_blend_series_row,
    compute_attack_compatibility_factor,
    compute_pairwise_interval_blend_factor,
    compute_symbolic_blend_bundle_for_window,
)
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
    HTI_ACOUSTIC_PROXY_SERIES_KEYS,
    acoustic_proxy_series_value,
    append_hti_acoustic_proxy_series_row,
    compute_H_TA_acoustic_contextual,
    compute_timbral_acoustic_affinity,
    disabled_acoustic_proxy_bundle,
    insufficient_window_acoustic_proxy_bundle,
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


def hti_pitch_occurrences_for_symbolic_layers(
    contrib: list[tuple[dict[str, Any], float]],
) -> list[tuple[float, float]]:
    """Pitched (midi, overlap_mass) pairs for optional interval-class diagnostics."""
    pitch_occurrences: list[tuple[float, float]] = []
    for e, ol in contrib:
        fam = str(e.get("family") or "")
        inst_e = str(e.get("instrument") or "")
        ol_f = float(ol)
        for p in e.get("pitches") or []:
            try:
                pf = float(p)
            except (TypeError, ValueError):
                continue
            skip_reg = is_percussion_family(fam) and (
                get_percussion_meta(inst_e).pitch_status == PitchStatus.UNPITCHED
            )
            if not skip_reg:
                pitch_occurrences.append((pf, ol_f))
    return pitch_occurrences


def append_hti_analyze_window_row(
    results: dict[str, list[Any]],
    series_keys: tuple[str, ...],
    analyzer: Any,
    *,
    feats: dict[str, Any] | None,
    t: float,
    geom: dict[str, Any],
    mnum: int | None,
    mode_label: str,
    h: float,
    h_strict: float,
    h_relaxed: float,
    ieff: float,
    r_relief: float,
    aff_full: dict[str, Any],
    acoustic_full: dict[str, Any],
    contrib: list[tuple[dict[str, Any], float]],
    lbl_r: str,
    aw: dict[str, float],
    cmp_class: str,
) -> None:
    """Append one window row to ``analyze_hti`` time-series dicts (empty or populated window)."""
    results["t"].append(float(t))
    results["window_start"].append(geom["window_start"])
    results["window_end"].append(geom["window_end"])
    results["edge_window"].append(bool(geom["edge_window"]))
    results["window_coverage_ratio"].append(float(geom["window_coverage_ratio"]))
    results["effective_window_overlap_duration"].append(float(geom["effective_window_overlap_duration"]))
    results["measure"].append(int(mnum) if mnum is not None else "")
    results["pitch_interpretation_mode"].append(mode_label)
    results["H_TI"].append(h)
    nanf = float("nan")
    if feats is None:
        results["H_TI_core"].append(float("nan"))
        for k in series_keys:
            if k in (
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
            ):
                continue
            if k in (
                "crescendo_active",
                "diminuendo_active",
                "dynamic_divergence_detected",
            ):
                results[k].append(False)
            elif k == "dynamic_interpretation_label":
                results[k].append("insufficient_dynamic_evidence")
            elif k == "dynamic_interpretation_label_subfamily_relieved":
                results[k].append(lbl_r)
            elif k == "same_subfamily_relief_factor":
                results[k].append(float(r_relief))
            elif k == "timbral_affinity_profile":
                results[k].append(str(getattr(analyzer, "timbral_affinity_profile", "conservative")))
            elif k == "timbral_affinity_relief_factor":
                results[k].append(float(getattr(analyzer, "timbral_affinity_relief_factor", 0.0)))
            elif k in ("timbral_affinity_rule_summary", "timbral_affinity_literature_sources"):
                results[k].append("")
            elif k == "timbral_affinity_dynamic_status" or k == "timbral_affinity_evidence_status":
                results[k].append("insufficient")
            elif k == "affinity_dynamic_interpretation_label":
                results[k].append("insufficient_dynamic_evidence_for_affinity_qualifier")
            elif k == "literature_affinity_unverified_rule_blocked":
                results[k].append(False)
            elif k in HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS:
                results[k].append({})
            elif k in HTI_ACOUSTIC_PROXY_SERIES_KEYS:
                results[k].append(
                    acoustic_proxy_series_value(
                        k,
                        insufficient_window_acoustic_proxy_bundle(),
                        nan_value=nanf,
                    )
                )
            elif k in HTI_SYMBOLIC_BLEND_SERIES_KEYS:
                if k == "interval_class_evidence_status":
                    results[k].append("")
                else:
                    results[k].append(nanf)
            elif k == "dynamic_evidence_status":
                results[k].append("insufficient")
            elif k == "dynamic_coverage_status":
                results[k].append("unavailable")
            elif k.endswith("_distribution") or k == "notated_dynamic_level_distribution":
                results[k].append({})
            elif (
                k == "technique_coverage_status"
                or k == "register_coverage_status"
                or k == "pairwise_interval_coverage_status"
            ):
                results[k].append("none")
            elif k == "active_weights":
                results[k].append(aw)
            elif k == "hti_comparability_class":
                results[k].append(cmp_class)
            elif k == "dominant_timbral_state" or k == "dominant_dynamic":
                results[k].append(None)
            elif k in (
                "dominant_instruments",
                "dominant_macrofamilies",
                "dominant_families",
                "dominant_timbral_states",
                "dominant_dynamics",
            ):
                results[k].append([])
            elif k in (
                "dominant_instrument_tie",
                "dominant_macrofamily_tie",
                "dominant_family_tie",
                "dominant_timbral_state_tie",
                "dominant_dynamic_tie",
            ):
                results[k].append(False)
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
                results[k].append(nanf)
            else:
                results[k].append(
                    nanf
                    if k
                    not in (
                        "dominant_instrument",
                        "dominant_family",
                        "dominant_instrumental_subfamily",
                        "dominant_macrofamily",
                    )
                    else ""
                )
        return

    results["H_TI_core"].append(float(feats["H_TI_core"]))
    results["H_TI_strict"].append(float(h_strict))
    results["H_TI_subfamily_relieved"].append(float(h_relaxed))
    results["same_subfamily_relief_factor"].append(float(r_relief))
    results["instrument_effective_uniformity"].append(float(ieff))
    results["instrument_uniformity"].append(float(feats["instrument_uniformity"]))
    results["instrumental_subfamily_uniformity"].append(float(feats["instrumental_subfamily_uniformity"]))
    results["macrofamily_uniformity"].append(float(feats["macrofamily_uniformity"]))
    results["family_uniformity"].append(float(feats["family_uniformity"]))
    tu = feats["technique_uniformity"]
    results["technique_uniformity"].append(float(tu) if math.isfinite(float(tu)) else float("nan"))
    rp = feats["register_proximity"]
    results["register_proximity"].append(float(rp) if math.isfinite(float(rp)) else float("nan"))
    rc = feats["register_compactness"]
    results["register_compactness"].append(float(rc) if math.isfinite(float(rc)) else float("nan"))
    rsp = feats["register_span_proximity"]
    results["register_span_proximity"].append(float(rsp) if math.isfinite(float(rsp)) else float("nan"))
    rsf = feats.get("register_span_factor", rsp)
    results["register_span_factor"].append(float(rsf) if math.isfinite(float(rsf)) else float("nan"))
    pip = feats["pairwise_interval_proximity"]
    results["pairwise_interval_proximity"].append(float(pip) if math.isfinite(float(pip)) else float("nan"))
    rpdf = feats.get("register_pair_distance_factor", pip)
    results["register_pair_distance_factor"].append(float(rpdf) if math.isfinite(float(rpdf)) else float("nan"))
    results["pairwise_interval_coverage_status"].append(str(feats["pairwise_interval_coverage_status"]))
    results["n_instruments"].append(int(feats["n_instruments"]))
    results["n_families"].append(int(feats["n_families"]))
    results["n_macrofamilies"].append(int(feats["n_macrofamilies"]))
    rs = feats["register_span_semitones"]
    results["register_span_semitones"].append(float(rs) if math.isfinite(float(rs)) else float("nan"))
    results["dominant_instrument"].append(str(feats["dominant_instrument"]))
    results["dominant_instruments"].append(list(feats["dominant_instruments"]))
    results["dominant_instrument_tie"].append(bool(feats["dominant_instrument_tie"]))
    results["dominant_instrument_share"].append(finite_share_float(feats["dominant_instrument_share"]))
    results["dominant_instrument_margin"].append(finite_share_float(feats["dominant_instrument_margin"]))
    results["dominant_instrumental_subfamily"].append(str(feats["dominant_instrumental_subfamily"]))
    results["dominant_macrofamily"].append(str(feats["dominant_macrofamily"]))
    results["dominant_macrofamilies"].append(list(feats["dominant_macrofamilies"]))
    results["dominant_macrofamily_tie"].append(bool(feats["dominant_macrofamily_tie"]))
    results["dominant_macrofamily_share"].append(finite_share_float(feats["dominant_macrofamily_share"]))
    results["dominant_macrofamily_margin"].append(finite_share_float(feats["dominant_macrofamily_margin"]))
    results["dominant_family"].append(str(feats["dominant_family"]))
    results["dominant_families"].append(list(feats["dominant_families"]))
    results["dominant_family_tie"].append(bool(feats["dominant_family_tie"]))
    results["dominant_family_share"].append(finite_share_float(feats["dominant_family_share"]))
    results["dominant_family_margin"].append(finite_share_float(feats["dominant_family_margin"]))
    results["dominant_timbral_state"].append(feats.get("dominant_timbral_state"))
    results["dominant_timbral_states"].append(list(feats["dominant_timbral_states"]))
    results["dominant_timbral_state_tie"].append(bool(feats["dominant_timbral_state_tie"]))
    results["dominant_timbral_state_share"].append(finite_share_float(feats["dominant_timbral_state_share"]))
    results["dominant_timbral_state_margin"].append(finite_share_float(feats["dominant_timbral_state_margin"]))
    results["technique_state_distribution"].append(dict(feats["technique_state_distribution"]))
    results["instrument_distribution"].append(dict(feats["instrument_distribution"]))
    results["family_distribution"].append(dict(feats["family_distribution"]))
    results["macrofamily_distribution"].append(dict(feats["macrofamily_distribution"]))
    results["technique_coverage_status"].append(str(feats["technique_coverage_status"]))
    results["register_coverage_status"].append(str(feats["register_coverage_status"]))
    results["active_weights"].append(aw)
    results["hti_comparability_class"].append(cmp_class)
    results["notated_dynamic_level_distribution"].append(dict(feats["notated_dynamic_level_distribution"]))
    results["notated_dynamic_coherence"].append(float(feats["notated_dynamic_coherence"]))
    results["dominant_dynamic"].append(feats.get("dominant_dynamic"))
    results["dominant_dynamics"].append(list(feats.get("dominant_dynamics") or []))
    results["dominant_dynamic_tie"].append(bool(feats.get("dominant_dynamic_tie", False)))
    results["dominant_dynamic_share"].append(finite_share_float(feats.get("dominant_dynamic_share")))
    results["dominant_dynamic_margin"].append(finite_share_float(feats.get("dominant_dynamic_margin")))
    results["dynamic_intensity_ordinal"].append(float(feats["dynamic_intensity_ordinal"]))
    results["dynamic_softness"].append(float(feats["dynamic_softness"]))
    results["dynamic_coverage_status"].append(str(feats["dynamic_coverage_status"]))
    results["crescendo_active"].append(bool(feats["crescendo_active"]))
    results["diminuendo_active"].append(bool(feats["diminuendo_active"]))
    results["dynamic_divergence_detected"].append(bool(feats["dynamic_divergence_detected"]))
    results["soft_blend_potential"].append(float(feats["soft_blend_potential"]))
    results["intra_family_convergence_potential"].append(float(feats["intra_family_convergence_potential"]))
    results["transparent_blend_potential"].append(float(feats["transparent_blend_potential"]))
    results["bright_salience_risk"].append(float(feats["bright_salience_risk"]))
    results["projection_divergence_risk"].append(float(feats["projection_divergence_risk"]))
    results["masked_tonal_mass_risk"].append(float(feats["masked_tonal_mass_risk"]))
    results["same_family_mixed_instrument_mass"].append(float(feats["same_family_mixed_instrument_mass"]))
    results["family_heterogeneity"].append(float(feats["family_heterogeneity"]))
    results["masking_context_weight"].append(float(feats["masking_context_weight"]))
    results["family_specific_projection_weight"].append(float(feats["family_specific_projection_weight"]))
    results["dynamic_interpretation_label"].append(str(feats["dynamic_interpretation_label"]))
    results["dynamic_interpretation_label_subfamily_relieved"].append(str(lbl_r))
    nanx = float("nan")
    results["H_TI_affinity_literature_relieved"].append(
        float(aff_full["H_TI_affinity_literature_relieved"])
        if aff_full and math.isfinite(float(aff_full.get("H_TI_affinity_literature_relieved", nanx)))
        else nanx
    )
    results["timbral_affinity_uniformity"].append(
        float(aff_full["timbral_affinity_uniformity"])
        if aff_full and math.isfinite(float(aff_full.get("timbral_affinity_uniformity", nanx)))
        else nanx
    )
    results["instrument_affinity_effective_uniformity"].append(
        float(aff_full["instrument_affinity_effective_uniformity"])
        if aff_full and math.isfinite(float(aff_full.get("instrument_affinity_effective_uniformity", nanx)))
        else nanx
    )
    results["timbral_affinity_profile"].append(str(aff_full.get("timbral_affinity_profile", "")))
    results["timbral_affinity_relief_factor"].append(
        float(
            aff_full.get(
                "timbral_affinity_relief_factor", getattr(analyzer, "timbral_affinity_relief_factor", 0.0)
            )
        )
    )
    results["timbral_affinity_dynamic_factor"].append(
        float(aff_full["timbral_affinity_dynamic_factor"])
        if aff_full and math.isfinite(float(aff_full.get("timbral_affinity_dynamic_factor", nanx)))
        else nanx
    )
    results["timbral_affinity_dynamic_status"].append(str(aff_full.get("timbral_affinity_dynamic_status", "")))
    results["affinity_dynamic_interpretation_label"].append(
        str(aff_full.get("affinity_dynamic_interpretation_label", ""))
    )
    results["H_TI_affinity_dynamic_conditioned"].append(
        float(aff_full["H_TI_affinity_dynamic_conditioned"])
        if aff_full and math.isfinite(float(aff_full.get("H_TI_affinity_dynamic_conditioned", nanx)))
        else nanx
    )
    results["timbral_affinity_evidence_status"].append(str(aff_full.get("timbral_affinity_evidence_status", "")))
    results["timbral_affinity_rule_summary"].append(str(aff_full.get("timbral_affinity_rule_summary", "")))
    results["timbral_affinity_literature_sources"].append(str(aff_full.get("timbral_affinity_literature_sources", "")))
    results["literature_affinity_unverified_rule_blocked"].append(
        bool(aff_full.get("literature_affinity_unverified_rule_blocked", False)) if aff_full else False
    )
    if getattr(analyzer, "include_symbolic_blend_potential", False) and contrib:
        po_sym = hti_pitch_occurrences_for_symbolic_layers(contrib)
        ivb = compute_pairwise_interval_blend_factor(po_sym)
        atk = compute_attack_compatibility_factor(contrib)
        tau_u = float(aff_full.get("timbral_affinity_uniformity", nanx))
        if not math.isfinite(tau_u):
            tau_u = float("nan")
        sympk = compute_symbolic_blend_bundle_for_window(
            feats,
            contrib,
            po_sym,
            h_ti_core=float(feats["H_TI_core"]),
            timbral_affinity_uniformity=tau_u,
        )
        append_hti_symbolic_blend_series_row(
            results,
            enabled=True,
            ivb=ivb,
            atk=atk,
            sympk=sympk,
            nan_value=nanx,
        )
    else:
        append_hti_symbolic_blend_series_row(
            results,
            enabled=False,
            ivb=None,
            atk=None,
            sympk=None,
            nan_value=nanx,
        )
    if bool(getattr(analyzer, "include_acoustic_proxy", False)) and acoustic_full:
        acb = acoustic_full
    else:
        acb = disabled_acoustic_proxy_bundle()
    append_hti_acoustic_proxy_series_row(results, acb, nan_value=nanx)
    results["dynamic_evidence_status"].append(str(feats["dynamic_evidence_status"]))
