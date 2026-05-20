"""
Feature-space **distance → similarity** helpers for ``H_fusion_acoustic_heuristic``.

Distances use only dimensions where **both** instruments expose finite values; per-dimension
weights renormalize over the active set so missing components shrink the effective comparison
basis without raising errors.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np

from homogeneity_analyser.acoustic_profiles.features import FUSION_FEATURE_FIELDS

DEFAULT_FEATURE_WEIGHTS: dict[str, float] = {k: 1.0 for k in FUSION_FEATURE_FIELDS}


def weighted_normalized_feature_distance(
    vec_a: Mapping[str, float | None],
    vec_b: Mapping[str, float | None],
    weights: Mapping[str, float] | None = None,
) -> tuple[float, int, list[str]]:
    """
    Return ``(distance, n_dims_used, active_dims)`` where distance is in ``[0, 1]``.

    For each active dimension ``k``, contribution is ``w_k |a_k - b_k| / sum(w_active)``,
    clipped per dimension to ``[0,1]`` on the assumption that stored features are already
    on comparable coarse scales.
    """
    w = dict(weights or DEFAULT_FEATURE_WEIGHTS)
    active: list[str] = []
    num = 0.0
    den = 0.0
    for k in FUSION_FEATURE_FIELDS:
        va = vec_a.get(k)
        vb = vec_b.get(k)
        if va is None or vb is None:
            continue
        if not (math.isfinite(va) and math.isfinite(vb)):
            continue
        wt = float(w.get(k, 1.0))
        if wt <= 0.0:
            continue
        active.append(k)
        den += wt
        num += wt * min(1.0, abs(float(va) - float(vb)))
    if den <= 1e-15:
        return 0.5, 0, []
    return float(num / den), len(active), active


def similarity_from_distance(distance: float, *, scale: float = 1.0) -> float:
    """Map distance ``d`` to ``[0,1]`` with ``sim = 1 - min(1, d/scale)``."""
    s = max(1e-9, float(scale))
    return float(np.clip(1.0 - min(1.0, float(distance) / s), 0.0, 1.0))


def mean_pairwise_profile_similarity(
    vectors: Sequence[Mapping[str, float | None]],
    masses: Sequence[float],
    weights: Mapping[str, float] | None = None,
    *,
    distance_scale: float = 0.55,
) -> tuple[float, float, int]:
    """
    Mass-weighted mean pairwise similarity over ``vectors``.

    Returns ``(similarity, mean_distance, n_pairs_used)``. Empty or single-note windows
    return neutral ``(0.5, 0.5, 0)``.
    """
    n = len(vectors)
    if n <= 1:
        return 0.5, 0.5, 0
    num_w = 0.0
    den_w = 0.0
    dist_acc = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            wi = max(0.0, float(masses[i] if i < len(masses) else 0.0))
            wj = max(0.0, float(masses[j] if j < len(masses) else 0.0))
            w_ij = wi * wj
            if w_ij <= 0.0:
                continue
            d, n_used, _ = weighted_normalized_feature_distance(vectors[i], vectors[j], weights)
            if n_used == 0:
                d = 0.5
            sim_ij = similarity_from_distance(d, scale=distance_scale)
            num_w += w_ij * sim_ij
            den_w += w_ij
            dist_acc += d
            pairs += 1
    if den_w <= 1e-15 or pairs == 0:
        return 0.5, 0.5, 0
    mean_d = dist_acc / pairs
    return float(num_w / den_w), float(mean_d), pairs
