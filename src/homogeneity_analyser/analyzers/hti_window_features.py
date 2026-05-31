"""Per-window H_TI feature assembly from pre-built symbolic score events."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from homogeneity_analyser.analyzers.dominant_distribution import dominant_with_ties
from homogeneity_analyser.analyzers.hti_concentration import herfindahl_from_masses
from homogeneity_analyser.analyzers.hti_dynamics import aggregate_notated_dynamics_for_window
from homogeneity_analyser.analyzers.hti_register_compactness import (
    collect_pitched_occurrences_from_contrib,
    compute_register_compactness_fields,
)
from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.analyzers.hti_technique_coverage import resolve_technique_uniformity_and_coverage
from homogeneity_analyser.analyzers.hti_window_overlap import build_window_contrib, event_overlap_ql
from homogeneity_analyser.analyzers.technique_state import compute_technique_uniformity_key_from_event


def extract_hti_window_features(
    events: list[dict[str, Any]],
    *,
    window_center: float,
    window_size: float,
    register_ref_semitones: float,
    is_event_active_in_window: Callable[[dict[str, Any], float, float], bool],
) -> dict[str, Any] | None:
    """
    Build one window's H_TI feature dict from symbolic events (instrument / family / technique / register).

    Returns ``None`` when the window has no positive instrument overlap mass. Private ``__*__`` keys
    hold overlap bookkeeping for optional layers in ``hti_analyze_series.enrich_hti_window_optional_layers``.
    """
    t_start = window_center - window_size / 2.0
    t_end = window_center + window_size / 2.0
    contrib = build_window_contrib(
        events,
        t_start=t_start,
        t_end=t_end,
        is_event_active_in_window=is_event_active_in_window,
    )
    if not contrib:
        return None

    inst_mass: dict[str, float] = defaultdict(float)
    fam_mass: dict[str, float] = defaultdict(float)
    macro_mass: dict[str, float] = defaultdict(float)
    tech_mass: dict[str, float] = defaultdict(float)

    for e, ol in contrib:
        inst = str(e.get("instrument") or "unknown")
        fam = str(e.get("family") or "unknown")
        inst_mass[inst] += ol
        fam_mass[fam] += ol
        macro_mass[macrofamily_from_instrumental_subfamily(fam)] += ol
        tuk = compute_technique_uniformity_key_from_event(e)
        if tuk:
            tech_mass[tuk] += ol

    tot_inst = float(sum(inst_mass.values()))
    if tot_inst <= 1e-15:
        return None

    instrument_uniformity = herfindahl_from_masses(dict(inst_mass))
    instrumental_subfamily_uniformity = herfindahl_from_masses(dict(fam_mass))
    macrofamily_uniformity = herfindahl_from_masses(dict(macro_mass))

    technique_uniformity, technique_coverage_status = resolve_technique_uniformity_and_coverage(
        dict(tech_mass), contrib
    )

    ref = float(register_ref_semitones)
    if not math.isfinite(ref) or ref <= 0.0:
        ref = 7.0
    register_span_pitches, pitch_occurrences = collect_pitched_occurrences_from_contrib(contrib)
    reg_bundle = compute_register_compactness_fields(pitch_occurrences, ref)
    span_semi = float(reg_bundle["register_span_semitones"])
    register_span_proximity = float(reg_bundle["register_span_proximity"])
    register_span_factor = float(reg_bundle.get("register_span_factor", register_span_proximity))
    pairwise_interval_proximity = float(reg_bundle["pairwise_interval_proximity"])
    register_pair_distance_factor = float(
        reg_bundle.get("register_pair_distance_factor", pairwise_interval_proximity)
    )
    pairwise_interval_coverage_status = str(reg_bundle["pairwise_interval_coverage_status"])
    register_compactness = float(reg_bundle["register_compactness"])
    register_proximity = float(reg_bundle["register_proximity"])
    register_coverage_status = str(reg_bundle["register_coverage_status"])

    inst_share = {k: float(v) / tot_inst for k, v in inst_mass.items()}
    fam_tot = float(sum(fam_mass.values())) or 1.0
    fam_share = {k: float(v) / fam_tot for k, v in fam_mass.items()}
    macro_tot = float(sum(macro_mass.values())) or 1.0
    macro_share = {k: float(v) / macro_tot for k, v in macro_mass.items()}
    tech_tot = float(sum(tech_mass.values())) or 1.0
    tech_share = {k: float(v) / tech_tot for k, v in tech_mass.items()} if tech_mass else {}

    d_inst = dominant_with_ties(dict(inst_share))
    d_fam = dominant_with_ties(dict(fam_share))
    d_macro = dominant_with_ties(dict(macro_share))
    d_tech = dominant_with_ties(dict(tech_share)) if tech_share else dominant_with_ties({})
    dom_inst = str(d_inst["dominant_primary"] or "")
    dom_fam = str(d_fam["dominant_primary"] or "")
    dom_macro = str(d_macro["dominant_primary"] or "")
    dom_ts = d_tech["dominant_primary"]

    ev_only = [e for e, _ol in contrib]
    dyn = aggregate_notated_dynamics_for_window(ev_only, event_overlap_ql, t_start, t_end)

    return {
        "instrument_uniformity": instrument_uniformity,
        "instrumental_subfamily_uniformity": instrumental_subfamily_uniformity,
        "family_uniformity": instrumental_subfamily_uniformity,
        "macrofamily_uniformity": macrofamily_uniformity,
        "technique_uniformity": technique_uniformity,
        "register_proximity": register_proximity,
        "register_compactness": register_compactness,
        "register_span_proximity": register_span_proximity,
        "register_span_factor": register_span_factor,
        "pairwise_interval_proximity": pairwise_interval_proximity,
        "register_pair_distance_factor": register_pair_distance_factor,
        "pairwise_interval_coverage_status": pairwise_interval_coverage_status,
        "register_span_semitones": span_semi,
        "register_coverage_status": register_coverage_status,
        "technique_coverage_status": technique_coverage_status,
        "n_instruments": len(inst_mass),
        "n_families": len(fam_mass),
        "n_macrofamilies": len(macro_mass),
        "dominant_instrument": dom_inst,
        "dominant_instruments": list(d_inst["dominant_all"]),
        "dominant_instrument_tie": bool(d_inst["tie"]),
        "dominant_instrument_share": d_inst["max_share"],
        "dominant_instrument_margin": d_inst["margin_to_second"],
        "dominant_instrumental_subfamily": dom_fam,
        "dominant_macrofamily": dom_macro,
        "dominant_macrofamilies": list(d_macro["dominant_all"]),
        "dominant_macrofamily_tie": bool(d_macro["tie"]),
        "dominant_macrofamily_share": d_macro["max_share"],
        "dominant_macrofamily_margin": d_macro["margin_to_second"],
        "dominant_family": dom_fam,
        "dominant_families": list(d_fam["dominant_all"]),
        "dominant_family_tie": bool(d_fam["tie"]),
        "dominant_family_share": d_fam["max_share"],
        "dominant_family_margin": d_fam["margin_to_second"],
        "dominant_timbral_state": dom_ts,
        "dominant_timbral_states": list(d_tech["dominant_all"]),
        "dominant_timbral_state_tie": bool(d_tech["tie"]),
        "dominant_timbral_state_share": d_tech["max_share"],
        "dominant_timbral_state_margin": d_tech["margin_to_second"],
        "instrument_distribution": dict(inst_share),
        "instrumental_subfamily_distribution": dict(fam_share),
        "family_distribution": dict(fam_share),
        "macrofamily_distribution": dict(macro_share),
        "technique_state_distribution": dict(tech_share),
        **dyn,
        "__contrib__": contrib,
        "__inst_mass__": dict(inst_mass),
        "__fam_mass__": dict(fam_mass),
        "__macro_mass__": dict(macro_mass),
        "__register_pitches__": list(register_span_pitches),
        "__span_semi__": float(span_semi) if math.isfinite(float(span_semi)) else float("nan"),
    }
