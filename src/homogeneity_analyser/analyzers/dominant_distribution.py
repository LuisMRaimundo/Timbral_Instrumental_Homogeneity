"""
Dominant category from a **share** distribution with explicit tie reporting.

Used for H_TI / export diagnostics only; does not enter homogeneity formulas.

**Tie ordering:** categories whose share is within ``tolerance`` of the maximum are tied.
``dominant_all`` lists all tied category names sorted **alphabetically** (case-sensitive Unicode order).
``dominant_primary`` is ``dominant_all[0]`` when non-empty (stable single-field backwards compatibility).
"""

from __future__ import annotations

import math
from typing import TypedDict


class DominantWithTiesResult(TypedDict):
    dominant_primary: str | None
    dominant_all: list[str]
    tie: bool
    max_share: float | None
    margin_to_second: float | None


def dominant_with_ties(distribution: dict[str, float], tolerance: float = 1e-9) -> DominantWithTiesResult:
    """
    Return dominant label(s), tie flag, max share, and margin to the second-largest **distinct** share.

    - If ``distribution`` is empty: all dominants null/empty, ``tie`` false, ``margin_to_second`` null.
    - If two or more categories tie at the top: ``margin_to_second`` is ``0.0``.
    - Otherwise ``margin_to_second = max_share - second_distinct_share`` (second is ``0.0`` if only one
      distinct positive mass exists).
    """
    if not distribution:
        return {
            "dominant_primary": None,
            "dominant_all": [],
            "tie": False,
            "max_share": None,
            "margin_to_second": None,
        }

    vals: list[float] = []
    for v in distribution.values():
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(fv):
            vals.append(fv)

    if not vals:
        return {
            "dominant_primary": None,
            "dominant_all": [],
            "tie": False,
            "max_share": None,
            "margin_to_second": None,
        }

    max_share = max(vals)
    if not math.isfinite(max_share):
        return {
            "dominant_primary": None,
            "dominant_all": [],
            "tie": False,
            "max_share": None,
            "margin_to_second": None,
        }

    tol = float(tolerance)
    tied = sorted(
        [str(k) for k, v in distribution.items() if math.isfinite(float(v)) and abs(float(v) - max_share) <= tol]
    )
    dominant_all = tied
    dominant_primary = dominant_all[0] if dominant_all else None
    tie = len(dominant_all) > 1

    if tie:
        margin_f = 0.0
    else:
        distinct_sorted = sorted({float(v) for v in distribution.values() if math.isfinite(float(v))}, reverse=True)
        second = float(distinct_sorted[1]) if len(distinct_sorted) > 1 else 0.0
        margin_f = float(max_share - second)

    return {
        "dominant_primary": dominant_primary,
        "dominant_all": dominant_all,
        "tie": tie,
        "max_share": float(max_share),
        "margin_to_second": margin_f,
    }


def dominant_line_label(
    *,
    label: str,
    primary: str | None,
    all_dominants: list[str] | None,
    tie: bool,
) -> str:
    """Human-readable ``Dominant X: a / b (tie)`` for summary / UI."""
    if not all_dominants:
        return f"{label}: (none)"
    if tie and len(all_dominants) > 1:
        joined = " / ".join(all_dominants)
        return f"{label}: {joined} (tie)"
    return f"{label}: {primary or all_dominants[0]}"
