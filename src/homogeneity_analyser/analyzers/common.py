"""Shared helpers for homogeneity metrics (weights, pitch space, note names)."""

from __future__ import annotations

import music21 as m21
import numpy as np


def overlap_quarter_length(event_start: float, event_end: float, window_start: float, window_end: float) -> float:
    """
    Sounding overlap of ``[event_start, event_end]`` with ``[window_start, window_end]``
    in quarter-note time. Positive only when the intervals intersect with positive measure.
    """
    return max(0.0, min(float(event_end), float(window_end)) - max(float(event_start), float(window_start)))


def normalize_homogeneity_weights(w1, w2, w3) -> tuple[float, float, float]:
    """
    Non-negative weights normalized to sum to 1. If all zero or invalid, use equal thirds.
    Used for the weighted geometric mean of m1, m2, m3.
    """
    try:
        a = (max(0.0, float(w1)), max(0.0, float(w2)), max(0.0, float(w3)))
    except (TypeError, ValueError):
        return (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
    s = a[0] + a[1] + a[2]
    if s <= 1e-15:
        return (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
    return (a[0] / s, a[1] / s, a[2] / s)


def combine_weighted_geometric(m1: float, m2: float, m3: float, w1: float, w2: float, w3: float) -> float:
    """
    Weighted geometric mean: exp(w1*log m1 + w2*log m2 + w3*log m3) with normalized weights.
    For equal weights 1/3 each, equals (m1*m2*m3)^(1/3).
    """
    w1, w2, w3 = normalize_homogeneity_weights(w1, w2, w3)
    eps = 1e-15
    x1, x2, x3 = max(float(m1), eps), max(float(m2), eps), max(float(m3), eps)
    return float(np.exp(w1 * np.log(x1) + w2 * np.log(x2) + w3 * np.log(x3)))


def normalize_pitch_space(value) -> str:
    """
    Map UI/API strings to ``absolute`` (MIDI pitch) or ``pitch_class`` (mod 12).

    Aliases for pitch-class mode: ``chromatic``, ``pc``, ``class``.
    Any other value defaults to ``absolute`` for robustness.
    """
    if value is None or value == "":
        return "absolute"
    v = str(value).strip().lower()
    if v in ("pitch_class", "chromatic", "pc", "class"):
        return "pitch_class"
    return "absolute"


def note_name_to_midi_ps(note_name: str) -> float:
    """Convert a note name (e.g. 'A1', 'E7', 'C4') to MIDI note number (float)."""
    p = m21.pitch.Pitch(note_name.strip())
    return float(p.ps)
