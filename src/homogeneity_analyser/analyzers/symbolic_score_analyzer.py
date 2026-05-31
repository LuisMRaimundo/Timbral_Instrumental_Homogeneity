"""Score loader and canonical symbolic event list (shared by H_TI and H_timbral)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.harmonic_pitch import normalize_harmonic_pitch_policy
from homogeneity_analyser.analyzers.hti_window_overlap import is_event_active_in_window
from homogeneity_analyser.analyzers.parsing_bridge import parse_score
from homogeneity_analyser.analyzers.pitch_interpretation import normalize_pitch_interpretation_mode
from homogeneity_analyser.analyzers.symbolic_event_pipeline import build_symbolic_score_events


class SymbolicScoreAnalyzer:
    """
    Load a music21 score and build the canonical symbolic event list.

    Subclasses add metric-specific window analysis (**H_TI** in ``hti.py``,
    **H_timbral** in ``timbral.py``). Score → events lives in
    ``symbolic_event_pipeline.build_symbolic_score_events`` (see ``docs/HTI_SYMBOLIC_PIPELINE.md``).
    """

    def __init__(
        self,
        score_path: str | None = None,
        time_step: float = 0.25,
        *,
        music21_score: Any | None = None,
        pitch_interpretation_mode: str | None = None,
        harmonic_pitch_policy: str | None = None,
    ) -> None:
        if music21_score is not None:
            self.score = music21_score
        elif score_path is not None:
            self.score = parse_score(score_path)
        else:
            raise TypeError("SymbolicScoreAnalyzer requires score_path or music21_score=…")
        ts = float(time_step)
        if not math.isfinite(ts) or ts <= 0.0:
            raise ValueError(f"time_step must be finite and > 0; got {time_step!r}.")
        self.end_time = float(self.score.highestTime)
        self.time_axis = np.arange(0.0, self.end_time + 1e-9, ts)
        self._pitch_interpretation_mode = normalize_pitch_interpretation_mode(pitch_interpretation_mode)
        self._harmonic_pitch_policy = normalize_harmonic_pitch_policy(harmonic_pitch_policy)
        self._events: list[dict[str, Any]] = []
        self._build_symbolic_events()

    @property
    def score_events(self) -> list[dict[str, Any]]:
        """Notation events built for H_TI / H_timbral / inspection (read-only reference)."""
        return self._events

    def _build_symbolic_events(self) -> None:
        self._events = build_symbolic_score_events(
            self.score,
            pitch_interpretation_mode=self._pitch_interpretation_mode,
            harmonic_pitch_policy=self._harmonic_pitch_policy,
        )

    def _active_in_window(self, ev: dict, t_start: float, t_end: float) -> bool:
        return is_event_active_in_window(ev, t_start, t_end)
