"""Sounding and written pitch resolution for symbolic score events."""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.analyzers.pitch_interpretation import interpret_note_sounding_pitch_ps_list
from homogeneity_analyser.analyzers.timbral_event_build import collect_written_pitches_from_note
from homogeneity_analyser.analyzers.timbral_sounding_pitch import _note_or_part_transposition


def resolve_note_pitches_for_event(
    n: Any,
    part: Any,
    *,
    pitch_interpretation_mode: str,
    harmonic_pitch_policy: str,
    canonical_instrument: str,
) -> tuple[list[float], list[dict[str, Any]] | None, list[float], str, bool]:
    """
    Resolve concert sounding pitches and written-pitch metadata for one note-like element.

    Returns ``(sounding_pitches, pitch_meta, written_pitches_ps, unpitched_display, is_unpitched)``.
    """
    pits, pitch_meta = interpret_note_sounding_pitch_ps_list(
        n,
        part,
        pitch_interpretation_mode,
        trans_resolver=_note_or_part_transposition,
        canonical_instrument=str(canonical_instrument),
        harmonic_pitch_policy=harmonic_pitch_policy,
    )
    from music21 import note as m21note

    is_unpitched = isinstance(n, m21note.Unpitched)
    written_ps, unpitched_display = collect_written_pitches_from_note(
        n,
        pitch_meta=pitch_meta,
        is_unpitched=is_unpitched,
    )
    return pits, pitch_meta, written_ps, unpitched_display, is_unpitched


def note_has_buildable_pitches(
    sounding_pitches: list[float],
    *,
    is_unpitched: bool,
) -> bool:
    """True when the note should produce a symbolic event (unpitched or at least one sounding pitch)."""
    if sounding_pitches:
        return True
    return bool(is_unpitched)
