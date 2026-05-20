"""Time-grid alignment for combining multiple analysis curves."""

from __future__ import annotations

from typing import Any

import numpy as np


def interpolate_onto_times(t_from: np.ndarray, y_from: np.ndarray, t_to: np.ndarray) -> np.ndarray:
    """Linear interpolation of ``y_from`` sampled at ``t_from`` onto the grid ``t_to``."""
    return np.interp(t_to, t_from, y_from)


def align_series_nearest(t_from: np.ndarray, values: list[Any], t_to: np.ndarray) -> list[Any]:
    """Map per-window labels (or mixed values) from ``t_from`` onto ``t_to`` using nearest-neighbor times."""
    if t_from.size == 0 or t_to.size == 0 or len(values) != int(t_from.size):
        return [None] * int(t_to.size)
    if t_from.shape == t_to.shape and np.allclose(t_from, t_to, rtol=0.0, atol=1e-9):
        return list(values)
    out: list[Any] = []
    for tv in t_to:
        j = int(np.argmin(np.abs(t_from - float(tv))))
        out.append(values[j])
    return out
