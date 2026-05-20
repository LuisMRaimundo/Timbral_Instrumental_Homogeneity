"""
General **H_notated_fusion_potential**: notation-derived fusion-potential proxy.

Uses overlap-weighted **Herfindahl** uniformity over canonical instruments, taxonomy families,
and **technique-only** buckets (same overlap slices as timbral/orchestration event construction),
plus **sounding MIDI** pairwise register proximity. The **instrument** axis uses
``effective_instrument_uniformity`` =
``instrument_uniformity + same_family_relief * max(0, family_uniformity - instrument_uniformity)``
(distribution-based same-family relief; **no** pairwise instrument tables or family-specific affinity tables).
**Does not** invoke legacy ``H_timbral`` formulas, family-specific pairwise kernels, or acoustic fusion heuristics.

**Not** measured audio; **not** FFT/spectral analysis.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.analyzers.timbral_concentration_splits import concentration_bundle_from_timbral_slices
from homogeneity_analyser.legacy.notated_fusion_dynamic import (
    compute_dynamic_coherence_bundle,
    neutral_dynamic_bundle,
)


def _notated_fusion_evidence_status(register_coverage_status: str, same_family_relief_profile: str) -> str:
    """Register coverage dominates; named relief profiles only qualify pitched-register symbolic paths."""
    if register_coverage_status in ("no_pitched_pairs", "insufficient_pairs"):
        return "symbolic_no_register_evidence"
    if str(same_family_relief_profile).strip().lower() == "strict":
        return "symbolic_register_proxy"
    return "literature_motivated_calibrated_proxy"


def _normalize_quadruple(a: float, b: float, c: float, d: float) -> tuple[float, float, float, float]:
    x, y, z, w = float(a), float(b), float(c), float(d)
    if not all(math.isfinite(v) and v >= 0.0 for v in (x, y, z, w)):
        raise ValueError("Notated-fusion weights must be finite and nonnegative.")
    s = x + y + z + w
    if s <= 1e-15 or not math.isfinite(s):
        raise ValueError("Notated-fusion weights must sum to a finite value > 0.")
    return x / s, y / s, z / s, w / s


def build_notated_fusion_slices_for_window(
    active_events: list[dict[str, Any]],
    t_start: float,
    t_end: float,
) -> tuple[list[dict[str, Any]], int, int, int]:
    """
    Build ``timbral_note_slices``-compatible rows (optional ``pitch``) for one window.

    Returns ``(slices, n_events, n_pitched_events, n_unpitched_events)`` where ``n_events`` counts
    score events with positive overlap in the window.
    """
    slices: list[dict[str, Any]] = []
    n_pitched_events = 0
    n_unpitched_events = 0
    n_events = 0
    for e in active_events:
        if not isinstance(e, dict):
            continue
        ol = max(0.0, min(float(e["end"]), t_end) - max(float(e["offset"]), t_start))
        if ol <= 0.0:
            continue
        n_events += 1
        pits = list(e.get("pitches") or [])
        ts_id = str(e.get("technique_state_id") or "")
        inst = str(e.get("instrument") or "")
        fam = str(e.get("family") or "")
        ts_raw = e.get("technique_state")
        ts_payload = ts_raw if isinstance(ts_raw, dict) else {}
        if pits:
            n_pitched_events += 1
            for p in pits:
                slices.append(
                    {
                        "overlap_ql": float(ol),
                        "instrument": inst,
                        "family": fam,
                        "technique_state_id": ts_id,
                        "technique_state": ts_payload,
                        "pitch": float(p),
                    }
                )
        else:
            n_unpitched_events += 1
            slices.append(
                {
                    "overlap_ql": float(ol),
                    "instrument": inst,
                    "family": fam,
                    "technique_state_id": ts_id,
                    "technique_state": ts_payload,
                }
            )
    return slices, n_events, n_pitched_events, n_unpitched_events


def compute_effective_instrument_uniformity_same_family_relief(
    instrument_uniformity: float,
    family_uniformity: float,
    *,
    same_family_relief: float,
) -> tuple[float, dict[str, float]]:
    """
    Distribution-based relief when multiple canonical instruments share mass within the same family.

    ``instrument_uniformity`` = ``sum_i p_i^2``, ``family_uniformity`` = ``sum_f P_f^2`` with ``P_f`` the
    total instrument mass in family ``f``. Then ``same_family_cross_instrument_mass = max(0, H_f - H_i)``
    and ``effective_instrument_uniformity = H_i + relief * mass`` with ``relief`` clamped to ``[0, 1]``.

    Returns detail scalars only; callers add ``same_family_relief_profile``, delta, and ``same_family_relief_applied``.
    """
    r = float(np.clip(float(same_family_relief), 0.0, 1.0))
    hi = float(instrument_uniformity)
    hf = float(family_uniformity)
    if not (math.isfinite(hi) and math.isfinite(hf)):
        raise ValueError("instrument_uniformity and family_uniformity must be finite.")
    hi = float(np.clip(hi, 0.0, 1.0))
    hf = float(np.clip(hf, 0.0, 1.0))
    cross = max(0.0, hf - hi)
    eff = float(np.clip(hi + r * cross, 0.0, 1.0))
    detail = {
        "instrument_uniformity": hi,
        "family_uniformity": hf,
        "same_family_cross_instrument_mass": cross,
        "same_family_relief": r,
        "effective_instrument_uniformity": eff,
    }
    return eff, detail


def compute_register_proximity_and_pair_stats(
    pitched_rows: list[tuple[float, float]],
    register_ref_semitones: float,
) -> tuple[float, int, float | None, float | None, float | None, str]:
    """
    ``pitched_rows`` are ``(midi, overlap_mass)`` per sounding pitch row.

    Returns
    ``(register_proximity, register_pair_count, mean_d, min_d, max_d, register_coverage_status)``.
    """
    ref = float(register_ref_semitones)
    if not math.isfinite(ref) or ref <= 0.0:
        ref = 12.0
    n = len(pitched_rows)
    if n < 2:
        return 1.0, 0, None, None, None, "insufficient_pairs" if n > 0 else "no_pitched_pairs"
    num = 0.0
    den = 0.0
    dists: list[float] = []
    for i in range(n):
        mi, wi = pitched_rows[i]
        for j in range(i + 1, n):
            mj, wj = pitched_rows[j]
            d_ij = abs(float(mi) - float(mj))
            p_ij = 1.0 / (1.0 + d_ij / ref)
            w_ij = max(0.0, float(wi)) * max(0.0, float(wj))
            dists.append(d_ij)
            num += w_ij * p_ij
            den += w_ij
    if den <= 1e-18:
        return 1.0, 0, None, None, None, "insufficient_pairs"
    rp = float(np.clip(num / den, 0.0, 1.0))
    n_pairs = n * (n - 1) // 2
    mean_d = float(sum(dists) / len(dists)) if dists else None
    min_d = float(min(dists)) if dists else None
    max_d = float(max(dists)) if dists else None
    return rp, n_pairs, mean_d, min_d, max_d, "ok"


def compute_notated_fusion_potential_from_slices(
    slices: list[dict[str, Any]],
    *,
    n_events: int,
    n_pitched_events: int,
    n_unpitched_events: int,
    register_ref_semitones: float = 12.0,
    same_family_relief: float = 0.55,
    same_family_relief_profile: str = "balanced",
    same_family_relief_from_override: bool = False,
    weight_instrument: float = 0.30,
    weight_family: float = 0.15,
    weight_technique: float = 0.25,
    weight_register: float = 0.30,
) -> tuple[float, dict[str, Any]]:
    """
    Compute ``H_notated_fusion_potential`` and per-window diagnostics from overlap slices.

    ``slices`` entries must include ``overlap_ql``, ``instrument``, ``family``, ``technique_state_id``;
    include ``pitch`` (sounding MIDI) for register proximity when present.
    """
    wi, wf, wt, wr = _normalize_quadruple(weight_instrument, weight_family, weight_technique, weight_register)
    eps = 1e-12
    bundle_slices: list[dict[str, Any]] = []
    pitched_rows: list[tuple[float, float]] = []
    total_mass = 0.0
    pitched_mass = 0.0
    for s in slices:
        if not isinstance(s, dict):
            continue
        ol = float(s.get("overlap_ql", 0.0) or 0.0)
        if ol <= 0.0:
            continue
        total_mass += ol
        row = {
            "overlap_ql": ol,
            "instrument": str(s.get("instrument") or ""),
            "family": str(s.get("family") or ""),
            "technique_state_id": str(s.get("technique_state_id") or ""),
        }
        bundle_slices.append(row)
        raw_p = s.get("pitch")
        if raw_p is not None:
            try:
                midi = float(raw_p)
            except (TypeError, ValueError):
                continue
            if math.isfinite(midi):
                pitched_rows.append((midi, ol))
                pitched_mass += ol

    if not bundle_slices:
        diag = _empty_notated_fusion_diag(
            wi,
            wf,
            wt,
            wr,
            float(register_ref_semitones),
            same_family_relief=float(same_family_relief),
            same_family_relief_profile=str(same_family_relief_profile),
            same_family_relief_from_override=bool(same_family_relief_from_override),
        )
        diag["n_events"] = int(n_events)
        diag["n_pitched_events"] = int(n_pitched_events)
        diag["n_unpitched_events"] = int(n_unpitched_events)
        return 0.5, diag

    bundle = concentration_bundle_from_timbral_slices(bundle_slices)
    hi = float(bundle["instrument_distribution_concentration"])
    hf = float(bundle["family_distribution_concentration"])
    ht = float(bundle["technique_only_concentration"])
    eff_i, relief_detail = compute_effective_instrument_uniformity_same_family_relief(
        hi, hf, same_family_relief=float(same_family_relief)
    )
    delta_i = float(relief_detail["effective_instrument_uniformity"]) - float(hi)
    applied_i = bool(delta_i > 1e-12)
    reg_prox, reg_pairs, mean_d, min_d, max_d, reg_cov = compute_register_proximity_and_pair_stats(
        pitched_rows,
        float(register_ref_semitones),
    )
    log_sum = (
        wi * math.log(max(eff_i, eps))
        + wf * math.log(max(hf, eps))
        + wt * math.log(max(ht, eps))
        + wr * math.log(max(reg_prox, eps))
    )
    h_nf = float(np.clip(math.exp(log_sum), 0.0, 1.0))

    midis = sorted({float(m) for m, _ in pitched_rows})
    pitch_span = float(max(midis) - min(midis)) if len(midis) > 1 else 0.0
    cov_ratio = float(pitched_mass / total_mass) if total_mass > 1e-18 else 0.0

    evidence_status = _notated_fusion_evidence_status(reg_cov, same_family_relief_profile)

    inst_dist = dict(bundle["instrument_distribution"])
    fam_dist = dict(bundle["family_distribution"])
    tech_only_dist = dict(bundle["technique_only_distribution"])
    full_state_dist = dict(bundle["technique_state_distribution_full"])

    out_diag: dict[str, Any] = {
        "H_notated_fusion_potential": h_nf,
        "instrument_uniformity": hi,
        "family_uniformity": hf,
        "technique_only_uniformity": ht,
        "register_proximity": reg_prox,
        "same_family_cross_instrument_mass": relief_detail["same_family_cross_instrument_mass"],
        "same_family_relief": relief_detail["same_family_relief"],
        "same_family_relief_profile": str(same_family_relief_profile),
        "same_family_relief_delta": delta_i,
        "same_family_relief_applied": applied_i,
        "same_family_relief_from_override": bool(same_family_relief_from_override),
        "effective_instrument_uniformity": relief_detail["effective_instrument_uniformity"],
        "mean_pairwise_register_distance": mean_d,
        "min_pairwise_register_distance": min_d,
        "max_pairwise_register_distance": max_d,
        "pitch_span_st": pitch_span,
        "lowest_midi": float(min(midis)) if midis else None,
        "highest_midi": float(max(midis)) if midis else None,
        "midi_set": midis,
        "n_events": int(n_events),
        "n_pitched_events": int(n_pitched_events),
        "n_unpitched_events": int(n_unpitched_events),
        "n_pitches": len(pitched_rows),
        "n_instruments": len(inst_dist),
        "n_families": len(fam_dist),
        "instrument_distribution": inst_dist,
        "family_distribution": fam_dist,
        "technique_only_distribution": tech_only_dist,
        "full_state_distribution": full_state_dist,
        "register_pair_count": int(reg_pairs),
        "register_pitch_coverage_ratio": cov_ratio,
        "register_coverage_status": reg_cov,
        "register_ref_semitones": float(register_ref_semitones),
        "weights": {
            "weight_instrument": wi,
            "weight_family": wf,
            "weight_technique": wt,
            "weight_register": wr,
        },
        "metric_kind": "notated_fusion_potential",
        "not_audio_analysis": True,
        "evidence_status": evidence_status,
    }
    return h_nf, out_diag


def _empty_notated_fusion_diag(
    wi: float,
    wf: float,
    wt: float,
    wr: float,
    register_ref: float,
    *,
    same_family_relief: float = 0.55,
    same_family_relief_profile: str = "balanced",
    same_family_relief_from_override: bool = False,
) -> dict[str, Any]:
    _, rel0 = compute_effective_instrument_uniformity_same_family_relief(
        0.5, 0.5, same_family_relief=same_family_relief
    )
    hi0 = 0.5
    eff0 = float(rel0["effective_instrument_uniformity"])
    d0 = eff0 - hi0
    ev = "symbolic_no_register_evidence"
    return {
        "H_notated_fusion_potential": 0.5,
        "instrument_uniformity": hi0,
        "family_uniformity": 0.5,
        "technique_only_uniformity": 0.5,
        "register_proximity": 1.0,
        "same_family_cross_instrument_mass": rel0["same_family_cross_instrument_mass"],
        "same_family_relief": rel0["same_family_relief"],
        "same_family_relief_profile": str(same_family_relief_profile),
        "same_family_relief_delta": d0,
        "same_family_relief_applied": bool(d0 > 1e-12),
        "same_family_relief_from_override": bool(same_family_relief_from_override),
        "effective_instrument_uniformity": eff0,
        "mean_pairwise_register_distance": None,
        "min_pairwise_register_distance": None,
        "max_pairwise_register_distance": None,
        "pitch_span_st": 0.0,
        "lowest_midi": None,
        "highest_midi": None,
        "midi_set": [],
        "n_events": 0,
        "n_pitched_events": 0,
        "n_unpitched_events": 0,
        "n_pitches": 0,
        "n_instruments": 0,
        "n_families": 0,
        "instrument_distribution": {},
        "family_distribution": {},
        "technique_only_distribution": {},
        "full_state_distribution": {},
        "register_pair_count": 0,
        "register_pitch_coverage_ratio": 0.0,
        "register_coverage_status": "no_pitched_pairs",
        "register_ref_semitones": float(register_ref),
        "weights": {
            "weight_instrument": wi,
            "weight_family": wf,
            "weight_technique": wt,
            "weight_register": wr,
        },
        "metric_kind": "notated_fusion_potential",
        "not_audio_analysis": True,
        "evidence_status": ev,
    }


class NotatedFusionPotentialAnalyzer:
    """
    Sliding-window **H_notated_fusion_potential** using timbral event construction only
    (same overlap slicing; no ``H_timbral`` scalar path).
    """

    def __init__(
        self,
        score_path: str | None = None,
        time_step: float = 0.25,
        timbral_config: dict[str, Any] | None = None,
        *,
        timbral_model_mode: str | None = None,
        register_ref_semitones: float = 12.0,
        same_family_relief: float = 0.55,
        same_family_relief_profile: str = "balanced",
        same_family_relief_from_override: bool = False,
        weight_notated_fusion_instrument: float = 0.30,
        weight_notated_fusion_family: float = 0.15,
        weight_notated_fusion_technique: float = 0.25,
        weight_notated_fusion_register: float = 0.30,
        weight_notated_fusion_dynamic: float = 0.10,
        music21_score: Any | None = None,
    ):
        self._timbral = TimbralHomogeneityAnalyzer(
            score_path=score_path,
            time_step=float(time_step),
            timbral_config=timbral_config,
            timbral_model_mode=timbral_model_mode,
            music21_score=music21_score,
        )
        self.register_ref_semitones = float(register_ref_semitones)
        self.same_family_relief = float(np.clip(float(same_family_relief), 0.0, 1.0))
        self.same_family_relief_profile = str(same_family_relief_profile or "balanced")
        self.same_family_relief_from_override = bool(same_family_relief_from_override)
        self.w_i, self.w_f, self.w_t, self.w_r = _normalize_quadruple(
            weight_notated_fusion_instrument,
            weight_notated_fusion_family,
            weight_notated_fusion_technique,
            weight_notated_fusion_register,
        )
        self.w_dyn = float(np.clip(float(weight_notated_fusion_dynamic), 0.0, 1.0))
        self.time_axis = self._timbral.time_axis
        self.end_time = self._timbral.end_time

    def compute_notated_fusion_window(self, window_center: float, window_size: float) -> dict[str, Any]:
        t_start = float(window_center) - float(window_size) / 2.0
        t_end = float(window_center) + float(window_size) / 2.0
        active = [e for e in self._timbral._events if e["offset"] < t_end and e["end"] > t_start]
        if not active:
            d = _empty_notated_fusion_diag(
                self.w_i,
                self.w_f,
                self.w_t,
                self.w_r,
                self.register_ref_semitones,
                same_family_relief=self.same_family_relief,
                same_family_relief_profile=self.same_family_relief_profile,
                same_family_relief_from_override=self.same_family_relief_from_override,
            )
            d["nf_empty_window"] = True
            d.update(
                neutral_dynamic_bundle(
                    float(d["H_notated_fusion_potential"]),
                    self.w_dyn,
                    reason="no_events",
                )
            )
            return d
        slices, n_ev, n_pe, n_ue = build_notated_fusion_slices_for_window(active, t_start, t_end)
        h, diag = compute_notated_fusion_potential_from_slices(
            slices,
            n_events=n_ev,
            n_pitched_events=n_pe,
            n_unpitched_events=n_ue,
            register_ref_semitones=self.register_ref_semitones,
            same_family_relief=self.same_family_relief,
            same_family_relief_profile=self.same_family_relief_profile,
            same_family_relief_from_override=self.same_family_relief_from_override,
            weight_instrument=self.w_i,
            weight_family=self.w_f,
            weight_technique=self.w_t,
            weight_register=self.w_r,
        )
        diag["H_notated_fusion_potential"] = float(h)
        diag["nf_empty_window"] = False
        dyn_pack = compute_dynamic_coherence_bundle(
            active,
            t_start,
            t_end,
            h_base=float(h),
            weight_dynamic=self.w_dyn,
        )
        diag.update(dyn_pack)
        return diag

    def analyze_notated_fusion_potential(
        self,
        window_size: float,
        progress_callback: Any = None,
        *,
        return_diagnostics: bool = True,
    ) -> dict[str, Any]:
        t_list: list[float] = []
        h_list: list[float] = []
        h_dyn_list: list[float] = []
        diag_list: list[dict[str, Any]] = []
        n = len(self.time_axis)
        for i, t in enumerate(self.time_axis):
            d = self.compute_notated_fusion_window(float(t), float(window_size))
            t_list.append(float(t))
            h_list.append(float(d["H_notated_fusion_potential"]))
            h_dyn_list.append(float(d.get("H_notated_fusion_potential_dynamic", d["H_notated_fusion_potential"])))
            if return_diagnostics:
                diag_list.append(d)
            if progress_callback is not None and n > 0:
                progress_callback((i + 1) / n, "H_notated_fusion_potential(t)")
        out: dict[str, Any] = {
            "t": t_list,
            "H_notated_fusion_potential": h_list,
            "H_notated_fusion_potential_dynamic": h_dyn_list,
        }
        if return_diagnostics:
            out["H_notated_fusion_potential_diagnostics"] = diag_list
        return out
