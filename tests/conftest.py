"""Pytest hooks — auto-mark legacy multimetric test modules."""

from __future__ import annotations

import pytest

# Whole modules that exercise JSON 1.8 / multimetric services (not H_TI product path).
_LEGACY_MODULES = frozenset(
    {
        "test_analysis_service",
        "test_cluster_metric",
        "test_fusion_acoustic_heuristic",
        "test_legacy_multimetric_ui_params",
        "test_legacy_package",
        "test_legacy_ui_params",
        "test_notated_fusion_dynamic",
        "test_notated_fusion_potential",
        "test_parse_ui_float",
        "test_timbral_decomposition",
        "test_timbral_fusion_corpus_validation",
        "test_timbral_ui_params",
    }
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        mod = item.module.__name__.rsplit(".", 1)[-1]
        if mod in _LEGACY_MODULES:
            item.add_marker(pytest.mark.legacy)
