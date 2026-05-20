"""
Adaptive H_TI window / step sizing (orchestration only — does not change the H_TI formula).

``window_mode`` selects how ``window_size_effective`` and ``time_step_effective`` are derived from
``excerpt_duration_quarterLength`` (score span in quarter lengths). ``edge_policy`` controls which
window centres are emitted and how edge overlap is flagged in exports.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np

HTI_WINDOW_MODE_MANUAL = "manual"
HTI_WINDOW_MODE_AUTO_DURATION = "auto_by_excerpt_duration"
HTI_WINDOW_MODE_AUTO_TARGET = "auto_by_target_windows"

HTI_EDGE_INCLUDE = "include_partial_windows"
HTI_EDGE_DROP = "drop_partial_windows"
HTI_EDGE_MARK = "mark_partial_windows"


def _clip(x: float, lo: float, hi: float) -> float:
    return float(min(hi, max(lo, x)))


def resolve_hti_windowing(
    p: Mapping[str, Any],
    *,
    excerpt_duration_quarter_length: float,
) -> dict[str, Any]:
    """
    Merge ``p`` with adaptive defaults and return effective window/step plus echo fields for export.

    ``excerpt_duration_quarter_length`` is typically ``analyzer.end_time`` (score length in ql).
    """
    mode = str(p.get("window_mode") or HTI_WINDOW_MODE_MANUAL).strip()
    edge = str(p.get("edge_policy") or HTI_EDGE_MARK).strip()

    w_in = float(p.get("window_size", 4.0))
    ts_in = float(p.get("time_step", 0.25))

    wr = float(p.get("window_ratio", 0.15))
    sr = float(p.get("step_ratio", 0.01))
    min_w = float(p.get("min_window_size", 0.5))
    max_w = float(p.get("max_window_size", 8.0))
    min_ts = float(p.get("min_time_step", 0.0625))
    max_ts = float(p.get("max_time_step", 1.0))
    twc = float(p.get("target_window_count", 100))
    wsr = float(p.get("window_to_step_ratio", 10.0))

    dur = float(excerpt_duration_quarter_length)
    if not math.isfinite(dur) or dur < 0.0:
        dur = 0.0

    if mode == HTI_WINDOW_MODE_MANUAL:
        w_eff = w_in
        ts_eff = ts_in
    elif mode == HTI_WINDOW_MODE_AUTO_DURATION:
        w_eff = _clip(dur * wr, min_w, max_w)
        ts_eff = _clip(dur * sr, min_ts, max_ts)
    elif mode == HTI_WINDOW_MODE_AUTO_TARGET:
        if twc <= 1e-12:
            twc = 100.0
        ts_eff = _clip(dur / twc, min_ts, max_ts)
        w_eff = _clip(ts_eff * wsr, min_w, max_w)
    else:
        raise ValueError(
            f"window_mode must be one of {HTI_WINDOW_MODE_MANUAL!r}, "
            f"{HTI_WINDOW_MODE_AUTO_DURATION!r}, {HTI_WINDOW_MODE_AUTO_TARGET!r}; got {mode!r}."
        )

    if edge not in (HTI_EDGE_INCLUDE, HTI_EDGE_DROP, HTI_EDGE_MARK):
        raise ValueError(
            f"edge_policy must be one of {HTI_EDGE_INCLUDE!r}, {HTI_EDGE_DROP!r}, {HTI_EDGE_MARK!r}; got {edge!r}."
        )

    return {
        "window_mode": mode,
        "edge_policy": edge,
        "window_size_input": w_in,
        "time_step_input": ts_in,
        "window_size_effective": float(w_eff),
        "time_step_effective": float(ts_eff),
        "excerpt_duration_quarterLength": float(dur),
        "window_ratio": float(wr),
        "step_ratio": float(sr),
        "target_window_count": float(twc),
        "window_to_step_ratio": float(wsr),
        "min_window_size": float(min_w),
        "max_window_size": float(max_w),
        "min_time_step": float(min_ts),
        "max_time_step": float(max_ts),
    }


def build_hti_window_centers(
    excerpt_end: float,
    time_step_effective: float,
    window_size_effective: float,
    edge_policy: str,
) -> list[float]:
    """Uniform centres from 0 inclusive; ``drop_partial_windows`` trims centres past the excerpt."""
    te = float(time_step_effective)
    if not math.isfinite(te) or te <= 0.0:
        return []
    end = float(excerpt_end)
    raw = np.arange(0.0, end + 1e-12, te, dtype=float)
    centers = [float(x) for x in raw]
    ep = str(edge_policy or HTI_EDGE_MARK)
    if ep == HTI_EDGE_DROP:
        w = float(window_size_effective)
        return [t for t in centers if t + 0.5 * w <= end + 1e-9]
    return centers


def hti_window_row_geometry(
    center: float,
    window_size: float,
    excerpt_start: float,
    excerpt_end: float,
    edge_policy: str,
) -> dict[str, Any]:
    """
    Nominal window bounds, overlap with the excerpt, coverage ratio, and ``edge_window`` flag.

    ``include_partial_windows``: never flags ``edge_window`` (legacy feel); coverage still reflects
    intersection with the excerpt. ``mark_partial_windows``: ``edge_window`` true when the nominal
    window extends outside the excerpt. ``drop_partial_windows``: rows should not be emitted for
    dropped centres; if present, same geometry as mark for consistency.
    """
    w = float(window_size)
    ideal_lo = float(center) - 0.5 * w
    ideal_hi = float(center) + 0.5 * w
    es = float(excerpt_start)
    ee = float(excerpt_end)
    clip_lo = max(es, ideal_lo)
    clip_hi = min(ee, ideal_hi)
    overlap = max(0.0, clip_hi - clip_lo)
    coverage = overlap / w if w > 1e-15 else 0.0
    partial = (ideal_lo < es - 1e-12) or (ideal_hi > ee + 1e-12)
    ep = str(edge_policy or HTI_EDGE_MARK)
    edge = False if ep == HTI_EDGE_INCLUDE else bool(partial)
    return {
        "window_start": ideal_lo,
        "window_end": ideal_hi,
        "window_coverage_ratio": float(coverage),
        "effective_window_overlap_duration": float(overlap),
        "edge_window": edge,
    }
