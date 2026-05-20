"""
Semantic names of ``default_profiles.json`` constants grouped for **H_timbral diagnostics**.

These frozensets list knobs that belong to each specialist branch. When a window's computation
actually invokes that branch's pairwise path (≥2 events and positive overlap mass), diagnostics
merge the corresponding set so ``constants_used`` reflects the real computation path.
"""

from __future__ import annotations

# --- Global timbral knobs (non-silent windows always touch register dampen + technique multiplier)
GLOBAL_ALWAYS_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "timbral_register_global_dampen_pairwise_coverage_max",
        "timbral_technique_component_offset",
        "timbral_technique_component_concentration_scale",
    }
)

TIMBRAL_DEFAULT_WEIGHT_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "timbral_default_weight_instrument",
        "timbral_default_weight_register",
        "timbral_default_family_bonus",
        "timbral_default_register_ref_semitones",
    }
)

PERCUSSION_REGISTER_BLEND_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "timbral_percussion_register_blend_pm_threshold",
        "timbral_percussion_register_blend_pun_threshold",
        "timbral_percussion_register_blend_multiplier",
    }
)

PERCUSSION_UNPITCHED_REGISTER_PROXY_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "percussion_unpitched_proxy_empty",
        "percussion_unpitched_proxy_single",
        "percussion_unpitched_proxy_span_divisor",
        "percussion_unpitched_proxy_min",
        "percussion_unpitched_proxy_max",
    }
)

STRING_PAIRWISE_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "string_section_similarity_matrix",
        "string_fallback_section_similarity",
        "string_register_tau_semitones_default",
        "string_technique_similarity_matrix",
    }
)

BRASS_PAIRWISE_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "brass_section_similarity_matrix",
        "brass_technique_similarity_matrix",
        "brass_register_same_section_zone_sim",
        "brass_register_same_section_fine_tau",
        "brass_register_same_section_blend_zone",
        "brass_register_same_section_blend_fine",
        "brass_register_cross_section_fine_tau",
        "brass_register_cross_section_blend_align",
        "brass_register_cross_section_blend_fine",
    }
)

CLARINET_PAIRWISE_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "clarinet_subtype_similarity_matrix",
        "clarinet_technique_similarity_matrix",
        "clarinet_register_zone_threshold_chalumeau_upper_midi",
        "clarinet_register_zone_threshold_clarion_upper_midi",
        "clarinet_register_same_subtype_zone_sim",
        "clarinet_register_same_subtype_fine_tau",
        "clarinet_register_same_subtype_blend_zone",
        "clarinet_register_same_subtype_blend_fine",
        "clarinet_register_cross_subtype_fine_tau",
        "clarinet_register_cross_subtype_blend_align",
        "clarinet_register_cross_subtype_blend_fine",
    }
)

FLUTE_PAIRWISE_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "flute_tessitura_bounds_midi",
        "flute_subtype_similarity_matrix",
        "flute_technique_similarity_matrix",
        "flute_register_same_subtype_zone_sim",
        "flute_register_same_subtype_fine_tau",
        "flute_register_same_subtype_blend_zone",
        "flute_register_same_subtype_blend_fine",
        "flute_register_cross_subtype_fine_tau",
        "flute_register_cross_subtype_blend_align",
        "flute_register_cross_subtype_blend_fine",
    }
)

DOUBLE_REED_PAIRWISE_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "double_reed_tessitura_bounds_midi",
        "double_reed_subtype_similarity_matrix",
        "double_reed_technique_similarity_matrix",
        "double_reed_register_same_subtype_zone_sim",
        "double_reed_register_same_subtype_fine_tau",
        "double_reed_register_same_subtype_blend_zone",
        "double_reed_register_same_subtype_blend_fine",
        "double_reed_register_cross_subtype_fine_tau",
        "double_reed_register_cross_subtype_blend_align",
        "double_reed_register_cross_subtype_blend_fine",
        "double_reed_cross_family_stub_flute_clarinet",
        "double_reed_cross_family_stub_other",
        "double_reed_pair_score_register_exp_tau",
    }
)

SAXOPHONE_PAIRWISE_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "saxophone_tessitura_bounds_midi",
        "saxophone_subtype_similarity_matrix",
        "saxophone_technique_similarity_matrix",
        "saxophone_register_same_subtype_zone_sim",
        "saxophone_register_same_subtype_fine_tau",
        "saxophone_register_same_subtype_blend_zone",
        "saxophone_register_same_subtype_blend_fine",
        "saxophone_register_cross_subtype_fine_tau",
        "saxophone_register_cross_subtype_blend_align",
        "saxophone_register_cross_subtype_blend_fine",
    }
)

PERCUSSION_PAIRWISE_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "percussion_macro_cross_similarity_matrix",
        "percussion_same_macro_default_similarity",
        "percussion_instrument_pair_overrides",
        "percussion_same_macro_map_fallback",
        "percussion_pitch_status_similarity_quasi_pitched",
        "percussion_pitch_status_similarity_unpitched_pitched",
        "percussion_pitch_status_similarity_unpitched_quasi",
        "percussion_pitch_status_similarity_fallback",
        "percussion_resonance_base",
        "percussion_resonance_scale",
        "percussion_resonance_decay",
        "percussion_noise_base",
        "percussion_noise_scale",
        "percussion_noise_decay",
        "percussion_damped_res_scale",
        "percussion_damped_noise_scale",
        "percussion_technique_similarity_matrix",
        "percussion_register_pitched_zone_sim",
        "percussion_register_pitched_fine_tau",
        "percussion_register_pitched_blend_zone",
        "percussion_register_pitched_blend_fine",
        "percussion_register_pitched_quasi_scale",
        "percussion_register_quasi_quasi_scale",
        "percussion_register_unpitched_bin_decay",
        "percussion_register_unpitched_bin_base",
        "percussion_register_unpitched_bin_scale",
        "percussion_register_unpitched_ps_tau",
        "percussion_register_unpitched_blend_bin",
        "percussion_register_unpitched_blend_ps",
        "percussion_register_fallback_exp_tau",
        "percussion_register_fallback_a",
        "percussion_register_fallback_b",
        "percussion_pairwise_resonance_weight_a",
        "percussion_pairwise_resonance_weight_b",
        "percussion_pairwise_noise_weight_a",
        "percussion_pairwise_noise_weight_b",
        "percussion_unpitched_proxy_empty",
        "percussion_unpitched_proxy_single",
        "percussion_unpitched_proxy_span_divisor",
        "percussion_unpitched_proxy_min",
        "percussion_unpitched_proxy_max",
    }
)

CROSS_TIMBRAL_SEMANTIC_NAMES: frozenset[str] = frozenset(
    {
        "cross_timbral_max_additive_boost",
        "cross_timbral_strength_tenor_sax_clarinet",
        "cross_timbral_strength_alto_sax_horn",
        "cross_timbral_strength_trumpet_oboe",
        "cross_timbral_strength_bass_clarinet_bassoon",
        "cross_timbral_strength_horn_bassoon",
        "cross_timbral_strength_high_clarinet_flute",
        "cross_timbral_strength_natural_horn_trumpet",
        "cross_timbral_tenor_sax_ps_low",
        "cross_timbral_tenor_sax_ps_high",
        "cross_timbral_soprano_clarinet_ps_low",
        "cross_timbral_soprano_clarinet_ps_high",
        "cross_timbral_tenor_sax_clarinet_abs_ps_max",
        "cross_timbral_alto_sax_ps_low",
        "cross_timbral_alto_sax_ps_high",
        "cross_timbral_horn_ps_low",
        "cross_timbral_horn_ps_high",
        "cross_timbral_alto_sax_horn_abs_ps_max",
        "cross_timbral_trumpet_ps_low",
        "cross_timbral_trumpet_ps_high",
        "cross_timbral_oboe_ps_low",
        "cross_timbral_oboe_ps_high",
        "cross_timbral_trumpet_oboe_abs_ps_max",
        "cross_timbral_natural_horn_ps_low",
        "cross_timbral_natural_horn_ps_high",
        "cross_timbral_trumpet_pair_ps_low",
        "cross_timbral_trumpet_pair_ps_high",
        "cross_timbral_natural_horn_trumpet_abs_ps_max",
        "cross_timbral_high_clarinet_ps_min",
        "cross_timbral_flute_ps_min",
        "cross_timbral_high_clar_flute_abs_ps_max",
    }
)

PAIRWISE_BRANCH_SEMANTIC_NAMES: dict[str, frozenset[str]] = {
    "string": STRING_PAIRWISE_SEMANTIC_NAMES,
    "brass": BRASS_PAIRWISE_SEMANTIC_NAMES,
    "clarinet": CLARINET_PAIRWISE_SEMANTIC_NAMES,
    "flute": FLUTE_PAIRWISE_SEMANTIC_NAMES,
    "double_reed": DOUBLE_REED_PAIRWISE_SEMANTIC_NAMES,
    "saxophone": SAXOPHONE_PAIRWISE_SEMANTIC_NAMES,
    "percussion": PERCUSSION_PAIRWISE_SEMANTIC_NAMES,
}
