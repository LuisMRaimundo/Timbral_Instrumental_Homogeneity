"""
Golden-output regression for H_TI_core numerical stability.

Locks verified scalar outputs for minimal MusicXML fixtures; does not change numerics
when behaviour matches documented geometry (record current values when not obvious).
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from music21 import converter

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"
_TOL = {"abs": 1e-9, "rel": 1e-9}

# Scenario B: two equal-mass pitched instruments, same family (violin + viola unison C5).
_GOLDEN_VIOLIN_VIOLA_H_TI_CORE = 0.7578582832551991


def _load(name: str):
    path = FIXTURE_DIR / name
    if not path.is_file():
        pytest.skip(f"missing fixture {name}")
    return converter.parse(str(path))


def _window_core(score, *, t0: float = 2.0, t1: float = 4.0, **kwargs) -> tuple[float, dict, dict]:
    an = SymbolicTIHomogeneityAnalyzer(music21_score=score, time_step=1.0, **kwargs)
    feats = an.extract_hti_window(t0, t1)
    if feats is None:
        return float("nan"), {}, {}
    h, _diag, aw = an.compute_H_TI(feats)
    return float(h), feats, aw


def _assert_hti_aliases_equal(results: dict, index: int = 0) -> None:
    h = float(results["H_TI_core"][index])
    assert results["H_TI"][index] == pytest.approx(h, **_TOL)
    assert results["H_TI_strict"][index] == pytest.approx(h, **_TOL)
    assert 0.0 <= h <= 1.0


class TestGoldenSingleSustainedPitched:
    """Scenario A: single-instrument-class sustained unison (two violins, same pitch)."""

    def test_two_violins_unison_core_and_uniformities(self) -> None:
        sc = _load("golden_two_violins_unison_c5.musicxml")
        h, feats, aw = _window_core(sc)
        assert h == pytest.approx(1.0, **_TOL)
        assert feats["instrument_uniformity"] == pytest.approx(1.0, **_TOL)
        assert feats["family_uniformity"] == pytest.approx(1.0, **_TOL)
        assert feats["technique_coverage_status"] == "ordinary_default_uniform"
        assert feats["register_coverage_status"] == "pitched"
        assert math.isfinite(float(feats["register_compactness"]))
        assert feats["register_span_semitones"] == pytest.approx(0.0, **_TOL)
        assert aw.keys() == {
            "instrument_uniformity",
            "family_uniformity",
            "technique_uniformity",
            "register_proximity",
        }
        assert sum(aw.values()) == pytest.approx(1.0, **_TOL)

    def test_analyze_series_exports_comparability_class(self) -> None:
        sc = _load("golden_two_violins_unison_c5.musicxml")
        an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        results = an.analyze_hti(4.0, edge_policy="mark_partial_windows")
        assert "hti_comparability_class" in results
        assert len(results["hti_comparability_class"]) == len(results["t"])
        assert results["hti_comparability_class"][2] == "full_4_component"

    def test_analyze_series_aliases_and_bounds(self) -> None:
        sc = _load("golden_two_violins_unison_c5.musicxml")
        an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        results = an.analyze_hti(4.0, edge_policy="mark_partial_windows")
        assert len(results["t"]) == 5
        for i in range(len(results["t"])):
            _assert_hti_aliases_equal(results, i)
        assert results["H_TI_core"][2] == pytest.approx(1.0, **_TOL)


class TestGoldenTwoPitchedEqualMass:
    """Scenario B: violin + viola, equal overlap mass at unison."""

    def test_violin_viola_golden_scalar_and_register(self) -> None:
        sc = _load("golden_violin_viola_unison_c5.musicxml")
        h, feats, aw = _window_core(sc)
        assert h == pytest.approx(_GOLDEN_VIOLIN_VIOLA_H_TI_CORE, **_TOL)
        assert feats["instrument_uniformity"] == pytest.approx(0.5, **_TOL)
        assert feats["family_uniformity"] == pytest.approx(1.0, **_TOL)
        assert feats["register_span_semitones"] == pytest.approx(0.0, **_TOL)
        assert feats["pairwise_interval_proximity"] == pytest.approx(1.0, **_TOL)
        assert "technique_uniformity" in aw
        assert "register_proximity" in aw

    def test_analyze_hti_aliases_match_golden(self) -> None:
        sc = _load("golden_violin_viola_unison_c5.musicxml")
        an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        results = an.analyze_hti(4.0)
        assert results["H_TI_core"][2] == pytest.approx(_GOLDEN_VIOLIN_VIOLA_H_TI_CORE, **_TOL)
        _assert_hti_aliases_equal(results, 2)


class TestGoldenOmittedComponentsRenormalise:
    """Scenario C: technique mixed or register omitted — active_weights renormalise."""

    def test_unpitched_omits_register_and_technique_from_active_weights(self) -> None:
        from music21 import stream

        sc = stream.Score()
        an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        an._events = [
            {
                "offset": 0.0,
                "end": 4.0,
                "instrument": "snare drum",
                "family": "percussion",
                "technique_state_id": "",
                "technique_state": {},
                "pitches": [],
                "dynamic_mark": "",
                "hairpin": "none",
            }
        ]
        feats = an.extract_hti_window(2.0, 4.0)
        assert feats is not None
        h, _diag, aw = an.compute_H_TI(feats)
        assert math.isfinite(h)
        assert "register_proximity" not in aw
        assert "technique_uniformity" not in aw
        assert aw["instrument_uniformity"] == pytest.approx(0.6153846153846154, rel=1e-12)
        assert sum(aw.values()) == pytest.approx(1.0, **_TOL)

    def test_explicit_mixed_technique_finite_core(self) -> None:
        sc = _load("golden_two_violins_sul_pont_ordinario.musicxml")
        h, feats, aw = _window_core(sc)
        assert feats["technique_coverage_status"] == "explicit_mixed"
        assert feats["technique_uniformity"] == pytest.approx(0.5, **_TOL)
        assert h == pytest.approx(0.9012504626108302, **_TOL)
        assert math.isfinite(h)
        assert "technique_uniformity" in aw


class TestGoldenOptionalLayersDoNotChangeCore:
    def test_symbolic_blend_and_acoustic_proxy_toggle(self) -> None:
        sc = _load("golden_violin_viola_unison_c5.musicxml")
        base = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        blend = SymbolicTIHomogeneityAnalyzer(
            music21_score=sc,
            time_step=1.0,
            include_symbolic_blend_potential=True,
        )
        acoustic = SymbolicTIHomogeneityAnalyzer(
            music21_score=sc,
            time_step=1.0,
            include_acoustic_proxy=True,
            acoustic_proxy_profile="conservative",
        )
        r0 = base.analyze_hti(4.0)
        r1 = blend.analyze_hti(4.0)
        r2 = acoustic.analyze_hti(4.0)
        for key in ("H_TI_core", "H_TI", "H_TI_strict"):
            assert r0[key] == r1[key]
            assert r0[key] == r2[key]


class TestGoldenMultiWindowSeries:
    """Scenario D: short score — stable series length, centres, edge flags."""

    def test_two_violins_series_geometry(self) -> None:
        sc = _load("golden_two_violins_unison_c5.musicxml")
        an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        results = an.analyze_hti(4.0, edge_policy="mark_partial_windows")
        assert results["t"] == pytest.approx([0.0, 1.0, 2.0, 3.0, 4.0], abs=1e-9)
        assert results["edge_window"] == [True, True, False, True, True]
        assert results["window_coverage_ratio"][0] == pytest.approx(0.5, **_TOL)
        assert results["window_coverage_ratio"][2] == pytest.approx(1.0, **_TOL)
        assert all(v == pytest.approx(1.0, **_TOL) for v in results["H_TI_core"])
