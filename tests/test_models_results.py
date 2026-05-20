from __future__ import annotations

import pytest

from homogeneity_analyser.models.results import HomogeneitySeriesResult


def test_homogeneity_series_roundtrip() -> None:
    raw = {"t": [0.0, 1.0], "H": [0.5, 0.6], "m1": [0.1, 0.2], "m2": [0.3, 0.4], "m3": [0.5, 0.6]}
    s = HomogeneitySeriesResult.from_legacy(raw)
    out = s.as_legacy_dict()
    assert out == raw


def test_homogeneity_series_rejects_length_mismatch() -> None:
    raw = {"t": [0.0, 1.0], "H": [0.5, 0.6], "m1": [0.1], "m2": [0.3], "m3": [0.5]}
    with pytest.raises(ValueError):
        HomogeneitySeriesResult.from_legacy(raw)
