"""Lazy legacy exports from ``homogeneity_analyser.analyzers``."""

from __future__ import annotations

import homogeneity_analyser.legacy as legacy
from homogeneity_analyser.analyzers import HomogeneityAnalyzer, RegisterUniformityAnalyzer


def test_lazy_legacy_same_class_as_package() -> None:
    assert HomogeneityAnalyzer is legacy.HomogeneityAnalyzer
    assert RegisterUniformityAnalyzer is legacy.RegisterUniformityAnalyzer
