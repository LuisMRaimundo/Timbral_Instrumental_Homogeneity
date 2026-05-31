"""Score metadata lookups used by H_TI time-series assembly (not metric math)."""

from __future__ import annotations

from typing import Any


def measure_number_at_ql(score: Any, t: float) -> int | None:
    """Return measure number containing quarter-length ``t``, or ``None``."""
    try:
        from music21 import stream as m21stream

        for part in score.parts:
            for m in part.getElementsByClass(m21stream.Measure):
                off = float(m.offset)
                dur = float(m.duration.quarterLength) if m.duration is not None else 0.0
                if off <= t < off + dur + 1e-9:
                    mn = getattr(m, "measureNumber", None)
                    if mn is not None and int(mn) not in (0,):
                        return int(mn)
        return None
    except (AttributeError, TypeError, ValueError):
        return None
