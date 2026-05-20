"""H_TI optional acoustic-proxy export keys stay aligned with analyzers and CSV/JSON."""

from __future__ import annotations

import math

from homogeneity_analyser.analyzers.hti import HTI_CSV_COLUMNS, HTI_EXPORT_TIME_SERIES_KEYS, hti_csv_row_dict
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
    HTI_ACOUSTIC_PROXY_CSV_JSON_DICT_KEYS,
    HTI_ACOUSTIC_PROXY_SERIES_KEYS,
    acoustic_proxy_series_value,
    append_hti_acoustic_proxy_series_row,
    disabled_acoustic_proxy_bundle,
    insufficient_window_acoustic_proxy_bundle,
)


def test_acoustic_proxy_series_keys_unique_and_ordered() -> None:
    assert len(HTI_ACOUSTIC_PROXY_SERIES_KEYS) == len(set(HTI_ACOUSTIC_PROXY_SERIES_KEYS))


def test_acoustic_proxy_csv_json_dict_keys_subset_of_series_keys() -> None:
    assert set(HTI_ACOUSTIC_PROXY_SERIES_KEYS).issuperset(HTI_ACOUSTIC_PROXY_CSV_JSON_DICT_KEYS)


def test_acoustic_proxy_series_keys_in_hti_exports() -> None:
    for k in HTI_ACOUSTIC_PROXY_SERIES_KEYS:
        assert k in HTI_CSV_COLUMNS
        assert k in HTI_EXPORT_TIME_SERIES_KEYS


def test_hti_csv_row_dict_json_encodes_acoustic_proxy_components() -> None:
    row = {"timbral_acoustic_affinity_components": {"register": 0.9, "technique": 1.0}}
    out = hti_csv_row_dict(row)
    for k in HTI_ACOUSTIC_PROXY_CSV_JSON_DICT_KEYS:
        if k in row:
            assert isinstance(out[k], str)
            assert out[k].startswith("{")


def test_append_hti_acoustic_proxy_series_row_disabled_and_insufficient_window() -> None:
    nan = float("nan")
    results: dict[str, list] = {k: [] for k in HTI_ACOUSTIC_PROXY_SERIES_KEYS}
    append_hti_acoustic_proxy_series_row(results, disabled_acoustic_proxy_bundle(), nan_value=nan)
    assert math.isnan(float(results["H_TA_acoustic_proxy"][0]))
    assert results["timbral_acoustic_affinity_components"][0] == {}
    assert results["timbral_acoustic_affinity_evidence_status"][0] == "disabled"
    assert results["timbral_acoustic_affinity_profile"][0] == ""
    assert results["acoustic_proxy_not_audio_analysis"][0] is True
    assert results["acoustic_proxy_validation_status"][0] == "score_derived_unvalidated"

    insuf = insufficient_window_acoustic_proxy_bundle()
    assert acoustic_proxy_series_value(
        "timbral_acoustic_affinity_profile", insuf, nan_value=nan
    ) == "disabled"
    assert acoustic_proxy_series_value(
        "timbral_acoustic_pairwise_summary", insuf, nan_value=nan
    ) == "disabled"


def test_append_hti_acoustic_proxy_series_row_preserves_finite_scalar() -> None:
    acb = disabled_acoustic_proxy_bundle()
    acb["timbral_acoustic_affinity"] = 0.75
    acb["H_TA_acoustic_proxy"] = 0.75
    acb["H_TA_acoustic_contextual"] = 0.7
    results: dict[str, list] = {k: [] for k in HTI_ACOUSTIC_PROXY_SERIES_KEYS}
    append_hti_acoustic_proxy_series_row(results, acb, nan_value=float("nan"))
    assert results["timbral_acoustic_affinity"][0] == 0.75
    assert results["H_TA_acoustic_contextual"][0] == 0.7
