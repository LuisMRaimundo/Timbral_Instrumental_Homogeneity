"""Per-window feature dict for the legacy **H_timbral** metric (events → features)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.brass_pairwise_timbral import is_brass_family
from homogeneity_analyser.analyzers.clarinet_pairwise_timbral import is_clarinet_family
from homogeneity_analyser.analyzers.double_reed_pairwise_timbral import is_double_reed_family
from homogeneity_analyser.analyzers.flute_pairwise_timbral import is_flute_family
from homogeneity_analyser.analyzers.hti_window_overlap import is_event_active_in_window as default_is_event_active_in_window
from homogeneity_analyser.analyzers.percussion_ontology import PitchStatus, get_percussion_meta
from homogeneity_analyser.analyzers.percussion_pairwise_timbral import is_percussion_family
from homogeneity_analyser.analyzers.saxophone_pairwise_timbral import is_saxophone_family
from homogeneity_analyser.analyzers.string_pairwise_timbral import is_bowed_orchestral_string
from homogeneity_analyser.analyzers.technique_state import (
    dominant_timbral_state,
    timbral_state_concentration_from_distribution,
)
from homogeneity_analyser.analyzers.timbral_concentration_splits import concentration_bundle_from_timbral_slices


def extract_timbral_window_features(
    events: list[dict[str, Any]],
    window_center: float,
    window_size: float,
    *,
    is_event_active_in_window: Callable[[dict[str, Any], float, float], bool] | None = None,
) -> dict[str, Any] | None:
    """Build the ``extract_timbral_features`` feature dict from symbolic score events."""
    active_fn = is_event_active_in_window if is_event_active_in_window is not None else default_is_event_active_in_window
    t_start = window_center - window_size / 2.0
    t_end = window_center + window_size / 2.0
    active = [e for e in events if active_fn(e, t_start, t_end)]
    if not active:
        return None
    n_score_events = len(active)
    event_overlap_mass = 0.0
    pitches = []
    instruments = set()
    families = set()
    string_events: list[dict[str, Any]] = []
    string_overlap_mass = 0.0
    brass_events: list[dict[str, Any]] = []
    brass_overlap_mass = 0.0
    flute_events: list[dict[str, Any]] = []
    flute_overlap_mass = 0.0
    clarinet_events: list[dict[str, Any]] = []
    clarinet_overlap_mass = 0.0
    double_reed_events: list[dict[str, Any]] = []
    double_reed_overlap_mass = 0.0
    saxophone_events: list[dict[str, Any]] = []
    saxophone_overlap_mass = 0.0
    percussion_events: list[dict[str, Any]] = []
    percussion_overlap_mass = 0.0
    percussion_unpitched_overlap_mass = 0.0
    percussion_pitched_overlap_mass = 0.0
    total_overlap_mass = 0.0
    timbral_note_slices: list[dict[str, Any]] = []
    register_span_pitches: list[float] = []
    state_mass: dict[str, float] = defaultdict(float)
    for e in active:
        ol = max(0.0, min(float(e["end"]), t_end) - max(float(e["offset"]), t_start))
        event_overlap_mass += float(ol)
        inst_e = str(e["instrument"])
        fam_e = str(e["family"])
        for p in e["pitches"]:
            pf = float(p)
            pitches.append(pf)
            total_overlap_mass += ol
            skip_reg = is_percussion_family(fam_e) and (
                get_percussion_meta(inst_e).pitch_status == PitchStatus.UNPITCHED
            )
            if not skip_reg:
                register_span_pitches.append(pf)
            ts_id = str(e.get("technique_state_id") or "")
            ts_raw = e.get("technique_state")
            if ts_id:
                state_mass[ts_id] += float(ol)
            timbral_note_slices.append(
                {
                    "instrument": str(e["instrument"]),
                    "family": str(e["family"]),
                    "instrument_source": str(e.get("instrument_source", "unknown")),
                    "pitch": float(p),
                    "onset": float(e["offset"]),
                    "note_end": float(e["end"]),
                    "overlap_ql": float(ol),
                    "technique_state_id": ts_id,
                    "technique_state": ts_raw if isinstance(ts_raw, dict) else {},
                }
            )
            if is_bowed_orchestral_string(str(e["instrument"])):
                string_events.append(
                    {
                        "instrument": str(e["instrument"]),
                        "pitch": float(p),
                        "technique": str(e["technique"]),
                        "overlap_ql": ol,
                        "technique_state_id": ts_id,
                        "technique_state": ts_raw if isinstance(ts_raw, dict) else {},
                    }
                )
                string_overlap_mass += ol
            if is_brass_family(str(e["family"])):
                brass_events.append(
                    {
                        "instrument": str(e["instrument"]),
                        "pitch": float(p),
                        "technique": str(e.get("brass_technique", "open")),
                        "overlap_ql": ol,
                        "technique_state_id": ts_id,
                        "technique_state": ts_raw if isinstance(ts_raw, dict) else {},
                    }
                )
                brass_overlap_mass += ol
            if is_flute_family(str(e["family"])):
                flute_events.append(
                    {
                        "instrument": str(e["instrument"]),
                        "pitch": float(p),
                        "technique": str(e.get("flute_technique", "ordinario")),
                        "overlap_ql": ol,
                        "technique_state_id": ts_id,
                        "technique_state": ts_raw if isinstance(ts_raw, dict) else {},
                    }
                )
                flute_overlap_mass += ol
            if is_clarinet_family(str(e["family"])):
                clarinet_events.append(
                    {
                        "instrument": str(e["instrument"]),
                        "pitch": float(p),
                        "technique": str(e.get("clarinet_technique", "ordinario")),
                        "overlap_ql": ol,
                        "technique_state_id": ts_id,
                        "technique_state": ts_raw if isinstance(ts_raw, dict) else {},
                    }
                )
                clarinet_overlap_mass += ol
            if is_double_reed_family(str(e["family"])):
                double_reed_events.append(
                    {
                        "instrument": str(e["instrument"]),
                        "family": str(e["family"]),
                        "pitch": float(p),
                        "technique": str(e.get("double_reed_technique", "ordinario")),
                        "overlap_ql": ol,
                        "technique_state_id": ts_id,
                        "technique_state": ts_raw if isinstance(ts_raw, dict) else {},
                    }
                )
                double_reed_overlap_mass += ol
            if is_saxophone_family(str(e["family"])):
                saxophone_events.append(
                    {
                        "instrument": str(e["instrument"]),
                        "pitch": float(p),
                        "technique": str(e.get("saxophone_technique", "ordinario")),
                        "overlap_ql": ol,
                        "technique_state_id": ts_id,
                        "technique_state": ts_raw if isinstance(ts_raw, dict) else {},
                    }
                )
                saxophone_overlap_mass += ol
            if is_percussion_family(str(e["family"])):
                percussion_events.append(
                    {
                        "instrument": str(e["instrument"]),
                        "pitch": float(p),
                        "technique": str(e.get("percussion_technique", "ordinario")),
                        "overlap_ql": ol,
                        "technique_state_id": ts_id,
                        "technique_state": ts_raw if isinstance(ts_raw, dict) else {},
                    }
                )
                percussion_overlap_mass += ol
                pstat = get_percussion_meta(inst_e).pitch_status
                if pstat == PitchStatus.UNPITCHED:
                    percussion_unpitched_overlap_mass += ol
                elif pstat in (PitchStatus.PITCHED, PitchStatus.QUASI_PITCHED):
                    percussion_pitched_overlap_mass += ol
        instruments.add(e["instrument"])
        families.add(e["family"])
    if not pitches:
        return None
    dist = dict(state_mass)
    conc = timbral_state_concentration_from_distribution(dist)
    dom = dominant_timbral_state(dist)
    split = concentration_bundle_from_timbral_slices(timbral_note_slices)
    return {
        "pitches": np.array(pitches, dtype=float),
        "register_span_pitches": np.array(register_span_pitches, dtype=float)
        if register_span_pitches
        else np.array([], dtype=float),
        "instruments": instruments,
        "families": families,
        "n_notes": len(pitches),
        "n_score_events": n_score_events,
        "n_instruments": len(instruments),
        "n_families": len(families),
        "event_overlap_mass": float(event_overlap_mass),
        "pitch_overlap_mass": float(total_overlap_mass),
        "string_events": string_events,
        "string_overlap_mass": string_overlap_mass,
        "brass_events": brass_events,
        "brass_overlap_mass": brass_overlap_mass,
        "flute_events": flute_events,
        "flute_overlap_mass": flute_overlap_mass,
        "clarinet_events": clarinet_events,
        "clarinet_overlap_mass": clarinet_overlap_mass,
        "double_reed_events": double_reed_events,
        "double_reed_overlap_mass": double_reed_overlap_mass,
        "saxophone_events": saxophone_events,
        "saxophone_overlap_mass": saxophone_overlap_mass,
        "percussion_events": percussion_events,
        "percussion_overlap_mass": percussion_overlap_mass,
        "percussion_unpitched_overlap_mass": percussion_unpitched_overlap_mass,
        "percussion_pitched_overlap_mass": percussion_pitched_overlap_mass,
        "total_overlap_mass": total_overlap_mass,
        "timbral_note_slices": timbral_note_slices,
        "timbral_state_distribution": dist,
        "timbral_state_concentration": conc,
        "dominant_timbral_state": dom,
        "instrument_distribution_concentration": float(split["instrument_distribution_concentration"]),
        "family_distribution_concentration": float(split["family_distribution_concentration"]),
        "technique_only_concentration": float(split["technique_only_concentration"]),
        "full_state_concentration": float(split["full_state_concentration"]),
        "legacy_concentration": float(conc),
        "technique_only_distribution": dict(split["technique_only_distribution"]),
        "technique_state_distribution_full": dict(split["technique_state_distribution_full"]),
    }
