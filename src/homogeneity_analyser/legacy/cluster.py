"""
Vertical pitch-cluster compactness **H_cluster** — instrumentation-independent.

Uses **concert (sounding) MIDI** per note (``timbral_sounding_pitch.sounding_pitch_ps_list``)
so transposing parts map to the same vertical sonority as identical concert pitch content.

**Empty windows** (no sounding pitch rows overlapping the analysis window): treated like the
``n_unique_pitches <= 1`` branch — ``H_cluster = 1.0``, ``n_events = 0``, and interval /
density diagnostics are zero-filled so exports stay JSON/CSV-safe. This keeps the series in
``[0, 1]`` and matches the “no vertical diversity” interpretation for silence or rests-only
windows.

**Formula** (``cluster_ref_span`` default 12.0 semitones):

- If ``n_unique_pitches <= 1``: ``H_cluster = 1.0``.
- Else: ``chromatic_density = n_unique_pitches / (span_st + 1)``,
  ``compactness = 1 / (1 + span_st / cluster_ref_span)``,
  ``H_cluster = sqrt(chromatic_density * compactness)``.

Timbral / orchestration logic is intentionally **not** used beyond sounding-pitch resolution.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.parsing_bridge import parse_score
from homogeneity_analyser.analyzers.technique_state import iter_timbral_elements
from homogeneity_analyser.analyzers.timbral_sounding_pitch import sounding_pitch_ps_list


def compute_cluster_diagnostics_from_midi_list(
    midi_values: list[float],
    *,
    cluster_ref_span: float = 12.0,
) -> dict[str, Any]:
    """
    Compute ``H_cluster`` and per-window diagnostics from a multiset of MIDI ``ps`` values.

    ``midi_values`` includes multiplicity (e.g. two parts on the same concert pitch appear
    twice). Span and chromatic density use **unique** pitches; ``duplicate_pitch_count`` is
    ``n_events - n_unique_pitches``.
    """
    crs = float(cluster_ref_span)
    if not math.isfinite(crs) or crs <= 0.0:
        crs = 12.0

    raw = [float(x) for x in midi_values if math.isfinite(float(x))]
    n_events = len(raw)
    if n_events == 0:
        return {
            "H_cluster": 1.0,
            "cluster_ref_span": crs,
            "cluster_empty_window": True,
            "n_events": 0,
            "n_unique_pitches": 0,
            "lowest_midi": 0.0,
            "highest_midi": 0.0,
            "span_st": 0.0,
            "chromatic_density": 0.0,
            "duplicate_pitch_count": 0,
            "mean_adjacent_interval": 0.0,
            "adjacent_interval_std": 0.0,
            "pitch_class_cardinality": 0,
            "compactness": 1.0,
        }

    uniq = sorted(set(raw))
    n_unique = len(uniq)
    lo = float(uniq[0])
    hi = float(uniq[-1])
    span_st = hi - lo
    dup = n_events - n_unique
    pc_card = len({int(p) % 12 for p in raw})

    if n_unique <= 1:
        return {
            "H_cluster": 1.0,
            "cluster_ref_span": crs,
            "cluster_empty_window": False,
            "n_events": n_events,
            "n_unique_pitches": n_unique,
            "lowest_midi": lo,
            "highest_midi": hi,
            "span_st": span_st,
            "chromatic_density": 1.0,
            "duplicate_pitch_count": dup,
            "mean_adjacent_interval": 0.0,
            "adjacent_interval_std": 0.0,
            "pitch_class_cardinality": pc_card,
            "compactness": 1.0,
        }

    gaps = np.diff(np.array(uniq, dtype=float))
    mean_gap = float(np.mean(gaps)) if gaps.size else 0.0
    std_gap = float(np.std(gaps)) if gaps.size else 0.0

    chromatic_density = float(n_unique / (span_st + 1.0))
    compactness = float(1.0 / (1.0 + span_st / crs))
    h_cluster = float(math.sqrt(max(0.0, chromatic_density * compactness)))
    h_cluster = float(max(0.0, min(1.0, h_cluster)))

    return {
        "H_cluster": h_cluster,
        "cluster_ref_span": crs,
        "cluster_empty_window": False,
        "n_events": n_events,
        "n_unique_pitches": n_unique,
        "lowest_midi": lo,
        "highest_midi": hi,
        "span_st": span_st,
        "chromatic_density": chromatic_density,
        "duplicate_pitch_count": dup,
        "mean_adjacent_interval": mean_gap,
        "adjacent_interval_std": std_gap,
        "pitch_class_cardinality": pc_card,
        "compactness": compactness,
    }


class ClusterHomogeneityAnalyzer:
    """
    Sliding-window **H_cluster** from sounding MIDI only (no instrument / technique terms).

    Parameters ``time_step`` and ``window_size`` follow the same quarter-note semantics as
    ``HomogeneityAnalyzer`` / ``TimbralHomogeneityAnalyzer`` (centered window).
    """

    def __init__(
        self,
        score_path: str | None = None,
        time_step: float = 0.25,
        cluster_ref_span: float = 12.0,
        *,
        music21_score: Any | None = None,
    ):
        if music21_score is not None:
            self.score = music21_score
        elif score_path is not None:
            self.score = parse_score(score_path)
        else:
            raise TypeError("ClusterHomogeneityAnalyzer requires score_path or music21_score=…")
        ts = float(time_step)
        if not math.isfinite(ts) or ts <= 0.0:
            raise ValueError(f"time_step must be finite and > 0; got {time_step!r}.")
        crs = float(cluster_ref_span)
        if not math.isfinite(crs) or crs <= 0.0:
            raise ValueError(f"cluster_ref_span must be finite and > 0; got {cluster_ref_span!r}.")
        self.cluster_ref_span = crs
        self.end_time = float(self.score.highestTime)
        self.time_axis = np.arange(0.0, self.end_time + 1e-9, ts)
        self._events: list[dict[str, Any]] = []
        self._build_events()

    def _build_events(self) -> None:
        for part in self.score.parts:
            for _off, _prio, kind, el in iter_timbral_elements(part):
                if kind != "note":
                    continue
                n = el
                o = float(n.offset)
                d = float(getattr(n, "quarterLength", 0.0))
                pits = sounding_pitch_ps_list(n, part)
                if not pits:
                    continue
                self._events.append({"offset": o, "end": o + d, "pitches": [float(p) for p in pits]})

    @staticmethod
    def _active_in_window(ev: dict[str, Any], t_start: float, t_end: float) -> bool:
        return float(ev["offset"]) < t_end and float(ev["end"]) > t_start

    def collect_sounding_midi_in_window(self, window_center: float, window_size: float) -> list[float]:
        t_start = float(window_center) - float(window_size) / 2.0
        t_end = float(window_center) + float(window_size) / 2.0
        active = [e for e in self._events if self._active_in_window(e, t_start, t_end)]
        out: list[float] = []
        for e in active:
            out.extend(float(p) for p in e["pitches"])
        return out

    def compute_cluster_window(self, window_center: float, window_size: float) -> dict[str, Any]:
        midis = self.collect_sounding_midi_in_window(window_center, window_size)
        return compute_cluster_diagnostics_from_midi_list(midis, cluster_ref_span=self.cluster_ref_span)

    def analyze_cluster(
        self,
        window_size: float,
        progress_callback: Any = None,
        *,
        return_diagnostics: bool = True,
    ) -> dict[str, Any]:
        t_list: list[float] = []
        h_list: list[float] = []
        diag_list: list[dict[str, Any]] = []
        n = len(self.time_axis)
        for i, t in enumerate(self.time_axis):
            d = self.compute_cluster_window(float(t), float(window_size))
            t_list.append(float(t))
            h_list.append(float(d["H_cluster"]))
            if return_diagnostics:
                diag_list.append(d)
            if progress_callback is not None and n > 0:
                progress_callback((i + 1) / n, "H_cluster(t)")
        out: dict[str, Any] = {"t": t_list, "H_cluster": h_list}
        if return_diagnostics:
            out["H_cluster_diagnostics"] = diag_list
        return out
