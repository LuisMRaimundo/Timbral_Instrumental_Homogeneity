"""Register compactness from pitched MIDI occurrences (H_TI register component)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.percussion_ontology import PitchStatus, get_percussion_meta
from homogeneity_analyser.analyzers.percussion_pairwise_timbral import is_percussion_family

_EPS = 1e-12


def compute_register_compactness_fields(
    pitch_occurrences: list[tuple[float, float]],
    register_ref_semitones: float,
) -> dict[str, Any]:
    """
    Register **compactness** diagnostics from pitched MIDI/ps occurrences.

    Each entry is ``(midi_pitch, overlap_mass)`` for one chord tone / sounding pitch
    (same overlap mass as the parent event for each listed pitch). Unpitched percussion
    must be excluded **before** calling.

    Returns ``register_span_proximity`` (outer span only), overlap-weighted mean
    ``pairwise_interval_proximity`` over unordered pairs, ``register_compactness`` as
    ``sqrt(max(ε, span) * max(ε, pairwise))``, and ``register_proximity`` equal to
    ``register_compactness`` (the value that enters **H_TI_core**'s weighted geometric mean).
    """
    ref = float(register_ref_semitones)
    if not math.isfinite(ref) or ref <= 0.0:
        ref = 7.0
    if not pitch_occurrences:
        nan = float("nan")
        return {
            "register_span_semitones": nan,
            "register_span_proximity": nan,
            "register_span_factor": nan,
            "pairwise_interval_proximity": nan,
            "register_pair_distance_factor": nan,
            "pairwise_interval_coverage_status": "unpitched_only",
            "register_compactness": nan,
            "register_proximity": nan,
            "register_coverage_status": "unpitched_only",
        }

    mids = [float(p) for p, _w in pitch_occurrences]
    arr = np.asarray(mids, dtype=float)
    span_semi = float(np.ptp(arr)) if arr.size > 1 else 0.0
    register_span_proximity = 1.0 / (1.0 + span_semi / ref)

    n = len(pitch_occurrences)
    if n < 2:
        pairwise_interval_proximity = 1.0
        pairwise_interval_coverage_status = "insufficient_pairs"
    else:
        num = 0.0
        den = 0.0
        for i in range(n):
            pi, wi = float(pitch_occurrences[i][0]), float(pitch_occurrences[i][1])
            wi = max(0.0, wi)
            for j in range(i + 1, n):
                pj, wj = float(pitch_occurrences[j][0]), float(pitch_occurrences[j][1])
                wj = max(0.0, wj)
                d = abs(pi - pj)
                prox = 1.0 / (1.0 + d / ref)
                wij = wi * wj
                num += wij * prox
                den += wij
        pairwise_interval_proximity = float(num / den) if den > 1e-15 else 1.0
        pairwise_interval_coverage_status = "sufficient_pairs"

    rp_span = max(float(register_span_proximity), _EPS)
    rp_pair = max(float(pairwise_interval_proximity), _EPS)
    register_compactness = float(np.clip(math.sqrt(rp_span * rp_pair), 0.0, 1.0))
    rsp = float(register_span_proximity)
    pip = float(pairwise_interval_proximity)
    return {
        "register_span_semitones": span_semi,
        "register_span_proximity": rsp,
        "register_span_factor": rsp,
        "pairwise_interval_proximity": pip,
        "register_pair_distance_factor": pip,
        "pairwise_interval_coverage_status": pairwise_interval_coverage_status,
        "register_compactness": register_compactness,
        "register_proximity": register_compactness,
        "register_coverage_status": "pitched",
    }


def collect_pitched_occurrences_from_contrib(
    contrib: list[tuple[dict[str, Any], float]],
) -> tuple[list[float], list[tuple[float, float]]]:
    """
    Extract pitched register samples from overlap-weighted window contributions.

    Returns ``(register_span_pitches, pitch_occurrences)`` where each occurrence is
    ``(midi, overlap_mass)``. Unpitched percussion is skipped (same rule as window extract).
    """
    register_span_pitches: list[float] = []
    pitch_occurrences: list[tuple[float, float]] = []
    for e, ol in contrib:
        fam = str(e.get("family") or "")
        inst_e = str(e.get("instrument") or "")
        ol_f = float(ol)
        for p in e.get("pitches") or []:
            try:
                pf = float(p)
            except (TypeError, ValueError):
                continue
            skip_reg = is_percussion_family(fam) and (
                get_percussion_meta(inst_e).pitch_status == PitchStatus.UNPITCHED
            )
            if not skip_reg:
                register_span_pitches.append(pf)
                pitch_occurrences.append((pf, ol_f))
    return register_span_pitches, pitch_occurrences
