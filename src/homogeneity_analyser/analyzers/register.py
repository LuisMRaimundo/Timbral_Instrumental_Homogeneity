"""Compatibility shim — implementation in ``homogeneity_analyser.legacy.register``."""

from homogeneity_analyser.legacy.register import *  # noqa: F403
from homogeneity_analyser.legacy.register import RegisterUniformityAnalyzer

__all__ = ["RegisterUniformityAnalyzer"]
