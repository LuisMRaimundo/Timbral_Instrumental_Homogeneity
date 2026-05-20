"""Acoustic literature registry, timbral numeric profile, and fusion feature vectors (no PDFs in the package)."""

from homogeneity_analyser.acoustic_profiles.features import (
    FUSION_FEATURE_FIELDS,
    get_fusion_feature_document,
    resolve_acoustic_feature_row,
)
from homogeneity_analyser.acoustic_profiles.model_config import (
    DEFAULT_PROFILES_JSON_PATH,
    all_timbral_acoustic_semantic_names,
    build_timbral_window_diagnostics_bundle,
    get_timbral_acoustic_profile_document,
    timbral_acoustic_diagnostics_bundle,
    timbral_float,
    timbral_numpy_matrix,
)
from homogeneity_analyser.acoustic_profiles.similarity import (
    DEFAULT_FEATURE_WEIGHTS,
    weighted_normalized_feature_distance,
)
from homogeneity_analyser.acoustic_profiles.source_registry import (
    REGISTRY_JSON_PATH,
    load_source_registry,
)
from homogeneity_analyser.acoustic_profiles.source_validation import (
    PAGE_REQUIRED_SENTINEL,
    SourceRegistryValidationError,
    validate_source_registry,
)
from homogeneity_analyser.acoustic_profiles.spectral_proxy import spectral_proxy_model_note

__all__ = [
    "DEFAULT_FEATURE_WEIGHTS",
    "DEFAULT_PROFILES_JSON_PATH",
    "FUSION_FEATURE_FIELDS",
    "PAGE_REQUIRED_SENTINEL",
    "REGISTRY_JSON_PATH",
    "SourceRegistryValidationError",
    "all_timbral_acoustic_semantic_names",
    "build_timbral_window_diagnostics_bundle",
    "get_fusion_feature_document",
    "get_timbral_acoustic_profile_document",
    "load_source_registry",
    "resolve_acoustic_feature_row",
    "spectral_proxy_model_note",
    "timbral_acoustic_diagnostics_bundle",
    "timbral_float",
    "timbral_numpy_matrix",
    "validate_source_registry",
    "weighted_normalized_feature_distance",
]
