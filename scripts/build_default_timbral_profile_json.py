"""Emit ``default_profiles.json`` from current module numeric state (run after changing formulas)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homogeneity_analyser.analyzers import brass_pairwise_timbral as bp
from homogeneity_analyser.analyzers import clarinet_pairwise_timbral as cp
from homogeneity_analyser.analyzers import double_reed_pairwise_timbral as dr
from homogeneity_analyser.analyzers import flute_pairwise_timbral as fp
from homogeneity_analyser.analyzers import percussion_pairwise_timbral as pp
from homogeneity_analyser.analyzers import saxophone_pairwise_timbral as sx
from homogeneity_analyser.analyzers import string_pairwise_timbral as sp
from homogeneity_analyser.analyzers import timbre_cross_relations as tc


def _mat(m: Any) -> list[list[float]]:
    import numpy as np

    return np.asarray(m, dtype=float).tolist()


def _flat_values() -> dict[str, Any]:
    order = list(sp._SECTION_ORDER)
    section_m = [[sp._SECTION_SIM[(order[i], order[j])] for j in range(4)] for i in range(4)]
    return {
        "string_section_similarity_matrix": section_m,
        "string_technique_similarity_matrix": _mat(sp._TECH_MAT),
        "string_register_tau_semitones_default": 7.5,
        "string_fallback_section_similarity": 0.35,
        "brass_section_similarity_matrix": _mat(bp._SECTION_SIM),
        "brass_tessitura_bounds_midi": [list(x) for x in bp._TESS_BOUNDS],
        "brass_technique_similarity_matrix": _mat(bp._TECH_MAT),
        "brass_register_same_section_zone_sim": [1.0, 0.88, 0.62, 0.42],
        "brass_register_same_section_fine_tau": 36.0,
        "brass_register_same_section_blend_zone": 0.78,
        "brass_register_same_section_blend_fine": 0.22,
        "brass_register_cross_section_fine_tau": 22.0,
        "brass_register_cross_section_blend_align": 0.52,
        "brass_register_cross_section_blend_fine": 0.48,
        "clarinet_subtype_similarity_matrix": _mat(cp._SUBTYPE_SIM),
        "clarinet_tessitura_bounds_midi": [list(x) for x in cp._CLAR_TESS_BOUNDS],
        "clarinet_technique_similarity_matrix": _mat(cp._TECH_MAT),
        "clarinet_register_zone_threshold_chalumeau_upper_midi": 66.0,
        "clarinet_register_zone_threshold_clarion_upper_midi": 80.0,
        "clarinet_register_same_subtype_zone_sim": [1.0, 0.9, 0.62],
        "clarinet_register_same_subtype_fine_tau": 28.0,
        "clarinet_register_same_subtype_blend_zone": 0.8,
        "clarinet_register_same_subtype_blend_fine": 0.2,
        "clarinet_register_cross_subtype_fine_tau": 22.0,
        "clarinet_register_cross_subtype_blend_align": 0.55,
        "clarinet_register_cross_subtype_blend_fine": 0.45,
        "flute_subtype_similarity_matrix": _mat(fp._SUBTYPE_SIM),
        "flute_tessitura_bounds_midi": [list(x) for x in fp._TESS_BOUNDS],
        "flute_technique_similarity_matrix": _mat(fp._TECH_MAT),
        "flute_register_same_subtype_zone_sim": [1.0, 0.88, 0.60, 0.40],
        "flute_register_same_subtype_fine_tau": 34.0,
        "flute_register_same_subtype_blend_zone": 0.78,
        "flute_register_same_subtype_blend_fine": 0.22,
        "flute_register_cross_subtype_fine_tau": 20.0,
        "flute_register_cross_subtype_blend_align": 0.52,
        "flute_register_cross_subtype_blend_fine": 0.48,
        "double_reed_subtype_similarity_matrix": _mat(dr._SUBTYPE_SIM),
        "double_reed_tessitura_bounds_midi": [list(x) for x in dr._DR_TESS_BOUNDS],
        "double_reed_technique_similarity_matrix": _mat(dr._TECH_MAT),
        "double_reed_register_same_subtype_zone_sim": [1.0, 0.89, 0.64],
        "double_reed_register_same_subtype_fine_tau": 30.0,
        "double_reed_register_same_subtype_blend_zone": 0.78,
        "double_reed_register_same_subtype_blend_fine": 0.22,
        "double_reed_register_cross_subtype_fine_tau": 24.0,
        "double_reed_register_cross_subtype_blend_align": 0.56,
        "double_reed_register_cross_subtype_blend_fine": 0.44,
        "double_reed_cross_family_stub_flute_clarinet": 0.32,
        "double_reed_cross_family_stub_other": 0.22,
        "double_reed_pair_score_register_exp_tau": 36.0,
        "saxophone_subtype_similarity_matrix": _mat(sx._SUBTYPE_SIM),
        "saxophone_tessitura_bounds_midi": [list(x) for x in sx._SAX_TESS_BOUNDS],
        "saxophone_technique_similarity_matrix": _mat(sx._TECH_MAT),
        "saxophone_register_same_subtype_zone_sim": [1.0, 0.91, 0.74, 0.56],
        "saxophone_register_same_subtype_fine_tau": 32.0,
        "saxophone_register_same_subtype_blend_zone": 0.78,
        "saxophone_register_same_subtype_blend_fine": 0.22,
        "saxophone_register_cross_subtype_fine_tau": 22.0,
        "saxophone_register_cross_subtype_blend_align": 0.55,
        "saxophone_register_cross_subtype_blend_fine": 0.45,
        "percussion_macro_cross_similarity_matrix": _mat(pp._MACRO_CROSS),
        "percussion_same_macro_map_fallback": 0.76,
        "percussion_same_macro_default_similarity": {k.name: float(v) for k, v in pp._SAME_MACRO_DEFAULT.items()},
        "percussion_instrument_pair_overrides": {f"{a}|{b}": v for (a, b), v in pp._INSTRUMENT_PAIR.items()},
        "percussion_pitch_status_similarity_quasi_pitched": 0.84,
        "percussion_pitch_status_similarity_unpitched_pitched": 0.52,
        "percussion_pitch_status_similarity_unpitched_quasi": 0.64,
        "percussion_pitch_status_similarity_fallback": 0.7,
        "percussion_resonance_decay": 0.75,
        "percussion_resonance_base": 0.42,
        "percussion_resonance_scale": 0.58,
        "percussion_noise_decay": 0.65,
        "percussion_noise_base": 0.45,
        "percussion_noise_scale": 0.55,
        "percussion_damped_res_scale": 0.68,
        "percussion_damped_noise_scale": 0.92,
        "percussion_tech_matrix_default_fill": 0.74,
        "percussion_technique_similarity_matrix": _mat(pp._TECH_MAT),
        "percussion_pairwise_resonance_weight_a": 0.38,
        "percussion_pairwise_resonance_weight_b": 0.62,
        "percussion_pairwise_noise_weight_a": 0.38,
        "percussion_pairwise_noise_weight_b": 0.62,
        "percussion_register_pitched_zone_sim": [1.0, 0.9, 0.74, 0.58],
        "percussion_register_pitched_fine_tau": 30.0,
        "percussion_register_pitched_blend_zone": 0.76,
        "percussion_register_pitched_blend_fine": 0.24,
        "percussion_register_pitched_quasi_scale": 0.88,
        "percussion_register_quasi_quasi_scale": 0.9,
        "percussion_register_unpitched_bin_decay": 2.2,
        "percussion_register_unpitched_bin_base": 0.48,
        "percussion_register_unpitched_bin_scale": 0.52,
        "percussion_register_unpitched_ps_tau": 50.0,
        "percussion_register_unpitched_blend_bin": 0.72,
        "percussion_register_unpitched_blend_ps": 0.28,
        "percussion_register_fallback_exp_tau": 40.0,
        "percussion_register_fallback_a": 0.62,
        "percussion_register_fallback_b": 0.22,
        "percussion_unpitched_proxy_empty": 0.82,
        "percussion_unpitched_proxy_single": 0.86,
        "percussion_unpitched_proxy_span_divisor": 4.5,
        "percussion_unpitched_proxy_min": 0.55,
        "percussion_unpitched_proxy_max": 0.94,
        "timbral_default_weight_instrument": 0.65,
        "timbral_default_weight_register": 0.35,
        "timbral_default_family_bonus": 0.65,
        "timbral_default_register_ref_semitones": 3.0,
        "timbral_register_global_dampen_pairwise_coverage_max": 0.12,
        "timbral_percussion_register_blend_pm_threshold": 0.88,
        "timbral_percussion_register_blend_pun_threshold": 0.72,
        "timbral_percussion_register_blend_multiplier": 1.12,
        "timbral_technique_component_offset": 0.18,
        "timbral_technique_component_concentration_scale": 0.82,
        "cross_timbral_max_additive_boost": float(tc._MAX_ADDITIVE_CROSS_BOOST),
        "cross_timbral_strength_tenor_sax_clarinet": float(tc._ST_TENOR_SAX_CLARINET),
        "cross_timbral_strength_alto_sax_horn": float(tc._ST_ALTO_SAX_HORN),
        "cross_timbral_strength_trumpet_oboe": float(tc._ST_TRUMPET_OBOE),
        "cross_timbral_strength_bass_clarinet_bassoon": float(tc._ST_BASS_CLAR_BASSOON),
        "cross_timbral_strength_horn_bassoon": float(tc._ST_HORN_BASSOON),
        "cross_timbral_strength_high_clarinet_flute": float(tc._ST_HIGH_CLAR_FLUTE),
        "cross_timbral_strength_natural_horn_trumpet": float(tc._ST_NATURAL_HORN_TRUMPET),
        "cross_timbral_tenor_sax_ps_low": 56.0,
        "cross_timbral_tenor_sax_ps_high": 84.0,
        "cross_timbral_soprano_clarinet_ps_low": 58.0,
        "cross_timbral_soprano_clarinet_ps_high": 90.0,
        "cross_timbral_tenor_sax_clarinet_abs_ps_max": 26.0,
        "cross_timbral_alto_sax_ps_low": 52.0,
        "cross_timbral_alto_sax_ps_high": 88.0,
        "cross_timbral_horn_ps_low": 50.0,
        "cross_timbral_horn_ps_high": 88.0,
        "cross_timbral_alto_sax_horn_abs_ps_max": 22.0,
        "cross_timbral_trumpet_ps_low": 56.0,
        "cross_timbral_trumpet_ps_high": 88.0,
        "cross_timbral_oboe_ps_low": 60.0,
        "cross_timbral_oboe_ps_high": 92.0,
        "cross_timbral_trumpet_oboe_abs_ps_max": 28.0,
        "cross_timbral_natural_horn_ps_low": 48.0,
        "cross_timbral_natural_horn_ps_high": 82.0,
        "cross_timbral_trumpet_pair_ps_low": 52.0,
        "cross_timbral_trumpet_pair_ps_high": 90.0,
        "cross_timbral_natural_horn_trumpet_abs_ps_max": 26.0,
        "cross_timbral_high_clarinet_ps_min": 74.0,
        "cross_timbral_flute_ps_min": 70.0,
        "cross_timbral_high_clar_flute_abs_ps_max": 18.0,
    }


def _role(name: str) -> str:
    if name.startswith("string_"):
        return "pairwise_string"
    if name.startswith("brass_"):
        return "pairwise_brass"
    if name.startswith("clarinet_"):
        return "pairwise_clarinet"
    if name.startswith("flute_"):
        return "pairwise_flute"
    if name.startswith("double_reed_"):
        return "pairwise_double_reed"
    if name.startswith("saxophone_"):
        return "pairwise_saxophone"
    if name.startswith("percussion_"):
        return "pairwise_percussion"
    if name.startswith("cross_timbral_"):
        return "cross_family_timbral_boost"
    if name.startswith("timbral_"):
        return "timbral_core_scalar"
    return "timbral"


def build_constants() -> list[dict[str, Any]]:
    flat = _flat_values()
    out: list[dict[str, Any]] = []
    page_na = "N/A (notation-only heuristic; no literature page claimed for this numeric knob)"
    for semantic_name, value in flat.items():
        out.append(
            {
                "semantic_name": semantic_name,
                "value": value,
                "description": f"Legacy default for {semantic_name} (extracted from code prior to config layer).",
                "affects": ["H_timbral"],
                "model_role": _role(semantic_name),
                "source_key": "project_specific",
                "page_reference": page_na,
                "rationale": (
                    "Symbolic / orchestration-side heuristic constant; not a measured acoustic sample. "
                    "Literature links may be added later via the acoustic source registry."
                ),
                "confidence": "low",
                "evidence_status": "provisional",
            }
        )
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dest = root / "src" / "homogeneity_analyser" / "acoustic_profiles" / "default_profiles.json"
    doc = {
        "profile_name": "legacy_default",
        "config_model_version": "1.0.0",
        "constants": build_constants(),
    }
    dest.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(doc['constants'])} constants to {dest}")


if __name__ == "__main__":
    main()
