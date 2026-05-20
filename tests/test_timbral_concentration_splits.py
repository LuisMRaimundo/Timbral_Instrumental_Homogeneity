"""Technique-only concentration splits (avoid double-counting instrument mix on technique axis)."""

from __future__ import annotations

import pytest

from homogeneity_analyser.analyzers.orchestration_symbolic import compute_orchestration_symbolic_from_slices
from homogeneity_analyser.analyzers.timbral_concentration_splits import (
    concentration_bundle_from_timbral_slices,
    technique_only_distribution_key,
)


def test_technique_only_key_examples():
    assert technique_only_distribution_key("", "Clarinet") == "__ordinary__"
    assert technique_only_distribution_key("Clarinet", "Clarinet") == "__ordinary__"
    assert technique_only_distribution_key("Bass Clarinet", "Bass Clarinet") == "__ordinary__"
    assert technique_only_distribution_key("Horn|stopped", "Horn") == "stopped"
    assert technique_only_distribution_key("Horn|open", "Horn") == "open"
    assert technique_only_distribution_key("violin|arco|sul_pont", "violin") == "arco|sul_pont"


def _s(
    *,
    instrument: str,
    family: str,
    technique_state_id: str,
    overlap_ql: float = 1.0,
) -> dict:
    return {
        "instrument": instrument,
        "family": family,
        "technique_state_id": technique_state_id,
        "overlap_ql": overlap_ql,
    }


def test_three_clarinets_one_bass_clarinet_ordinary_technique_only_is_one():
    slices = [_s(instrument="Clarinet", family="woodwinds", technique_state_id="Clarinet")] * 3 + [
        _s(instrument="Bass Clarinet", family="woodwinds", technique_state_id="Bass Clarinet")
    ]
    b = concentration_bundle_from_timbral_slices(slices)
    assert b["technique_only_concentration"] == pytest.approx(1.0)
    assert b["full_state_concentration"] < 1.0


def test_mixed_horn_open_stopped_technique_only_below_one():
    slices = [_s(instrument="Horn", family="brass", technique_state_id="Horn|open")] * 2 + [
        _s(instrument="Horn", family="brass", technique_state_id="Horn|stopped")
    ] * 2
    b = concentration_bundle_from_timbral_slices(slices)
    assert b["technique_only_concentration"] < 1.0


def test_mixed_violin_arco_pizz_technique_only_below_one():
    slices = [_s(instrument="Violin", family="strings", technique_state_id="Violin|arco")] * 2 + [
        _s(instrument="Violin", family="strings", technique_state_id="Violin|pizz")
    ] * 2
    b = concentration_bundle_from_timbral_slices(slices)
    assert b["technique_only_concentration"] < 1.0


def test_orchestration_symbolic_reports_full_and_only_uniformities():
    mixed = [_s(instrument="Clarinet", family="woodwinds", technique_state_id="Clarinet")] * 3 + [
        _s(instrument="Bass Clarinet", family="woodwinds", technique_state_id="Bass Clarinet")
    ]
    _, d = compute_orchestration_symbolic_from_slices(mixed)
    assert d["technique_only_concentration"] == pytest.approx(1.0)
    assert d["full_technique_state_uniformity"] < 1.0
    assert d["technique_uniformity"] == d["technique_only_concentration"]
