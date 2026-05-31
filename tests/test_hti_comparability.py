"""Unit tests for ``hti_comparability`` classification."""

from __future__ import annotations

import pytest

from homogeneity_analyser.analyzers.hti_comparability import (
    HTI_COMPARABILITY_CLASSES,
    classify_hti_comparability_class,
)


@pytest.mark.parametrize("label", HTI_COMPARABILITY_CLASSES)
def test_comparability_labels_are_stable_strings(label: str) -> None:
    assert isinstance(label, str) and label


def test_no_active_events_when_feats_missing() -> None:
    assert classify_hti_comparability_class(feats=None, active_weights={}) == "no_active_events"


def test_full_four_component() -> None:
    aw = {
        "instrument_uniformity": 0.4,
        "family_uniformity": 0.25,
        "technique_uniformity": 0.15,
        "register_proximity": 0.2,
    }
    feats = {"instrument_uniformity": 1.0}
    assert classify_hti_comparability_class(feats=feats, active_weights=aw) == "full_4_component"


def test_instrument_family_only() -> None:
    aw = {"instrument_uniformity": 0.6153846153846154, "family_uniformity": 0.38461538461538464}
    feats = {"instrument_uniformity": 1.0}
    assert classify_hti_comparability_class(feats=feats, active_weights=aw) == "instrument_family_only"


def test_no_technique_keeps_register() -> None:
    aw = {
        "instrument_uniformity": 0.5,
        "family_uniformity": 0.3125,
        "register_proximity": 0.1875,
    }
    feats = {"register_coverage_status": "pitched"}
    assert classify_hti_comparability_class(feats=feats, active_weights=aw) == "no_technique"


def test_no_register_keeps_technique() -> None:
    aw = {
        "instrument_uniformity": 0.5,
        "family_uniformity": 0.3125,
        "technique_uniformity": 0.1875,
    }
    feats = {"technique_coverage_status": "explicit_uniform"}
    assert classify_hti_comparability_class(feats=feats, active_weights=aw) == "no_register"
