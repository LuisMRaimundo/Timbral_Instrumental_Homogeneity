"""Typed models for analysis outputs."""

from homogeneity_analyser.models.config import PitchSpaceMode
from homogeneity_analyser.models.results import (
    HomogeneitySeriesResult,
    RegisterSeriesResult,
    TimbralSeriesResult,
)
from homogeneity_analyser.models.timbral_semantics import (
    TIMBRAL_MODEL_SEMANTICS_VERSION,
    TimbralModelMode,
    assert_active_timbral_model_mode,
    timbral_model_metadata_for_diagnostics,
)

__all__ = [
    "TIMBRAL_MODEL_SEMANTICS_VERSION",
    "HomogeneitySeriesResult",
    "PitchSpaceMode",
    "RegisterSeriesResult",
    "TimbralModelMode",
    "TimbralSeriesResult",
    "assert_active_timbral_model_mode",
    "timbral_model_metadata_for_diagnostics",
]
