"""
Pairwise symbolic similarity for **bowed orchestral strings** in H_timbral.

Only canonical instruments ``violin``, ``viola``, ``cello``, ``double bass`` use this path.
Harp, guitar, etc. stay on the legacy timbral instrument component.

This is **notation-based orchestration similarity**, not acoustic timbre estimation.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from homogeneity_analyser.acoustic_profiles.model_config import timbral_float, timbral_numpy_matrix
from homogeneity_analyser.analyzers.string_technique import (
    TECH_ARCO,
    TECH_HARMONIC,
    TECH_MUTED,
    TECH_PIZZ,
    TECH_SUL_PONT,
    TECH_SUL_TASTO,
    TECH_TREMOLO,
    TECH_UNKNOWN,
)
from homogeneity_analyser.analyzers.technique_state import (
    technique_state_from_dict,
    technique_state_similarity,
)

# Canonical names must match ``instrument_taxonomy`` for these four.
BOWED_ORCHESTRAL_STRINGS = frozenset({"violin", "viola", "cello", "double bass"})

_SECTION_ORDER = ("violin", "viola", "cello", "double bass")

# Explicit section similarity (symmetric). Values from ``default_profiles.json``.
_SECTION_SIM: dict[tuple[str, str], float] = {}
_m_section = timbral_numpy_matrix("string_section_similarity_matrix")
for i, si in enumerate(_SECTION_ORDER):
    for j, sj in enumerate(_SECTION_ORDER):
        _SECTION_SIM[(si, sj)] = float(_m_section[i, j])


def is_bowed_orchestral_string(canonical_instrument: str) -> bool:
    return canonical_instrument in BOWED_ORCHESTRAL_STRINGS


def section_similarity(inst_a: str, inst_b: str) -> float:
    """Similarity in [0, 1] for two bowed orchestral string canonical names."""
    return float(_SECTION_SIM.get((inst_a, inst_b), timbral_float("string_fallback_section_similarity")))


def register_similarity_pitch(ps_a: float, ps_b: float, tau_semitones: float | None = None) -> float:
    """Continuous MIDI (pitch space) proximity; 1.0 at unison, decays with |Δ|."""
    if tau_semitones is None:
        tau_semitones = timbral_float("string_register_tau_semitones_default")
    tau = max(float(tau_semitones), 0.5)
    return float(math.exp(-abs(float(ps_a) - float(ps_b)) / tau))


# Technique similarity matrix (symmetric). Values are heuristic symbolic distances.
_TECH_KEYS = (
    TECH_ARCO,
    TECH_TREMOLO,
    TECH_SUL_PONT,
    TECH_SUL_TASTO,
    TECH_HARMONIC,
    TECH_MUTED,
    TECH_PIZZ,
    TECH_UNKNOWN,
)
# Order matches _TECH_KEYS index (loaded from ``default_profiles.json``).
_TECH_MAT = timbral_numpy_matrix("string_technique_similarity_matrix")
_TECH_INDEX = {k: i for i, k in enumerate(_TECH_KEYS)}


def technique_similarity(tech_a: str, tech_b: str) -> float:
    ia = _TECH_INDEX.get(tech_a, _TECH_INDEX[TECH_UNKNOWN])
    ib = _TECH_INDEX.get(tech_b, _TECH_INDEX[TECH_UNKNOWN])
    return float(_TECH_MAT[ia, ib])


def _pairwise_string_homogeneity_multistate(events: list[dict[str, Any]]) -> float:
    """Multi-dimensional :class:`~homogeneity_analyser.analyzers.technique_state.TechniqueState` similarity."""
    evs: list[dict[str, Any]] = []
    states: list[Any] = []
    for e in events:
        raw = e.get("technique_state")
        if not isinstance(raw, dict):
            continue
        w = float(e.get("overlap_ql", 0.0))
        if w <= 0:
            continue
        evs.append(e)
        states.append(technique_state_from_dict(raw))
    n = len(states)
    if n <= 1:
        return 1.0
    num = 0.0
    den = 0.0
    for i in range(n):
        wi = float(evs[i].get("overlap_ql", 0.0))
        for j in range(i + 1, n):
            wj = float(evs[j].get("overlap_ql", 0.0))
            w_pair = wi * wj
            s_sec = section_similarity(str(evs[i]["instrument"]), str(evs[j]["instrument"]))
            s_reg = register_similarity_pitch(float(evs[i]["pitch"]), float(evs[j]["pitch"]))
            s_tec = technique_state_similarity(states[i], states[j])
            num += w_pair * (s_sec * s_reg * s_tec)
            den += w_pair
    if den <= 0.0:
        return 1.0
    return float(np.clip(num / den, 0.0, 1.0))


def pairwise_string_homogeneity(events: list[dict[str, Any]]) -> float:
    """
    Mean of pair_similarity = section * register * technique, weighted by overlap mass.

    ``events`` items: ``instrument`` (canonical bowed string), ``pitch`` (MIDI ps),
    ``technique`` (normalized id), ``overlap_ql`` (duration overlap with window, >0).

    If ``technique_state`` dict is present on events, uses multi-dimensional state
    similarity instead of the legacy single-label matrix.
    """
    if events and isinstance(events[0].get("technique_state"), dict):
        return _pairwise_string_homogeneity_multistate(events)
    n = len(events)
    if n <= 1:
        return 1.0
    num = 0.0
    den = 0.0
    for i in range(n):
        ei = events[i]
        wi = float(ei.get("overlap_ql", 0.0))
        if wi <= 0:
            continue
        for j in range(i + 1, n):
            ej = events[j]
            wj = float(ej.get("overlap_ql", 0.0))
            if wj <= 0:
                continue
            w_pair = wi * wj
            s_sec = section_similarity(str(ei["instrument"]), str(ej["instrument"]))
            s_reg = register_similarity_pitch(float(ei["pitch"]), float(ej["pitch"]))
            s_tec = technique_similarity(str(ei["technique"]), str(ej["technique"]))
            num += w_pair * (s_sec * s_reg * s_tec)
            den += w_pair
    if den <= 0.0:
        return 1.0
    return float(np.clip(num / den, 0.0, 1.0))


def blend_string_and_legacy_instrument_component(
    h_pairwise_strings: float,
    legacy_instr_component: float,
    string_overlap_mass: float,
    total_overlap_mass: float,
) -> float:
    """
    Conservative mix when strings share the window with non-strings.

    ``f = string_overlap_mass / total_overlap_mass`` (0..1). Instrument component is
    ``f * h_pairwise + (1-f) * legacy``. Pure strings (f≈1) use the pairwise model.
    """
    tot = max(float(total_overlap_mass), 1e-12)
    f = float(np.clip(string_overlap_mass / tot, 0.0, 1.0))
    return float(f * h_pairwise_strings + (1.0 - f) * legacy_instr_component)
