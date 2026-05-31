"""
Analysis service facade — backward-compatible imports.

| Module | Role |
|--------|------|
| ``analysis_service_hti`` | **H_TI** product — ``run_symbolic_ti_homogeneity_analysis`` |
| ``analysis_service_legacy`` | Multimetric / combined JSON **1.8** (H(t), H_timbral metric, cluster, fusion, U(t)) |

The symbolic **event pipeline** (score → events, taxonomy, pitches) lives in
``analyzers/symbolic_score_analyzer.py`` and ``analyzers/symbolic_event_pipeline.py``;
``timbral.py`` hosts only the legacy **H_timbral** metric on the same events.
"""

from __future__ import annotations

from homogeneity_analyser.services.analysis_service_hti import run_symbolic_ti_homogeneity_analysis
from homogeneity_analyser.services.analysis_service_legacy import (
    LEGACY_TIMBRAL_SUMMARY_WARNING,
    PROVISIONAL_NO_SOURCE_GOVERNANCE_MSG,
    TIMBRAL_DIAGNOSTIC_TABLE_HEADERS,
    flatten_timbral_diagnostic_row,
    run_both_and_combine,
    run_cluster_analysis,
    run_fusion_acoustic_heuristic_analysis,
    run_homogeneity_analysis,
    run_notated_fusion_potential_analysis,
    run_orchestration_symbolic_analysis,
    run_register_uniformity_analysis,
    run_timbral_analysis,
    write_timbral_diagnostics_csv,
)

__all__ = [
    "LEGACY_TIMBRAL_SUMMARY_WARNING",
    "PROVISIONAL_NO_SOURCE_GOVERNANCE_MSG",
    "TIMBRAL_DIAGNOSTIC_TABLE_HEADERS",
    "flatten_timbral_diagnostic_row",
    "run_both_and_combine",
    "run_cluster_analysis",
    "run_fusion_acoustic_heuristic_analysis",
    "run_homogeneity_analysis",
    "run_notated_fusion_potential_analysis",
    "run_orchestration_symbolic_analysis",
    "run_register_uniformity_analysis",
    "run_symbolic_ti_homogeneity_analysis",
    "run_timbral_analysis",
    "write_timbral_diagnostics_csv",
]
