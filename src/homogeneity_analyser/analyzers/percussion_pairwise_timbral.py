"""
Second-generation pairwise symbolic similarity for **percussion** in H_timbral.

Combines instrument/macro-class ontology, pitch-role handling, coarse resonance/noise
proxies, technique, and register-or-size similarity. See ``docs/H_TIMBRAL_PERCUSSION.md``.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from homogeneity_analyser.acoustic_profiles.model_config import (
    get_timbral_acoustic_value,
    timbral_float,
    timbral_float_tuple,
    timbral_numpy_matrix,
)
from homogeneity_analyser.analyzers.percussion_ontology import (
    PercussionMacroClass,
    PitchStatus,
    get_percussion_meta,
)
from homogeneity_analyser.analyzers.percussion_technique import (
    PERC_BOWED,
    PERC_BRUSHES,
    PERC_CYM_CRASH,
    PERC_CYM_SUSPENDED,
    PERC_DAMPED,
    PERC_MALLET_FELT,
    PERC_MALLET_HARD,
    PERC_MALLET_SOFT,
    PERC_MALLET_YARN,
    PERC_OPEN,
    PERC_ORDINARIO,
    PERC_RIM,
    PERC_ROLLED,
    PERC_SNARE_OFF,
    PERC_SNARE_ON,
    PERC_STICKS,
    PERC_UNKNOWN,
    PERC_VIB_NO_PEDAL,
    PERC_VIB_PEDAL,
)
from homogeneity_analyser.analyzers.string_pairwise_timbral import (
    blend_string_and_legacy_instrument_component as _blend_overlap_timbral_component,
)
from homogeneity_analyser.analyzers.technique_state import timbral_event_technique_pair_similarity
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_PERCUSSION

_MACRO_ORDER: list[PercussionMacroClass] = [
    PercussionMacroClass.TUNED_MEMBRANOPHONE,
    PercussionMacroClass.UNTUNED_MEMBRANOPHONE,
    PercussionMacroClass.WOODEN_BAR_IDIOPHONE,
    PercussionMacroClass.METALLIC_PITCHED_IDIOPHONE,
    PercussionMacroClass.PLATE_SHELL_METAL,
    PercussionMacroClass.SMALL_HIGH_METAL,
    PercussionMacroClass.MISC_SMALL_IDIOPHONE,
    PercussionMacroClass.GENERIC,
]

# Cross-macro baseline (symmetric); values from ``default_profiles.json`` (pre-symmetrized export).
_MACRO_CROSS = timbral_numpy_matrix("percussion_macro_cross_similarity_matrix")

_SAME_MACRO_DEFAULT: dict[PercussionMacroClass, float] = {
    PercussionMacroClass[k]: float(v)
    for k, v in get_timbral_acoustic_value("percussion_same_macro_default_similarity").items()
}


def _load_instrument_pair_overrides() -> dict[tuple[str, str], float]:
    """Load pair overrides keyed the same way legacy ``_INSTRUMENT_PAIR`` was *queried*.

    The historical dict used author-chosen ``(a, b)`` tuple order, but
    :func:`percussion_instrument_similarity` always looked up ``_pair_key(inst_a, inst_b)``
    (lexicographically sorted). An entry only took effect when that sorted key equalled the
    stored tuple — e.g. ``("snare drum", "bass drum")`` in the dict never matched
    ``("bass drum", "snare drum")`` from ``_pair_key``, so the same-macro default applied.
    """
    raw = get_timbral_acoustic_value("percussion_instrument_pair_overrides")
    out: dict[tuple[str, str], float] = {}
    for k, v in raw.items():
        a, b = str(k).split("|", 1)
        t_orig = (a, b)
        t_sorted = t_orig if a <= b else (b, a)
        if t_orig == t_sorted:
            out[t_sorted] = float(v)
    return out


_INSTRUMENT_PAIR = _load_instrument_pair_overrides()
_PERC_SAME_MACRO_FALLBACK = timbral_float("percussion_same_macro_map_fallback")


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)


def is_percussion_family(family: str) -> bool:
    return family == FAMILY_PERCUSSION


def percussion_instrument_similarity(inst_a: str, inst_b: str) -> float:
    if inst_a == inst_b:
        return 1.0
    k = _pair_key(inst_a, inst_b)
    if k in _INSTRUMENT_PAIR:
        return float(_INSTRUMENT_PAIR[k])
    ma = get_percussion_meta(inst_a).macro
    mb = get_percussion_meta(inst_b).macro
    if ma == mb:
        return float(_SAME_MACRO_DEFAULT.get(ma, _PERC_SAME_MACRO_FALLBACK))
    ia = _MACRO_ORDER.index(ma)
    ib = _MACRO_ORDER.index(mb)
    return float(_MACRO_CROSS[ia, ib])


def _pitch_status_similarity(ps_a: PitchStatus, ps_b: PitchStatus) -> float:
    if ps_a == ps_b:
        return 1.0
    pair = {ps_a, ps_b}
    if pair == {PitchStatus.PITCHED, PitchStatus.QUASI_PITCHED}:
        return timbral_float("percussion_pitch_status_similarity_quasi_pitched")
    if PitchStatus.UNPITCHED in pair and PitchStatus.PITCHED in pair:
        return timbral_float("percussion_pitch_status_similarity_unpitched_pitched")
    if PitchStatus.UNPITCHED in pair and PitchStatus.QUASI_PITCHED in pair:
        return timbral_float("percussion_pitch_status_similarity_unpitched_quasi")
    return timbral_float("percussion_pitch_status_similarity_fallback")


def _resonance_noise_factors(meta_a, meta_b, tech_a: str, tech_b: str) -> tuple[float, float]:
    rd = abs(int(meta_a.resonance) - int(meta_b.resonance))
    res_sim = float(
        timbral_float("percussion_resonance_base")
        + timbral_float("percussion_resonance_scale") * math.exp(-rd * timbral_float("percussion_resonance_decay"))
    )
    nd = abs(int(meta_a.noise) - int(meta_b.noise))
    noise_sim = float(
        timbral_float("percussion_noise_base")
        + timbral_float("percussion_noise_scale") * math.exp(-nd * timbral_float("percussion_noise_decay"))
    )
    if tech_a == PERC_DAMPED or tech_b == PERC_DAMPED:
        if tech_a == PERC_DAMPED and tech_b == PERC_DAMPED:
            pass
        elif PERC_ORDINARIO in (tech_a, tech_b) or PERC_OPEN in (tech_a, tech_b):
            res_sim *= timbral_float("percussion_damped_res_scale")
            noise_sim *= timbral_float("percussion_damped_noise_scale")
    return res_sim, noise_sim


_TECH_ORDER = (
    PERC_ORDINARIO,
    PERC_MALLET_HARD,
    PERC_MALLET_SOFT,
    PERC_MALLET_FELT,
    PERC_MALLET_YARN,
    PERC_STICKS,
    PERC_BRUSHES,
    PERC_ROLLED,
    PERC_BOWED,
    PERC_DAMPED,
    PERC_OPEN,
    PERC_SNARE_ON,
    PERC_SNARE_OFF,
    PERC_VIB_PEDAL,
    PERC_VIB_NO_PEDAL,
    PERC_CYM_SUSPENDED,
    PERC_CYM_CRASH,
    PERC_RIM,
    PERC_UNKNOWN,
)
_TECH_INDEX = {k: i for i, k in enumerate(_TECH_ORDER)}
_TECH_MAT = timbral_numpy_matrix("percussion_technique_similarity_matrix")
_PERC_PITCHED_ZONE_SIM = timbral_float_tuple("percussion_register_pitched_zone_sim", length=4)
_PERC_PITCHED_FINE_TAU = timbral_float("percussion_register_pitched_fine_tau")
_PERC_PITCHED_BLEND_Z = timbral_float("percussion_register_pitched_blend_zone")
_PERC_PITCHED_BLEND_F = timbral_float("percussion_register_pitched_blend_fine")
_PERC_PITCHED_QUASI_SCALE = timbral_float("percussion_register_pitched_quasi_scale")
_PERC_QUASI_QUASI_SCALE = timbral_float("percussion_register_quasi_quasi_scale")
_PERC_UNP_BIN_DEC = timbral_float("percussion_register_unpitched_bin_decay")
_PERC_UNP_BIN_BASE = timbral_float("percussion_register_unpitched_bin_base")
_PERC_UNP_BIN_SCALE = timbral_float("percussion_register_unpitched_bin_scale")
_PERC_UNP_PS_TAU = timbral_float("percussion_register_unpitched_ps_tau")
_PERC_UNP_BLEND_BIN = timbral_float("percussion_register_unpitched_blend_bin")
_PERC_UNP_BLEND_PS = timbral_float("percussion_register_unpitched_blend_ps")
_PERC_FALLBACK_TAU = timbral_float("percussion_register_fallback_exp_tau")
_PERC_FALLBACK_A = timbral_float("percussion_register_fallback_a")
_PERC_FALLBACK_B = timbral_float("percussion_register_fallback_b")
_PERC_PAIR_RES_A = timbral_float("percussion_pairwise_resonance_weight_a")
_PERC_PAIR_RES_B = timbral_float("percussion_pairwise_resonance_weight_b")
_PERC_PAIR_NOISE_A = timbral_float("percussion_pairwise_noise_weight_a")
_PERC_PAIR_NOISE_B = timbral_float("percussion_pairwise_noise_weight_b")
_PERC_UNP_PROXY_EMPTY = timbral_float("percussion_unpitched_proxy_empty")
_PERC_UNP_PROXY_SINGLE = timbral_float("percussion_unpitched_proxy_single")
_PERC_UNP_PROXY_DIV = timbral_float("percussion_unpitched_proxy_span_divisor")
_PERC_UNP_PROXY_MIN = timbral_float("percussion_unpitched_proxy_min")
_PERC_UNP_PROXY_MAX = timbral_float("percussion_unpitched_proxy_max")


def percussion_technique_similarity(tech_a: str, tech_b: str) -> float:
    ia = _TECH_INDEX.get(tech_a, _TECH_INDEX[PERC_UNKNOWN])
    ib = _TECH_INDEX.get(tech_b, _TECH_INDEX[PERC_UNKNOWN])
    return float(_TECH_MAT[ia, ib])


def _tessitura_zone(lo: float, hi: float, ps: float) -> int:
    if hi <= lo:
        return 1
    t = (ps - lo) / (hi - lo)
    return int(min(3, max(0, t * 4.0)))


def percussion_register_size_similarity(
    inst_a: str,
    ps_a: float,
    tech_a: str,
    inst_b: str,
    ps_b: float,
    tech_b: str,
) -> float:
    ma = get_percussion_meta(inst_a)
    mb = get_percussion_meta(inst_b)

    pitched_a = ma.pitch_status == PitchStatus.PITCHED and ma.tessitura_lo is not None
    pitched_b = mb.pitch_status == PitchStatus.PITCHED and mb.tessitura_lo is not None
    quasi_a = ma.pitch_status == PitchStatus.QUASI_PITCHED and ma.tessitura_lo is not None
    quasi_b = mb.pitch_status == PitchStatus.QUASI_PITCHED and mb.tessitura_lo is not None

    def _pitched_pair(lo_a, hi_a, lo_b, hi_b) -> float:
        za = _tessitura_zone(lo_a, hi_a, ps_a)
        zb = _tessitura_zone(lo_b, hi_b, ps_b)
        zd = abs(za - zb)
        sim_z = _PERC_PITCHED_ZONE_SIM[min(zd, 3)]
        fine = math.exp(-abs(float(ps_a) - float(ps_b)) / _PERC_PITCHED_FINE_TAU)
        return float(_PERC_PITCHED_BLEND_Z * sim_z + _PERC_PITCHED_BLEND_F * fine)

    if (
        pitched_a
        and pitched_b
        and ma.tessitura_hi is not None
        and mb.tessitura_hi is not None
        and ma.tessitura_lo is not None
        and mb.tessitura_lo is not None
    ):
        return _pitched_pair(ma.tessitura_lo, ma.tessitura_hi, mb.tessitura_lo, mb.tessitura_hi)
    if (
        pitched_a
        and quasi_b
        and ma.tessitura_lo is not None
        and ma.tessitura_hi is not None
        and mb.tessitura_lo is not None
        and mb.tessitura_hi is not None
    ):
        lo_a, hi_a = ma.tessitura_lo, ma.tessitura_hi
        lo_b, hi_b = mb.tessitura_lo, mb.tessitura_hi
        return float(_PERC_PITCHED_QUASI_SCALE * _pitched_pair(lo_a, hi_a, lo_b, hi_b))
    if (
        pitched_b
        and quasi_a
        and ma.tessitura_lo is not None
        and ma.tessitura_hi is not None
        and mb.tessitura_lo is not None
        and mb.tessitura_hi is not None
    ):
        lo_a, hi_a = ma.tessitura_lo, ma.tessitura_hi
        lo_b, hi_b = mb.tessitura_lo, mb.tessitura_hi
        return float(_PERC_PITCHED_QUASI_SCALE * _pitched_pair(lo_a, hi_a, lo_b, hi_b))
    if quasi_a and quasi_b and ma.tessitura_lo and mb.tessitura_lo:
        if ma.tessitura_hi is None or mb.tessitura_hi is None:
            return float(
                _PERC_FALLBACK_A * math.exp(-abs(float(ps_a) - float(ps_b)) / _PERC_FALLBACK_TAU) + _PERC_FALLBACK_B
            )
        lo_a, hi_a = ma.tessitura_lo, ma.tessitura_hi
        lo_b, hi_b = mb.tessitura_lo, mb.tessitura_hi
        return float(_PERC_QUASI_QUASI_SCALE * _pitched_pair(lo_a, hi_a, lo_b, hi_b))

    if ma.pitch_status == PitchStatus.UNPITCHED and mb.pitch_status == PitchStatus.UNPITCHED:
        bd = abs(int(ma.size_bin) - int(mb.size_bin))
        bin_sim = float(_PERC_UNP_BIN_BASE + _PERC_UNP_BIN_SCALE * math.exp(-bd / _PERC_UNP_BIN_DEC))
        weak_ps = float(math.exp(-abs(float(ps_a) - float(ps_b)) / _PERC_UNP_PS_TAU))
        return float(_PERC_UNP_BLEND_BIN * bin_sim + _PERC_UNP_BLEND_PS * weak_ps)

    return float(_PERC_FALLBACK_A * math.exp(-abs(float(ps_a) - float(ps_b)) / _PERC_FALLBACK_TAU) + _PERC_FALLBACK_B)


def pairwise_percussion_homogeneity(events: list[dict[str, Any]]) -> float:
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
            ia = str(ei["instrument"])
            ib = str(ej["instrument"])
            ps_a = float(ei["pitch"])
            ps_b = float(ej["pitch"])
            ta = str(ei.get("technique", PERC_ORDINARIO))
            tb = str(ej.get("technique", PERC_ORDINARIO))
            meta_a = get_percussion_meta(ia)
            meta_b = get_percussion_meta(ib)
            s_inst = percussion_instrument_similarity(ia, ib)
            s_ps = _pitch_status_similarity(meta_a.pitch_status, meta_b.pitch_status)
            s_res, s_noise = _resonance_noise_factors(meta_a, meta_b, ta, tb)
            s_tech = timbral_event_technique_pair_similarity(
                ei, ej, matrix_similarity=percussion_technique_similarity, technique_key="technique"
            )
            s_reg = percussion_register_size_similarity(ia, ps_a, ta, ib, ps_b, tb)
            combined = (
                s_inst
                * s_ps
                * s_tech
                * s_reg
                * (_PERC_PAIR_RES_A + _PERC_PAIR_RES_B * s_res)
                * (_PERC_PAIR_NOISE_A + _PERC_PAIR_NOISE_B * s_noise)
            )
            num += w_pair * float(np.clip(combined, 0.0, 1.0))
            den += w_pair
    if den <= 0.0:
        return 1.0
    return float(np.clip(num / den, 0.0, 1.0))


def unpitched_percussion_register_proxy(events: list[dict[str, Any]]) -> float:
    """
    Register-like factor for **unpitched** percussion when global pitch span is meaningless.

    Uses ontology ``size_bin`` spread across unpitched hits in the window (notation-only).
    """
    bins: list[int] = []
    for ei in events or []:
        inst = str(ei.get("instrument", ""))
        meta = get_percussion_meta(inst)
        if meta.pitch_status != PitchStatus.UNPITCHED:
            continue
        wi = float(ei.get("overlap_ql", 0.0) or 0.0)
        if wi <= 0.0:
            continue
        bins.append(int(meta.size_bin))
    if not bins:
        return _PERC_UNP_PROXY_EMPTY
    if len(bins) == 1:
        return _PERC_UNP_PROXY_SINGLE
    span = max(bins) - min(bins)
    return float(np.clip(1.0 / (1.0 + span / _PERC_UNP_PROXY_DIV), _PERC_UNP_PROXY_MIN, _PERC_UNP_PROXY_MAX))


def blend_percussion_and_legacy_instrument_component(
    h_pairwise_percussion: float,
    current_instr_component: float,
    percussion_overlap_mass: float,
    total_overlap_mass: float,
) -> float:
    return _blend_overlap_timbral_component(
        h_pairwise_percussion,
        current_instr_component,
        percussion_overlap_mass,
        total_overlap_mass,
    )
