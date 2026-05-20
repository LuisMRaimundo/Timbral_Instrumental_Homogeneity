"""
Register uniformity U(t) within a MIDI pitch band.

**Overlap weighting:** each note/chord contributes ``overlap`` quarter lengths in
``[window_start, window_end]`` (same rule as ``homogeneity.overlap_quarter_length``).
Register bins use ``numpy.histogram(..., weights=…)``. A short edge overlap carries less
mass than a note sustained through the window.

**Chords:** overlap mass is **split equally** among chord tones (same convention as
``HomogeneityAnalyzer.extract_features``), then only tones inside ``[register_low,
register_high]`` are accumulated (split mass is not renormalised across out-of-range tones).

**Pitch source:** ``music21`` ``Pitch.ps`` on flattened notes — **written / display**
MIDI, not automatic concert transposition. For concert register, preprocess the score or
extend this module with a ``pitch_mode`` in a future revision.
"""

from __future__ import annotations

import math

import numpy as np

from homogeneity_analyser.analyzers.common import overlap_quarter_length
from homogeneity_analyser.analyzers.parsing_bridge import parse_score


class RegisterUniformityAnalyzer:
    """
    Registral spread uniformity U(t) within ``[register_low, register_high]`` (MIDI pitch).

    Pass ``score_path=…`` or ``music21_score=…`` (with ``register_low_ps`` / ``register_high_ps``).

    **Uniformity** means *evenness of occupancy* across semitone bins in that band
    (normalised Shannon entropy of the overlap-weighted histogram), not voice-leading quality.
    One occupied bin (single sustained pitch class) → ``0``; empty window → ``NaN``.
    """

    def __init__(
        self,
        score_path: str | None = None,
        register_low_ps: float | None = None,
        register_high_ps: float | None = None,
        time_step: float = 0.25,
        *,
        music21_score=None,
    ):
        if register_low_ps is None or register_high_ps is None:
            raise TypeError("register_low_ps and register_high_ps are required")
        if music21_score is not None:
            self.score = music21_score
        elif score_path is not None:
            self.score = parse_score(score_path)
        else:
            raise TypeError("RegisterUniformityAnalyzer requires score_path or music21_score=…")
        ts = float(time_step)
        if not math.isfinite(ts) or ts <= 0.0:
            raise ValueError(f"time_step must be finite and > 0; got {time_step!r}.")
        self.flat = self.score.flatten()
        self.events = list(self.flat.notes)
        self.end_time = float(self.score.highestTime)
        self.time_axis = np.arange(0.0, self.end_time + 1e-9, ts)
        self.register_low = float(min(register_low_ps, register_high_ps))
        self.register_high = float(max(register_low_ps, register_high_ps))
        # Semitone bins over the register range
        n_semitones = max(1, int(round(self.register_high - self.register_low)) + 1)  # noqa: RUF046
        self._bin_edges = np.linspace(self.register_low - 0.5, self.register_high + 0.5, n_semitones + 1)
        self._n_bins = len(self._bin_edges) - 1
        self._max_entropy = float(np.log(max(1, self._n_bins)))

    def _active_in_window(self, e, t_start: float, t_end: float) -> bool:
        onset = float(e.offset)
        dur = float(e.quarterLength) if hasattr(e, "quarterLength") else 0.0
        return (onset < t_end) and ((onset + dur) > t_start)

    def _weighted_pitches_in_register(self, window_center: float, window_size: float) -> tuple[np.ndarray, np.ndarray]:
        """Pitch ``ps`` values in the register band with per-sample overlap weights (ql)."""
        t_start = window_center - window_size / 2.0
        t_end = window_center + window_size / 2.0
        active = [e for e in self.events if self._active_in_window(e, t_start, t_end)]
        pitches: list[float] = []
        weights: list[float] = []
        for e in active:
            o = float(e.offset)
            d = float(e.quarterLength) if hasattr(e, "quarterLength") else 0.0
            ol = overlap_quarter_length(o, o + d, t_start, t_end)
            if ol <= 0.0:
                continue
            if e.isNote:
                ps = float(e.pitch.ps)
                if self.register_low <= ps <= self.register_high:
                    pitches.append(ps)
                    weights.append(ol)
            elif e.isChord:
                plist = list(e.pitches)
                k = max(1, len(plist))
                w_tone = ol / float(k)
                for p in plist:
                    ps = float(p.ps)
                    if self.register_low <= ps <= self.register_high:
                        pitches.append(ps)
                        weights.append(w_tone)
        return np.array(pitches, dtype=float), np.array(weights, dtype=float)

    def compute_uniformity(self, pitches: np.ndarray, weights: np.ndarray | None = None) -> float:
        """
        Normalised entropy of the (weighted) pitch histogram over semitone bins → ``[0, 1]``.

        With ``weights is None``, each sample has unit weight (legacy unweighted behaviour).
        """
        if pitches.size == 0:
            return float("nan")
        if weights is None:
            weights = np.ones_like(pitches, dtype=float)
        if weights.shape != pitches.shape:
            raise ValueError("weights must match pitches shape")
        wtot = float(weights.sum())
        if wtot <= 0.0:
            return float("nan")
        if pitches.size == 1:
            return 0.0
        counts, _ = np.histogram(pitches, bins=self._bin_edges, weights=weights)
        total = float(counts.sum())
        if total <= 0.0:
            return float("nan")
        pmf = counts / total
        pmf = pmf[pmf > 0]
        if pmf.size <= 1:
            return 0.0
        entropy = -float(np.sum(pmf * np.log(pmf)))
        if self._max_entropy <= 0:
            return 0.0
        U = entropy / self._max_entropy
        return float(np.clip(U, 0.0, 1.0))

    def analyze_score(self, window_size: float, progress_callback=None):
        results: dict[str, list[float]] = {"t": [], "U": []}
        n = len(self.time_axis)
        for i, t in enumerate(self.time_axis):
            pitches, wts = self._weighted_pitches_in_register(float(t), window_size)
            U = self.compute_uniformity(pitches, wts)
            results["t"].append(float(t))
            results["U"].append(U)
            if progress_callback and n > 0:
                progress_callback((i + 1) / n, "Register uniformity U(t)")
        return results
