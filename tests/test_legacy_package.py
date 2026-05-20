"""Legacy multimetric package layout and stable public imports."""

from __future__ import annotations

import homogeneity_analyser.legacy as legacy
from homogeneity_analyser.analyzers import (
    ClusterHomogeneityAnalyzer,
    FusionAcousticHeuristicAnalyzer,
    HomogeneityAnalyzer,
    NotatedFusionPotentialAnalyzer,
    OrchestrationSymbolicAnalyzer,
    RegisterUniformityAnalyzer,
)
from homogeneity_analyser.legacy import LEGACY_ANALYZER_EXPORT_NAMES, LEGACY_JSON_EXPORT_SCHEMA_VERSION
from homogeneity_analyser.services.json_export import JSON_EXPORT_SCHEMA_VERSION


def test_legacy_analyzer_names_unique() -> None:
    assert len(LEGACY_ANALYZER_EXPORT_NAMES) == len(set(LEGACY_ANALYZER_EXPORT_NAMES))


def test_legacy_json_schema_matches_combined_export() -> None:
    assert LEGACY_JSON_EXPORT_SCHEMA_VERSION == JSON_EXPORT_SCHEMA_VERSION == "1.8"


def test_shim_imports_match_legacy_package() -> None:
    assert HomogeneityAnalyzer is legacy.HomogeneityAnalyzer
    assert ClusterHomogeneityAnalyzer is legacy.ClusterHomogeneityAnalyzer
    assert OrchestrationSymbolicAnalyzer is legacy.OrchestrationSymbolicAnalyzer
    assert NotatedFusionPotentialAnalyzer is legacy.NotatedFusionPotentialAnalyzer
    assert FusionAcousticHeuristicAnalyzer is legacy.FusionAcousticHeuristicAnalyzer
    assert RegisterUniformityAnalyzer is legacy.RegisterUniformityAnalyzer
