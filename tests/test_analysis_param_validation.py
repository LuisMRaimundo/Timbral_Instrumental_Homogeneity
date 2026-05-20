"""Service-layer parameter validation and ``safe_nan_summary``."""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pytest

from homogeneity_analyser.services.analysis_service import (
    run_both_and_combine,
    run_homogeneity_analysis,
    run_register_uniformity_analysis,
    run_symbolic_ti_homogeneity_analysis,
    run_timbral_analysis,
)
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS, DEFAULT_TIMBRAL_PARAMS
from homogeneity_analyser.services.param_validation import (
    AnalysisParameterError,
    safe_nan_summary,
    validate_fusion_acoustic_heuristic_params,
    validate_hti_params,
    validate_timbral_params,
)
from homogeneity_analyser.services.result_assembly import format_homogeneity_summary

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"


class TestSafeNanSummary(unittest.TestCase):
    def test_empty_all_none(self) -> None:
        s = safe_nan_summary([])
        self.assertEqual(s, {"min": None, "mean": None, "max": None})

    def test_all_nan_all_none(self) -> None:
        s = safe_nan_summary([np.nan, np.nan])
        self.assertEqual(s, {"min": None, "mean": None, "max": None})

    def test_finite_values(self) -> None:
        s = safe_nan_summary([1.0, 2.0, np.nan, 3.0])
        self.assertAlmostEqual(s["min"], 1.0)
        self.assertAlmostEqual(s["mean"], 2.0)
        self.assertAlmostEqual(s["max"], 3.0)


class TestFormatHomogeneitySummarySafeStats(unittest.TestCase):
    def test_all_nan_H_shows_n_a(self) -> None:
        class _An:
            end_time = 10.0

        text = format_homogeneity_summary(
            {"H": [np.nan, np.nan, np.nan]},
            _An(),
            [],
            [],
            {
                "pitch_space": "absolute",
                "pitch_bin_step": 1.0,
                "silence_intra_value": 0.5,
                "silence_transition_value": 0.5,
            },
        )
        self.assertIn("H min: n/a", text)
        self.assertIn("H mean: n/a", text)
        self.assertIn("H max: n/a", text)


@pytest.mark.legacy
class TestServiceRejectsInvalidParams(unittest.TestCase):
    def test_homogeneity_zero_window_size(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_homogeneity_analysis(str(FIXTURE_XML), {"window_size": 0.0, "time_step": 0.5, "sigma": 12.0})
        self.assertIsNotNone(out.get("error"))
        self.assertIsNone(out.get("analyzer"))
        self.assertIn("window_size", out["error"].lower())

    def test_homogeneity_zero_time_step(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_homogeneity_analysis(str(FIXTURE_XML), {"time_step": 0.0, "window_size": 4.0, "sigma": 12.0})
        self.assertIsNotNone(out.get("error"))
        self.assertIn("time_step", out["error"].lower())

    def test_homogeneity_negative_sigma(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_homogeneity_analysis(str(FIXTURE_XML), {"sigma": -1.0, "window_size": 4.0, "time_step": 0.5})
        self.assertIsNotNone(out.get("error"))
        self.assertIn("sigma", out["error"].lower())

    def test_homogeneity_zero_pitch_bin_step(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_homogeneity_analysis(str(FIXTURE_XML), {"pitch_bin_step": 0.0, "window_size": 4.0, "time_step": 0.5})
        self.assertIsNotNone(out.get("error"))
        self.assertIn("pitch_bin_step", out["error"].lower())

    def test_homogeneity_negative_weight_rejected_before_normalize(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_homogeneity_analysis(
            str(FIXTURE_XML),
            {"weight_m1": -0.1, "window_size": 4.0, "time_step": 0.5, "sigma": 12.0},
        )
        self.assertIsNotNone(out.get("error"))
        self.assertIn("weight_m1", out["error"].lower())

    def test_register_zero_window(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_register_uniformity_analysis(
            str(FIXTURE_XML),
            {"window_size": 0.0, "register_low": "C4", "register_high": "C5"},
        )
        self.assertIsNotNone(out.get("error"))
        self.assertIn("window_size", out["error"].lower())

    def test_timbral_invalid_register_ref(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_timbral_analysis(
            str(FIXTURE_XML),
            {"timbral_config": {"register_ref_semitones": 0.0}, "time_step": 0.5, "window_size": 4.0},
        )
        self.assertIsNotNone(out.get("error"))
        self.assertIn("register_ref_semitones", out["error"].lower())

    def test_run_both_invalid_sigma(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_both_and_combine(str(FIXTURE_XML), time_step=0.5, window_size=4.0, sigma=0.0)
        self.assertIsNotNone(out.get("error"))
        self.assertIn("sigma", out["error"].lower())
        self.assertIsNone(out.get("out_homogeneity"))

    def test_valid_homogeneity_still_ok(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_homogeneity_analysis(str(FIXTURE_XML), {"time_step": 0.5, "window_size": 4.0, "sigma": 12.0})
        self.assertIsNone(out.get("error"))
        self.assertIsNotNone(out.get("analyzer"))

    def test_register_summary_all_nan_no_crash(self) -> None:
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_register_uniformity_analysis(
            str(FIXTURE_XML),
            {
                "time_step": 0.5,
                "window_size": 4.0,
                "register_low": 118.0,
                "register_high": 126.0,
            },
        )
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertIn("n/a", out["summary"])


@pytest.mark.legacy
class TestTimbralModelModeValidation(unittest.TestCase):
    def test_legacy_default_validates(self) -> None:
        validate_timbral_params(dict(DEFAULT_TIMBRAL_PARAMS))

    def test_symbolic_mode_validates(self) -> None:
        p = {**DEFAULT_TIMBRAL_PARAMS, "timbral_model_mode": "symbolic"}
        validate_timbral_params(p)

    def test_acoustic_heuristic_mode_validates(self) -> None:
        p = {**DEFAULT_TIMBRAL_PARAMS, "timbral_model_mode": "acoustic_heuristic"}
        validate_timbral_params(p)

    def test_nested_timbral_model_mode_matches_top_level_legacy(self) -> None:
        p = {
            **DEFAULT_TIMBRAL_PARAMS,
            "timbral_model_mode": "legacy",
            "timbral_config": {"timbral_model_mode": "legacy", "weight_instrument": 0.5},
        }
        validate_timbral_params(p)


class TestHtiParams(unittest.TestCase):
    def test_default_bundle_valid(self) -> None:
        validate_hti_params(dict(DEFAULT_HTI_PARAMS))

    def test_zero_weight_sum_rejected(self) -> None:
        p = {
            **DEFAULT_HTI_PARAMS,
            "weight_instrument_uniformity": 0.0,
            "weight_family_uniformity": 0.0,
            "weight_technique_uniformity": 0.0,
            "weight_register_proximity": 0.0,
        }
        with self.assertRaises(AnalysisParameterError):
            validate_hti_params(p)

    def test_run_hti_on_fixture(self) -> None:
        out = run_symbolic_ti_homogeneity_analysis(
            str(FIXTURE_XML),
            {**DEFAULT_HTI_PARAMS, "time_step": 1.0, "window_size": 4.0},
        )
        self.assertIsNone(out.get("error"))
        res = out["results"]
        self.assertIn("H_TI", res)
        self.assertGreater(len(res["t"]), 0)

    def test_timbral_affinity_profile_invalid(self) -> None:
        with self.assertRaises(AnalysisParameterError):
            validate_hti_params({**DEFAULT_HTI_PARAMS, "timbral_affinity_profile": "not_a_profile"})

    def test_include_symbolic_blend_potential_must_be_boolish(self) -> None:
        with self.assertRaises(AnalysisParameterError):
            validate_hti_params({**DEFAULT_HTI_PARAMS, "include_symbolic_blend_potential": "maybe"})


class TestAnalysisParameterError(unittest.TestCase):
    def test_is_value_error_subclass(self) -> None:
        self.assertTrue(issubclass(AnalysisParameterError, ValueError))


@pytest.mark.legacy
class TestFusionAcousticHeuristicParams(unittest.TestCase):
    def test_valid_default_bundle(self) -> None:
        from homogeneity_analyser.services.constants import DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS

        validate_fusion_acoustic_heuristic_params(dict(DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS))

    def test_zero_weight_sum_rejected(self) -> None:
        from homogeneity_analyser.services.constants import DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS

        p = {
            **DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS,
            "weight_fusion_profile": 0.0,
            "weight_fusion_spectral": 0.0,
            "weight_fusion_technique": 0.0,
            "weight_fusion_register": 0.0,
        }
        with self.assertRaises(AnalysisParameterError):
            validate_fusion_acoustic_heuristic_params(p)

    def test_n_harmonics_out_of_range(self) -> None:
        from homogeneity_analyser.services.constants import DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS

        p = {**DEFAULT_FUSION_ACOUSTIC_HEURISTIC_PARAMS, "fusion_n_harmonics": 2}
        with self.assertRaises(AnalysisParameterError):
            validate_fusion_acoustic_heuristic_params(p)
