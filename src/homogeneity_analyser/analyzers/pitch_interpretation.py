"""
Pitch interpretation for H_TI / timbral register evidence and symbolic inspection.

Supports MusicXML transposed vs concert-pitch exports, optional stripping of
octave-only transposition components, and microtonal accidentals when ``<alter>``
is missing or zero but accidental text encodes quarter tones.
"""

from __future__ import annotations

import contextlib
import math
import re
from typing import Any, Literal, cast

_MUSIC21_STEP = Literal["C", "D", "E", "F", "G", "A", "B"]
_VALID_MUSIC21_STEPS: frozenset[str] = frozenset({"C", "D", "E", "F", "G", "A", "B"})


def _coerce_music21_step(step: object) -> _MUSIC21_STEP:
    s = str(step) if step is not None else "C"
    return cast(_MUSIC21_STEP, s if s in _VALID_MUSIC21_STEPS else "C")


PITCH_INTERPRETATION_MUSICXML_SOUNDING = "musicxml_sounding"
PITCH_INTERPRETATION_XML_AS_REAL = "xml_pitch_as_real"
PITCH_INTERPRETATION_IGNORE_OCTAVE = "ignore_octave_transpositions_only"
PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS = "xml_pitch_as_real_with_octave_transposers"

PITCH_INTERPRETATION_MODES: tuple[str, ...] = (
    PITCH_INTERPRETATION_MUSICXML_SOUNDING,
    PITCH_INTERPRETATION_XML_AS_REAL,
    PITCH_INTERPRETATION_IGNORE_OCTAVE,
    PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
)

# Written an octave above sounding; in "real pitch + octave transposers" mode apply only this.
_OCTAVE_DOWN_CONCERT_CANONICAL: frozenset[str] = frozenset({"double bass", "contrabassoon"})


def normalize_pitch_interpretation_mode(mode: str | None) -> str:
    s = str(mode or "").strip()
    if s in PITCH_INTERPRETATION_MODES:
        return s
    return PITCH_INTERPRETATION_MUSICXML_SOUNDING


def _accidental_text(pitch: Any) -> str:
    acc = getattr(pitch, "accidental", None)
    if acc is None:
        return ""
    for attr in ("fullName", "name", "unicode"):
        v = getattr(acc, attr, None)
        if v is not None and str(v).strip():
            return str(v).strip()
    return str(acc)


def _norm_acc_key(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = s.replace("–", "-").replace("—", "-")
    return s


# music21 + common MusicXML exporter spellings → alter in semitones
_ACC_NAME_TO_ALTER: dict[str, float] = {
    "natural": 0.0,
    "sharp": 1.0,
    "flat": -1.0,
    "double-sharp": 2.0,
    "double-flat": -2.0,
    "flat-flat": -2.0,
    "half-sharp": 0.5,
    "half-flat": -0.5,
    "one-and-a-half-sharp": 1.5,
    "one-and-a-half-flat": -1.5,
    "quarter-sharp": 0.5,
    "quarter-flat": -0.5,
    "three-quarters-sharp": 1.5,
    "three-quarters-flat": -1.5,
    "triple-sharp": 3.0,
    "triple-flat": -3.0,
}


def _infer_alter_from_accidental_text(text: str) -> tuple[float | None, str]:
    """
    Return (alter, status) where status is ``inferred_from_text``, ``explicit_natural``, or ``unknown``.
    """
    if not text.strip():
        return None, "none"
    nk = _norm_acc_key(text)
    if nk == "natural":
        return 0.0, "explicit_natural"
    if nk in _ACC_NAME_TO_ALTER:
        return float(_ACC_NAME_TO_ALTER[nk]), "inferred_from_text"
    # loose phrases
    if "quarter" in nk and "sharp" in nk:
        return 0.5, "inferred_from_text"
    if "quarter" in nk and "flat" in nk:
        return -0.5, "inferred_from_text"
    if "three" in nk and "quarter" in nk and "sharp" in nk:
        return 1.5, "inferred_from_text"
    if "three" in nk and "quarter" in nk and "flat" in nk:
        return -1.5, "inferred_from_text"
    if "half" in nk and "sharp" in nk:
        return 0.5, "inferred_from_text"
    if "half" in nk and "flat" in nk:
        return -0.5, "inferred_from_text"
    return None, "unknown"


def compute_effective_alter(pitch: Any) -> dict[str, Any]:
    """
    Combine MusicXML / music21 ``alter`` with accidental text for microtonal coverage.

    Does not invent values for unknown accidental text (``microtonal_accidental_status``).
    """
    raw_alter = getattr(pitch, "alter", None)
    acc_text = _accidental_text(pitch)
    raw_xml_alter: float | None = None
    if raw_alter is not None:
        try:
            raw_xml_alter = float(raw_alter)
        except (TypeError, ValueError):
            raw_xml_alter = None

    effective_alter = 0.0
    status = "none"

    if raw_xml_alter is not None and abs(float(raw_xml_alter)) > 1e-12:
        effective_alter = float(raw_xml_alter)
        status = "explicit_alter"
    else:
        inferred, st = _infer_alter_from_accidental_text(acc_text)
        if inferred is not None:
            effective_alter = float(inferred)
            status = st
        elif acc_text.strip():
            effective_alter = float(raw_xml_alter or 0.0)
            status = "unknown"
        else:
            effective_alter = float(raw_xml_alter or 0.0)
            status = "none"

    if status == "inferred_from_text" and abs(float(effective_alter)) < 1e-12:
        status = "explicit_natural"

    frac = abs(float(effective_alter) % 1.0)
    micro_frac = frac > 1e-9 and frac < (1.0 - 1e-9)
    micro_detected = bool(micro_frac)

    return {
        "raw_xml_alter": raw_xml_alter,
        "accidental_text": acc_text,
        "microtonal_accidental_detected": micro_detected,
        "effective_alter": float(effective_alter),
        "microtonal_accidental_status": status,
    }


def transpose_reduced_to_chromatic_band(semitones: float) -> float:
    """Reduce by whole octaves (±12) until in ``(-12, 12)`` (octaves map to 0)."""
    t = float(semitones)
    if not math.isfinite(t):
        return 0.0
    while t >= 12.0:
        t -= 12.0
    while t <= -12.0:
        t += 12.0
    return t


def decompose_transpose_semitones(total_semitones: float) -> tuple[float, float]:
    """
    Split ``total_semitones`` into (chromatic_remainder, octave_semitones) with
    ``chromatic_remainder + octave_semitones == total_semitones`` and
    ``chromatic_remainder`` in ``(-12, 12]`` after folding octaves.
    """
    t = float(total_semitones)
    if not math.isfinite(t):
        return 0.0, 0.0
    chrom = transpose_reduced_to_chromatic_band(t)
    oct_part = float(t - chrom)
    return chrom, oct_part


def _transposition_semitones(trans: Any) -> float:
    if trans is None:
        return 0.0
    try:
        ch = getattr(trans, "chromatic", None)
        if ch is not None:
            return float(ch.semitones)
    except (AttributeError, TypeError, ValueError):
        pass
    try:
        return float(trans.semitones)
    except (AttributeError, TypeError, ValueError):
        return 0.0


def _base_midi_letter_octave(pitch: Any) -> float:
    """
    12-TET MIDI (``pitch.ps``) for the notated **letter + octave only** (natural, no alteration).

    ``effective_written_midi`` = this base + ``effective_alter`` (quarter tones, sharps, flats).
    """
    from music21 import pitch as mp

    st = getattr(pitch, "step", None) or "C"
    oc = getattr(pitch, "octave", None)
    if oc is None:
        oc = getattr(pitch, "implicitOctave", None)
    if oc is None:
        oc = 4
    p0 = mp.Pitch(step=_coerce_music21_step(st), octave=int(oc))
    p0.accidental = None
    with contextlib.suppress(AttributeError, TypeError, ValueError):
        setattr(p0, "alter", 0.0)  # noqa: B010 — music21 stubs treat ``alter`` as read-only; runtime assignment is intentional.
    return float(p0.ps)


def interpret_pitch_tone(
    pitch: Any,
    trans: Any,
    *,
    mode: str,
    canonical_instrument: str | None = None,
) -> dict[str, Any]:
    """
    One chord tone: written/sounding ps, transpose bookkeeping, interpretation mode.

    ``trans`` is the music21 transposition Interval (or None) from timbral resolution.
    ``canonical_instrument`` is the taxonomy id (e.g. ``double bass``, ``contrabassoon``) when known.
    """
    mode_n = normalize_pitch_interpretation_mode(mode)
    alt_bundle = compute_effective_alter(pitch)
    eff_alt = float(alt_bundle["effective_alter"])
    try:
        base_ps = _base_midi_letter_octave(pitch)
    except (AttributeError, TypeError, ValueError):
        base_ps = float(getattr(pitch, "ps", 0.0) or 0.0) - eff_alt
    written_ps = float(base_ps + eff_alt)

    raw_written_ps = float(getattr(pitch, "ps", written_ps))
    t_inst = _transposition_semitones(trans)
    chrom_d, oct_d = decompose_transpose_semitones(t_inst)
    canon = str(canonical_instrument or "").strip().lower()

    sounding_ps: float
    total_applied: float

    if mode_n == PITCH_INTERPRETATION_XML_AS_REAL:
        total_applied = 0.0
        sounding_ps = written_ps
    elif mode_n == PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS:
        total_applied = float(oct_d) if canon in _OCTAVE_DOWN_CONCERT_CANONICAL else 0.0
        sounding_ps = float(written_ps + total_applied)
    elif mode_n == PITCH_INTERPRETATION_IGNORE_OCTAVE:
        total_applied = float(chrom_d)
        sounding_ps = float(written_ps + total_applied)
    else:  # musicxml_sounding
        if trans is None:
            total_applied = 0.0
            sounding_ps = written_ps
        else:
            try:
                from music21 import pitch as mp

                p_eff = mp.Pitch()
                p_eff.ps = float(written_ps)
                sounding_ps = float(p_eff.transpose(trans).ps)
            except (AttributeError, TypeError, ValueError):
                sounding_ps = written_ps
            total_applied = float(sounding_ps - written_ps)

    chrom_a, oct_a = decompose_transpose_semitones(total_applied)

    return {
        **alt_bundle,
        "raw_written_pitch": str(getattr(pitch, "nameWithOctave", "") or ""),
        "raw_written_midi": float(raw_written_ps),
        "effective_written_midi": float(written_ps),
        "effective_sounding_midi": float(sounding_ps),
        "chromatic_transpose_detected": float(chrom_d),
        "octave_transpose_detected": float(oct_d),
        "chromatic_transpose_applied": float(chrom_a),
        "octave_transpose_applied": float(oct_a),
        "total_transpose_applied": float(total_applied),
        "transpose_applied": float(total_applied),
        "pitch_interpretation_mode": mode_n,
    }


def interpret_note_sounding_pitch_ps_list(
    note: Any,
    part: Any,
    mode: str,
    *,
    trans_resolver: Any,
    canonical_instrument: str | None = None,
    harmonic_pitch_policy: str | None = None,
) -> tuple[list[float], list[dict[str, Any]]]:
    """
    Return (sounding_ps_list, per_tone_metadata) for a Note or Chord.

    ``trans_resolver`` is typically ``timbral_sounding_pitch._note_or_part_transposition``.
    """
    from music21 import chord as m21chord
    from music21 import note as m21note

    trans = trans_resolver(note, part)
    mode_n = normalize_pitch_interpretation_mode(mode)
    pits: list[float] = []
    meta: list[dict[str, Any]] = []
    if isinstance(note, m21note.Note):
        m = interpret_pitch_tone(note.pitch, trans, mode=mode_n, canonical_instrument=canonical_instrument)
        pits.append(float(m["effective_sounding_midi"]))
        meta.append(m)
    elif isinstance(note, m21chord.Chord):
        for p in note.pitches:
            m = interpret_pitch_tone(p, trans, mode=mode_n, canonical_instrument=canonical_instrument)
            pits.append(float(m["effective_sounding_midi"]))
            meta.append(m)
    else:
        return [], []

    from homogeneity_analyser.analyzers.harmonic_pitch import finalize_harmonic_pitches_for_note

    finalize_harmonic_pitches_for_note(
        note,
        part,
        mode_n,
        trans_resolver,
        canonical_instrument,
        harmonic_pitch_policy,
        pits,
        meta,
    )
    return pits, meta
