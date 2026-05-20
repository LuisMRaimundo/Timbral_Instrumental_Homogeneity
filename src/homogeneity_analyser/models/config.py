"""Stable option labels (symbolic analysis only — no audio pipeline)."""

from __future__ import annotations

from enum import Enum


class PitchSpaceMode(str, Enum):
    """Pitch quantization axis for H(t) intra-window PMFs."""

    ABSOLUTE = "absolute"
    PITCH_CLASS = "pitch_class"
