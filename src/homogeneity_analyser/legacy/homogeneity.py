"""
Distribution homogeneity H(t) — HomogeneityAnalyzer.

**Window overlap (quarter-note time):** for each note or chord ``e`` with notated onset
``o`` and end ``o + quarterLength``, overlap with window ``[t_start, t_end]`` is
``max(0, min(o+ql, t_end) - max(o, t_start))``. Features use this overlap as mass; a
note that barely clips the window contributes far less than one that sounds throughout.

**Pitch (H intra):** pitch PMFs are built with ``numpy.histogram(..., weights=…)``.
**Chords:** each chord's overlap mass is **split equally** among its notated pitch classes
(k tones → weight ``overlap / k`` per tone). Total pitch mass in the window then equals
the sum of event overlaps (conserved mass), not ``k × overlap``.

**Duration (H intra):** duration bins use **within-window overlap duration** (same
``overlap`` in ql), not full notated ``quarterLength`` — a local texture feature. Each
**event** (note or chord) contributes one overlap-duration sample weighted by ``overlap``.

**Densities (explicit):**
  - ``onset_event_density`` / legacy ``density_scalar``: onsets in ``[t_start, t_end)``,
    count of **notated events** / window length.
  - ``pitch_onset_density``: sum over those onsets of pitch-class count (chord → k) / window.
  - ``sounding_event_overlap_density`` / legacy ``sounding_density``: sum of per-event
    overlaps / window length.
  - ``sounding_pitch_overlap_density``: sum of per-pitch overlap weights (chord-split) / window;
    with equal chord splitting this equals ``sounding_event_overlap_density``.

**Pitch values:** ``music21`` ``Note`` / ``Chord`` pitches as flattened from the score —
**written / display** MIDI ``ps``, not automatic concert transposition. For concert-pitch
texture, preprocess the score or use a future ``pitch_mode`` API; timbral analysis uses a
separate sounding-pitch path (``timbral_sounding_pitch``).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import wasserstein_distance

from homogeneity_analyser.analyzers.common import (
    combine_weighted_geometric,
    normalize_homogeneity_weights,
    normalize_pitch_space,
    overlap_quarter_length,
)
from homogeneity_analyser.analyzers.parsing_bridge import parse_score

# m3 sustained-texture branch: treat as sustained when onset density is low but overlap is high.
M3_SUSTAINED_ONSET_DENSITY_MAX = 0.4
M3_SUSTAINED_SOUNDING_DENSITY_MIN = 0.3


class HomogeneityAnalyzer:
    """
    Distribution homogeneity H(t) — symbolic texture uniformity in sliding windows.

    Construct with ``score_path=…`` or ``music21_score=…`` (in-memory ``music21`` score).

    At each time t, ``H(t) = (m1 * m2 * m3) ** (1/3)`` with m1,m2,m3 in [0,1].

    - **m1** (``compute_metric_intra``): 1 − normalized entropy of duration, pitch, and
      joint pitch×duration distributions; empty window → ``silence_intra_value``.
    - **m2** (``compute_metric_inter``): Wasserstein stability between consecutive
      windows on pitch PMFs; ``exp(-w/sigma)``; missing neighbor → ``silence_transition_value``.
    - **m3** (``compute_metric_scale``): agreement of onset density across scaled windows
      (``1/(1+mean|diff|)``) with optional sustained-texture branch. Scale logic uses
      ``onset_event_density`` (``density_scalar``) unless the sustained branch triggers,
      in which case it compares ``sounding_event_overlap_density`` (``sounding_density``).
    """

    def __init__(
        self,
        score_path: str | None = None,
        time_step: float = 0.25,
        pitch_bin_step: float = 1.0,
        dur_bins=(0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 8.0, 16.0),
        pitch_space: str = "absolute",
        silence_intra_value: float = 0.5,
        silence_transition_value: float = 0.5,
        allow_partial_scales: bool = True,
        *,
        music21_score=None,
    ):
        ts = float(time_step)
        if not math.isfinite(ts) or ts <= 0.0:
            raise ValueError(f"time_step must be finite and > 0; got {time_step!r}.")
        pbs = float(pitch_bin_step)
        if not math.isfinite(pbs) or pbs <= 0.0:
            raise ValueError(f"pitch_bin_step must be finite and > 0; got {pitch_bin_step!r}.")
        if music21_score is not None:
            self.score = music21_score
        elif score_path is not None:
            self.score = parse_score(score_path)
        else:
            raise TypeError("HomogeneityAnalyzer requires score_path or music21_score=…")
        self.flat = self.score.flatten()
        self.events = list(self.flat.notes)
        self.end_time = float(self.score.highestTime)
        self.time_axis = np.arange(0.0, self.end_time + 1e-9, ts)
        self.pitch_space = normalize_pitch_space(pitch_space)
        self.pitch_bin_step = float(pitch_bin_step)
        self.silence_intra_value = float(np.clip(silence_intra_value, 0.0, 1.0))
        self.silence_transition_value = float(np.clip(silence_transition_value, 0.0, 1.0))
        self.allow_partial_scales = bool(allow_partial_scales)
        all_vals = []
        for e in self.events:
            if e.isNote:
                all_vals.append(self._pitch_value(float(e.pitch.ps)))
            elif e.isChord:
                all_vals.extend([self._pitch_value(float(p.ps)) for p in e.pitches])
        if len(all_vals) == 0:
            pmin, pmax = (0.0, 11.0) if self.pitch_space == "pitch_class" else (21.0, 108.0)
        else:
            pmin, pmax = min(all_vals), max(all_vals)
        if self.pitch_space == "pitch_class":
            self.pitch_edges = np.arange(-0.5, 12.5, 1.0)
        else:
            pmin -= 2 * self.pitch_bin_step
            pmax += 2 * self.pitch_bin_step
            self.pitch_edges = np.arange(pmin, pmax + self.pitch_bin_step, self.pitch_bin_step)
        self.pitch_centers = 0.5 * (self.pitch_edges[:-1] + self.pitch_edges[1:])
        self.dur_edges = np.array(dur_bins, dtype=float)

    def _pitch_value(self, ps: float) -> float:
        if self.pitch_space == "pitch_class":
            return float(ps % 12.0)
        return float(ps)

    def _active_in_window(self, e, t_start, t_end) -> bool:
        onset = float(e.offset)
        dur = float(e.quarterLength) if hasattr(e, "quarterLength") else 0.0
        return (onset < t_end) and ((onset + dur) > t_start)

    def _event_overlap_ql(self, e, t_start: float, t_end: float) -> float:
        o = float(e.offset)
        d = float(e.quarterLength) if hasattr(e, "quarterLength") else 0.0
        return overlap_quarter_length(o, o + d, t_start, t_end)

    def extract_features(self, window_center: float, window_size: float):
        t_start = window_center - window_size / 2.0
        t_end = window_center + window_size / 2.0
        active = [e for e in self.events if self._active_in_window(e, t_start, t_end)]
        if len(active) == 0:
            return None

        onset_events = [e for e in self.events if (float(e.offset) >= t_start and float(e.offset) < t_end)]
        onset_event_density = len(onset_events) / max(window_size, 1e-12)
        pitch_onset_density = sum(
            (1 if e.isNote else len(e.pitches)) for e in onset_events if (e.isNote or e.isChord)
        ) / max(window_size, 1e-12)

        pitch_w_p: list[float] = []
        pitch_w_w: list[float] = []
        joint_p: list[float] = []
        joint_d: list[float] = []
        joint_w: list[float] = []
        dur_e: list[float] = []
        dur_w: list[float] = []
        sounding_time = 0.0
        pitch_overlap_mass = 0.0

        for e in active:
            ol = self._event_overlap_ql(e, t_start, t_end)
            if ol <= 0.0:
                continue
            sounding_time += ol
            overlap_dur = ol
            if e.isNote:
                pitch_w_p.append(self._pitch_value(float(e.pitch.ps)))
                pitch_w_w.append(ol)
                joint_p.append(self._pitch_value(float(e.pitch.ps)))
                joint_d.append(overlap_dur)
                joint_w.append(ol)
                dur_e.append(overlap_dur)
                dur_w.append(ol)
                pitch_overlap_mass += ol
            elif e.isChord:
                raw_ps = [self._pitch_value(float(p.ps)) for p in e.pitches]
                k = max(1, len(raw_ps))
                w_tone = ol / float(k)
                for p in raw_ps:
                    pitch_w_p.append(p)
                    pitch_w_w.append(w_tone)
                    joint_p.append(p)
                    joint_d.append(overlap_dur)
                    joint_w.append(w_tone)
                    pitch_overlap_mass += w_tone
                dur_e.append(overlap_dur)
                dur_w.append(ol)

        sounding_event_overlap_density = sounding_time / max(window_size, 1e-12)
        sounding_pitch_overlap_density = pitch_overlap_mass / max(window_size, 1e-12)

        if len(pitch_w_p) > 0:
            p_counts, _ = np.histogram(pitch_w_p, bins=self.pitch_edges, weights=pitch_w_w)
            p_sum = float(p_counts.sum())
            p_pmf = p_counts / max(p_sum, 1e-15)
        else:
            p_pmf = np.zeros(len(self.pitch_centers), dtype=float)

        if len(dur_e) > 0:
            d_counts, _ = np.histogram(dur_e, bins=self.dur_edges, weights=dur_w)
            d_sum = float(d_counts.sum())
            d_pmf = d_counts / max(d_sum, 1e-15)
        else:
            d_pmf = np.zeros(len(self.dur_edges) - 1, dtype=float)

        if len(joint_p) > 0 and len(joint_d) == len(joint_p) == len(joint_w):
            pd_counts, _, _ = np.histogram2d(joint_p, joint_d, bins=[self.pitch_edges, self.dur_edges], weights=joint_w)
            pd_sum = float(pd_counts.sum())
            pd_pmf = pd_counts / max(pd_sum, 1e-15)
        else:
            pd_pmf = np.zeros((len(self.pitch_centers), len(self.dur_edges) - 1), dtype=float)

        return {
            "pitch_pmf": p_pmf,
            "dur_pmf": d_pmf,
            "pitch_dur_pmf": pd_pmf,
            "onset_event_density": float(onset_event_density),
            "pitch_onset_density": float(pitch_onset_density),
            "sounding_event_overlap_density": float(sounding_event_overlap_density),
            "sounding_pitch_overlap_density": float(sounding_pitch_overlap_density),
            "density_scalar": float(onset_event_density),
            "sounding_density": float(sounding_event_overlap_density),
        }

    def _entropy_from_pmf(self, pmf: np.ndarray) -> float:
        p = pmf[pmf > 0]
        if p.size == 0:
            return 0.0
        return float(-np.sum(p * np.log2(p)))

    def compute_metric_intra(self, features):
        if features is None:
            return self.silence_intra_value
        dur_pmf = features["dur_pmf"]
        pitch_pmf = features["pitch_pmf"]
        joint_pmf = features["pitch_dur_pmf"].ravel()
        max_h_dur = np.log2(len(dur_pmf)) if len(dur_pmf) > 1 else 0.0
        max_h_pitch = np.log2(len(pitch_pmf)) if len(pitch_pmf) > 1 else 0.0
        max_h_joint = np.log2(joint_pmf.size) if joint_pmf.size > 1 else 0.0
        h_dur = self._entropy_from_pmf(dur_pmf)
        h_pitch = self._entropy_from_pmf(pitch_pmf)
        h_joint = self._entropy_from_pmf(joint_pmf)
        m_dur = 1.0 if max_h_dur <= 0 else 1.0 - (h_dur / max_h_dur)
        m_pitch = 1.0 if max_h_pitch <= 0 else 1.0 - (h_pitch / max_h_pitch)
        m_joint = 1.0 if max_h_joint <= 0 else 1.0 - (h_joint / max_h_joint)
        return float(np.clip((m_dur + m_pitch + m_joint) / 3.0, 0.0, 1.0))

    def compute_metric_inter(self, feat_curr, feat_prev, sigma: float):
        if feat_curr is None and feat_prev is None:
            return 1.0
        if feat_curr is None or feat_prev is None:
            return self.silence_transition_value
        if feat_curr["pitch_pmf"].sum() <= 0 or feat_prev["pitch_pmf"].sum() <= 0:
            return 0.0
        w = wasserstein_distance(
            self.pitch_centers,
            self.pitch_centers,
            u_weights=feat_curr["pitch_pmf"],
            v_weights=feat_prev["pitch_pmf"],
        )
        return float(np.exp(-w / max(sigma, 1e-9)))

    def compute_metric_scale(self, t: float, base_size: float, scales=(1.0, 2.0, 4.0)):
        feats = [self.extract_features(t, base_size * s) for s in scales]
        if all(f is None for f in feats):
            return 1.0
        if any(f is None for f in feats) and not self.allow_partial_scales:
            return 0.0
        if any(f is None for f in feats) and self.allow_partial_scales:
            feats = [f for f in feats if f is not None]
            if len(feats) <= 1:
                return 1.0
        sustained = all(
            f["density_scalar"] < M3_SUSTAINED_ONSET_DENSITY_MAX
            and f["sounding_density"] > M3_SUSTAINED_SOUNDING_DENSITY_MIN
            for f in feats
        )
        diffs = []
        for i in range(len(feats) - 1):
            if sustained:
                d = abs(feats[i]["sounding_density"] - feats[i + 1]["sounding_density"])
            else:
                d = abs(feats[i]["density_scalar"] - feats[i + 1]["density_scalar"])
            diffs.append(d)
        if not diffs:
            return 1.0
        return float(1.0 / (1.0 + float(np.mean(diffs))))

    def analyze_score(
        self,
        window_size: float,
        sigma: float,
        scales=(1.0, 2.0, 4.0),
        weight_m1: float = 1.0 / 3.0,
        weight_m2: float = 1.0 / 3.0,
        weight_m3: float = 1.0 / 3.0,
        progress_callback=None,
    ):
        w1, w2, w3 = normalize_homogeneity_weights(weight_m1, weight_m2, weight_m3)
        results = {"t": [], "H": [], "m1": [], "m2": [], "m3": []}
        prev_feat = None
        n = len(self.time_axis)
        for i, t in enumerate(self.time_axis):
            curr_feat = self.extract_features(float(t), window_size)
            m1 = self.compute_metric_intra(curr_feat)
            m2 = self.compute_metric_inter(curr_feat, prev_feat, sigma=sigma) if prev_feat is not None else 1.0
            m3 = self.compute_metric_scale(float(t), window_size, scales=scales)
            H_t = combine_weighted_geometric(m1, m2, m3, w1, w2, w3)
            results["t"].append(float(t))
            results["H"].append(float(H_t))
            results["m1"].append(float(m1))
            results["m2"].append(float(m2))
            results["m3"].append(float(m3))
            prev_feat = curr_feat
            if progress_callback and n > 0:
                progress_callback((i + 1) / n, "Homogeneity H(t)")
        return results

    def segment_homogeneity(self, results, z_threshold: float = 2.5, min_gap: int = 4):
        H = np.array(results["H"], dtype=float)
        if H.size < 3:
            return []
        d = np.abs(np.diff(H))
        mu, sigma = float(np.mean(d)), float(np.std(d))
        if sigma <= 1e-9:
            return []
        peaks = np.where(d > (mu + z_threshold * sigma))[0] + 1
        filtered = []
        last = -min_gap
        for p in peaks:
            if p - last >= min_gap:
                filtered.append(int(p))
                last = int(p)
        return filtered

    def segment_homogeneity_pelt(self, results, penalty: float = 0.05, min_size: int = 4):
        H = np.array(results["H"], dtype=float)
        n = H.size
        if n < 2 * min_size:
            return []
        csum = np.cumsum(H)
        csum2 = np.cumsum(H * H)

        def seg_cost(i, j):
            length = j - i
            if length <= 0:
                return 0.0
            sum_x = csum[j - 1] - (csum[i - 1] if i > 0 else 0.0)
            sum_x2 = csum2[j - 1] - (csum2[i - 1] if i > 0 else 0.0)
            mean = sum_x / length
            return float(sum_x2 - 2 * mean * sum_x + length * mean * mean)

        F = np.full(n + 1, np.inf)
        F[0] = -penalty
        cp = {0: []}
        R = {0}
        for t in range(min_size, n + 1):
            candidates = []
            for s in list(R):
                if t - s < min_size:
                    continue
                cost = F[s] + seg_cost(s, t) + penalty
                candidates.append((cost, s))
            if not candidates:
                continue
            best_cost, best_s = min(candidates, key=lambda x: x[0])
            F[t] = best_cost
            cp[t] = cp[best_s] + [best_s]
            new_R = set()
            for s in [*list(R), t - min_size]:
                if t - s < min_size:
                    continue
                if F[s] + seg_cost(s, t) + penalty <= F[t] + penalty:
                    new_R.add(s)
            R = new_R
        return [c for c in cp.get(n, []) if c != 0 and c != n]
