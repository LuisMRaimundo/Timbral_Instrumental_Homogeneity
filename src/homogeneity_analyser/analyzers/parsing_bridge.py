"""Thin bridge from analyzers to I/O (keeps analyzer package free of UI concerns)."""

from homogeneity_analyser.io.score_loader import parse_score

__all__ = ["parse_score"]
