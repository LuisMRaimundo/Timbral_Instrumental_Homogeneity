"""Architecture contract: H_TI must not depend on TimbralHomogeneityAnalyzer inheritance."""

from __future__ import annotations

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.symbolic_score_analyzer import SymbolicScoreAnalyzer
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer


def test_hti_inherits_symbolic_score_analyzer_only() -> None:
    assert issubclass(SymbolicTIHomogeneityAnalyzer, SymbolicScoreAnalyzer)
    assert not issubclass(SymbolicTIHomogeneityAnalyzer, TimbralHomogeneityAnalyzer)


def test_timbral_inherits_symbolic_score_analyzer() -> None:
    assert issubclass(TimbralHomogeneityAnalyzer, SymbolicScoreAnalyzer)
    assert TimbralHomogeneityAnalyzer is not SymbolicScoreAnalyzer
