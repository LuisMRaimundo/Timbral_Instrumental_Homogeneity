"""
Active-component selection and renormalisation for H_TI_core.

Pure helpers extracted from ``hti.py``; behaviour must stay identical to the
pre-extraction ``compute_H_TI`` weighting path.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

_EPS = 1e-12

DEFAULT_W_INSTR = 0.40
DEFAULT_W_FAM = 0.25
DEFAULT_W_TECH = 0.15
DEFAULT_W_REG = 0.20


def weighted_geometric_mean_hti(
    components: dict[str, float],
    weights: dict[str, float],
    keys: list[str],
) -> float:
    wsum = sum(max(0.0, float(weights[k])) for k in keys)
    if wsum <= 1e-15:
        return float("nan")
    acc = 0.0
    for k in keys:
        wk = max(0.0, float(weights[k])) / wsum
        ck = max(float(components[k]), _EPS)
        acc += wk * math.log(ck)
    return float(np.clip(math.exp(acc), 0.0, 1.0))


def compute_hti_active_components(
    feats: dict[str, Any] | None,
    *,
    w_instr: float = DEFAULT_W_INSTR,
    w_fam: float = DEFAULT_W_FAM,
    w_tech: float = DEFAULT_W_TECH,
    w_reg: float = DEFAULT_W_REG,
    instrument_uniformity_component: float | None = None,
) -> tuple[float, dict[str, float], dict[str, float], dict[str, Any]]:
    """
    Build H_TI_core components, renormalised active weights, and a diagnostic fragment.

    Returns ``(h_core, components, active_weights, diag)`` where ``diag`` matches the
    second return value previously produced by ``SymbolicTIHomogeneityAnalyzer.compute_H_TI``.
    """
    base_w = {
        "instrument_uniformity": float(w_instr),
        "family_uniformity": float(w_fam),
        "technique_uniformity": float(w_tech),
        "register_proximity": float(w_reg),
    }
    if feats is None:
        aw = {k: v / sum(base_w.values()) for k, v in base_w.items()}
        return float("nan"), {}, aw, {"reason": "no_active_events"}

    iu_raw = float(feats["instrument_uniformity"])
    if instrument_uniformity_component is not None and math.isfinite(float(instrument_uniformity_component)):
        iu_use = float(instrument_uniformity_component)
    else:
        iu_use = iu_raw
    comp: dict[str, float] = {
        "instrument_uniformity": iu_use,
        "family_uniformity": float(feats["family_uniformity"]),
    }
    active: list[str] = ["instrument_uniformity", "family_uniformity"]
    weights = dict(base_w)

    tstat = str(feats.get("technique_coverage_status") or "")
    if tstat not in ("unavailable", "ambiguous") and math.isfinite(
        float(feats.get("technique_uniformity", float("nan")))
    ):
        comp["technique_uniformity"] = float(feats["technique_uniformity"])
        active.append("technique_uniformity")
    else:
        weights.pop("technique_uniformity", None)

    rstat = str(feats.get("register_coverage_status") or "")
    if rstat == "pitched" and math.isfinite(float(feats.get("register_proximity", float("nan")))):
        comp["register_proximity"] = float(feats["register_proximity"])
        active.append("register_proximity")
    else:
        weights.pop("register_proximity", None)

    wsum = sum(weights.values())
    if wsum <= 1e-15:
        return float("nan"), {}, {}, {"reason": "zero_weights"}
    renorm = {k: float(weights[k]) / wsum for k in active}
    h = weighted_geometric_mean_hti(comp, renorm, active)
    diag = {
        "H_TI": h,
        "H_TI_core": h,
        "technique_coverage_status": feats.get("technique_coverage_status"),
        "register_coverage_status": feats.get("register_coverage_status"),
        "components": {k: comp.get(k) for k in active},
    }
    return h, comp, renorm, diag
