"""
Neutral symbolic orchestration homogeneity **H_orchestration_symbolic**.

Uses the same **notation-derived event slices** as ``H_timbral`` (canonical instrument, family,
``technique_state_id``, overlap quarter-length mass) but **does not** apply family-specific
pairwise fusion matrices or cross-family boosts.

Uniformity is **Herfindahl** (``sum p^2``) over overlap-weighted shares of instruments and families,
and over **technique-only** buckets (instrument-stripped ``technique_state_id`` tails) so
ordinary clarinet vs bass clarinet is not double-counted on the technique axis. The diagnostic
``full_technique_state_uniformity`` retains the legacy-style Herfindahl on full
``technique_state_id`` strings.

.. math::

   H_{\\text{orch}} = w_i \\sum_i p_i^2 + w_f \\sum_f p_f^2 + w_t \\sum_t p_t^2

with default ``(w_i, w_f, w_t) = (0.45, 0.25, 0.30)`` normalized to sum 1.

**Empty windows** (no overlapping notated pitch slices): returns **0.5** for the scalar and
components (neutral / unknown orchestration density).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.analyzers.timbral_concentration_splits import (
    concentration_bundle_from_timbral_slices,
    herfindahl_concentration,  # noqa: F401 — re-exported for tests and backwards-compatible imports
)


def _normalize_triplet(a: float, b: float, c: float) -> tuple[float, float, float]:
    x, y, z = float(a), float(b), float(c)
    if not all(math.isfinite(v) and v >= 0.0 for v in (x, y, z)):
        raise ValueError("Orchestration weights must be finite and nonnegative.")
    s = x + y + z
    if s <= 1e-15 or not math.isfinite(s):
        raise ValueError("Orchestration weights must sum to a finite value > 0.")
    return x / s, y / s, z / s


def compute_orchestration_symbolic_from_slices(
    slices: list[dict[str, Any]],
    *,
    weight_instrument: float = 0.45,
    weight_family: float = 0.25,
    weight_technique: float = 0.30,
) -> tuple[float, dict[str, Any]]:
    """
    Compute ``H_orchestration_symbolic`` and diagnostics from ``timbral_note_slices``-like rows.

    Each row should include ``overlap_ql``, ``instrument``, ``family``, ``technique_state_id``.
    """
    wi, wf, wt = _normalize_triplet(weight_instrument, weight_family, weight_technique)
    active_slices = [s for s in slices if isinstance(s, dict) and float(s.get("overlap_ql", 0.0) or 0.0) > 0.0]
    if not active_slices:
        diag = {
            "H_orchestration_symbolic": 0.5,
            "instrument_uniformity": 0.5,
            "family_uniformity": 0.5,
            "technique_uniformity": 0.5,
            "full_technique_state_uniformity": 0.5,
            "weight_instrument": wi,
            "weight_family": wf,
            "weight_technique": wt,
            "instrument_distribution": {},
            "family_distribution": {},
            "technique_distribution": {},
            "technique_only_distribution": {},
            "instrument_distribution_concentration": 0.5,
            "family_distribution_concentration": 0.5,
            "technique_only_concentration": 0.5,
            "full_state_concentration": 0.5,
            "legacy_concentration": 0.5,
            "orch_empty_window": True,
        }
        return 0.5, diag

    bundle = concentration_bundle_from_timbral_slices(active_slices)
    hi = float(bundle["instrument_distribution_concentration"])
    hf = float(bundle["family_distribution_concentration"])
    ht_only = float(bundle["technique_only_concentration"])
    h_full = float(bundle["full_state_concentration"])
    h_orch = float(np.clip(wi * hi + wf * hf + wt * ht_only, 0.0, 1.0))

    diag = {
        "H_orchestration_symbolic": h_orch,
        "instrument_uniformity": hi,
        "family_uniformity": hf,
        "technique_uniformity": ht_only,
        "full_technique_state_uniformity": h_full,
        "weight_instrument": wi,
        "weight_family": wf,
        "weight_technique": wt,
        "instrument_distribution": dict(bundle["instrument_distribution"]),
        "family_distribution": dict(bundle["family_distribution"]),
        "technique_distribution": dict(bundle["technique_state_distribution_full"]),
        "technique_only_distribution": dict(bundle["technique_only_distribution"]),
        "instrument_distribution_concentration": hi,
        "family_distribution_concentration": hf,
        "technique_only_concentration": ht_only,
        "full_state_concentration": h_full,
        "legacy_concentration": h_full,
        "orch_empty_window": False,
    }
    return h_orch, diag


class OrchestrationSymbolicAnalyzer:
    """
    Sliding-window **H_orchestration_symbolic** using ``TimbralHomogeneityAnalyzer`` event/slice
    construction only (``H_timbral`` formula is not invoked).
    """

    def __init__(
        self,
        score_path: str | None = None,
        time_step: float = 0.25,
        timbral_config: dict[str, Any] | None = None,
        *,
        timbral_model_mode: str | None = None,
        weight_orchestration_instrument: float = 0.45,
        weight_orchestration_family: float = 0.25,
        weight_orchestration_technique: float = 0.30,
        music21_score: Any | None = None,
    ):
        self._timbral = TimbralHomogeneityAnalyzer(
            score_path=score_path,
            time_step=float(time_step),
            timbral_config=timbral_config,
            timbral_model_mode=timbral_model_mode,
            music21_score=music21_score,
        )
        self.w_i, self.w_f, self.w_t = _normalize_triplet(
            weight_orchestration_instrument,
            weight_orchestration_family,
            weight_orchestration_technique,
        )
        self.time_axis = self._timbral.time_axis
        self.end_time = self._timbral.end_time

    def compute_orchestration_window(self, window_center: float, window_size: float) -> dict[str, Any]:
        feats = self._timbral.extract_timbral_features(float(window_center), float(window_size))
        if feats is None:
            wi, wf, wt = self.w_i, self.w_f, self.w_t
            return {
                "H_orchestration_symbolic": 0.5,
                "instrument_uniformity": 0.5,
                "family_uniformity": 0.5,
                "technique_uniformity": 0.5,
                "weight_instrument": wi,
                "weight_family": wf,
                "weight_technique": wt,
                "instrument_distribution": {},
                "family_distribution": {},
                "technique_distribution": {},
                "orch_empty_window": True,
            }
        slices = feats.get("timbral_note_slices") or []
        h, diag = compute_orchestration_symbolic_from_slices(
            slices if isinstance(slices, list) else [],
            weight_instrument=self.w_i,
            weight_family=self.w_f,
            weight_technique=self.w_t,
        )
        diag["H_orchestration_symbolic"] = float(h)
        return diag

    def analyze_orchestration_symbolic(
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
            d = self.compute_orchestration_window(float(t), float(window_size))
            t_list.append(float(t))
            h_list.append(float(d["H_orchestration_symbolic"]))
            if return_diagnostics:
                diag_list.append(d)
            if progress_callback is not None and n > 0:
                progress_callback((i + 1) / n, "H_orchestration_symbolic(t)")
        out: dict[str, Any] = {"t": t_list, "H_orchestration_symbolic": h_list}
        if return_diagnostics:
            out["H_orchestration_symbolic_diagnostics"] = diag_list
        return out
