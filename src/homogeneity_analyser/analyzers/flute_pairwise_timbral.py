"""
Pairwise symbolic similarity for **flute-family** instruments in H_timbral (notation only).

Orchestral core: ``flute``, ``alto flute``, ``bass flute``, ``piccolo``. Other flute-family
canonicals map to an ``other`` bucket. See ``docs/H_TIMBRAL_FLUTES.md``.
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
from homogeneity_analyser.analyzers.flute_technique import (
    FLUTE_AIR_KEYS,
    FLUTE_BREATHY,
    FLUTE_FLUTTER,
    FLUTE_HARMONIC,
    FLUTE_ORDINARIO,
    FLUTE_UNKNOWN,
    FLUTE_VIBRATO,
    FLUTE_WHISTLE,
)
from homogeneity_analyser.analyzers.string_pairwise_timbral import (
    blend_string_and_legacy_instrument_component as blend_flute_family_and_legacy_instrument_component,
)
from homogeneity_analyser.analyzers.technique_state import timbral_event_technique_pair_similarity
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_FLUTES

# Subtype indices: 0 flute, 1 alto flute, 2 bass flute, 3 piccolo, 4 other (fife, ethnic flutes, …)
_FLUTE_INST_TO_IDX: dict[str, int] = {
    "flute": 0,
    "alto flute": 1,
    "bass flute": 2,
    "piccolo": 3,
    "fife": 4,
    "pan flute": 4,
    "shakuhachi": 4,
    "dizi": 4,
    "bansuri": 4,
    "tin whistle": 4,
    "ocarina": 4,
}

# (low_midi, high_midi) sounding-ish bounds per subtype bucket
_TESS_BOUNDS: list[tuple[float, float]] = timbral_bounds_list("flute_tessitura_bounds_midi")

_SUBTYPE_SIM = timbral_numpy_matrix("flute_subtype_similarity_matrix")

_TECH_KEYS = (
    FLUTE_ORDINARIO,
    FLUTE_VIBRATO,
    FLUTE_BREATHY,
    FLUTE_FLUTTER,
    FLUTE_HARMONIC,
    FLUTE_WHISTLE,
    FLUTE_AIR_KEYS,
    FLUTE_UNKNOWN,
)
_TECH_MAT = timbral_numpy_matrix("flute_technique_similarity_matrix")
_TECH_INDEX = {k: i for i, k in enumerate(_TECH_KEYS)}
_FL_SAME_ZONE = timbral_float_tuple("flute_register_same_subtype_zone_sim", length=4)
_FL_SAME_FINE_TAU = timbral_float("flute_register_same_subtype_fine_tau")
_FL_SAME_BLEND_Z = timbral_float("flute_register_same_subtype_blend_zone")
_FL_SAME_BLEND_F = timbral_float("flute_register_same_subtype_blend_fine")
_FL_CROSS_FINE_TAU = timbral_float("flute_register_cross_subtype_fine_tau")
_FL_CROSS_ALIGN = timbral_float("flute_register_cross_subtype_blend_align")
_FL_CROSS_FINE = timbral_float("flute_register_cross_subtype_blend_fine")


def is_flute_family(family: str) -> bool:
    return family == FAMILY_FLUTES


def flute_subtype_index(canonical_instrument: str) -> int:
    return int(_FLUTE_INST_TO_IDX.get(canonical_instrument, 4))


def flute_subtype_similarity(inst_a: str, inst_b: str) -> float:
    ia = flute_subtype_index(inst_a)
    ib = flute_subtype_index(inst_b)
    return float(_SUBTYPE_SIM[ia, ib])


def _norm_height(idx: int, ps: float) -> float:
    lo, hi = _TESS_BOUNDS[idx]
    if hi <= lo:
        return 0.5
    return float(np.clip((ps - lo) / (hi - lo), 0.0, 1.0))


def _tessitura_zone(idx: int, ps: float) -> int:
    lo, hi = _TESS_BOUNDS[idx]
    if hi <= lo:
        return 1
    t = (ps - lo) / (hi - lo)
    return int(min(3, max(0, t * 4.0)))


def flute_tessitura_similarity(inst_a: str, ps_a: float, inst_b: str, ps_b: float) -> float:
    ia = flute_subtype_index(inst_a)
    ib = flute_subtype_index(inst_b)
    if ia == ib:
        za = _tessitura_zone(ia, ps_a)
        zb = _tessitura_zone(ib, ps_b)
        zd = abs(za - zb)
        sim_z = _FL_SAME_ZONE[min(zd, 3)]
        fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _FL_SAME_FINE_TAU)
        return float(_FL_SAME_BLEND_Z * sim_z + _FL_SAME_BLEND_F * fine)
    ha = _norm_height(ia, ps_a)
    hb = _norm_height(ib, ps_b)
    align = 1.0 - abs(ha - hb)
    fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _FL_CROSS_FINE_TAU)
    return float(_FL_CROSS_ALIGN * align + _FL_CROSS_FINE * fine)


def flute_technique_similarity(tech_a: str, tech_b: str) -> float:
    ia = _TECH_INDEX.get(tech_a, _TECH_INDEX[FLUTE_UNKNOWN])
    ib = _TECH_INDEX.get(tech_b, _TECH_INDEX[FLUTE_UNKNOWN])
    return float(_TECH_MAT[ia, ib])


def pairwise_flute_homogeneity(events: list[dict[str, Any]]) -> float:
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
            s_sub = flute_subtype_similarity(str(ei["instrument"]), str(ej["instrument"]))
            s_tec = timbral_event_technique_pair_similarity(
                ei, ej, matrix_similarity=flute_technique_similarity, technique_key="technique"
            )
            s_tes = flute_tessitura_similarity(
                str(ei["instrument"]),
                float(ei["pitch"]),
                str(ej["instrument"]),
                float(ej["pitch"]),
            )
            num += w_pair * (s_sub * s_tec * s_tes)
            den += w_pair
    if den <= 0.0:
        return 1.0
    return float(np.clip(num / den, 0.0, 1.0))


def blend_flute_and_legacy_instrument_component(
    h_pairwise_flute: float,
    current_instr_component: float,
    flute_overlap_mass: float,
    total_overlap_mass: float,
) -> float:
    return blend_flute_family_and_legacy_instrument_component(
        h_pairwise_flute,
        current_instr_component,
        flute_overlap_mass,
        total_overlap_mass,
    )
