"""
Pairwise symbolic similarity for **brass** instruments in H_timbral (notation only).

Uses canonical taxonomy names; ``bass trombone`` is distinct from ``trombone``. See
``docs/H_TIMBRAL_BRASS.md``.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from homogeneity_analyser.acoustic_profiles.model_config import (
    timbral_bounds_list,
    timbral_float,
    timbral_float_tuple,
    timbral_numpy_matrix,
)
from homogeneity_analyser.analyzers.brass_technique import (
    BRASS_BUCKET,
    BRASS_CUIVRE,
    BRASS_CUP,
    BRASS_FLUTTER,
    BRASS_HARMON,
    BRASS_MUTED_GENERIC,
    BRASS_OPEN,
    BRASS_STOPPED,
    BRASS_STRAIGHT,
    BRASS_UNKNOWN,
)
from homogeneity_analyser.analyzers.string_pairwise_timbral import (
    blend_string_and_legacy_instrument_component as blend_pairwise_and_legacy_instrument_component,
)
from homogeneity_analyser.analyzers.technique_state import timbral_event_technique_pair_similarity
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BRASS

# Section indices: 0 trumpet-like, 1 horn-like, 2 tenor trombone, 3 bass trombone, 4 tuba-like
_BRASS_INST_TO_SECTION: dict[str, int] = {
    "trumpet": 0,
    "bass trumpet": 0,
    "cornet": 0,
    "flugelhorn": 0,
    "mellophone": 0,
    "bugle": 0,
    "cornett": 0,
    "horn": 1,
    "natural horn": 1,
    "wagner tuba": 1,
    "alphorn": 1,
    "trombone": 2,
    "bass trombone": 3,
    "tuba": 4,
    "euphonium": 4,
    "cimbasso": 4,
    "sousaphone": 4,
    "serpent": 4,
    "ophicleide": 4,
    "didgeridoo": 4,
}

# (low_midi, high_midi) concert-ish sounding bounds per section bucket
_TESS_BOUNDS: list[tuple[float, float]] = timbral_bounds_list("brass_tessitura_bounds_midi")

_SECTION_SIM = timbral_numpy_matrix("brass_section_similarity_matrix")

_TECH_KEYS = (
    BRASS_OPEN,
    BRASS_STRAIGHT,
    BRASS_CUP,
    BRASS_HARMON,
    BRASS_BUCKET,
    BRASS_STOPPED,
    BRASS_CUIVRE,
    BRASS_FLUTTER,
    BRASS_MUTED_GENERIC,
    BRASS_UNKNOWN,
)
# Symmetric technique similarity (notation-level). Includes ``cuivre`` vs ``open`` / ``stopped``.
_TECH_MAT = timbral_numpy_matrix("brass_technique_similarity_matrix")
_TECH_INDEX = {k: i for i, k in enumerate(_TECH_KEYS)}
_BRASS_SAME_SECTION_ZONE_SIM = timbral_float_tuple("brass_register_same_section_zone_sim", length=4)
_BRASS_SAME_SECTION_FINE_TAU = timbral_float("brass_register_same_section_fine_tau")
_BRASS_SAME_SECTION_BLEND_ZONE = timbral_float("brass_register_same_section_blend_zone")
_BRASS_SAME_SECTION_BLEND_FINE = timbral_float("brass_register_same_section_blend_fine")
_BRASS_CROSS_SECTION_FINE_TAU = timbral_float("brass_register_cross_section_fine_tau")
_BRASS_CROSS_SECTION_BLEND_ALIGN = timbral_float("brass_register_cross_section_blend_align")
_BRASS_CROSS_SECTION_BLEND_FINE = timbral_float("brass_register_cross_section_blend_fine")


def is_brass_family(family: str) -> bool:
    return family == FAMILY_BRASS


def brass_section_index(canonical_instrument: str) -> int:
    return int(_BRASS_INST_TO_SECTION.get(canonical_instrument, 2))


def brass_section_similarity(inst_a: str, inst_b: str) -> float:
    ia = brass_section_index(inst_a)
    ib = brass_section_index(inst_b)
    return float(_SECTION_SIM[ia, ib])


def _norm_height(section_idx: int, ps: float) -> float:
    lo, hi = _TESS_BOUNDS[section_idx]
    if hi <= lo:
        return 0.5
    return float(np.clip((ps - lo) / (hi - lo), 0.0, 1.0))


def _tessitura_zone(section_idx: int, ps: float) -> int:
    lo, hi = _TESS_BOUNDS[section_idx]
    if hi <= lo:
        return 1
    t = (ps - lo) / (hi - lo)
    return int(min(3, max(0, t * 4.0)))


def brass_register_similarity(inst_a: str, ps_a: float, inst_b: str, ps_b: float) -> float:
    ia = brass_section_index(inst_a)
    ib = brass_section_index(inst_b)
    if ia == ib:
        za = _tessitura_zone(ia, ps_a)
        zb = _tessitura_zone(ib, ps_b)
        zd = abs(za - zb)
        sim_z = _BRASS_SAME_SECTION_ZONE_SIM[min(zd, 3)]
        fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _BRASS_SAME_SECTION_FINE_TAU)
        return float(_BRASS_SAME_SECTION_BLEND_ZONE * sim_z + _BRASS_SAME_SECTION_BLEND_FINE * fine)
    ha = _norm_height(ia, ps_a)
    hb = _norm_height(ib, ps_b)
    align = 1.0 - abs(ha - hb)
    fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _BRASS_CROSS_SECTION_FINE_TAU)
    return float(_BRASS_CROSS_SECTION_BLEND_ALIGN * align + _BRASS_CROSS_SECTION_BLEND_FINE * fine)


def brass_technique_similarity(tech_a: str, tech_b: str) -> float:
    ia = _TECH_INDEX.get(tech_a, _TECH_INDEX[BRASS_UNKNOWN])
    ib = _TECH_INDEX.get(tech_b, _TECH_INDEX[BRASS_UNKNOWN])
    return float(_TECH_MAT[ia, ib])


def pairwise_brass_homogeneity(events: list[dict[str, Any]]) -> float:
    """Weighted mean of section × register × technique over unordered brass event pairs."""
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
            s_sec = brass_section_similarity(str(ei["instrument"]), str(ej["instrument"]))
            s_reg = brass_register_similarity(
                str(ei["instrument"]),
                float(ei["pitch"]),
                str(ej["instrument"]),
                float(ej["pitch"]),
            )
            s_tec = timbral_event_technique_pair_similarity(
                ei, ej, matrix_similarity=brass_technique_similarity, technique_key="technique"
            )
            num += w_pair * (s_sec * s_reg * s_tec)
            den += w_pair
    if den <= 0.0:
        return 1.0
    return float(np.clip(num / den, 0.0, 1.0))


def blend_brass_and_legacy_instrument_component(
    h_pairwise_brass: float,
    current_instr_component: float,
    brass_overlap_mass: float,
    total_overlap_mass: float,
) -> float:
    """Same mass-ratio blend as strings; refines an already partially-refined instrument term."""
    return blend_pairwise_and_legacy_instrument_component(
        h_pairwise_brass,
        current_instr_component,
        brass_overlap_mass,
        total_overlap_mass,
    )
