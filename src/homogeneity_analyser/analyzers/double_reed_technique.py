"""
Light symbolic double-reed playing states for **H_timbral** (notation only).

Secondary to subtype and register. Non–double-reed families return ``ordinario`` (unused).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BASSOONS, FAMILY_OBOES

if TYPE_CHECKING:
    from music21.note import GeneralNote

DR_ORDINARIO = "ordinario"
DR_FLUTTER = "flutter"
DR_MULTIPHONIC = "multiphonic"
DR_BISBIGLIANDO = "bisbigliando"
DR_BREATHY = "breathy"
DR_UNKNOWN = "unknown"

_ALL = frozenset({DR_ORDINARIO, DR_FLUTTER, DR_MULTIPHONIC, DR_BISBIGLIANDO, DR_BREATHY, DR_UNKNOWN})


def double_reed_technique_from_note(n: GeneralNote, *, family: str) -> str:
    if family not in (FAMILY_OBOES, FAMILY_BASSOONS):
        return DR_ORDINARIO

    blob = notation_text_context_for_note(n)
    if re.search(r"bisbigliando", blob):
        return DR_BISBIGLIANDO
    if re.search(r"multiphonic|multi\s*phonic|double\s*tone|split\s*tone", blob):
        return DR_MULTIPHONIC
    if re.search(r"flutter|flz\.?|flatter", blob):
        return DR_FLUTTER
    if re.search(r"breath(y|ed)?|airy|covered|voicé|voce|dunkel|dark\s*tone", blob):
        return DR_BREATHY
    if re.search(r"normale|ordinario|ord\.|natural", blob):
        return DR_ORDINARIO
    if re.search(r"\bord\b", blob):
        return DR_ORDINARIO
    return DR_UNKNOWN


def is_double_reed_technique_label(x: str) -> bool:
    return x in _ALL
