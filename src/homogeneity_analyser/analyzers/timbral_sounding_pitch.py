"""
Concert (sounding) MIDI pitch for **timbral** tessitura and register logic.

``music21`` encodes written pitches on transposing parts; the **note-local**
``Instrument.transposition`` (from ``note.getInstrument()`` when available) maps
written → sounding so doublings (e.g. flute → piccolo) use the correct transposition.
Falls back to the part default when the note has only a generic empty ``Instrument``.
Other analyzers (e.g. pitch-class entropy ``H(t)``) are unchanged and still use
whatever representation their own pipelines expect.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from music21.note import GeneralNote


def sounding_pitch_ps_list(note: GeneralNote, part: Any) -> list[float]:
    """
    Return concert MIDI pitch-space values for each sounding pitch of ``note``.

    ``part`` must be the ``music21.stream.Part`` containing ``note`` so the correct
    instrument (and transposition) can be resolved.
    """
    from music21 import chord
    from music21 import note as m21note

    trans = _note_or_part_transposition(note, part)
    if isinstance(note, m21note.Note):
        return [_transpose_pitch_ps(note.pitch, trans)]
    if isinstance(note, chord.Chord):
        return [_transpose_pitch_ps(p, trans) for p in note.pitches]
    return []


def _note_or_part_transposition(note: Any, part: Any) -> Any:
    """
    Prefer transposition from ``note.getInstrument()`` (reflects mid-part instrument changes).
    If music21 attached only the generic empty ``instrument.Instrument``, fall back to the part.
    """
    try:
        gf = getattr(note, "getInstrument", None)
        if callable(gf):
            ins = gf()
            if ins is not None:
                t = getattr(ins, "transposition", None)
                if t is not None:
                    return t
                if ins.__class__.__name__ == "Instrument":
                    return _part_transposition(part)
                return None
    except (AttributeError, TypeError, ValueError):
        pass
    return _part_transposition(part)


def _part_transposition(part: Any) -> Any:
    try:
        ins = part.getInstrument(returnDefault=True)
    except (AttributeError, TypeError, ValueError):
        return None
    if ins is None:
        return None
    return getattr(ins, "transposition", None)


def _transpose_pitch_ps(pitch: Any, trans: Any) -> float:
    if trans is None:
        return float(pitch.ps)
    try:
        return float(pitch.transpose(trans).ps)
    except (AttributeError, TypeError, ValueError):
        return float(pitch.ps)
