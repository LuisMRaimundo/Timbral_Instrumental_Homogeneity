"""Default parameter bundles for analysis services."""

from __future__ import annotations

DEFAULT_HOMOGENEITY_PARAMS = {
    "time_step": 0.25,
    "window_size": 4.0,
    "sigma": 12.0,
    "pitch_space": "absolute",
    "pitch_bin_step": 1.0,
    "silence_intra_value": 0.5,
    "silence_transition_value": 0.5,
    "allow_partial_scales": True,
    "single_aggregate": False,
    "weight_m1": 1.0 / 3.0,
    "weight_m2": 1.0 / 3.0,
    "weight_m3": 1.0 / 3.0,
}

DEFAULT_TIMBRAL_PARAMS = {
    "time_step": 0.25,
    "window_size": 4.0,
    "timbral_config": None,
    "timbral_model_mode": "legacy",
}

# Register span reference (semitones) for proximity: 1 / (1 + span / ref). Profiles + optional override.
REGISTER_REF_PROFILE_SEMITONES: dict[str, float] = {
    "strict": 3.0,
    "balanced": 7.0,
    "permissive": 12.0,
}
DEFAULT_REGISTER_REF_PROFILE = "balanced"

# Symbolic timbral–instrumental homogeneity H_TI(t) — single primary metric (see analyzers.hti).
DEFAULT_HTI_PARAMS = {
    "time_step": 0.25,
    "window_size": 4.0,
    "window_mode": "manual",
    "edge_policy": "mark_partial_windows",
    "window_ratio": 0.15,
    "step_ratio": 0.01,
    "min_window_size": 0.5,
    "max_window_size": 8.0,
    "min_time_step": 0.0625,
    "max_time_step": 1.0,
    "target_window_count": 100.0,
    "window_to_step_ratio": 10.0,
    "register_ref_profile": DEFAULT_REGISTER_REF_PROFILE,
    "register_ref_semitones": None,
    "pitch_interpretation_mode": "musicxml_sounding",
    "harmonic_pitch_policy": "conservative",
    "weight_instrument_uniformity": 0.40,
    "weight_family_uniformity": 0.25,
    "weight_technique_uniformity": 0.15,
    "weight_register_proximity": 0.20,
    "same_subfamily_relief_factor": 0.0,
    "timbral_affinity_relief_factor": 0.0,
    "timbral_affinity_profile": "conservative",
    "dynamic_affinity_enabled": True,
    "export_affinity_pairs": False,
    "include_symbolic_blend_potential": False,
    "include_acoustic_proxy": False,
    "acoustic_proxy_profile": "conservative",
    "acoustic_proxy_pairwise_export": False,
    "acoustic_proxy_include_interval_class": False,
    "acoustic_proxy_min_evidence_policy": "omit_missing_components",
    "source_mechanism_weight": None,
    "family_similarity_weight": None,
    "technique_similarity_weight": None,
    "register_tessitura_weight": None,
    "dynamic_similarity_weight": None,
    "attack_similarity_weight": None,
}

# Single reusable disclaimer for UI, JSON exports, and documentation cross-refs.
SYMBOLIC_HOMOGENEITY_SCOPE_DISCLAIMER = (
    "This software operates on symbolic score notation (MusicXML / MIDI semantics) only. "
    "H_TI_core is a notation-derived symbolic homogeneity scalar. Optional literature-conditioned layers "
    "(timbral affinity relief, interval-class blend factors, attack-class compatibility, dynamic conditioning) "
    "are symbolic proxies for research workflows — not measured acoustic fusion, not psychoacoustic validation, "
    "not SPL or spectral analysis of audio."
)


def resolve_register_ref_semitones(params: dict) -> float:
    """Resolve numeric register reference from optional override or named profile."""
    ovr = params.get("register_ref_semitones")
    if ovr is not None and str(ovr).strip() != "":
        return float(ovr)
    prof = str(params.get("register_ref_profile") or DEFAULT_REGISTER_REF_PROFILE).strip().lower()
    if prof not in REGISTER_REF_PROFILE_SEMITONES:
        prof = DEFAULT_REGISTER_REF_PROFILE
    return float(REGISTER_REF_PROFILE_SEMITONES[prof])


DEFAULT_REGISTER_UNIFORMITY_PARAMS = {
    "time_step": 0.25,
    "window_size": 4.0,
    "register_low": "A1",
    "register_high": "E7",
}

DEFAULT_CLUSTER_PARAMS = {
    "time_step": 0.25,
    "window_size": 4.0,
    "cluster_ref_span": 12.0,
}

DEFAULT_ORCHESTRATION_SYMBOLIC_PARAMS = {
    "time_step": 0.25,
    "window_size": 4.0,
    "timbral_config": None,
    "timbral_model_mode": "legacy",
    "weight_orchestration_instrument": 0.45,
    "weight_orchestration_family": 0.25,
    "weight_orchestration_technique": 0.30,
}

DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS = {
    "time_step": 0.25,
    "window_size": 4.0,
    "timbral_config": None,
    "timbral_model_mode": "legacy",
    "weight_fusion_profile": 0.35,
    "weight_fusion_spectral": 0.35,
    "weight_fusion_technique": 0.15,
    "weight_fusion_register": 0.15,
    "fusion_n_harmonics": 12,
    "fusion_roughness_scale": 14.0,
    "fusion_register_ref_span_semitones": 36.0,
    "fusion_profile_distance_scale": 0.55,
}

# Named calibration profiles for ``same_family_relief`` (distribution-based; no per-instrument tables).
SAME_FAMILY_RELIEF_PROFILES: dict[str, float] = {
    "strict": 0.0,
    "conservative": 0.45,
    "balanced": 0.55,
    "permissive": 0.65,
}
DEFAULT_SAME_FAMILY_RELIEF_PROFILE = "balanced"

DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS = {
    "time_step": 0.25,
    "window_size": 4.0,
    "timbral_config": None,
    "timbral_model_mode": "legacy",
    "notated_fusion_register_ref_semitones": 12.0,
    "same_family_relief_profile": DEFAULT_SAME_FAMILY_RELIEF_PROFILE,
    "same_family_relief_override": None,
    "weight_notated_fusion_instrument": 0.30,
    "weight_notated_fusion_family": 0.15,
    "weight_notated_fusion_technique": 0.25,
    "weight_notated_fusion_register": 0.30,
    "weight_notated_fusion_dynamic": 0.10,
}
