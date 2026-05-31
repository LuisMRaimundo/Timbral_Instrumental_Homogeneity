"""Helpers for building symbolic timbral score events (extracted from ``timbral.py``)."""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.analyzers.brass_pairwise_timbral import is_brass_family
from homogeneity_analyser.analyzers.brass_technique import (
    brass_matrix_key_from_technique_state,
    brass_technique_from_note,
)
from homogeneity_analyser.analyzers.clarinet_pairwise_timbral import is_clarinet_family
from homogeneity_analyser.analyzers.clarinet_technique import clarinet_technique_from_note
from homogeneity_analyser.analyzers.double_reed_pairwise_timbral import is_double_reed_family
from homogeneity_analyser.analyzers.double_reed_technique import double_reed_technique_from_note
from homogeneity_analyser.analyzers.flute_pairwise_timbral import is_flute_family
from homogeneity_analyser.analyzers.flute_technique import flute_technique_from_note
from homogeneity_analyser.analyzers.percussion_technique import percussion_technique_from_note
from homogeneity_analyser.analyzers.saxophone_pairwise_timbral import is_saxophone_family
from homogeneity_analyser.analyzers.saxophone_technique import saxophone_technique_from_note
from homogeneity_analyser.analyzers.string_pairwise_timbral import is_bowed_orchestral_string
from homogeneity_analyser.analyzers.string_technique import string_technique_from_note
from homogeneity_analyser.analyzers.symbolic_blend_layers import (
    clarinet_register_zone_from_soundings,
    load_symbolic_blend_conditioning_profile,
)
from homogeneity_analyser.analyzers.technique_state import (
    compute_technique_uniformity_key,
    explicit_technique_audit_label,
    explicit_technique_detected,
    legacy_string_technique_from_state,
    technique_state_id,
    technique_state_to_dict,
)


def note_salient_accent(n: Any) -> bool:
    """True when the note carries a salient accent-class articulation (symbolic, not SPL)."""
    from music21 import articulations

    for a in getattr(n, "articulations", None) or []:
        if isinstance(a, articulations.Accent | articulations.StrongAccent):
            return True
        marc = getattr(articulations, "Marcato", None)
        if marc is not None and isinstance(a, marc):
            return True
    return False


def collect_written_pitches_from_note(
    n: Any,
    *,
    pitch_meta: list[dict[str, Any]] | None,
    is_unpitched: bool,
) -> tuple[list[float], str]:
    """Return ``(written_pitches_ps, unpitched_display)`` for one note-like element."""
    from music21 import chord as m21chord
    from music21 import note as m21note

    written_ps: list[float] = []
    unpitched_display = ""
    if pitch_meta:
        written_ps = [float(m["effective_written_midi"]) for m in pitch_meta]
    elif isinstance(n, m21note.Note):
        written_ps = [float(n.pitch.ps)]
    elif isinstance(n, m21chord.Chord):
        written_ps = [float(p.ps) for p in n.pitches]
    elif is_unpitched:
        try:
            unpitched_display = str(n.displayName())
        except (AttributeError, TypeError, ValueError):
            unpitched_display = "unpitched"
    return written_ps, unpitched_display


def brass_symbolic_blend_tendency_for_instrument(instrument: str, family: str) -> str:
    blend_cfg = load_symbolic_blend_conditioning_profile()
    bb = blend_cfg.get("brass_bright_tendency_instruments") or []
    bm = blend_cfg.get("brass_mellow_tendency_instruments") or []
    bright_b = {str(x).strip().lower() for x in bb}
    mellow_b = {str(x).strip().lower() for x in bm}
    inst_l = str(instrument).strip().lower()
    if not is_brass_family(str(family)):
        return "n/a"
    if inst_l in bright_b:
        return "bright_cylindrical_tendency"
    if inst_l in mellow_b:
        return "conical_mellow_tendency"
    return "brass_unclassified_tendency"


def collect_per_family_technique_fields(
    n: Any,
    st: Any,
    *,
    instrument: str,
    family: str,
) -> dict[str, str]:
    """Family-specific technique label fields attached to each built event."""
    if is_bowed_orchestral_string(str(instrument)):
        tech = legacy_string_technique_from_state(st)
    else:
        tech = string_technique_from_note(n)
    if is_brass_family(str(family)):
        btech = brass_matrix_key_from_technique_state(st)
    else:
        btech = brass_technique_from_note(n, family=family)
    ftech = str(st.primary) if is_flute_family(str(family)) else flute_technique_from_note(n, family=family)
    ctech = str(st.primary) if is_clarinet_family(str(family)) else clarinet_technique_from_note(n, family=family)
    dtech = (
        str(st.primary) if is_double_reed_family(str(family)) else double_reed_technique_from_note(n, family=family)
    )
    saxtech = (
        str(st.primary) if is_saxophone_family(str(family)) else saxophone_technique_from_note(n, family=family)
    )
    perctech = percussion_technique_from_note(n, family=family)
    return {
        "technique": tech,
        "brass_technique": btech,
        "flute_technique": ftech,
        "clarinet_technique": ctech,
        "double_reed_technique": dtech,
        "saxophone_technique": saxtech,
        "percussion_technique": perctech,
    }


def build_timbral_score_event(
    *,
    n: Any,
    part_index: int,
    part: Any,
    ctx: Any,
    instrument: str,
    family: str,
    inst_src: str,
    orch_labels: dict[str, str],
    pits: list[float],
    written_ps: list[float],
    pitch_meta: list[dict[str, Any]] | None,
    is_unpitched: bool,
    unpitched_display: str,
    audit_surf: dict[str, Any],
    st: Any,
    harmonic_pitch_policy: str,
    note_salient_accent: bool,
) -> dict[str, Any]:
    """Assemble one symbolic event dict for ``TimbralHomogeneityAnalyzer._events``."""
    o = float(n.offset)
    d = float(getattr(n, "quarterLength", 0.0))
    ts_dict = technique_state_to_dict(st)
    ts_id = technique_state_id(instrument, family, st)
    tu_key = compute_technique_uniformity_key(instrument, family, st)
    blend_cfg = load_symbolic_blend_conditioning_profile()
    crz = (
        clarinet_register_zone_from_soundings([float(x) for x in pits], blend_cfg)
        if is_clarinet_family(str(family))
        else "n/a"
    )
    tech_fields = collect_per_family_technique_fields(n, st, instrument=instrument, family=family)
    return {
        "offset": o,
        "end": o + d,
        "onset": o,
        "note_end": o + d,
        "duration_ql": d,
        "overlap_ql": d,
        "pitches": pits,
        "written_pitches_ps": written_ps,
        "pitch_tone_metadata": pitch_meta,
        "part_index": int(part_index),
        "part_id": str(getattr(part, "id", "") or ""),
        "part_name": str(getattr(part, "partName", "") or ""),
        "raw_part_name": orch_labels["raw_part_name"],
        "section_label": orch_labels["section_label"],
        "desk_group": orch_labels["desk_group"],
        "part_label_original": orch_labels["part_label_original"],
        "is_unpitched": bool(is_unpitched),
        "unpitched_display": unpitched_display,
        **audit_surf,
        "instrument": instrument,
        "family": family,
        "instrument_source": inst_src,
        **tech_fields,
        "technique_state": ts_dict,
        "technique_state_id": ts_id,
        "technique_uniformity_key": tu_key,
        "explicit_technique": explicit_technique_audit_label(instrument, family, st),
        "explicit_technique_detected": bool(explicit_technique_detected(instrument, family, st)),
        "dynamic_mark": str(ctx.dynamic_mark or ""),
        "hairpin": str(ctx.hairpin or "none"),
        "salient_articulation": bool(note_salient_accent),
        "harmonic_pitch_policy": str(harmonic_pitch_policy),
        "clarinet_register_zone": crz,
        "brass_symbolic_blend_tendency": brass_symbolic_blend_tendency_for_instrument(instrument, family),
    }
