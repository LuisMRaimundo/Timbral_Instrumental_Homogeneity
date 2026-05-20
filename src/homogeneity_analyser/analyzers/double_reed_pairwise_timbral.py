"""
Pairwise symbolic similarity for **orchestral double reeds** (oboe + bassoon families).

Taxonomy keeps ``FAMILY_OBOES`` and ``FAMILY_BASSOONS`` separate; this module adds a
**macro-cluster** similarity table so oboe-side and bassoon-side pairs are graded, not
treated like unrelated woodwinds. See ``docs/H_TIMBRAL_DOUBLE_REEDS.md``.
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
from homogeneity_analyser.analyzers.double_reed_technique import (
    DR_BREATHY,
    DR_FLUTTER,
    DR_MULTIPHONIC,
    DR_ORDINARIO,
    DR_UNKNOWN,
)
from homogeneity_analyser.analyzers.string_pairwise_timbral import (
    blend_string_and_legacy_instrument_component as _blend_overlap_timbral_component,
)
from homogeneity_analyser.analyzers.technique_state import timbral_event_technique_pair_similarity
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OBOES,
)

# Indices: 0 oboe, 1 cor anglais, 2 oboe d'amore, 3 oboe da caccia, 4 bass oboe,
#          5 other oboe-family, 6 bassoon, 7 contrabassoon, 8 other bassoon-family
_DR_INST_TO_IDX: dict[str, int] = {
    "oboe": 0,
    "cor anglais": 1,
    "oboe d'amore": 2,
    "oboe da caccia": 3,
    "bass oboe": 4,
    "musette": 5,
    "shawm": 5,
    "duduk": 5,
    "suona": 5,
    "bassoon": 6,
    "contrabassoon": 7,
    "dulcian": 8,
    "racket": 8,
    "crumhorn": 8,
}

# Sounding MIDI (concert) practical spans per index
_DR_TESS_BOUNDS: list[tuple[float, float]] = timbral_bounds_list("double_reed_tessitura_bounds_midi")

_SUBTYPE_SIM = timbral_numpy_matrix("double_reed_subtype_similarity_matrix")

_TECH_KEYS = (DR_ORDINARIO, DR_FLUTTER, DR_MULTIPHONIC, DR_BREATHY, DR_UNKNOWN)
_TECH_MAT = timbral_numpy_matrix("double_reed_technique_similarity_matrix")
_TECH_INDEX = {k: i for i, k in enumerate(_TECH_KEYS)}
_DR_SAME_SUBTYPE_ZONE_SIM = timbral_float_tuple("double_reed_register_same_subtype_zone_sim", length=3)
_DR_SAME_SUBTYPE_FINE_TAU = timbral_float("double_reed_register_same_subtype_fine_tau")
_DR_SAME_SUBTYPE_BLEND_ZONE = timbral_float("double_reed_register_same_subtype_blend_zone")
_DR_SAME_SUBTYPE_BLEND_FINE = timbral_float("double_reed_register_same_subtype_blend_fine")
_DR_CROSS_SUBTYPE_FINE_TAU = timbral_float("double_reed_register_cross_subtype_fine_tau")
_DR_CROSS_SUBTYPE_BLEND_ALIGN = timbral_float("double_reed_register_cross_subtype_blend_align")
_DR_CROSS_SUBTYPE_BLEND_FINE = timbral_float("double_reed_register_cross_subtype_blend_fine")
_DR_CROSS_STUB_FL_CL = timbral_float("double_reed_cross_family_stub_flute_clarinet")
_DR_CROSS_STUB_OTHER = timbral_float("double_reed_cross_family_stub_other")
_DR_PAIR_SCORE_REG_TAU = timbral_float("double_reed_pair_score_register_exp_tau")


def is_double_reed_family(family: str) -> bool:
    return family in (FAMILY_OBOES, FAMILY_BASSOONS)


def double_reed_subtype_index(canonical_instrument: str) -> int:
    if canonical_instrument in _DR_INST_TO_IDX:
        return int(_DR_INST_TO_IDX[canonical_instrument])
    if "contrabassoon" in canonical_instrument:
        return 7
    if "bassoon" in canonical_instrument:
        return 6
    return 5


def double_reed_instrument_similarity(inst_a: str, inst_b: str) -> float:
    ia = double_reed_subtype_index(inst_a)
    ib = double_reed_subtype_index(inst_b)
    return float(_SUBTYPE_SIM[ia, ib])


def _norm_height(idx: int, ps: float) -> float:
    lo, hi = _DR_TESS_BOUNDS[idx]
    if hi <= lo:
        return 0.5
    return float(np.clip((ps - lo) / (hi - lo), 0.0, 1.0))


def _register_zone(idx: int, ps: float) -> int:
    lo, hi = _DR_TESS_BOUNDS[idx]
    if hi <= lo:
        return 1
    t = (ps - lo) / (hi - lo)
    return int(min(2, max(0, t * 3.0)))


def double_reed_register_similarity(inst_a: str, ps_a: float, inst_b: str, ps_b: float) -> float:
    ia = double_reed_subtype_index(inst_a)
    ib = double_reed_subtype_index(inst_b)
    if ia == ib:
        za = _register_zone(ia, ps_a)
        zb = _register_zone(ib, ps_b)
        zd = abs(za - zb)
        sim_z = _DR_SAME_SUBTYPE_ZONE_SIM[min(zd, 2)]
        fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _DR_SAME_SUBTYPE_FINE_TAU)
        return float(_DR_SAME_SUBTYPE_BLEND_ZONE * sim_z + _DR_SAME_SUBTYPE_BLEND_FINE * fine)
    ha = _norm_height(ia, ps_a)
    hb = _norm_height(ib, ps_b)
    align = 1.0 - abs(ha - hb)
    fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _DR_CROSS_SUBTYPE_FINE_TAU)
    return float(_DR_CROSS_SUBTYPE_BLEND_ALIGN * align + _DR_CROSS_SUBTYPE_BLEND_FINE * fine)


def double_reed_technique_similarity(tech_a: str, tech_b: str) -> float:
    ia = _TECH_INDEX.get(tech_a, _TECH_INDEX[DR_UNKNOWN])
    ib = _TECH_INDEX.get(tech_b, _TECH_INDEX[DR_UNKNOWN])
    return float(_TECH_MAT[ia, ib])


def _cross_family_instrument_stub(family_non_dr: str) -> float:
    """Low instrument factor when pairing double reed with common non–double-reed winds."""
    if family_non_dr in (FAMILY_FLUTES, FAMILY_CLARINETS):
        return _DR_CROSS_STUB_FL_CL
    return _DR_CROSS_STUB_OTHER


def double_reed_pair_score(
    inst_a: str,
    fam_a: str,
    ps_a: float,
    tech_a: str,
    inst_b: str,
    fam_b: str,
    ps_b: float,
    tech_b: str,
) -> float:
    """
    Symbolic pair score for tests and diagnostics.

    When both sides are oboe/bassoon families, uses the full table × register × technique.
    When exactly one side is double-reed and the other is flute/clarinet (etc.), uses a
    low cross-cluster stub so e.g. oboe+bassoon > oboe+flute at comparable registers.
    """
    da = is_double_reed_family(fam_a)
    db = is_double_reed_family(fam_b)
    tech = double_reed_technique_similarity(tech_a, tech_b)
    reg = math.exp(-abs(float(ps_a) - float(ps_b)) / _DR_PAIR_SCORE_REG_TAU)
    if da and db:
        return float(
            double_reed_instrument_similarity(inst_a, inst_b)
            * double_reed_register_similarity(inst_a, ps_a, inst_b, ps_b)
            * tech
        )
    if da ^ db:
        fam_nd = fam_b if da else fam_a
        stub = _cross_family_instrument_stub(fam_nd)
        return float(stub * reg * tech)
    return float(0.5 * reg * tech)


def pairwise_double_reed_homogeneity(events: list[dict[str, Any]]) -> float:
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
            s_inst = double_reed_instrument_similarity(str(ei["instrument"]), str(ej["instrument"]))
            s_reg = double_reed_register_similarity(
                str(ei["instrument"]),
                float(ei["pitch"]),
                str(ej["instrument"]),
                float(ej["pitch"]),
            )
            s_tec = timbral_event_technique_pair_similarity(
                ei, ej, matrix_similarity=double_reed_technique_similarity, technique_key="technique"
            )
            num += w_pair * (s_inst * s_reg * s_tec)
            den += w_pair
    if den <= 0.0:
        return 1.0
    return float(np.clip(num / den, 0.0, 1.0))


def blend_double_reed_and_legacy_instrument_component(
    h_pairwise_double_reed: float,
    current_instr_component: float,
    double_reed_overlap_mass: float,
    total_overlap_mass: float,
) -> float:
    return _blend_overlap_timbral_component(
        h_pairwise_double_reed,
        current_instr_component,
        double_reed_overlap_mass,
        total_overlap_mass,
    )
