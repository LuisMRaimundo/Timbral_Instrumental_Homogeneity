"""Technique uniformity and coverage_status resolution for H_TI windows."""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.analyzers.hti_concentration import herfindahl_from_masses
from homogeneity_analyser.analyzers.technique_state import (
    compute_technique_uniformity_key_from_event,
    event_has_special_explicit_technique,
)


def resolve_technique_uniformity_and_coverage(
    tech_mass: dict[str, float],
    contrib: list[tuple[dict[str, Any], float]],
) -> tuple[float, str]:
    """
    Return ``(technique_uniformity, technique_coverage_status)`` for one overlap window.

    Mirrors the branch logic previously inlined in ``SymbolicTIHomogeneityAnalyzer.extract_hti_window``.
    """
    tot_ol = float(sum(ol for _, ol in contrib))
    m_nonempty = sum(ol for e, ol in contrib if compute_technique_uniformity_key_from_event(e).strip())
    m_empty = max(0.0, tot_ol - m_nonempty)
    any_special = any(event_has_special_explicit_technique(e) for e, _ol in contrib)
    all_non_special = not any_special
    tech_keys_nonempty = [k for k, v in tech_mass.items() if str(k).strip() and float(v) > 1e-15]
    n_distinct_uniformity_keys = len({k for k in tech_keys_nonempty})

    if m_nonempty <= 1e-12:
        return float("nan"), "unavailable"
    if tot_ol > 1e-12 and m_empty / tot_ol > 0.15 and m_nonempty / tot_ol > 0.15:
        return float("nan"), "ambiguous"
    if all_non_special:
        return 1.0, "ordinary_default_uniform"
    if any_special and n_distinct_uniformity_keys >= 2:
        return herfindahl_from_masses(dict(tech_mass)), "explicit_mixed"
    if any_special and n_distinct_uniformity_keys == 1:
        return 1.0, "explicit_uniform"
    return float("nan"), "unavailable"
