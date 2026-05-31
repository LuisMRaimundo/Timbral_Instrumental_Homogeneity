"""Overlap mass between symbolic score events and a quarter-length analysis window."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def event_overlap_ql(event: dict[str, Any], t_start: float, t_end: float) -> float:
    """Return overlap duration in quarter lengths between ``event`` and ``[t_start, t_end)``."""
    o = float(event["offset"])
    end = float(event["end"])
    return max(0.0, min(end, t_end) - max(o, t_start))


def build_window_contrib(
    events: list[dict[str, Any]],
    *,
    t_start: float,
    t_end: float,
    is_event_active_in_window: Callable[[dict[str, Any], float, float], bool],
) -> list[tuple[dict[str, Any], float]]:
    """
    Active events in the window with positive overlap mass.

    ``is_event_active_in_window`` is typically ``TimbralHomogeneityAnalyzer._active_in_window``.
    """
    active = [e for e in events if is_event_active_in_window(e, t_start, t_end)]
    contrib: list[tuple[dict[str, Any], float]] = []
    for e in active:
        ol = event_overlap_ql(e, t_start, t_end)
        if ol > 0.0:
            contrib.append((e, float(ol)))
    return contrib
