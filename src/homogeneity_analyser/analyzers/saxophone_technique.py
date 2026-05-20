"""
Symbolic saxophone-family production states for **H_timbral** (notation only).

Parses common directions and lyrics; many scores omit extended techniques. ``unknown``
pairs moderately with ``ordinario`` in the technique matrix.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_SAXOPHONES

if TYPE_CHECKING:
    from music21.note import GeneralNote

SAX_ORDINARIO = "ordinario"
SAX_SUBTONE = "subtone"
SAX_GROWL = "growl"
SAX_FLUTTER = "flutter"
SAX_SLAP = "slap"
SAX_BREATHY = "breathy"
SAX_OVERTONE_SPECIAL = "overtone_special"
SAX_UNKNOWN = "unknown"

_ALL = frozenset(
    {
        SAX_ORDINARIO,
        SAX_SUBTONE,
        SAX_GROWL,
        SAX_FLUTTER,
        SAX_SLAP,
        SAX_BREATHY,
        SAX_OVERTONE_SPECIAL,
        SAX_UNKNOWN,
    }
)


def _keyword_sax_technique(blob: str) -> str | None:
    if not blob:
        return None
    if re.search(r"overtone|altissimo\s*effect|special\s*effect|split\s*tone|multiphonic", blob):
        return SAX_OVERTONE_SPECIAL
    if re.search(r"slap\s*tongue|slapt\.?|schlag", blob):
        return SAX_SLAP
    if re.search(r"flutter|flz\.?|flatter", blob):
        return SAX_FLUTTER
    if re.search(r"growl|buzz\s*tone|dirty\s*tone", blob):
        return SAX_GROWL
    if re.search(r"subtone|sub\s*tone|demi\s*jeu|half\s*air", blob):
        return SAX_SUBTONE
    if re.search(r"breath(y|ed)?|airy|open\s*sound|ghost\s*note", blob):
        return SAX_BREATHY
    if re.search(r"normale|ordinario|ord\.|natural", blob):
        return SAX_ORDINARIO
    return None


def saxophone_technique_from_note(n: GeneralNote, *, family: str) -> str:
    """Best-effort saxophone technique; non-sax families return ``ordinario`` (unused)."""
    if family != FAMILY_SAXOPHONES:
        return SAX_ORDINARIO

    blob = notation_text_context_for_note(n)
    kw = _keyword_sax_technique(blob)
    if kw is not None:
        return kw

    if re.search(r"\bord\b", blob):
        return SAX_ORDINARIO

    return SAX_UNKNOWN


def is_saxophone_technique_label(x: str) -> bool:
    return x in _ALL
