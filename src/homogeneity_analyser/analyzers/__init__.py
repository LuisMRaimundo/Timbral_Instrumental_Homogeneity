"""
Computational core: H_TI (product) plus lazy legacy re-exports.

**Product:** ``SymbolicTIHomogeneityAnalyzer``, ``SymbolicScoreAnalyzer``, ``TimbralHomogeneityAnalyzer``,
``common``. **Legacy multimetric:** import ``homogeneity_analyser.legacy`` (not the shim
files in this directory — see ``analyzers/README.md``).
"""

from __future__ import annotations

import importlib
from typing import Any

from homogeneity_analyser.analyzers.common import (
    combine_weighted_geometric,
    normalize_homogeneity_weights,
    normalize_pitch_space,
    note_name_to_midi_ps,
)
from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.symbolic_score_analyzer import SymbolicScoreAnalyzer
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer

_LEGACY_NAMES: dict[str, tuple[str, str]] = {
    "ClusterHomogeneityAnalyzer": ("homogeneity_analyser.legacy.cluster", "ClusterHomogeneityAnalyzer"),
    "FusionAcousticHeuristicAnalyzer": (
        "homogeneity_analyser.legacy.fusion_acoustic_heuristic",
        "FusionAcousticHeuristicAnalyzer",
    ),
    "HomogeneityAnalyzer": ("homogeneity_analyser.legacy.homogeneity", "HomogeneityAnalyzer"),
    "NotatedFusionPotentialAnalyzer": (
        "homogeneity_analyser.legacy.notated_fusion_potential",
        "NotatedFusionPotentialAnalyzer",
    ),
    "OrchestrationSymbolicAnalyzer": (
        "homogeneity_analyser.legacy.orchestration_symbolic",
        "OrchestrationSymbolicAnalyzer",
    ),
    "RegisterUniformityAnalyzer": ("homogeneity_analyser.legacy.register", "RegisterUniformityAnalyzer"),
}

__all__ = [
    "ClusterHomogeneityAnalyzer",
    "FusionAcousticHeuristicAnalyzer",
    "HomogeneityAnalyzer",
    "NotatedFusionPotentialAnalyzer",
    "OrchestrationSymbolicAnalyzer",
    "RegisterUniformityAnalyzer",
    "SymbolicScoreAnalyzer",
    "SymbolicTIHomogeneityAnalyzer",
    "TimbralHomogeneityAnalyzer",
    "combine_weighted_geometric",
    "normalize_homogeneity_weights",
    "normalize_pitch_space",
    "note_name_to_midi_ps",
]


def __getattr__(name: str) -> Any:
    if name in _LEGACY_NAMES:
        mod_path, attr = _LEGACY_NAMES[name]
        return getattr(importlib.import_module(mod_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
