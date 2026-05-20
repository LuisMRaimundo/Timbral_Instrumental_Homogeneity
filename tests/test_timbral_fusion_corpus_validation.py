"""Sanity checks driven by ``validation/cases/timbral_fusion_cases.csv`` and fixtures."""

from __future__ import annotations

import csv

import pytest
import importlib.util
from pathlib import Path

from homogeneity_analyser.services.analysis_service import (
    run_cluster_analysis,
    run_fusion_acoustic_heuristic_analysis,
    run_orchestration_symbolic_analysis,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = REPO_ROOT / "validation" / "cases"
CSV_PATH = CASES_DIR / "timbral_fusion_cases.csv"
PARAMS = {"time_step": 0.25, "window_size": 4.0}
# Same concert chromatic cluster (B3–D4); H_cluster must match across these fixtures.
CHROMATIC_CLUSTER_FIXTURES = frozenset(
    {
        "cf01_horns_stopped_chromatic.xml",
        "cf02_violins_arco_chromatic.xml",
        "cf03_clarinets_bass_chromatic.xml",
        "cf04_horns_mixed_open_stopped.xml",
        "cf05_violins_mixed_arco_pizz.xml",
    }
)


def _load_bands_module():
    spec = importlib.util.spec_from_file_location("validation_cases_bands", CASES_DIR / "bands.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_cases() -> list[dict[str, str]]:
    assert CSV_PATH.is_file()
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _first_window_bundle(fixture_name: str) -> tuple[float, float, float, dict]:
    path = str(CASES_DIR / fixture_name)
    out_c = run_cluster_analysis(path, PARAMS)
    out_o = run_orchestration_symbolic_analysis(path, PARAMS)
    out_f = run_fusion_acoustic_heuristic_analysis(path, PARAMS)
    for label, out in (("cluster", out_c), ("orch", out_o), ("fusion", out_f)):
        assert not out.get("error"), f"{label}: {out.get('error')}"
    hc = float(out_c["results"]["H_cluster"][0])
    ho = float(out_o["results"]["H_orchestration_symbolic"][0])
    hf = float(out_f["results"]["H_fusion_acoustic_heuristic"][0])
    diag = (out_f["results"].get("H_fusion_acoustic_heuristic_diagnostics") or [{}])[0]
    assert isinstance(diag, dict)
    return hc, ho, hf, diag


@pytest.fixture(scope="module")
def bands_mod():
    return _load_bands_module()


def test_h_cluster_identical_for_same_sounding_chromatic_cluster() -> None:
    """Cases cf01–cf05 share one chromatic concert cluster; H_cluster must match exactly."""
    rows = [r for r in _read_cases() if r["score_fixture"] in CHROMATIC_CLUSTER_FIXTURES]
    assert len(rows) == 5
    vals: list[float] = []
    for r in rows:
        hc, _, _, _ = _first_window_bundle(r["score_fixture"])
        vals.append(hc)
    assert max(vals) - min(vals) < 1e-9


@pytest.mark.parametrize("case_row", _read_cases(), ids=lambda r: r["case_id"])
def test_case_expectations_bands_and_confidence(case_row: dict[str, str], bands_mod) -> None:
    hc, ho, hf, diag = _first_window_bundle(case_row["score_fixture"])
    assert bands_mod.value_matches_expected_band(hc, case_row["expected_H_cluster_band"])
    assert bands_mod.value_matches_expected_band(ho, case_row["expected_H_orchestration_symbolic_band"])
    assert bands_mod.value_matches_expected_band(hf, case_row["expected_H_fusion_acoustic_heuristic_band"])
    conf = float(diag["confidence_score"])
    assert conf >= float(case_row["expected_confidence_min"])


def test_fusion_diagnostics_include_expected_source_keys() -> None:
    """Every ``source_keys`` token from the CSV must appear in ``sources_used`` (fusion window)."""
    rows = _read_cases()
    for r in rows:
        _, _, _, diag = _first_window_bundle(r["score_fixture"])
        used = set(diag.get("sources_used") or [])
        assert used, f"{r['case_id']}: fusion diagnostics must list sources_used"
        for token in (x.strip() for x in r["source_keys"].split(",") if x.strip()):
            assert token in used, f"{r['case_id']}: expected source key {token!r} in {sorted(used)}"


def test_confidence_is_internal_model_score_not_constant_one() -> None:
    """Fusion confidence stays in (0,1) and below 1.0 for these fixtures (no false certainty)."""
    r0 = _read_cases()[0]
    _, _, _, diag = _first_window_bundle(r0["score_fixture"])
    c = float(diag["confidence_score"])
    assert 0.0 < c < 1.0
    assert isinstance(diag.get("confidence_label"), str) and diag["confidence_label"].strip()
