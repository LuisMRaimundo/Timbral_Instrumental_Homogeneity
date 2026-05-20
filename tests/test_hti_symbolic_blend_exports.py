"""H_TI optional symbolic-blend export keys stay aligned with analyzers and CSV/JSON."""

from __future__ import annotations

import math

from homogeneity_analyser.analyzers.hti import HTI_CSV_COLUMNS, HTI_EXPORT_TIME_SERIES_KEYS, hti_csv_row_dict
from homogeneity_analyser.analyzers.symbolic_blend_layers import (
    HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS,
    HTI_SYMBOLIC_BLEND_SERIES_KEYS,
    append_hti_symbolic_blend_series_row,
    compute_pairwise_interval_blend_factor,
)


def test_symbolic_blend_series_keys_in_hti_exports() -> None:
    for k in HTI_SYMBOLIC_BLEND_SERIES_KEYS:
        assert k in HTI_CSV_COLUMNS
        assert k in HTI_EXPORT_TIME_SERIES_KEYS


def test_hti_csv_row_dict_json_encodes_symbolic_blend_dict_columns() -> None:
    row = {
        "interval_class_profile": {"seconds_sevenths": 1.0},
        "interval_class_profile_display": {"second-class / seventh-class equivalence group": 1.0},
        "literal_interval_semitone_pair_mass": {"2": 1.0},
        "chromatic_mod12_pair_mass": {"2": 1.0},
        "symbolic_blend_components": {"H_TI_core": 0.9},
    }
    out = hti_csv_row_dict(row)
    for k in HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS:
        if k in row:
            assert isinstance(out[k], str)
            assert out[k].startswith("{")


def test_append_hti_symbolic_blend_series_row_disabled_and_enabled() -> None:
    results: dict[str, list] = {k: [] for k in HTI_SYMBOLIC_BLEND_SERIES_KEYS}
    append_hti_symbolic_blend_series_row(
        results, enabled=False, ivb=None, atk=None, sympk=None, nan_value=float("nan")
    )
    assert math.isnan(float(results["interval_class_blend_factor"][0]))
    assert results["interval_class_profile"][0] == {}
    assert results["interval_class_evidence_status"][0] == ""

    ivb = compute_pairwise_interval_blend_factor([(60.0, 1.0), (62.0, 1.0)])
    results2: dict[str, list] = {k: [] for k in HTI_SYMBOLIC_BLEND_SERIES_KEYS}
    append_hti_symbolic_blend_series_row(
        results2,
        enabled=True,
        ivb=ivb,
        atk={"attack_compatibility_factor": 1.0, "attack_class_distribution": {"x": 1.0}},
        sympk={"symbolic_blend_potential": 0.5, "symbolic_blend_components": {"H_TI_core": 0.8}},
        nan_value=float("nan"),
    )
    assert results2["literal_interval_semitone_pair_mass"][0].get("2", 0) > 0.99
