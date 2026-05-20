"""
Pairwise symbolic similarity for **clarinet-family** instruments in H_timbral (notation only).

Canonical subtypes follow ``instrument_taxonomy`` (distinct soprano transpositions). Register
zones use **sounding** ``pitch.ps`` (concert). See ``docs/H_TIMBRAL_CLARINETS.md``.
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
from homogeneity_analyser.analyzers.clarinet_technique import (
    CLARINET_BREATHY,
    CLARINET_FLUTTER,
    CLARINET_LIGHT_VIBRATO,
    CLARINET_MULTIPHONIC,
    CLARINET_ORDINARIO,
    CLARINET_SLAP,
    CLARINET_UNKNOWN,
)
from homogeneity_analyser.analyzers.string_pairwise_timbral import (
    blend_string_and_legacy_instrument_component as blend_clarinet_family_and_legacy_instrument_component,
)
from homogeneity_analyser.analyzers.technique_state import timbral_event_technique_pair_similarity
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_CLARINETS

# Order: a, b-flat, c, e-flat, generic, alto, basset horn, basset clarinet, bass, contrabass
_CLAR_INST_TO_IDX: dict[str, int] = {
    "a clarinet": 0,
    "b flat clarinet": 1,
    "c clarinet": 2,
    "e flat clarinet": 3,
    "clarinet": 4,
    "alto clarinet": 5,
    "basset horn": 6,
    "basset clarinet": 7,
    "bass clarinet": 8,
    "contrabass clarinet": 9,
}

# Practical sounding MIDI range per subtype (concert)
_CLAR_TESS_BOUNDS: list[tuple[float, float]] = timbral_bounds_list("clarinet_tessitura_bounds_midi")

_SUBTYPE_SIM = timbral_numpy_matrix("clarinet_subtype_similarity_matrix")

_TECH_KEYS = (
    CLARINET_ORDINARIO,
    CLARINET_LIGHT_VIBRATO,
    CLARINET_FLUTTER,
    CLARINET_BREATHY,
    CLARINET_SLAP,
    CLARINET_MULTIPHONIC,
    CLARINET_UNKNOWN,
)
_TECH_MAT = timbral_numpy_matrix("clarinet_technique_similarity_matrix")
_TECH_INDEX = {k: i for i, k in enumerate(_TECH_KEYS)}
_CLAR_ZONE_THRESH_CHAL = timbral_float("clarinet_register_zone_threshold_chalumeau_upper_midi")
_CLAR_ZONE_THRESH_CLAR = timbral_float("clarinet_register_zone_threshold_clarion_upper_midi")
_CLAR_SAME_SUBTYPE_ZONE_SIM = timbral_float_tuple("clarinet_register_same_subtype_zone_sim", length=3)
_CLAR_SAME_SUBTYPE_FINE_TAU = timbral_float("clarinet_register_same_subtype_fine_tau")
_CLAR_SAME_SUBTYPE_BLEND_ZONE = timbral_float("clarinet_register_same_subtype_blend_zone")
_CLAR_SAME_SUBTYPE_BLEND_FINE = timbral_float("clarinet_register_same_subtype_blend_fine")
_CLAR_CROSS_SUBTYPE_FINE_TAU = timbral_float("clarinet_register_cross_subtype_fine_tau")
_CLAR_CROSS_SUBTYPE_BLEND_ALIGN = timbral_float("clarinet_register_cross_subtype_blend_align")
_CLAR_CROSS_SUBTYPE_BLEND_FINE = timbral_float("clarinet_register_cross_subtype_blend_fine")


def is_clarinet_family(family: str) -> bool:
    return family == FAMILY_CLARINETS


def clarinet_subtype_index(canonical_instrument: str) -> int:
    return int(_CLAR_INST_TO_IDX.get(canonical_instrument, 4))


def clarinet_subtype_similarity(inst_a: str, inst_b: str) -> float:
    ia = clarinet_subtype_index(inst_a)
    ib = clarinet_subtype_index(inst_b)
    return float(_SUBTYPE_SIM[ia, ib])


def _norm_height(idx: int, ps: float) -> float:
    lo, hi = _CLAR_TESS_BOUNDS[idx]
    if hi <= lo:
        return 0.5
    return float(np.clip((ps - lo) / (hi - lo), 0.0, 1.0))


def _register_zone(idx: int, ps: float) -> int:
    """0 = chalumeau/low, 1 = clarion/mid, 2 = altissimo/high (soprano); thirds for others."""
    if idx <= 4:
        if ps < _CLAR_ZONE_THRESH_CHAL:
            return 0
        if ps < _CLAR_ZONE_THRESH_CLAR:
            return 1
        return 2
    lo, hi = _CLAR_TESS_BOUNDS[idx]
    if hi <= lo:
        return 1
    t = (ps - lo) / (hi - lo)
    return int(min(2, max(0, t * 3.0)))


def clarinet_register_similarity(inst_a: str, ps_a: float, inst_b: str, ps_b: float) -> float:
    ia = clarinet_subtype_index(inst_a)
    ib = clarinet_subtype_index(inst_b)
    if ia == ib:
        za = _register_zone(ia, ps_a)
        zb = _register_zone(ib, ps_b)
        zd = abs(za - zb)
        sim_z = _CLAR_SAME_SUBTYPE_ZONE_SIM[min(zd, 2)]
        fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _CLAR_SAME_SUBTYPE_FINE_TAU)
        return float(_CLAR_SAME_SUBTYPE_BLEND_ZONE * sim_z + _CLAR_SAME_SUBTYPE_BLEND_FINE * fine)
    ha = _norm_height(ia, ps_a)
    hb = _norm_height(ib, ps_b)
    align = 1.0 - abs(ha - hb)
    fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _CLAR_CROSS_SUBTYPE_FINE_TAU)
    return float(_CLAR_CROSS_SUBTYPE_BLEND_ALIGN * align + _CLAR_CROSS_SUBTYPE_BLEND_FINE * fine)


def clarinet_technique_similarity(tech_a: str, tech_b: str) -> float:
    ia = _TECH_INDEX.get(tech_a, _TECH_INDEX[CLARINET_UNKNOWN])
    ib = _TECH_INDEX.get(tech_b, _TECH_INDEX[CLARINET_UNKNOWN])
    return float(_TECH_MAT[ia, ib])


def pairwise_clarinet_homogeneity(events: list[dict[str, Any]]) -> float:
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
            s_sub = clarinet_subtype_similarity(str(ei["instrument"]), str(ej["instrument"]))
            s_reg = clarinet_register_similarity(
                str(ei["instrument"]),
                float(ei["pitch"]),
                str(ej["instrument"]),
                float(ej["pitch"]),
            )
            s_tec = timbral_event_technique_pair_similarity(
                ei, ej, matrix_similarity=clarinet_technique_similarity, technique_key="technique"
            )
            num += w_pair * (s_sub * s_reg * s_tec)
            den += w_pair
    if den <= 0.0:
        return 1.0
    return float(np.clip(num / den, 0.0, 1.0))


def blend_clarinet_and_legacy_instrument_component(
    h_pairwise_clarinet: float,
    current_instr_component: float,
    clarinet_overlap_mass: float,
    total_overlap_mass: float,
) -> float:
    return blend_clarinet_family_and_legacy_instrument_component(
        h_pairwise_clarinet,
        current_instr_component,
        clarinet_overlap_mass,
        total_overlap_mass,
    )
