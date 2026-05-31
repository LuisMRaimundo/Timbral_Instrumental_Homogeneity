"""Score → symbolic event list (shared by H_TI and H_timbral infrastructure)."""

from __future__ import annotations

import copy
from typing import Any

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.analyzers.symbolic_instrument_resolve import (
    effective_instrument_for_note,
    part_instrument_fallback,
)
from homogeneity_analyser.analyzers.symbolic_pitch_resolve import (
    note_has_buildable_pitches,
    resolve_note_pitches_for_event,
)
from homogeneity_analyser.analyzers.technique_state import (
    TechniqueStateContext,
    apply_persistent_text,
    direction_element_text,
    iter_timbral_elements,
    merge_note_technique_state,
)
from homogeneity_analyser.analyzers.timbral_event_build import build_timbral_score_event, note_salient_accent
from homogeneity_analyser.taxonomy.instrument_taxonomy import resolve_instrument_taxonomy


def build_symbolic_score_events(
    score: Any,
    *,
    pitch_interpretation_mode: str,
    harmonic_pitch_policy: str,
) -> list[dict[str, Any]]:
    """
    Walk ``score.parts`` and return the canonical symbolic event list for H_TI / H_timbral.

    Instrument taxonomy, pitch interpretation, technique state, and audit surfaces are resolved
    per note; timeline technique context advances on ``direction`` elements only.
    """
    from homogeneity_analyser.services.score_audit import note_symbolic_audit_surface

    events: list[dict[str, Any]] = []
    for part_index, part in enumerate(score.parts):
        fb_raw, _fb_src = part_instrument_fallback(part)
        part_default_canon, part_default_fam, _part_orch = resolve_instrument_taxonomy(str(fb_raw))
        ctx = TechniqueStateContext(family=part_default_fam, instrument=part_default_canon)
        prev_key: tuple[str, str] | None = None
        for _off, _prio, kind, el in iter_timbral_elements(part):
            if kind == "direction":
                from music21 import dynamics as m21dynamics

                if isinstance(el, m21dynamics.Crescendo):
                    ctx.hairpin = "crescendo"
                    continue
                if isinstance(el, m21dynamics.Diminuendo):
                    ctx.hairpin = "diminuendo"
                    continue
                apply_persistent_text(direction_element_text(el), ctx)
                continue
            n = el
            instrument, family, inst_src, orch_labels = effective_instrument_for_note(n, part)
            key = (str(instrument), str(family))
            if prev_key is not None and key != prev_key:
                dm_carry, hp_carry = ctx.dynamic_mark, ctx.hairpin
                ctx = TechniqueStateContext(family=family, instrument=instrument)
                ctx.dynamic_mark, ctx.hairpin = dm_carry, hp_carry
            prev_key = key
            pits, pitch_meta, written_ps, unpitched_display, is_unpitched = resolve_note_pitches_for_event(
                n,
                part,
                pitch_interpretation_mode=pitch_interpretation_mode,
                harmonic_pitch_policy=harmonic_pitch_policy,
                canonical_instrument=str(instrument),
            )
            if not note_has_buildable_pitches(pits, is_unpitched=is_unpitched):
                continue
            audit_surf = note_symbolic_audit_surface(n)
            work = copy.copy(ctx)
            apply_persistent_text(notation_text_context_for_note(n, measure_text="none"), work)
            st = merge_note_technique_state(work, n, instrument=instrument, family=family)
            events.append(
                build_timbral_score_event(
                    n=n,
                    part_index=part_index,
                    part=part,
                    ctx=ctx,
                    instrument=instrument,
                    family=family,
                    inst_src=inst_src,
                    orch_labels=orch_labels,
                    pits=pits,
                    written_ps=written_ps,
                    pitch_meta=pitch_meta,
                    is_unpitched=is_unpitched,
                    unpitched_display=unpitched_display,
                    audit_surf=audit_surf,
                    st=st,
                    harmonic_pitch_policy=str(harmonic_pitch_policy),
                    note_salient_accent=note_salient_accent(n),
                )
            )
    return events
