"""
Symbolic clarinet-family playing states for **H_timbral** (notation only).

Parses common directions and lyrics; many scores omit technique text. ``unknown`` pairs
moderately with ``ordinario`` in the technique matrix.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_CLARINETS

if TYPE_CHECKING:
    from music21.note import GeneralNote

CLARINET_ORDINARIO = "ordinario"
CLARINET_LIGHT_VIBRATO = "light_vibrato"
CLARINET_FLUTTER = "flutter"
CLARINET_BREATHY = "breathy"
CLARINET_SLAP = "slap"
CLARINET_MULTIPHONIC = "multiphonic"
CLARINET_BISBIGLIANDO = "bisbigliando"
CLARINET_UNKNOWN = "unknown"

_ALL = frozenset(
    {
        CLARINET_ORDINARIO,
        CLARINET_LIGHT_VIBRATO,
        CLARINET_FLUTTER,
        CLARINET_BREATHY,
        CLARINET_SLAP,
        CLARINET_MULTIPHONIC,
        CLARINET_BISBIGLIANDO,
        CLARINET_UNKNOWN,
    }
)


def _keyword_clarinet_technique(blob: str) -> str | None:
    if not blob:
        return None
    if re.search(r"bisbigliando", blob):
        return CLARINET_BISBIGLIANDO
    if re.search(r"multiphonic|multi\s*phonic|double\s*tone|split\s*tone|polyphonic", blob):
        return CLARINET_MULTIPHONIC
    if re.search(r"slap\s*tongue|slapt\.?|schlag\s*zunge|slap\s*tonguing", blob):
        return CLARINET_SLAP
    if re.search(r"flutter|flz\.?|flatter", blob):
        return CLARINET_FLUTTER
    if re.search(r"breath(y|ed)?|airy|aeolian|\bsouffle\b|air\s*rich|air\s*tone", blob):
        return CLARINET_BREATHY
    if re.search(r"senza\s*vib|non\s*vib|ohne\s*vibr", blob):
        return CLARINET_ORDINARIO
    if re.search(r"light\s*vib|vib\s*legg|vibrat(o)?\s*leggero", blob):
        return CLARINET_LIGHT_VIBRATO
    if re.search(r"\bvib(rato)?\b|\bvibr\b", blob):
        return CLARINET_LIGHT_VIBRATO
    if re.search(r"normale|ordinario|ord\.|natural", blob):
        return CLARINET_ORDINARIO
    return None


def clarinet_technique_from_note(n: GeneralNote, *, family: str) -> str:
    """Best-effort clarinet technique; non-clarinet families return ``ordinario`` (unused)."""
    if family != FAMILY_CLARINETS:
        return CLARINET_ORDINARIO

    blob = notation_text_context_for_note(n)
    kw = _keyword_clarinet_technique(blob)
    if kw is not None:
        return kw

    if re.search(r"\bord\b|\bopen\b", blob):
        return CLARINET_ORDINARIO

    return CLARINET_UNKNOWN


def is_clarinet_technique_label(x: str) -> bool:
    return x in _ALL
