"""Seven equal-width [0, 1] bands for timbral/fusion corpus expectations."""

from __future__ import annotations

BAND_ORDER: tuple[str, ...] = (
    "very_low",
    "low",
    "medium_low",
    "medium",
    "medium_high",
    "high",
    "very_high",
)


def scalar_to_band(value: float) -> str:
    """Map a scalar in ``[0, 1]`` to a band label (``int(value * 7)`` with clamp at top)."""
    v = max(0.0, min(1.0, float(value)))
    idx = int(v * 7.0)
    if idx >= len(BAND_ORDER):
        idx = len(BAND_ORDER) - 1
    return BAND_ORDER[idx]


def value_matches_expected_band(value: float, expected_band: str) -> bool:
    if expected_band not in BAND_ORDER:
        raise ValueError(f"Unknown band {expected_band!r}; use one of {BAND_ORDER}")
    return scalar_to_band(value) == expected_band
