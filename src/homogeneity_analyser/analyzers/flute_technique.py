"""
Symbolic flute-family playing states for **H_timbral** refinement (not audio).

Parses common directions and lyrics; many scores omit technique text. ``unknown`` pairs
moderately with ``ordinario`` in the technique matrix.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_FLUTES

if TYPE_CHECKING:
    from music21.note import GeneralNote

FLUTE_ORDINARIO = "ordinario"
FLUTE_VIBRATO = "vibrato"
FLUTE_BREATHY = "breathy"
FLUTE_FLUTTER = "flutter"
FLUTE_HARMONIC = "harmonic"
FLUTE_WHISTLE = "whistle"
FLUTE_JET_WHISTLE = "jet_whistle"
FLUTE_AIR_KEYS = "air_keys"
FLUTE_UNKNOWN = "unknown"

_ALL = frozenset(
    {
        FLUTE_ORDINARIO,
        FLUTE_VIBRATO,
        FLUTE_BREATHY,
        FLUTE_FLUTTER,
        FLUTE_HARMONIC,
        FLUTE_WHISTLE,
        FLUTE_JET_WHISTLE,
        FLUTE_AIR_KEYS,
        FLUTE_UNKNOWN,
    }
)


def _keyword_flute_technique(blob: str) -> str | None:
    if not blob:
        return None
    if re.search(r"jet\s*whistle", blob):
        return FLUTE_JET_WHISTLE
    if re.search(r"whistle\s*tone|whistle-tone|flageolet|overblow", blob):
        return FLUTE_WHISTLE
    if "harmonic" in blob or "flautando" in blob:
        return FLUTE_HARMONIC
    if re.search(r"flutter|flz\.?|flatter", blob):
        return FLUTE_FLUTTER
    if re.search(r"breath(y|ed)?|airy|aeolian|\bsouffle\b", blob):
        return FLUTE_BREATHY
    if re.search(r"key\s*click|clack|slap|percussive\s*air", blob):
        return FLUTE_AIR_KEYS
    if re.search(r"\bvib(rato)?\b|vibr", blob):
        return FLUTE_VIBRATO
    if re.search(r"normale|ordinario|ord\.|natural", blob):
        return FLUTE_ORDINARIO
    return None


def flute_technique_from_note(n: GeneralNote, *, family: str) -> str:
    """Best-effort flute technique; non-flute families return ``ordinario`` (unused downstream)."""
    if family != FAMILY_FLUTES:
        return FLUTE_ORDINARIO

    from music21 import articulations

    for a in getattr(n, "articulations", None) or []:
        if isinstance(a, articulations.Harmonic):
            return FLUTE_HARMONIC

    blob = notation_text_context_for_note(n)
    kw = _keyword_flute_technique(blob)
    if kw is not None:
        return kw

    if re.search(r"\bord\b|\bopen\b", blob):
        return FLUTE_ORDINARIO

    return FLUTE_UNKNOWN


def is_flute_technique_label(x: str) -> bool:
    return x in _ALL
