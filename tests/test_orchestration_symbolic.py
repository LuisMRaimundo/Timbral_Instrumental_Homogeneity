"""Tests for neutral H_orchestration_symbolic (Herfindahl slice core)."""

from __future__ import annotations

import pytest

from homogeneity_analyser.analyzers.orchestration_symbolic import (
    compute_orchestration_symbolic_from_slices,
    herfindahl_concentration,
)


def _slice(
    *,
    instrument: str,
    family: str,
    technique_state_id: str,
    overlap_ql: float = 1.0,
) -> dict:
    return {
        "overlap_ql": overlap_ql,
        "instrument": instrument,
        "family": family,
        "technique_state_id": technique_state_id,
    }


def test_four_horns_vs_four_violins_equal_when_shares_match():
    """No family fusion: identical mass layout → identical H (labels differ only by category name)."""
    horns = [
        _slice(instrument="Horn", family="brass", technique_state_id="stopped"),
    ] * 4
    violins = [
        _slice(instrument="Violin", family="strings", technique_state_id="arco"),
    ] * 4
    h_h, d_h = compute_orchestration_symbolic_from_slices(horns)
    h_v, d_v = compute_orchestration_symbolic_from_slices(violins)
    assert h_h == pytest.approx(h_v, rel=0, abs=1e-9)
    assert d_h["instrument_uniformity"] == pytest.approx(1.0)
    assert d_v["instrument_uniformity"] == pytest.approx(1.0)
    assert d_h["family_uniformity"] == pytest.approx(1.0)
    assert d_v["family_uniformity"] == pytest.approx(1.0)


def test_three_clarinets_one_bass_clarinet_between_uniform_and_random():
    """Two canonical instruments, one family: instrument Herfindahl 0.625; not double-penalized by extra family axis."""
    uniform = [_slice(instrument="Clarinet", family="woodwinds", technique_state_id="ord")] * 4
    mixed = [_slice(instrument="Clarinet", family="woodwinds", technique_state_id="ord")] * 3 + [
        _slice(instrument="Bass Clarinet", family="woodwinds", technique_state_id="ord")
    ]
    h_u, d_u = compute_orchestration_symbolic_from_slices(uniform)
    h_m, d_m = compute_orchestration_symbolic_from_slices(mixed)
    assert h_u > h_m
    assert d_m["instrument_uniformity"] == pytest.approx(0.625)  # (3/4)^2 + (1/4)^2
    assert d_m["family_uniformity"] == pytest.approx(1.0)
    # Still clearly above neutral empty-window 0.5 on the scalar
    assert h_m > 0.55


def test_mixed_technique_lowers_technique_uniformity():
    uniform_tech = [_slice(instrument="Violin", family="strings", technique_state_id="arco")] * 4
    mixed_tech = [_slice(instrument="Violin", family="strings", technique_state_id="arco")] * 2 + [
        _slice(instrument="Violin", family="strings", technique_state_id="pizz")
    ] * 2
    _, d_u = compute_orchestration_symbolic_from_slices(uniform_tech)
    _, d_m = compute_orchestration_symbolic_from_slices(mixed_tech)
    assert d_u["technique_uniformity"] == pytest.approx(1.0)
    assert d_m["technique_uniformity"] == pytest.approx(0.5)
    assert d_m["H_orchestration_symbolic"] < d_u["H_orchestration_symbolic"]


def test_mixed_open_stopped_horns_lower_than_uniform_stopped():
    stopped = [_slice(instrument="Horn", family="brass", technique_state_id="stopped")] * 4
    mixed = [_slice(instrument="Horn", family="brass", technique_state_id="stopped")] * 2 + [
        _slice(instrument="Horn", family="brass", technique_state_id="open")
    ] * 2
    h_s, _ = compute_orchestration_symbolic_from_slices(stopped)
    h_x, _ = compute_orchestration_symbolic_from_slices(mixed)
    assert h_s > h_x


def test_herfindahl_empty_returns_half():
    assert herfindahl_concentration({}) == pytest.approx(0.5)
