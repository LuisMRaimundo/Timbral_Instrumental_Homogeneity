"""Tests for notation-derived H_notated_fusion_potential (taxonomy-general, no legacy pairwise kernels)."""

from __future__ import annotations

import math

import pytest
import random
from pathlib import Path
from typing import Any

from homogeneity_analyser.analyzers.notated_fusion_potential import (
    build_notated_fusion_slices_for_window,
    compute_effective_instrument_uniformity_same_family_relief,
    compute_notated_fusion_potential_from_slices,
    compute_register_proximity_and_pair_stats,
)
from homogeneity_analyser.models.results import NotatedFusionPotentialSeriesResult
from homogeneity_analyser.services.analysis_service import run_notated_fusion_potential_analysis
from homogeneity_analyser.services.param_validation import (
    resolve_notated_fusion_same_family_relief,
    same_family_relief_override_provided,
)


def _row(ol: float, inst: str, fam: str, tid: str, pitch: float | None = None) -> dict[str, Any]:
    d: dict[str, Any] = {"overlap_ql": ol, "instrument": inst, "family": fam, "technique_state_id": tid}
    if pitch is not None:
        d["pitch"] = float(pitch)
    return d


def _four_same_inst(*, inst: str, fam: str, tech: str, midis: list[float], ol: float = 1.0) -> list[dict]:
    return [
        {
            "overlap_ql": ol,
            "instrument": inst,
            "family": fam,
            "technique_state_id": tech,
            "pitch": float(m),
        }
        for m in midis
    ]


def test_close_register_higher_than_wide_for_strings_woodwinds_brass() -> None:
    """Same fourfold scoring layout: compact MIDI block should beat a wide spread (three families)."""
    close_midis = [60.0, 61.0, 62.0, 63.0]
    wide_midis = [48.0, 60.0, 72.0, 84.0]
    for inst, fam in (
        ("Violin", "strings"),
        ("Flute", "woodwinds"),
        ("Trumpet", "brass"),
    ):
        s_close = _four_same_inst(inst=inst, fam=fam, tech="ord", midis=close_midis)
        s_wide = _four_same_inst(inst=inst, fam=fam, tech="ord", midis=wide_midis)
        h_c, _ = compute_notated_fusion_potential_from_slices(
            s_close, n_events=4, n_pitched_events=4, n_unpitched_events=0, register_ref_semitones=12.0
        )
        h_w, _ = compute_notated_fusion_potential_from_slices(
            s_wide, n_events=4, n_pitched_events=4, n_unpitched_events=0, register_ref_semitones=12.0
        )
        assert h_c > h_w, (inst, h_c, h_w)


def test_same_pitch_layout_different_single_instruments_near_equal() -> None:
    """No family-specific acoustic bias: identical masses + midis → identical scalar."""
    midis = [60.0, 60.0, 60.0, 60.0]
    layouts = [
        ("Violin", "strings"),
        ("Flute", "woodwinds"),
        ("Horn", "brass"),
        ("Trumpet", "brass"),
    ]
    hs: list[float] = []
    for inst, fam in layouts:
        s = _four_same_inst(inst=inst, fam=fam, tech="ordinary", midis=midis)
        h, _ = compute_notated_fusion_potential_from_slices(
            s, n_events=4, n_pitched_events=4, n_unpitched_events=0, register_ref_semitones=12.0
        )
        hs.append(h)
    assert max(hs) - min(hs) <= 1e-9


def test_mixed_instruments_same_family_reduces_instrument_uniformity_only() -> None:
    slices = [_row(1.0, "Clarinet", "woodwinds", "ord", 60.0) for _ in range(3)] + [
        _row(1.0, "Bass Clarinet", "woodwinds", "ord", 60.0)
    ]
    _, d = compute_notated_fusion_potential_from_slices(
        slices, n_events=4, n_pitched_events=4, n_unpitched_events=0, register_ref_semitones=12.0
    )
    assert d["family_uniformity"] == pytest.approx(1.0)
    assert d["technique_only_uniformity"] == pytest.approx(1.0)
    assert d["instrument_uniformity"] == pytest.approx(0.625)
    assert d["same_family_cross_instrument_mass"] == pytest.approx(0.375)
    assert d["effective_instrument_uniformity"] == pytest.approx(0.625 + 0.55 * 0.375)
    eff_u = float(d["effective_instrument_uniformity"])
    inst_u = float(d["instrument_uniformity"])
    assert d["same_family_relief_delta"] == pytest.approx(eff_u - inst_u)
    assert d["same_family_relief_applied"] is True
    assert d["same_family_relief_profile"] == "balanced"
    assert d["evidence_status"] == "literature_motivated_calibrated_proxy"


def test_mixed_families_lowers_family_uniformity() -> None:
    uniform_fam = _four_same_inst(inst="Violin", fam="strings", tech="arco", midis=[60.0, 61.0, 62.0, 63.0])
    mixed = [
        _row(1.0, "Violin", "strings", "arco", 60.0),
        _row(1.0, "Flute", "woodwinds", "ord", 61.0),
        _row(1.0, "Horn", "brass", "open", 62.0),
        _row(1.0, "Clarinet", "woodwinds", "ord", 63.0),
    ]
    _, d_u = compute_notated_fusion_potential_from_slices(
        uniform_fam, n_events=4, n_pitched_events=4, n_unpitched_events=0, register_ref_semitones=12.0
    )
    _, d_m = compute_notated_fusion_potential_from_slices(
        mixed, n_events=4, n_pitched_events=4, n_unpitched_events=0, register_ref_semitones=12.0
    )
    assert d_m["family_uniformity"] < d_u["family_uniformity"]


def test_mixed_technique_reduces_technique_only_uniformity() -> None:
    arco = _four_same_inst(inst="Violin", fam="strings", tech="violin|arco", midis=[60.0, 61.0, 62.0, 63.0])
    mixed = [
        _row(1.0, "Violin", "strings", "violin|arco", 60.0),
        _row(1.0, "Violin", "strings", "violin|arco", 61.0),
        _row(1.0, "Violin", "strings", "violin|pizz", 62.0),
        _row(1.0, "Violin", "strings", "violin|pizz", 63.0),
    ]
    _, d_a = compute_notated_fusion_potential_from_slices(
        arco, n_events=4, n_pitched_events=4, n_unpitched_events=0, register_ref_semitones=12.0
    )
    _, d_x = compute_notated_fusion_potential_from_slices(
        mixed, n_events=4, n_pitched_events=4, n_unpitched_events=0, register_ref_semitones=12.0
    )
    assert d_x["technique_only_uniformity"] < d_a["technique_only_uniformity"]


def test_register_proximity_decreases_with_pairwise_distance() -> None:
    rows2 = [(60.0, 1.0), (60.0, 1.0)]
    r0, _, _, _, _, _ = compute_register_proximity_and_pair_stats(rows2, 12.0)
    prev = r0
    for d in (3, 6, 12, 24, 48):
        rows = [(60.0, 1.0), (60.0 + float(d), 1.0)]
        r, _, _, _, _, st = compute_register_proximity_and_pair_stats(rows, 12.0)
        assert st == "ok"
        assert r < prev
        prev = r


def test_unpitched_only_window_diagnostics() -> None:
    slices = [
        {"overlap_ql": 1.0, "instrument": "Bass Drum", "family": "percussion", "technique_state_id": "bd|ordinary"},
        {"overlap_ql": 1.0, "instrument": "Snare Drum", "family": "percussion", "technique_state_id": "sn|ordinary"},
    ]
    h, d = compute_notated_fusion_potential_from_slices(
        slices, n_events=2, n_pitched_events=0, n_unpitched_events=2, register_ref_semitones=12.0
    )
    assert math.isfinite(h)
    assert d["register_coverage_status"] == "no_pitched_pairs"
    assert d["evidence_status"] == "symbolic_no_register_evidence"
    assert d["register_proximity"] == pytest.approx(1.0)
    assert d["register_pair_count"] == 0


def test_mixed_pitched_and_unpitched_register_uses_pitched_pairs_only() -> None:
    slices = [
        _row(1.0, "Violin", "strings", "violin|arco", 60.0),
        _row(1.0, "Violin", "strings", "violin|arco", 61.0),
        _row(2.0, "Snare Drum", "percussion", "sn|ordinary"),
    ]
    _, d = compute_notated_fusion_potential_from_slices(
        slices, n_events=3, n_pitched_events=2, n_unpitched_events=1, register_ref_semitones=12.0
    )
    assert d["register_coverage_status"] == "ok"
    assert d["n_pitched_events"] == 2
    assert d["n_unpitched_events"] == 1
    assert d["register_pitch_coverage_ratio"] == pytest.approx(2.0 / 4.0)


def test_build_slices_from_events_unpitched_and_pitched() -> None:
    active = [
        {
            "offset": 0.0,
            "end": 4.0,
            "pitches": [60.0],
            "instrument": "Violin",
            "family": "strings",
            "technique_state_id": "violin|arco",
        },
        {
            "offset": 0.0,
            "end": 4.0,
            "pitches": [],
            "instrument": "Snare Drum",
            "family": "percussion",
            "technique_state_id": "sn|ordinary",
        },
    ]
    slices, n_ev, n_pe, n_ue = build_notated_fusion_slices_for_window(active, 0.0, 4.0)
    assert n_ev == 2 and n_pe == 1 and n_ue == 1
    assert len(slices) == 2


def test_same_family_relief_numeric_cases_1_to_6() -> None:
    """Distribution-based diagnostics (no instrument/family special cases)."""
    # 1 — single instrument
    s1 = [_row(1.0, "Violin", "strings", "v|arco", 60.0)]
    _, d1 = compute_notated_fusion_potential_from_slices(
        s1,
        n_events=1,
        n_pitched_events=1,
        n_unpitched_events=0,
        same_family_relief=0.45,
        same_family_relief_profile="conservative",
    )
    assert d1["instrument_uniformity"] == pytest.approx(1.0)
    assert d1["family_uniformity"] == pytest.approx(1.0)
    assert d1["same_family_cross_instrument_mass"] == pytest.approx(0.0)
    assert d1["effective_instrument_uniformity"] == pytest.approx(1.0)

    # 2 — two instruments, same family, equal mass
    s2 = [_row(0.5, "Violin", "strings", "v|arco", 60.0), _row(0.5, "Viola", "strings", "va|arco", 61.0)]
    _, d2 = compute_notated_fusion_potential_from_slices(
        s2,
        n_events=2,
        n_pitched_events=2,
        n_unpitched_events=0,
        same_family_relief=0.45,
        same_family_relief_profile="conservative",
    )
    assert d2["instrument_uniformity"] == pytest.approx(0.5)
    assert d2["family_uniformity"] == pytest.approx(1.0)
    assert d2["same_family_cross_instrument_mass"] == pytest.approx(0.5)

    # 3 — four instruments, same family, equal mass
    s3 = [
        _row(0.25, "Flute", "flutes", "ord", 60.0),
        _row(0.25, "Piccolo", "flutes", "ord", 61.0),
        _row(0.25, "Alto Flute", "flutes", "ord", 62.0),
        _row(0.25, "Bass Flute", "flutes", "ord", 63.0),
    ]
    _, d3 = compute_notated_fusion_potential_from_slices(
        s3,
        n_events=4,
        n_pitched_events=4,
        n_unpitched_events=0,
        same_family_relief=0.45,
        same_family_relief_profile="conservative",
    )
    assert d3["instrument_uniformity"] == pytest.approx(0.25)
    assert d3["family_uniformity"] == pytest.approx(1.0)
    assert d3["same_family_cross_instrument_mass"] == pytest.approx(0.75)

    # 4 — uneven same-family (user 0.75 / 0.25)
    s4 = [_row(0.75, "Clarinet", "clarinets", "ord", 60.0), _row(0.25, "Bass Clarinet", "clarinets", "ord", 61.0)]
    _, d4 = compute_notated_fusion_potential_from_slices(
        s4,
        n_events=2,
        n_pitched_events=2,
        n_unpitched_events=0,
        same_family_relief=0.45,
        same_family_relief_profile="conservative",
    )
    assert d4["instrument_uniformity"] == pytest.approx(0.625)
    assert d4["family_uniformity"] == pytest.approx(1.0)
    assert d4["same_family_cross_instrument_mass"] == pytest.approx(0.375)

    # 5 — two families, two instruments each, equal split
    s5 = [
        _row(0.25, "Violin", "strings", "v|arco", 60.0),
        _row(0.25, "Viola", "strings", "va|arco", 61.0),
        _row(0.25, "Flute", "woodwinds", "ord", 62.0),
        _row(0.25, "Oboe", "woodwinds", "ord", 63.0),
    ]
    _, d5 = compute_notated_fusion_potential_from_slices(
        s5,
        n_events=4,
        n_pitched_events=4,
        n_unpitched_events=0,
        same_family_relief=0.45,
        same_family_relief_profile="conservative",
    )
    assert d5["instrument_uniformity"] == pytest.approx(0.25)
    assert d5["family_uniformity"] == pytest.approx(0.5)
    assert d5["same_family_cross_instrument_mass"] == pytest.approx(0.25)

    # 6 — four different families
    s6 = [
        _row(0.25, "Violin", "strings", "v|arco", 60.0),
        _row(0.25, "Flute", "woodwinds", "ord", 61.0),
        _row(0.25, "Horn", "brass", "open", 62.0),
        _row(0.25, "Clarinet", "clarinets", "ord", 63.0),
    ]
    _, d6 = compute_notated_fusion_potential_from_slices(
        s6,
        n_events=4,
        n_pitched_events=4,
        n_unpitched_events=0,
        same_family_relief=0.45,
        same_family_relief_profile="conservative",
    )
    assert d6["instrument_uniformity"] == pytest.approx(0.25)
    assert d6["family_uniformity"] == pytest.approx(0.25)
    assert d6["same_family_cross_instrument_mass"] == pytest.approx(0.0)
    assert d6["effective_instrument_uniformity"] == pytest.approx(d6["instrument_uniformity"])


def test_same_family_relief_extremes_and_mid_bounds() -> None:
    """Cases 7–9: relief 0 / 1 / default bracketing."""
    hi, hf = 0.625, 1.0
    cross = max(0.0, hf - hi)

    eff0, d0 = compute_effective_instrument_uniformity_same_family_relief(hi, hf, same_family_relief=0.0)
    assert eff0 == pytest.approx(hi)
    assert d0["effective_instrument_uniformity"] == pytest.approx(d0["instrument_uniformity"])

    eff1, d1 = compute_effective_instrument_uniformity_same_family_relief(hi, hf, same_family_relief=1.0)
    assert eff1 == pytest.approx(hf)
    assert d1["effective_instrument_uniformity"] == pytest.approx(d1["family_uniformity"])

    eff_m, dm = compute_effective_instrument_uniformity_same_family_relief(hi, hf, same_family_relief=0.55)
    assert dm["instrument_uniformity"] <= eff_m <= dm["family_uniformity"]
    assert eff_m == pytest.approx(hi + 0.55 * cross)

    s = [_row(0.75, "Trombone", "brass", "ord", 50.0), _row(0.25, "Bass Trombone", "brass", "ord", 48.0)]
    for relief in (0.0, 1.0, 0.55):
        _, d = compute_notated_fusion_potential_from_slices(
            s,
            n_events=2,
            n_pitched_events=2,
            n_unpitched_events=0,
            same_family_relief=relief,
            register_ref_semitones=12.0,
        )
        hi_w = float(d["instrument_uniformity"])
        hf_w = float(d["family_uniformity"])
        eff_w = float(d["effective_instrument_uniformity"])
        if relief == 0.0:
            assert eff_w == pytest.approx(hi_w)
        elif relief == 1.0:
            assert eff_w == pytest.approx(hf_w)
        else:
            assert hi_w <= eff_w <= hf_w


def test_same_family_relief_random_mass_splits_property() -> None:
    """For any nonnegative masses on instruments in one family, cross = hf - hi and eff brackets."""
    rng = random.Random(42)
    for _ in range(80):
        k = rng.randint(2, 8)
        raw = [rng.random() for _ in range(k)]
        s_mass = sum(raw)
        masses = [x / s_mass for x in raw]
        hi = sum(m * m for m in masses)
        hf = 1.0
        cross = max(0.0, hf - hi)
        assert cross == pytest.approx(hf - hi)
        for r in (0.0, 0.31, 1.0):
            eff, d = compute_effective_instrument_uniformity_same_family_relief(hi, hf, same_family_relief=r)
            assert d["same_family_cross_instrument_mass"] == pytest.approx(cross)
            assert eff == pytest.approx(hi + r * cross)
            if r == 0.0:
                assert eff == pytest.approx(hi)
            elif r == 1.0:
                assert eff == pytest.approx(hf)
            else:
                assert hi <= eff <= hf


def test_case4_balanced_clarinet_bass_effective_uniformity() -> None:
    s4 = [_row(0.75, "Clarinet", "clarinets", "ord", 60.0), _row(0.25, "Bass Clarinet", "clarinets", "ord", 61.0)]
    _, d = compute_notated_fusion_potential_from_slices(
        s4,
        n_events=2,
        n_pitched_events=2,
        n_unpitched_events=0,
        same_family_relief=0.55,
        same_family_relief_profile="balanced",
        register_ref_semitones=12.0,
    )
    assert d["effective_instrument_uniformity"] == pytest.approx(0.83125)


def test_four_identical_instruments_H_invariant_across_relief_values() -> None:
    s = _four_same_inst(inst="Violin", fam="strings", tech="ord", midis=[60.0, 61.0, 62.0, 63.0])
    hs: list[float] = []
    for r in (0.0, 0.45, 0.55, 0.65):
        h, d = compute_notated_fusion_potential_from_slices(
            s, n_events=4, n_pitched_events=4, n_unpitched_events=0, same_family_relief=r, register_ref_semitones=12.0
        )
        assert d["same_family_cross_instrument_mass"] == pytest.approx(0.0)
        hs.append(h)
    assert max(hs) - min(hs) <= 1e-9


def test_monotonicity_H_notated_vs_relief_when_cross_mass_positive() -> None:
    slices = [_row(1.0, "Clarinet", "woodwinds", "ord", 60.0) for _ in range(3)] + [
        _row(1.0, "Bass Clarinet", "woodwinds", "ord", 61.0)
    ]
    hs: list[float] = []
    for r in (0.0, 0.45, 0.55, 0.65):
        h, _ = compute_notated_fusion_potential_from_slices(
            slices,
            n_events=4,
            n_pitched_events=4,
            n_unpitched_events=0,
            same_family_relief=r,
            register_ref_semitones=12.0,
        )
        hs.append(h)
    assert hs[0] < hs[1] < hs[2] < hs[3]


def test_balanced_higher_than_conservative_same_family_mix() -> None:
    slices = [_row(1.0, "Clarinet", "woodwinds", "ord", 60.0) for _ in range(3)] + [
        _row(1.0, "Bass Clarinet", "woodwinds", "ord", 61.0)
    ]
    h_cons, _ = compute_notated_fusion_potential_from_slices(
        slices,
        n_events=4,
        n_pitched_events=4,
        n_unpitched_events=0,
        same_family_relief=0.45,
        same_family_relief_profile="conservative",
        register_ref_semitones=12.0,
    )
    h_bal, _ = compute_notated_fusion_potential_from_slices(
        slices,
        n_events=4,
        n_pitched_events=4,
        n_unpitched_events=0,
        same_family_relief=0.55,
        same_family_relief_profile="balanced",
        register_ref_semitones=12.0,
    )
    h_four, _ = compute_notated_fusion_potential_from_slices(
        _four_same_inst(inst="Clarinet", fam="woodwinds", tech="ord", midis=[60.0, 61.0, 62.0, 63.0]),
        n_events=4,
        n_pitched_events=4,
        n_unpitched_events=0,
        same_family_relief=0.55,
        register_ref_semitones=12.0,
    )
    assert h_bal > h_cons
    assert h_bal < h_four


def test_strict_profile_register_ok_evidence_symbolic_register_proxy() -> None:
    s = [_row(0.5, "Violin", "strings", "a", 60.0), _row(0.5, "Viola", "strings", "a", 61.0)]
    _, d = compute_notated_fusion_potential_from_slices(
        s,
        n_events=2,
        n_pitched_events=2,
        n_unpitched_events=0,
        same_family_relief=0.0,
        same_family_relief_profile="strict",
        register_ref_semitones=12.0,
    )
    assert d["evidence_status"] == "symbolic_register_proxy"


def test_same_family_relief_override_provided_semantics() -> None:
    assert same_family_relief_override_provided(None) is False
    assert same_family_relief_override_provided("") is False
    assert same_family_relief_override_provided("  \t ") is False
    assert same_family_relief_override_provided(0.0) is True
    assert same_family_relief_override_provided(0) is True
    assert same_family_relief_override_provided("0") is True
    assert same_family_relief_override_provided("0.55") is True
    assert same_family_relief_override_provided(False) is False
    assert same_family_relief_override_provided(True) is False


def test_resolve_notated_fusion_same_family_relief_profiles_and_override() -> None:
    r, prof, ovr = resolve_notated_fusion_same_family_relief(
        {"same_family_relief_profile": "balanced", "same_family_relief_override": None}
    )
    assert r == pytest.approx(0.55)
    assert prof == "balanced"
    assert ovr is False

    r, prof, ovr = resolve_notated_fusion_same_family_relief(
        {"same_family_relief_profile": "balanced", "same_family_relief_override": ""}
    )
    assert r == pytest.approx(0.55)
    assert prof == "balanced"
    assert ovr is False

    r, prof, ovr = resolve_notated_fusion_same_family_relief(
        {"same_family_relief_profile": "balanced", "same_family_relief_override": 0.0}
    )
    assert r == pytest.approx(0.0)
    assert prof == "balanced"
    assert ovr is True

    r, prof, ovr = resolve_notated_fusion_same_family_relief({"same_family_relief_profile": "strict"})
    assert r == pytest.approx(0.0)
    assert prof == "strict"
    assert ovr is False

    r, prof, ovr = resolve_notated_fusion_same_family_relief({"same_family_relief_profile": "conservative"})
    assert r == pytest.approx(0.45)
    assert prof == "conservative"
    assert ovr is False

    r, prof, ovr = resolve_notated_fusion_same_family_relief({"same_family_relief_profile": "permissive"})
    assert r == pytest.approx(0.65)
    assert prof == "permissive"
    assert ovr is False

    r, prof, ovr = resolve_notated_fusion_same_family_relief(
        {"same_family_relief_profile": "strict", "same_family_relief_override": 0.4}
    )
    assert r == pytest.approx(0.4)
    assert prof == "strict"
    assert ovr is True


def test_cf03_three_clarinets_one_bass_balanced_no_override() -> None:
    """validation/cases/cf03 — balanced profile must resolve ρ=0.55 (not Gradio-style spurious 0.0)."""
    repo = Path(__file__).resolve().parents[1]
    xml_path = repo / "validation" / "cases" / "cf03_clarinets_bass_chromatic.xml"
    if not xml_path.is_file():
        pytest.skip("cf03_clarinets_bass_chromatic.xml not found")
    out = run_notated_fusion_potential_analysis(
        str(xml_path),
        {
            "same_family_relief_profile": "balanced",
            "time_step": 1.0,
            "window_size": 8.0,
        },
    )
    assert out.get("error") is None
    p = out.get("notated_fusion_parameters") or {}
    assert p["same_family_relief"] == pytest.approx(0.55)
    assert p["same_family_relief_profile"] == "balanced"
    assert p.get("same_family_relief_from_override") is False

    d0 = (out.get("results") or {}).get("H_notated_fusion_potential_diagnostics", [{}])[0]
    assert d0["instrument_uniformity"] == pytest.approx(0.625)
    assert d0["family_uniformity"] == pytest.approx(1.0)
    assert d0["same_family_cross_instrument_mass"] == pytest.approx(0.375)
    assert d0["same_family_relief"] == pytest.approx(0.55)
    assert d0["effective_instrument_uniformity"] == pytest.approx(0.83125)
    assert d0["same_family_relief_applied"] is True
    assert float(d0["same_family_relief_delta"]) > 1e-12

    h0 = float((out.get("results") or {}).get("H_notated_fusion_potential", [0.0])[0])
    out_s = run_notated_fusion_potential_analysis(
        str(xml_path),
        {
            "same_family_relief_profile": "strict",
            "time_step": 1.0,
            "window_size": 8.0,
        },
    )
    assert out_s.get("error") is None
    h_strict = float((out_s.get("results") or {}).get("H_notated_fusion_potential", [0.0])[0])
    assert h0 > h_strict + 1e-6
    assert h_strict == pytest.approx(0.8359793505, rel=1e-9, abs=1e-9)
    assert 0.90 <= h0 <= 0.915

    h_four, _ = compute_notated_fusion_potential_from_slices(
        _four_same_inst(inst="Clarinet", fam="woodwinds", tech="ord", midis=[60.0, 61.0, 62.0, 63.0]),
        n_events=4,
        n_pitched_events=4,
        n_unpitched_events=0,
        same_family_relief=0.55,
        same_family_relief_profile="balanced",
        register_ref_semitones=12.0,
    )
    assert h0 < float(h_four) - 1e-6
    assert float(h_four) == pytest.approx(0.962568277419765, rel=1e-9, abs=1e-9)


def test_notated_fusion_series_result_roundtrip() -> None:
    raw = {
        "t": [0.0, 1.0],
        "H_notated_fusion_potential": [0.7, 0.8],
        "H_notated_fusion_potential_diagnostics": [{"a": 1}, {"b": 2}],
    }
    s = NotatedFusionPotentialSeriesResult.from_legacy(raw)
    out = s.as_legacy_dict()
    assert out["H_notated_fusion_potential"] == [0.7, 0.8]
    assert len(out["H_notated_fusion_potential_diagnostics"]) == 2
    assert out["H_notated_fusion_potential_dynamic"] == [0.7, 0.8]

    raw2 = {
        "t": [0.0, 1.0],
        "H_notated_fusion_potential": [0.7, 0.8],
        "H_notated_fusion_potential_diagnostics": [
            {"H_notated_fusion_potential_dynamic": 0.65},
            {"H_notated_fusion_potential_dynamic": 0.75},
        ],
    }
    s2 = NotatedFusionPotentialSeriesResult.from_legacy(raw2)
    out2 = s2.as_legacy_dict()
    assert out2["H_notated_fusion_potential_dynamic"] == [0.65, 0.75]
