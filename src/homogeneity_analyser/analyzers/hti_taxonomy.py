"""
Macrofamily vs instrumental subfamily (taxonomy row).

The catalogue's ``family`` field (e.g. ``flutes``, ``clarinets``, ``brass``) is an **instrumental
subfamily** — finer than a single "strings vs winds" split, but coarser than canonical instrument.
**Macrofamily** groups those rows for an additional overlap-mass Herfindahl diagnostic.
"""

from __future__ import annotations

from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_KEYBOARD,
    FAMILY_OBOES,
    FAMILY_OTHER,
    FAMILY_PERCUSSION,
    FAMILY_RECORDERS,
    FAMILY_SAXOPHONES,
    FAMILY_STRINGS,
    FAMILY_VOICE,
)

_WOODWIND_SUBFAMILIES: frozenset[str] = frozenset(
    {
        FAMILY_FLUTES,
        FAMILY_RECORDERS,
        FAMILY_OBOES,
        FAMILY_CLARINETS,
        FAMILY_BASSOONS,
        FAMILY_SAXOPHONES,
    }
)


def macrofamily_from_instrumental_subfamily(subfamily: str) -> str:
    """
    Map taxonomy ``family`` (instrumental subfamily) to a coarse macrofamily bucket.

    ``FAMILY_OTHER`` / unknown names map to ``other``.
    """
    s = str(subfamily or "").strip()
    if s == FAMILY_STRINGS:
        return "strings"
    if s in _WOODWIND_SUBFAMILIES:
        return "woodwinds"
    if s == FAMILY_BRASS:
        return "brass"
    if s == FAMILY_PERCUSSION:
        return "percussion"
    if s == FAMILY_KEYBOARD:
        return "keyboards"
    if s == FAMILY_VOICE:
        return "voice"
    if not s or s == FAMILY_OTHER:
        return "other"
    return "other"
