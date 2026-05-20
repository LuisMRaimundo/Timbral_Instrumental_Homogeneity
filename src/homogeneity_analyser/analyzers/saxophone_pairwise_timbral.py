"""
Pairwise symbolic similarity for **saxophone-family** instruments in H_timbral (notation only).

Canonical subtypes follow ``instrument_taxonomy``; generic ``saxophone`` maps to a dedicated
low-confidence bucket. See ``docs/H_TIMBRAL_SAXOPHONES.md``.
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
from homogeneity_analyser.analyzers.saxophone_technique import (
    SAX_BREATHY,
    SAX_FLUTTER,
    SAX_GROWL,
    SAX_ORDINARIO,
    SAX_OVERTONE_SPECIAL,
    SAX_SLAP,
    SAX_SUBTONE,
    SAX_UNKNOWN,
)
from homogeneity_analyser.analyzers.string_pairwise_timbral import (
    blend_string_and_legacy_instrument_component as _blend_overlap_timbral_component,
)
from homogeneity_analyser.analyzers.technique_state import timbral_event_technique_pair_similarity
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_SAXOPHONES

# 0 sopranino … 5 bass; 6 = generic / unspecified saxophone
_SAX_INST_TO_IDX: dict[str, int] = {
    "sopranino saxophone": 0,
    "soprano saxophone": 1,
    "alto saxophone": 2,
    "tenor saxophone": 3,
    "baritone saxophone": 4,
    "bass saxophone": 5,
    "saxophone": 6,
}

# Practical sounding MIDI spans (concert)
_SAX_TESS_BOUNDS: list[tuple[float, float]] = timbral_bounds_list("saxophone_tessitura_bounds_midi")

_SUBTYPE_SIM = timbral_numpy_matrix("saxophone_subtype_similarity_matrix")

_TECH_KEYS = (
    SAX_ORDINARIO,
    SAX_SUBTONE,
    SAX_GROWL,
    SAX_FLUTTER,
    SAX_SLAP,
    SAX_BREATHY,
    SAX_OVERTONE_SPECIAL,
    SAX_UNKNOWN,
)
_TECH_MAT = timbral_numpy_matrix("saxophone_technique_similarity_matrix")
_TECH_INDEX = {k: i for i, k in enumerate(_TECH_KEYS)}
_SAX_SAME_ZONE = timbral_float_tuple("saxophone_register_same_subtype_zone_sim", length=4)
_SAX_SAME_FINE_TAU = timbral_float("saxophone_register_same_subtype_fine_tau")
_SAX_SAME_BLEND_Z = timbral_float("saxophone_register_same_subtype_blend_zone")
_SAX_SAME_BLEND_F = timbral_float("saxophone_register_same_subtype_blend_fine")
_SAX_CROSS_FINE_TAU = timbral_float("saxophone_register_cross_subtype_fine_tau")
_SAX_CROSS_ALIGN = timbral_float("saxophone_register_cross_subtype_blend_align")
_SAX_CROSS_FINE = timbral_float("saxophone_register_cross_subtype_blend_fine")


def is_saxophone_family(family: str) -> bool:
    return family == FAMILY_SAXOPHONES


def saxophone_subtype_index(canonical_instrument: str) -> int:
    return int(_SAX_INST_TO_IDX.get(canonical_instrument, 6))


def saxophone_subtype_similarity(inst_a: str, inst_b: str) -> float:
    ia = saxophone_subtype_index(inst_a)
    ib = saxophone_subtype_index(inst_b)
    return float(_SUBTYPE_SIM[ia, ib])


def _norm_height(idx: int, ps: float) -> float:
    lo, hi = _SAX_TESS_BOUNDS[idx]
    if hi <= lo:
        return 0.5
    return float(np.clip((ps - lo) / (hi - lo), 0.0, 1.0))


def _tessitura_zone(idx: int, ps: float) -> int:
    lo, hi = _SAX_TESS_BOUNDS[idx]
    if hi <= lo:
        return 1
    t = (ps - lo) / (hi - lo)
    return int(min(3, max(0, t * 4.0)))


def saxophone_tessitura_similarity(inst_a: str, ps_a: float, inst_b: str, ps_b: float) -> float:
    ia = saxophone_subtype_index(inst_a)
    ib = saxophone_subtype_index(inst_b)
    if ia == ib:
        za = _tessitura_zone(ia, ps_a)
        zb = _tessitura_zone(ib, ps_b)
        zd = abs(za - zb)
        sim_z = _SAX_SAME_ZONE[min(zd, 3)]
        fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _SAX_SAME_FINE_TAU)
        return float(_SAX_SAME_BLEND_Z * sim_z + _SAX_SAME_BLEND_F * fine)
    ha = _norm_height(ia, ps_a)
    hb = _norm_height(ib, ps_b)
    align = 1.0 - abs(ha - hb)
    fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _SAX_CROSS_FINE_TAU)
    return float(_SAX_CROSS_ALIGN * align + _SAX_CROSS_FINE * fine)


def saxophone_technique_similarity(tech_a: str, tech_b: str) -> float:
    ia = _TECH_INDEX.get(tech_a, _TECH_INDEX[SAX_UNKNOWN])
    ib = _TECH_INDEX.get(tech_b, _TECH_INDEX[SAX_UNKNOWN])
    return float(_TECH_MAT[ia, ib])


def pairwise_saxophone_homogeneity(events: list[dict[str, Any]]) -> float:
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
            s_sub = saxophone_subtype_similarity(str(ei["instrument"]), str(ej["instrument"]))
            s_tes = saxophone_tessitura_similarity(
                str(ei["instrument"]),
                float(ei["pitch"]),
                str(ej["instrument"]),
                float(ej["pitch"]),
            )
            s_tec = timbral_event_technique_pair_similarity(
                ei, ej, matrix_similarity=saxophone_technique_similarity, technique_key="technique"
            )
            num += w_pair * (s_sub * s_tes * s_tec)
            den += w_pair
    if den <= 0.0:
        return 1.0
    return float(np.clip(num / den, 0.0, 1.0))


def blend_saxophone_and_legacy_instrument_component(
    h_pairwise_saxophone: float,
    current_instr_component: float,
    saxophone_overlap_mass: float,
    total_overlap_mass: float,
) -> float:
    return _blend_overlap_timbral_component(
        h_pairwise_saxophone,
        current_instr_component,
        saxophone_overlap_mass,
        total_overlap_mass,
    )
