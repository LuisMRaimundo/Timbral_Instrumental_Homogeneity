"""Herfindahl concentration helpers for H_TI window masses (pure, no UI)."""

from __future__ import annotations

import math
from typing import Any, cast

import numpy as np


def herfindahl_from_masses(masses: dict[str, float]) -> float:
    tot = float(sum(max(0.0, float(v)) for v in masses.values()))
    if tot <= 1e-15:
        return 0.0
    s = 0.0
    for v in masses.values():
        p = max(0.0, float(v)) / tot
        s += p * p
    return float(np.clip(s, 0.0, 1.0))


def finite_share_float(raw: object) -> float:
    if raw is None:
        return float("nan")
    try:
        v = float(cast(Any, raw))
    except (TypeError, ValueError):
        return float("nan")
    return v if math.isfinite(v) else float("nan")
