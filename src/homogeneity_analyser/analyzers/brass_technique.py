"""
Symbolic brass playing states for **H_timbral** refinement (not audio).

Parses common MusicXML / music21 articulations and free-text directions. Many scores omit
mute text; ``unknown`` / ``muted_generic`` fall back to moderate similarity to ``open``.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BRASS

if TYPE_CHECKING:
    from music21.note import GeneralNote

BRASS_OPEN = "open"
BRASS_STRAIGHT = "straight_mute"
BRASS_CUP = "cup_mute"
BRASS_HARMON = "harmon_mute"
BRASS_BUCKET = "bucket_mute"
BRASS_STOPPED = "stopped"
BRASS_HALF_STOPPED = "half_stopped"
BRASS_CUIVRE = "cuivre"
BRASS_FLUTTER = "flutter"
BRASS_MUTED_GENERIC = "muted_generic"
BRASS_UNKNOWN = "unknown"

_ALL = frozenset(
    {
        BRASS_OPEN,
        BRASS_STRAIGHT,
        BRASS_CUP,
        BRASS_HARMON,
        BRASS_BUCKET,
        BRASS_STOPPED,
        BRASS_HALF_STOPPED,
        BRASS_CUIVRE,
        BRASS_FLUTTER,
        BRASS_MUTED_GENERIC,
        BRASS_UNKNOWN,
    }
)


def _keyword_brass_technique(blob: str) -> str | None:
    if not blob:
        return None
    if re.search(
        r"\bcuivr(e|é)s?\b|très\s+cuivr|tres\s+cuivr|\bbrassy\b|\bbrassily\b|\bmetallic"
        r"|\bmetallico\b|\bschmetternd\b|bells?\s+up|bell\s+up|pavillons?\s+en\s+l'air|campana\s+in\s+aria",
        blob,
        re.I,
    ):
        if re.search(r"cuivres\s+bouch|sons?\s+bouch", blob, re.I):
            return BRASS_STOPPED
        return BRASS_CUIVRE
    if re.search(r"flutter|flz\.?|flatter", blob):
        return BRASS_FLUTTER
    if "wah" in blob or "wah-wah" in blob:
        return BRASS_HARMON
    if "harmon" in blob:
        return BRASS_HARMON
    if "bucket" in blob:
        return BRASS_BUCKET
    if re.search(r"\bcup\b.*mute|mute.*\bcup\b", blob) or re.search(r"\bcup\s+mute\b", blob):
        return BRASS_CUP
    if re.search(r"\bstraight\b.*mute|mute.*\bstraight\b|\bst\.?\s*mute\b", blob):
        return BRASS_STRAIGHT
    if re.search(
        r"\bstopped\b|bouch[ée]|gestopft|gestopf|chiuso|stopp|hand stop",
        blob,
        re.I,
    ):
        return BRASS_STOPPED
    if re.search(r"senza\s+sord|open(\s+|$)|ordinario|normale", blob):
        return BRASS_OPEN
    if re.search(r"con\s+sord|muted|mit dampfer|sourdine", blob):
        return BRASS_MUTED_GENERIC
    if "mute" in blob or "sord" in blob:
        return BRASS_MUTED_GENERIC
    return None


def brass_technique_from_note(n: GeneralNote, *, family: str) -> str:
    """Best-effort brass technique; non-brass parts return ``open`` (unused downstream)."""
    if family != FAMILY_BRASS:
        return BRASS_OPEN

    from music21 import articulations

    for a in getattr(n, "articulations", None) or []:
        if isinstance(a, articulations.Stopped):
            return BRASS_STOPPED

    blob = notation_text_context_for_note(n)
    kw = _keyword_brass_technique(blob)
    if kw is not None:
        return kw

    if re.search(r"\bopen\b|\bord\b", blob):
        return BRASS_OPEN

    return BRASS_UNKNOWN


def is_brass_technique_label(x: str) -> bool:
    return x in _ALL


def brass_matrix_key_from_technique_state(st: object) -> str:
    """
    Map a :class:`~homogeneity_analyser.analyzers.technique_state.TechniqueState` to a
    discrete key for ``brass_pairwise_timbral`` similarity (duck-typed to avoid import cycles).
    """
    mute = getattr(st, "mute", "none") or "none"
    prim = getattr(st, "primary", "unknown") or "unknown"
    art = getattr(st, "articulation_effect", "none") or "none"
    if art == "flutter":
        return BRASS_FLUTTER
    if mute == "straight_mute":
        return BRASS_STRAIGHT
    if mute == "cup_mute":
        return BRASS_CUP
    if mute in ("harmon_mute", "harmon_stem_in", "harmon_stem_out"):
        return BRASS_HARMON
    if mute == "bucket_mute":
        return BRASS_BUCKET
    if mute == "muted_generic":
        return BRASS_MUTED_GENERIC
    if prim == "stopped":
        return BRASS_STOPPED
    if prim == "half_stopped":
        return BRASS_STOPPED
    if prim == "cuivre":
        return BRASS_CUIVRE
    if prim == "open":
        return BRASS_OPEN
    return BRASS_UNKNOWN
