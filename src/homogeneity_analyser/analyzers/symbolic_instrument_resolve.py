"""Canonical instrument and family resolution from music21 parts and notes."""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_OTHER, resolve_instrument_taxonomy


def raw_instrument_name_from_m21(ins: Any) -> str:
    """Best-effort display name from a music21 ``Instrument`` instance."""
    if ins is None:
        return ""
    try:
        best = getattr(ins, "bestName", None)
        nm = best() if callable(best) else getattr(ins, "instrumentName", "")
        name = str(nm or "").strip()
        if name:
            return name
    except (AttributeError, TypeError, ValueError):
        pass
    return ""


def local_m21_instrument_for_note(note: Any) -> Any:
    """
    Return the music21 ``Instrument`` considered active at ``note`` (doublings / inserts),
    or ``None`` if only a generic empty shell is present and no class context exists.
    """
    try:
        gf = getattr(note, "getInstrument", None)
        if callable(gf):
            ins = gf()
            if ins is not None:
                if ins.__class__.__name__ != "Instrument":
                    return ins
                if raw_instrument_name_from_m21(ins):
                    return ins
    except (AttributeError, TypeError, ValueError):
        pass
    try:
        from music21 import instrument as m21inst

        return note.getContextByClass(m21inst.Instrument)
    except (AttributeError, TypeError, ValueError):
        return None


def part_instrument_fallback(part: Any) -> tuple[str, str]:
    """
    Part-level instrument string when no note-local name resolves, plus source tag.

    Returns ``(raw_name, "part_context" | "part_name_fallback" | "unknown")``.
    """
    try:
        instrs = part.getInstruments()
        if instrs:
            i0 = instrs[0]
            best = getattr(i0, "bestName", None)
            nm = best() if callable(best) else getattr(i0, "instrumentName", "")
            name = str(nm or "").strip()
            if name:
                return name, "part_context"
    except (AttributeError, TypeError, ValueError, IndexError):
        pass
    raw = getattr(part, "partName", None) or getattr(part, "id", None) or "unknown"
    if raw == "unknown":
        return "unknown", "unknown"
    return str(raw), "part_name_fallback"


def effective_instrument_for_note(n: Any, part: Any) -> tuple[str, str, str, dict[str, str]]:
    """
    Resolve taxonomy ``(canonical_instrument, family, instrument_source, orchestration_labels)``.

    ``instrument_source``: ``note_context`` | ``part_context`` | ``part_name_fallback`` | ``unknown``.
    ``orchestration_labels`` maps ``part_label_original``, ``raw_part_name``, ``section_label``, ``desk_group``.
    """
    fb_raw, fb_src = part_instrument_fallback(part)
    fb_canon, fb_fam, fb_meta = resolve_instrument_taxonomy(str(fb_raw))

    local_ins = local_m21_instrument_for_note(n)
    raw_local = raw_instrument_name_from_m21(local_ins) if local_ins is not None else ""

    if raw_local:
        canon, fam, loc_meta = resolve_instrument_taxonomy(str(raw_local))
        if (canon, fam) != (fb_canon, fb_fam):
            return canon, fam, "note_context", loc_meta
        if str(fb_meta.get("desk_group") or "") or str(fb_meta.get("section_label") or ""):
            return canon, fam, fb_src, fb_meta
        return canon, fam, fb_src, loc_meta

    canon, fam = fb_canon, fb_fam
    if fb_src == "unknown" or (canon == "unknown" and fam == FAMILY_OTHER):
        return canon, fam, "unknown", fb_meta
    return canon, fam, fb_src, fb_meta
