"""Unit tests for ``hti_active_weights`` (H_TI_core component renormalisation)."""

from __future__ import annotations

import math

import pytest

from homogeneity_analyser.analyzers.hti_active_weights import (
    compute_hti_active_components,
    weighted_geometric_mean_hti,
)


def test_none_feats_returns_nan_and_full_weight_template() -> None:
    h, comp, aw, diag = compute_hti_active_components(None)
    assert math.isnan(h)
    assert comp == {}
    assert diag["reason"] == "no_active_events"
    assert set(aw) == {
        "instrument_uniformity",
        "family_uniformity",
        "technique_uniformity",
        "register_proximity",
    }
    assert sum(aw.values()) == pytest.approx(1.0, abs=1e-12)


def test_ambiguous_technique_omits_technique_weight() -> None:
    feats = {
        "instrument_uniformity": 0.5,
        "family_uniformity": 1.0,
        "technique_uniformity": float("nan"),
        "technique_coverage_status": "ambiguous",
        "register_coverage_status": "pitched",
        "register_proximity": 1.0,
    }
    h, comp, aw, _diag = compute_hti_active_components(feats)
    assert math.isfinite(h)
    assert "technique_uniformity" not in aw
    assert "technique_uniformity" not in comp
    assert "register_proximity" in aw
    assert sum(aw.values()) == pytest.approx(1.0, abs=1e-12)


def test_unavailable_technique_same_as_ambiguous_for_weights() -> None:
    feats = {
        "instrument_uniformity": 1.0,
        "family_uniformity": 1.0,
        "technique_uniformity": float("nan"),
        "technique_coverage_status": "unavailable",
        "register_coverage_status": "pitched",
        "register_proximity": 1.0,
    }
    _h, _comp, aw, _diag = compute_hti_active_components(feats)
    assert "technique_uniformity" not in aw


def test_weighted_geometric_mean_single_component() -> None:
    v = weighted_geometric_mean_hti(
        {"instrument_uniformity": 0.25},
        {"instrument_uniformity": 1.0},
        ["instrument_uniformity"],
    )
    assert v == pytest.approx(0.25, abs=1e-12)
