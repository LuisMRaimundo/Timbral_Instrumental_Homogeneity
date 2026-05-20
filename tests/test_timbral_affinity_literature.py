"""Literature-governed symbolic timbral affinity (optional H_TI relief layer)."""

from __future__ import annotations

import math

import pytest

from homogeneity_analyser.analyzers.timbral_affinity import (
    compute_timbral_affinity_bundle_for_window,
    compute_timbral_affinity_uniformity,
    finalize_timbral_affinity_dynamic,
    pairwise_similarity,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_KEYBOARD,
    FAMILY_OBOES,
    FAMILY_OTHER,
    FAMILY_PERCUSSION,
    FAMILY_STRINGS,
)


def _ev(
    instrument: str,
    family: str,
    ol: float = 1.0,
    *,
    technique_state: dict | None = None,
) -> dict:
    d: dict = {
        "instrument": instrument,
        "family": family,
        "technique_uniformity_key": "ordinary_default_uniform",
        "dynamic_mark": "pp",
        "hairpin": "none",
    }
    if technique_state is not None:
        d["technique_state"] = technique_state
    return d


def _contrib(*items: tuple[dict, float]) -> list[tuple[dict, float]]:
    return list(items)


def test_strict_profile_timbral_affinity_equals_instrument_uniformity_two_events() -> None:
    a = _ev("clarinet", FAMILY_CLARINETS, 0.5)
    b = _ev("bass clarinet", FAMILY_CLARINETS, 0.5)
    c = _contrib((a, 0.5), (b, 0.5))
    inst_u = 0.5  # two distinct instruments equal mass
    out = compute_timbral_affinity_uniformity(c, profile="strict")
    assert out["timbral_affinity_uniformity"] == pytest.approx(inst_u)


def test_relief_zero_hti_affinity_equals_core() -> None:
    feats = {
        "instrument_uniformity": 0.625,
        "family_uniformity": 1.0,
        "instrumental_subfamily_uniformity": 1.0,
        "technique_coverage_status": "explicit_uniform",
        "technique_uniformity": 1.0,
        "register_coverage_status": "pitched",
        "register_proximity": 1.0,
    }

    def _fake_compute_h_ti(f, **kwargs):
        comp = kwargs.get("instrument_uniformity_component")
        if comp is not None and math.isfinite(float(comp)):
            return float(comp), {}, {"instrument_uniformity": 1.0}
        return float(f["instrument_uniformity"]), {}, {"instrument_uniformity": 1.0}

    c = _contrib(
        (_ev("clarinet", FAMILY_CLARINETS, 0.75), 0.75),
        (_ev("bass clarinet", FAMILY_CLARINETS, 0.25), 0.25),
    )
    aff = compute_timbral_affinity_bundle_for_window(
        c,
        feats,
        profile="conservative",
        relief_factor=0.0,
        instrument_uniformity=float(feats["instrument_uniformity"]),
        compute_h_ti=_fake_compute_h_ti,
        feats_for_h_ti=feats,
        w_instr=1.0,
        w_fam=0.0,
        w_tech=0.0,
        w_reg=0.0,
        collect_pairs=False,
    )
    assert aff["H_TI_affinity_literature_relieved"] == pytest.approx(0.625)


def test_clarinet_bass_clarinet_tau_exceeds_instrument_uniformity() -> None:
    c = _contrib(
        (_ev("clarinet", FAMILY_CLARINETS, 0.75), 0.75),
        (_ev("bass clarinet", FAMILY_CLARINETS, 0.25), 0.25),
    )
    out = compute_timbral_affinity_uniformity(c, profile="conservative")
    assert out["timbral_affinity_uniformity"] > 0.625


def test_oboe_cor_higher_than_oboe_bassoon() -> None:
    s1, _, _ = pairwise_similarity(
        _ev("oboe", FAMILY_OBOES, 1.0),
        _ev("cor anglais", FAMILY_OBOES, 1.0),
        profile="conservative",
    )
    s2, _, _ = pairwise_similarity(
        _ev("oboe", FAMILY_OBOES, 1.0),
        _ev("bassoon", FAMILY_BASSOONS, 1.0),
        profile="conservative",
    )
    assert s1 > s2


def test_oboe_bassoon_higher_than_oboe_trumpet() -> None:
    s_ob_bsn, _, _ = pairwise_similarity(
        _ev("oboe", FAMILY_OBOES, 1.0),
        _ev("bassoon", FAMILY_BASSOONS, 1.0),
        profile="conservative",
    )
    s_ob_tpt, _, _ = pairwise_similarity(
        _ev("oboe", FAMILY_OBOES, 1.0),
        _ev("trumpet", FAMILY_BRASS, 1.0),
        profile="conservative",
    )
    assert s_ob_bsn > s_ob_tpt


def test_bassoon_contrabassoon_high() -> None:
    s, _, _ = pairwise_similarity(
        _ev("bassoon", FAMILY_BASSOONS, 1.0),
        _ev("contrabassoon", FAMILY_BASSOONS, 1.0),
        profile="conservative",
    )
    assert s >= 0.88


def test_flute_alto_higher_than_flute_piccolo() -> None:
    s_alto, _, _ = pairwise_similarity(
        _ev("flute", FAMILY_FLUTES, 1.0),
        _ev("alto flute", FAMILY_FLUTES, 1.0),
        profile="conservative",
    )
    s_pic, _, _ = pairwise_similarity(
        _ev("flute", FAMILY_FLUTES, 1.0),
        _ev("piccolo", FAMILY_FLUTES, 1.0),
        profile="conservative",
    )
    assert s_alto > s_pic


def test_trumpet_cornet_high_flugel_lower() -> None:
    s_tc, _, _ = pairwise_similarity(
        _ev("trumpet", FAMILY_BRASS, 1.0),
        _ev("cornet", FAMILY_BRASS, 1.0),
        profile="moderate",
    )
    s_tf, _, _ = pairwise_similarity(
        _ev("trumpet", FAMILY_BRASS, 1.0),
        _ev("flugelhorn", FAMILY_BRASS, 1.0),
        profile="moderate",
    )
    assert s_tc > s_tf


def test_horn_trombone_moderate_not_identity() -> None:
    s, rid, _sk = pairwise_similarity(
        _ev("horn", FAMILY_BRASS, 1.0),
        _ev("trombone", FAMILY_BRASS, 1.0),
        profile="moderate",
    )
    assert 0.45 <= s <= 0.75
    assert "horn" in rid or "lip" in rid or "brass" in rid


def test_string_pizz_harp_moderate_profile() -> None:
    vln = _ev(
        "violin",
        FAMILY_STRINGS,
        1.0,
        technique_state={
            "family": FAMILY_STRINGS,
            "instrument": "violin",
            "primary": "pizzicato",
            "mute": "none",
            "contact_point": "ordinary",
            "excitation": "ordinary",
            "articulation_effect": "none",
            "resonance": "ordinary",
            "noise_component": "ordinary",
            "pressure": "ordinary",
            "beater": "ordinary",
            "stroke": "ordinary",
            "special": (),
        },
    )
    hp = _ev("harp", FAMILY_STRINGS, 1.0)
    s, _, _ = pairwise_similarity(vln, hp, profile="moderate")
    assert s >= 0.5


def test_pizz_woodblock_not_in_conservative() -> None:
    vln = _ev(
        "violin",
        FAMILY_STRINGS,
        1.0,
        technique_state={
            "family": FAMILY_STRINGS,
            "instrument": "violin",
            "primary": "pizzicato",
            "mute": "none",
            "contact_point": "ordinary",
            "excitation": "ordinary",
            "articulation_effect": "none",
            "resonance": "ordinary",
            "noise_component": "ordinary",
            "pressure": "ordinary",
            "beater": "ordinary",
            "stroke": "ordinary",
            "special": (),
        },
    )
    wb = _ev("wood block", FAMILY_PERCUSSION, 1.0)
    s_cons, _, _ = pairwise_similarity(vln, wb, profile="conservative")
    s_mod, _, _ = pairwise_similarity(vln, wb, profile="moderate")
    assert s_mod >= s_cons


def test_col_legno_woodblock_moderate() -> None:
    vln = _ev(
        "violin",
        FAMILY_STRINGS,
        1.0,
        technique_state={
            "family": FAMILY_STRINGS,
            "instrument": "violin",
            "primary": "col legno battuto",
            "mute": "none",
            "contact_point": "ordinary",
            "excitation": "ordinary",
            "articulation_effect": "none",
            "resonance": "ordinary",
            "noise_component": "ordinary",
            "pressure": "ordinary",
            "beater": "ordinary",
            "stroke": "ordinary",
            "special": (),
        },
    )
    wb = _ev("wood block", FAMILY_PERCUSSION, 1.0)
    s, rid, _sk = pairwise_similarity(vln, wb, profile="moderate")
    assert s >= 0.45
    assert "col_legno" in rid or "wood" in rid or "struck" in rid


def test_celesta_glockenspiel_moderate() -> None:
    s, _, _ = pairwise_similarity(
        _ev("celesta", FAMILY_KEYBOARD, 1.0),
        _ev("glockenspiel", FAMILY_PERCUSSION, 1.0),
        profile="moderate",
    )
    assert s >= 0.55


def test_cymbal_tam_tam_moderate() -> None:
    s, _, _ = pairwise_similarity(
        _ev("cymbal", FAMILY_PERCUSSION, 1.0),
        _ev("tam-tam", FAMILY_PERCUSSION, 1.0),
        profile="moderate",
    )
    assert s >= 0.4


def test_unknown_instrument_low_cross() -> None:
    s, _, _ = pairwise_similarity(
        _ev("clarinet", FAMILY_CLARINETS, 1.0),
        _ev("not_a_real_instrument_xyz", FAMILY_OTHER, 1.0),
        profile="moderate",
    )
    assert s <= 0.2


def test_finalize_dynamic_disabled() -> None:
    aff = {"H_TI_affinity_literature_relieved": 0.7}
    out = finalize_timbral_affinity_dynamic(aff, {}, dynamic_affinity_enabled=False)
    assert math.isnan(float(out["timbral_affinity_dynamic_factor"]))


@pytest.mark.parametrize(
    "inst_a,inst_b",
    [
        ("oboe", "cor anglais"),
        ("clarinet", "bass clarinet"),
        ("flute", "piccolo"),
    ],
)
def test_hti_affinity_exceeds_core_when_relief_positive(inst_a: str, inst_b: str) -> None:
    fam_a = FAMILY_OBOES if "oboe" in inst_a else FAMILY_CLARINETS if "clarinet" in inst_a else FAMILY_FLUTES
    fam_b = (
        FAMILY_OBOES
        if "oboe" in inst_b or "cor" in inst_b
        else FAMILY_CLARINETS
        if "clarinet" in inst_b
        else FAMILY_FLUTES
    )
    c = _contrib((_ev(inst_a, fam_a, 0.5), 0.5), (_ev(inst_b, fam_b, 0.5), 0.5))
    feats = {
        "instrument_uniformity": 0.5,
        "family_uniformity": 1.0,
        "instrumental_subfamily_uniformity": 1.0,
        "technique_coverage_status": "explicit_uniform",
        "technique_uniformity": 1.0,
        "register_coverage_status": "pitched",
        "register_proximity": 1.0,
    }

    def _compute_h_ti(f, **kwargs):
        comp = kwargs.get("instrument_uniformity_component")
        iu = float(comp) if comp is not None and math.isfinite(float(comp)) else float(f["instrument_uniformity"])
        return float(iu) ** 0.4, {}, {}

    aff = compute_timbral_affinity_bundle_for_window(
        c,
        feats,
        profile="conservative",
        relief_factor=0.5,
        instrument_uniformity=0.5,
        compute_h_ti=_compute_h_ti,
        feats_for_h_ti=feats,
        w_instr=1.0,
        w_fam=0.0,
        w_tech=0.0,
        w_reg=0.0,
        collect_pairs=False,
    )
    h_core = 0.5**0.4
    assert aff["H_TI_affinity_literature_relieved"] > h_core - 1e-9
