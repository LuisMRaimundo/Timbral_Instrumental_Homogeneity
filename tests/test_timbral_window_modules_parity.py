"""Parity tests for H_timbral window module extraction (features + metric)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest
from music21 import articulations, instrument, meter, note, stream

from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.analyzers.timbral_window_features import extract_timbral_window_features
from homogeneity_analyser.analyzers.timbral_window_metric import (
    compute_timbral_window_decomposition,
    compute_timbral_window_metric,
)


def _assert_timbral_features_equal(a: dict | None, b: dict | None) -> None:
    assert (a is None) == (b is None)
    if a is None:
        return
    assert set(a.keys()) == set(b.keys())
    for key in a:
        va, vb = a[key], b[key]
        if isinstance(va, np.ndarray):
            assert isinstance(vb, np.ndarray)
            np.testing.assert_array_equal(va, vb)
        elif isinstance(va, set):
            assert va == vb
        elif isinstance(va, float):
            assert va == pytest.approx(float(vb))
        elif isinstance(va, list) and va and isinstance(va[0], dict):
            assert len(va) == len(vb)
            for row_a, row_b in zip(va, vb, strict=True):
                assert row_a == row_b
        else:
            assert va == vb


def _string_unison_score() -> stream.Score:
    sc = stream.Score()
    for _ in range(2):
        p = stream.Part()
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, instrument.Violin())
        p.insert(0, note.Note("G4", quarterLength=4.0))
        sc.append(p)
    return sc


def _woodwind_brass_mix_score() -> stream.Score:
    sc = stream.Score()
    clar = stream.Part()
    clar.insert(0, meter.TimeSignature("4/4"))
    clar.insert(0, instrument.Clarinet())
    clar.insert(0, note.Note("E4", quarterLength=4.0))
    horn = stream.Part()
    horn.insert(0, meter.TimeSignature("4/4"))
    horn.insert(0, instrument.Horn())
    horn.insert(0, note.Note("G4", quarterLength=4.0))
    sc.insert(0, clar)
    sc.insert(0, horn)
    return sc


def _unpitched_percussion_score() -> stream.Score:
    sc = stream.Score()
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.SnareDrum())
    n = note.Unpitched()
    n.staffLine = 3
    n.quarterLength = 4.0
    p.insert(0, n)
    sc.insert(0, p)
    return sc


def _explicit_technique_score() -> stream.Score:
    sc = stream.Score()
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Violin())
    n = note.Note("A4", quarterLength=4.0)
    n.articulations = [articulations.Pizzicato()]
    p.insert(0, n)
    sc.insert(0, p)
    return sc


def _empty_window_score() -> stream.Score:
    sc = stream.Score()
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Flute())
    p.insert(0, note.Note("C5", quarterLength=2.0))
    sc.insert(0, p)
    return sc


@pytest.mark.parametrize(
    ("score_fn", "center", "window"),
    [
        (_string_unison_score, 2.0, 4.0),
        (_woodwind_brass_mix_score, 2.0, 4.0),
        (_unpitched_percussion_score, 2.0, 4.0),
        (_explicit_technique_score, 2.0, 4.0),
        (_empty_window_score, 10.0, 4.0),
    ],
)
def test_extract_timbral_window_features_matches_analyzer_method(
    score_fn: Callable[[], stream.Score],
    center: float,
    window: float,
) -> None:
    an = TimbralHomogeneityAnalyzer(music21_score=score_fn(), time_step=0.25)
    via_method = an.extract_timbral_features(center, window)
    via_module = extract_timbral_window_features(
        an._events,
        center,
        window,
        is_event_active_in_window=an._active_in_window,
    )
    _assert_timbral_features_equal(via_method, via_module)


@pytest.mark.parametrize(
    ("score_fn", "center", "window"),
    [
        (_string_unison_score, 2.0, 4.0),
        (_woodwind_brass_mix_score, 2.0, 4.0),
        (_unpitched_percussion_score, 2.0, 4.0),
        (_explicit_technique_score, 2.0, 4.0),
    ],
)
def test_timbral_window_metric_matches_analyzer_methods(
    score_fn: Callable[[], stream.Score],
    center: float,
    window: float,
) -> None:
    an = TimbralHomogeneityAnalyzer(music21_score=score_fn(), time_step=0.25)
    feats = an.extract_timbral_features(center, window)
    h_method = an.compute_H_timbral(feats)
    h_module = compute_timbral_window_metric(
        feats,
        timbral_config=an._timbral_config,
        timbral_model_mode=an._timbral_model_mode,
    )
    assert h_method == pytest.approx(h_module, abs=1e-12)
    _, d_method = an.compute_H_timbral_decomposition(feats)
    _, d_module = compute_timbral_window_decomposition(
        feats,
        timbral_config=an._timbral_config,
        timbral_model_mode=an._timbral_model_mode,
    )
    assert d_method == d_module
