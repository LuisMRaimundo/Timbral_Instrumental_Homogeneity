"""Optional literature-conditioned symbolic blend layers (not H_TI_core)."""

from __future__ import annotations

from pathlib import Path

import pytest

from homogeneity_analyser.analyzers.symbolic_blend_layers import (
    clarinet_register_zone_penalty,
    compute_attack_compatibility_factor,
    compute_interval_class_blend_factor,
    compute_pairwise_interval_blend_factor,
    interval_class_blend_weight,
    interval_class_display_label,
    interval_class_key_for_d12,
    load_symbolic_blend_conditioning_profile,
)
from homogeneity_analyser.analyzers.timbral_affinity import pairwise_similarity
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BRASS, FAMILY_CLARINETS, FAMILY_STRINGS


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


def test_seconds_sevenths_key_maps_mod12_second_and_minor_seventh() -> None:
    assert interval_class_key_for_d12(1) == "seconds_sevenths"
    assert interval_class_key_for_d12(2) == "seconds_sevenths"
    assert interval_class_key_for_d12(10) == "seconds_sevenths"
    assert interval_class_key_for_d12(11) == "seconds_sevenths"
    assert interval_class_key_for_d12(7) == "fifth_twelfth"


def test_interval_class_display_label_for_seconds_sevenths() -> None:
    cfg = load_symbolic_blend_conditioning_profile()
    lab = interval_class_display_label("seconds_sevenths", cfg)
    assert "second-class" in lab
    assert "seventh-class" in lab
    assert "equivalence" in lab


def test_literal_semitone_mass_separate_from_interval_class_profile() -> None:
    """C4–D4: literal 2 semitones; mod-12 class 2 → seconds_sevenths bucket (not a literal 7th)."""
    cfg = load_symbolic_blend_conditioning_profile()
    out = compute_interval_class_blend_factor([60.0, 62.0], None, cfg=cfg)
    prof = out["interval_class_profile"]
    assert prof.get("seconds_sevenths", 0.0) > 0.99
    lit = out["literal_interval_semitone_pair_mass"]
    assert lit.get("2", 0.0) > 0.99
    assert lit.get("11", 0.0) == 0.0
    disp = out["interval_class_profile_display"]
    assert any("second-class" in k for k in disp)
    mod12 = out["chromatic_mod12_pair_mass"]
    assert mod12.get("2", 0.0) > 0.99


def test_interval_class_blend_ordering_unison_over_fifth_over_seconds() -> None:
    cfg = load_symbolic_blend_conditioning_profile()
    _, w0 = interval_class_blend_weight(0, cfg)
    _, w7 = interval_class_blend_weight(7, cfg)
    _, w1 = interval_class_blend_weight(1, cfg)
    assert w0 > w7 > w1


def test_pairwise_interval_blend_factor_weights_unison_above_cluster() -> None:
    cfg = load_symbolic_blend_conditioning_profile()
    po = [(60.0, 1.0), (72.0, 1.0)]  # octave class → d12 0
    u = compute_pairwise_interval_blend_factor(po, cfg=cfg)["pairwise_interval_blend_factor"]
    po2 = [(60.0, 1.0), (61.0, 1.0)]  # minor second
    s = compute_pairwise_interval_blend_factor(po2, cfg=cfg)["pairwise_interval_blend_factor"]
    assert u > s


def test_attack_mismatch_plucked_vs_bowed_lowers_factor() -> None:
    cfg = load_symbolic_blend_conditioning_profile()
    vln_arco = {
        "instrument": "violin",
        "family": FAMILY_STRINGS,
        "technique_uniformity_key": "arco",
        "technique_state": {
            "family": FAMILY_STRINGS,
            "instrument": "violin",
            "primary": "ordinary",
            "mute": "none",
            "contact_point": "ordinary",
            "excitation": "arco",
            "articulation_effect": "none",
            "resonance": "ordinary",
            "noise_component": "ordinary",
            "pressure": "ordinary",
            "beater": "ordinary",
            "stroke": "ordinary",
            "special": (),
        },
    }
    vln_pizz = {
        "instrument": "violin",
        "family": FAMILY_STRINGS,
        "technique_uniformity_key": "pizzicato",
        "technique_state": {
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
    }
    c_hom = [(vln_arco, 0.5), (vln_arco, 0.5)]
    c_mix = [(vln_arco, 0.5), (vln_pizz, 0.5)]
    h = compute_attack_compatibility_factor(c_hom, cfg=cfg)["attack_compatibility_factor"]
    m = compute_attack_compatibility_factor(c_mix, cfg=cfg)["attack_compatibility_factor"]
    assert h > m


def test_string_harmonic_not_equivalent_to_arco_same_instrument() -> None:
    arco = {
        "instrument": "violin",
        "family": FAMILY_STRINGS,
        "technique_uniformity_key": "harmonic_natural_harmonic",
        "technique_state": {
            "family": FAMILY_STRINGS,
            "instrument": "violin",
            "primary": "ordinary",
            "mute": "none",
            "contact_point": "ordinary",
            "excitation": "arco",
            "articulation_effect": "none",
            "resonance": "ordinary",
            "noise_component": "ordinary",
            "pressure": "ordinary",
            "beater": "ordinary",
            "stroke": "ordinary",
            "special": ("harmonic:natural_harmonic",),
        },
    }
    ordn = {
        "instrument": "violin",
        "family": FAMILY_STRINGS,
        "technique_uniformity_key": "ordinary_default_uniform",
        "technique_state": {
            "family": FAMILY_STRINGS,
            "instrument": "violin",
            "primary": "ordinary",
            "mute": "none",
            "contact_point": "ordinary",
            "excitation": "arco",
            "articulation_effect": "none",
            "resonance": "ordinary",
            "noise_component": "ordinary",
            "pressure": "ordinary",
            "beater": "ordinary",
            "stroke": "ordinary",
            "special": (),
        },
    }
    s, rid, _ = pairwise_similarity(arco, ordn, profile="moderate")
    assert s < 1.0
    assert "harmonic" in rid


def test_clarinet_register_zones_affect_symbolic_blend_penalty() -> None:
    cfg = load_symbolic_blend_conditioning_profile()
    low = {"family": FAMILY_CLARINETS, "pitches": [55.0]}
    high = {"family": FAMILY_CLARINETS, "pitches": [80.0]}
    p = clarinet_register_zone_penalty(low, high, cfg)
    assert p < 1.0


def test_conservative_profile_blocks_source_key_only_registry_pairs() -> None:
    s_cons, _, _ = pairwise_similarity(
        _ev("trumpet", FAMILY_BRASS, 1.0),
        _ev("cornet", FAMILY_BRASS, 1.0),
        profile="conservative",
    )
    s_mod, _, _ = pairwise_similarity(
        _ev("trumpet", FAMILY_BRASS, 1.0),
        _ev("cornet", FAMILY_BRASS, 1.0),
        profile="moderate",
    )
    assert s_mod > s_cons + 1e-6
    assert s_cons <= 0.25


def test_hti_core_series_unchanged_when_symbolic_blend_bundle_enabled() -> None:
    from homogeneity_analyser.services.analysis_service import run_symbolic_ti_homogeneity_analysis

    xml = Path(__file__).resolve().parents[1] / "validation" / "fixtures_musicxml" / "step_density.xml"
    if not xml.is_file():
        pytest.skip("fixture missing")
    base = {"window_size": 4.0, "time_step": 1.0, "timbral_affinity_relief_factor": 0.0}
    out_off = run_symbolic_ti_homogeneity_analysis(str(xml), {**base, "include_symbolic_blend_potential": False})
    out_on = run_symbolic_ti_homogeneity_analysis(str(xml), {**base, "include_symbolic_blend_potential": True})
    assert out_off.get("error") is None and out_on.get("error") is None
    r1 = out_off.get("results") or {}
    r2 = out_on.get("results") or {}
    assert r1.get("H_TI_core") == r2.get("H_TI_core")
