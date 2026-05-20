"""Label priority and edge cases for ``hti_dynamic_conditioning``."""

from __future__ import annotations

from homogeneity_analyser.analyzers.hti_dynamic_conditioning import pick_dynamic_interpretation_label


def test_string_mixed_technique_priority_over_cross_family() -> None:
    feats = {
        "dynamic_coverage_status": "explicit",
        "string_technique_state_mixed": True,
        "n_macrofamilies": 3,
        "brass_family_active": True,
        "masked_tonal_mass_risk": 0.9,
        "projection_divergence_risk": 0.9,
        "dominant_dynamic": "ff",
        "dynamic_intensity_ordinal": 0.88,
    }
    assert pick_dynamic_interpretation_label(feats) == "string_mixed_technique_heterogeneity"


def test_cross_family_transparent_blend_potential() -> None:
    feats = {
        "dynamic_coverage_status": "explicit",
        "string_technique_state_mixed": False,
        "n_macrofamilies": 2,
        "brass_family_active": True,
        "clarinet_family_active": False,
        "flute_family_active": True,
        "string_family_active": True,
        "dominant_dynamic": "mp",
        "dynamic_intensity_ordinal": 0.43,
        "masked_tonal_mass_risk": 0.08,
        "projection_divergence_risk": 0.04,
        "masking_context_weight": 0.32,
        "transparent_blend_potential": 0.36,
        "same_family_mixed_instrument_mass": 0.0,
        "percussion_overlap_fraction": 0.0,
        "non_percussion_sustained_overlap_fraction": 1.0,
    }
    assert pick_dynamic_interpretation_label(feats) == "cross_family_transparent_blend_potential"


def test_percussion_insufficient_fusion_evidence() -> None:
    feats = {
        "dynamic_coverage_status": "explicit",
        "string_technique_state_mixed": False,
        "n_macrofamilies": 1,
        "brass_family_active": False,
        "clarinet_family_active": False,
        "flute_family_active": False,
        "double_reed_family_active": False,
        "string_family_active": False,
        "dominant_dynamic": "mf",
        "dynamic_intensity_ordinal": 0.55,
        "masked_tonal_mass_risk": 0.05,
        "projection_divergence_risk": 0.02,
        "masking_context_weight": 0.2,
        "transparent_blend_potential": 0.05,
        "same_family_mixed_instrument_mass": 0.0,
        "percussion_overlap_fraction": 0.92,
        "non_percussion_sustained_overlap_fraction": 0.05,
    }
    assert pick_dynamic_interpretation_label(feats) == "percussion_dynamic_salience_insufficient_fusion_evidence"
