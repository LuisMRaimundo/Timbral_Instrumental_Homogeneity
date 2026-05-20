"""
Conservative **notation text context** for technique heuristics (``H_timbral``).

Combines **note-local** lyrics/expressions with **measure-level** staff directions only when
those directions occur **at or before** the note's offset within the measure (default), or
``measure_text="none"`` for note-local only (used together with chronological direction
scanning in ``timbral.TimbralHomogeneityAnalyzer``).

``legacy`` mode (all text in the measure) is retained only for explicit backwards-compatible
checks; it must not be used where later directions must not affect earlier notes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from music21 import stream as m21stream
    from music21.note import GeneralNote


def notation_text_context_for_note(
    n: GeneralNote,
    *,
    measure_text: Literal["none", "prior", "legacy"] = "prior",
) -> str:
    """
    Lowercased, space-joined text: note-local attachments plus optional measure-level text.

    ``measure_text``:
    - ``none``: only lyrics / expressions attached to the note (no measure-wide merge).
    - ``prior`` (default): ``TextExpression`` / ``RehearsalMark`` / ``Dynamic`` in the same
      measure whose offset is **strictly less than** the note's offset in that measure
      (later directions do not affect earlier notes).
    - ``legacy``: previous behaviour — all same-measure directions (retroactive; avoid in
      timbral event building when a chronological tracker is used).
    """
    chunks: list[str] = []
    loc = _note_local_text_blob(n)
    if loc:
        chunks.append(loc)
    if measure_text == "legacy":
        meas_blob = _measure_level_text_blob_legacy(n)
        if meas_blob:
            chunks.append(meas_blob)
    elif measure_text == "prior":
        meas_blob = _measure_level_text_blob_prior_to_note(n)
        if meas_blob:
            chunks.append(meas_blob)
    return " ".join(chunks).strip().lower()


def _note_local_text_blob(n: GeneralNote) -> str:
    parts: list[str] = []
    for ly in getattr(n, "lyrics", None) or []:
        t = getattr(ly, "text", None) or str(ly)
        if t:
            parts.append(str(t).lower())
    for ex in getattr(n, "expressions", None) or []:
        c = getattr(ex, "content", None)
        if c:
            parts.append(str(c).lower())
        parts.append(type(ex).__name__.lower())
    return " ".join(parts)


def _note_offset_in_parent_measure(n: GeneralNote) -> tuple[m21stream.Measure | None, float | None]:
    from music21 import stream

    try:
        meas_raw = n.getContextByClass(stream.Measure)
    except (AttributeError, TypeError, ValueError):
        return None, None
    if meas_raw is None or not isinstance(meas_raw, stream.Measure):
        return None, None
    meas: stream.Measure = meas_raw
    try:
        return meas, float(n.getOffsetBySite(meas))
    except (AttributeError, TypeError, ValueError):
        return meas, None


def _measure_level_text_blob_prior_to_note(n: GeneralNote) -> str:
    """Collect measure directions strictly **before** the note's offset (no retroactivity)."""
    from music21 import dynamics, expressions

    meas, n_off = _note_offset_in_parent_measure(n)
    if meas is None or n_off is None:
        return ""
    parts: list[str] = []
    try:
        for tex in meas.recurse().getElementsByClass(expressions.TextExpression):
            c = getattr(tex, "content", None)
            if not c:
                continue
            try:
                eo = float(tex.getOffsetBySite(meas))
            except (AttributeError, TypeError, ValueError):
                continue
            if eo < n_off:
                parts.append(str(c).lower())
        for rm in meas.recurse().getElementsByClass(expressions.RehearsalMark):
            c = getattr(rm, "content", None)
            if not c:
                continue
            try:
                eo = float(rm.getOffsetBySite(meas))
            except (AttributeError, TypeError, ValueError):
                continue
            if eo < n_off:
                parts.append(str(c).lower())
        for dyn in meas.recurse().getElementsByClass(dynamics.Dynamic):
            v = getattr(dyn, "value", None)
            if v is None or not str(v).strip():
                continue
            try:
                eo = float(dyn.getOffsetBySite(meas))
            except (AttributeError, TypeError, ValueError):
                continue
            if eo < n_off:
                parts.append(str(v).strip().lower())
    except (AttributeError, TypeError, ValueError):
        pass
    return " ".join(parts)


def _measure_level_text_blob_legacy(n: GeneralNote) -> str:
    """All same-measure directions (old behaviour)."""
    from music21 import dynamics, expressions, stream

    try:
        meas_raw = n.getContextByClass(stream.Measure)
    except (AttributeError, TypeError, ValueError):
        return ""
    if meas_raw is None or not isinstance(meas_raw, stream.Measure):
        return ""
    meas: stream.Measure = meas_raw
    parts: list[str] = []
    try:
        for tex in meas.recurse().getElementsByClass(expressions.TextExpression):
            c = getattr(tex, "content", None)
            if c:
                parts.append(str(c).lower())
        for rm in meas.recurse().getElementsByClass(expressions.RehearsalMark):
            c = getattr(rm, "content", None)
            if c:
                parts.append(str(c).lower())
        for dyn in meas.recurse().getElementsByClass(dynamics.Dynamic):
            v = getattr(dyn, "value", None)
            if v is not None and str(v).strip():
                parts.append(str(v).strip().lower())
    except (AttributeError, TypeError, ValueError):
        pass
    return " ".join(parts)
