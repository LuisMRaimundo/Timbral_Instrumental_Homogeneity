"""
Legacy / internal multimetric analysers (research, batch JSON, tests).

**Not** the user-facing H_TI product. Combined exports use ``schema_version`` **1.8**
(see ``homogeneity_analyser.services.json_export.JSON_EXPORT_SCHEMA_VERSION``).

Primary product: ``SymbolicTIHomogeneityAnalyzer`` in ``homogeneity_analyser.analyzers.hti``.
"""

from __future__ import annotations

from homogeneity_analyser.legacy.cluster import ClusterHomogeneityAnalyzer
from homogeneity_analyser.legacy.fusion_acoustic_heuristic import FusionAcousticHeuristicAnalyzer
from homogeneity_analyser.legacy.homogeneity import HomogeneityAnalyzer
from homogeneity_analyser.legacy.notated_fusion_potential import NotatedFusionPotentialAnalyzer
from homogeneity_analyser.legacy.orchestration_symbolic import OrchestrationSymbolicAnalyzer
from homogeneity_analyser.legacy.register import RegisterUniformityAnalyzer

LEGACY_JSON_EXPORT_SCHEMA_VERSION = "1.8"

LEGACY_ANALYZER_EXPORT_NAMES: tuple[str, ...] = (
    "HomogeneityAnalyzer",
    "ClusterHomogeneityAnalyzer",
    "OrchestrationSymbolicAnalyzer",
    "NotatedFusionPotentialAnalyzer",
    "FusionAcousticHeuristicAnalyzer",
    "RegisterUniformityAnalyzer",
)

__all__ = [
    "LEGACY_ANALYZER_EXPORT_NAMES",
    "LEGACY_JSON_EXPORT_SCHEMA_VERSION",
    "ClusterHomogeneityAnalyzer",
    "FusionAcousticHeuristicAnalyzer",
    "HomogeneityAnalyzer",
    "NotatedFusionPotentialAnalyzer",
    "OrchestrationSymbolicAnalyzer",
    "RegisterUniformityAnalyzer",
]
