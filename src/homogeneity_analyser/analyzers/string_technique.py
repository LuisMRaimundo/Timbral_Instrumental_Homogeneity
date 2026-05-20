"""
Symbolic string playing-technique labels for **H_timbral** refinement (not audio).

music21 exposes some techniques as articulations or expressions; many scores only
encode directions as free text. This module normalizes a small vocabulary used by
``string_pairwise_timbral``. It is intentionally incomplete vs full MusicXML semantics.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note

if TYPE_CHECKING:
    from music21.note import GeneralNote

# Normalized technique ids (stable strings for matrix lookup)
TECH_ARCO = "arco"
TECH_TREMOLO = "tremolo"
TECH_SUL_PONT = "sul_pont"
TECH_SUL_TASTO = "sul_tasto"
TECH_HARMONIC = "harmonic"
TECH_MUTED = "muted"
TECH_PIZZ = "pizz"
TECH_UNKNOWN = "unknown"

_ALL_TECHS = frozenset(
    {
        TECH_ARCO,
        TECH_TREMOLO,
        TECH_SUL_PONT,
        TECH_SUL_TASTO,
        TECH_HARMONIC,
        TECH_MUTED,
        TECH_PIZZ,
        TECH_UNKNOWN,
    }
)


def _keyword_technique(blob: str) -> str | None:
    if not blob:
        return None
    if re.search(r"\bpizz(icato)?\b|snap\s*pizz|bartok\s*pizz", blob):
        return TECH_PIZZ
    if "sul pont" in blob or "sulpont" in blob.replace(" ", "") or " ponticello" in blob:
        return TECH_SUL_PONT
    # ``molto flautando`` is bow pressure / colour, not sul tasto contact (see ``technique_state``).
    if re.search(r"\bmolto\s+flautando\b", blob):
        return TECH_UNKNOWN
    if "sul tasto" in blob or "sultasto" in blob.replace(" ", "") or "flautando" in blob:
        return TECH_SUL_TASTO
    if "tremolo" in blob or " trem." in blob or blob.strip() == "trem":
        return TECH_TREMOLO
    if re.search(
        r"\b(con\s+)?sord(ino)?\b|\bmuted\b|\bmit dampfer\b|\bgestopft\b|"
        r"\bou?r\s*bouche\b|\bstop\b",
        blob,
    ):
        return TECH_MUTED
    if "harm" in blob and ("onic" in blob or blob.startswith("harm")):
        return TECH_HARMONIC
    if re.search(r"\barco\b|\bord(inary)?\b|\bnormale\b|\bnatural\b", blob):
        return TECH_ARCO
    return None


def string_technique_from_note(n: GeneralNote) -> str:
    """
    Best-effort symbolic technique for a note or chord on a string part.

    Priority: explicit pizzicato / harmonic classes → tremolo expression →
    keyword scan on ``notation_text_context_for_note`` (note-local + measure directions
    **strictly before** the note by default) → bowed defaults (spiccato/staccato treated as
    arco-family) → unknown.
    """
    from music21 import articulations, expressions

    # --- Strong articulation / expression signals ---
    for a in getattr(n, "articulations", None) or []:
        if isinstance(
            a,
            articulations.Pizzicato
            | articulations.NailPizzicato
            | articulations.SnapPizzicato
            | articulations.FrettedPluck,
        ):
            return TECH_PIZZ
        if isinstance(a, articulations.StringHarmonic | articulations.Harmonic):
            return TECH_HARMONIC
        if isinstance(a, articulations.Stopped):
            return TECH_MUTED

    for ex in getattr(n, "expressions", None) or []:
        if isinstance(ex, expressions.Tremolo):
            return TECH_TREMOLO

    blob = notation_text_context_for_note(n)
    kw = _keyword_technique(blob)
    if kw is not None:
        return kw

    # Near-arco bow strokes / short notes (still bowed lane)
    for a in getattr(n, "articulations", None) or []:
        if isinstance(
            a,
            articulations.Spiccato
            | articulations.Staccato
            | articulations.Staccatissimo
            | articulations.Tenuto
            | articulations.DetachedLegato
            | articulations.UpBow
            | articulations.DownBow,
        ):
            return TECH_ARCO

    p = getattr(n, "pitch", None)
    if p is not None and getattr(p, "harmonicString", None):
        return TECH_HARMONIC

    return TECH_UNKNOWN


def is_normalized_technique(x: str) -> bool:
    return x in _ALL_TECHS
