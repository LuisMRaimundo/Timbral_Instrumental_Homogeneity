"""CSV row dict construction and H_TI alias consistency in exports."""

from __future__ import annotations

import json

import pytest

from homogeneity_analyser.analyzers.hti import HTI_CSV_COLUMNS, hti_csv_row_dict
from homogeneity_analyser.analyzers.symbolic_blend_layers import HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import HTI_ACOUSTIC_PROXY_CSV_JSON_DICT_KEYS


def test_hti_csv_row_dict_json_encodes_distributions() -> None:
    row = {
        "H_TI": 0.75,
        "H_TI_core": 0.75,
        "H_TI_strict": 0.75,
        "active_weights": {"instrument_uniformity": 0.4, "family_uniformity": 0.6},
        "instrument_distribution": {"violin": 0.5, "viola": 0.5},
        "dominant_instruments": ["violin", "viola"],
    }
    for k in HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS:
        row[k] = {"a": 1}
    for k in HTI_ACOUSTIC_PROXY_CSV_JSON_DICT_KEYS:
        row[k] = {"b": 2}
    out = hti_csv_row_dict(row)
    assert json.loads(out["active_weights"]) == row["active_weights"]
    assert json.loads(out["instrument_distribution"]) == row["instrument_distribution"]
    assert json.loads(out["dominant_instruments"]) == row["dominant_instruments"]
    for k in HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS:
        assert isinstance(out[k], str)
        assert json.loads(out[k]) == {"a": 1}


def test_hti_core_columns_present_in_csv_registry() -> None:
    for k in ("H_TI", "H_TI_core", "H_TI_strict"):
        assert k in HTI_CSV_COLUMNS


def test_csv_row_preserves_numeric_aliases() -> None:
    row = {"H_TI": 0.9, "H_TI_core": 0.9, "H_TI_strict": 0.9, "t_quarterLength": 2.0}
    out = hti_csv_row_dict(row)
    assert out["H_TI"] == pytest.approx(0.9)
    assert out["H_TI_core"] == out["H_TI_strict"]
