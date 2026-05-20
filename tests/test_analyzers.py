"""Unit tests for HomogeneityAnalyzer and TimbralHomogeneityAnalyzer."""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from homogeneity_analyser.analyzers import (
    HomogeneityAnalyzer,
    RegisterUniformityAnalyzer,
    TimbralHomogeneityAnalyzer,
    combine_weighted_geometric,
    normalize_homogeneity_weights,
    normalize_pitch_space,
    note_name_to_midi_ps,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"


class TestHomogeneityAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FIXTURE_XML.is_file():
            raise unittest.SkipTest(f"Fixture not found: {FIXTURE_XML}")
        cls.analyzer = HomogeneityAnalyzer(
            score_path=str(FIXTURE_XML),
            time_step=0.5,
            pitch_space="absolute",
        )

    def test_extract_features_silence(self):
        feats = self.analyzer.extract_features(0.0, 1.0)
        if feats is not None:
            self.assertIn("pitch_pmf", feats)
            self.assertIn("density_scalar", feats)

    def test_extract_features_with_notes(self):
        feats = self.analyzer.extract_features(8.0, 4.0)
        self.assertIsNotNone(feats)
        self.assertIn("pitch_pmf", feats)
        self.assertIn("dur_pmf", feats)
        self.assertIn("density_scalar", feats)
        self.assertIn("sounding_density", feats)
        self.assertTrue(feats["pitch_pmf"].size > 0)

    def test_compute_metric_intra_none(self):
        out = self.analyzer.compute_metric_intra(None)
        self.assertEqual(out, 0.5)

    def test_compute_metric_intra_valid(self):
        feats = self.analyzer.extract_features(8.0, 4.0)
        if feats is not None:
            m1 = self.analyzer.compute_metric_intra(feats)
            self.assertGreaterEqual(m1, 0.0)
            self.assertLessEqual(m1, 1.0)

    def test_compute_metric_inter_silence(self):
        self.assertEqual(self.analyzer.compute_metric_inter(None, None, 12.0), 1.0)
        self.assertEqual(self.analyzer.compute_metric_inter(None, {}, 12.0), 0.5)

    def test_compute_metric_scale(self):
        m3 = self.analyzer.compute_metric_scale(8.0, 2.0, scales=(1.0, 2.0))
        self.assertGreaterEqual(m3, 0.0)
        self.assertLessEqual(m3, 1.0)

    def test_analyze_score_returns_curves(self):
        results = self.analyzer.analyze_score(window_size=4.0, sigma=12.0)
        self.assertIn("t", results)
        self.assertIn("H", results)
        self.assertIn("m1", results)
        self.assertEqual(len(results["t"]), len(results["H"]))
        self.assertEqual(len(results["m1"]), len(results["H"]))
        self.assertTrue(all(0 <= h <= 1 for h in results["H"]))

    def test_weighted_geometric_matches_equal_thirds(self):
        m1, m2, m3 = 0.8, 0.5, 0.4
        w = combine_weighted_geometric(m1, m2, m3, 1 / 3, 1 / 3, 1 / 3)
        direct = (m1 * m2 * m3) ** (1.0 / 3.0)
        self.assertAlmostEqual(w, direct, places=10)

    def test_weights_normalize(self):
        a, b, c = normalize_homogeneity_weights(1, 1, 1)
        self.assertAlmostEqual(a, 1 / 3)
        self.assertAlmostEqual(b, 1 / 3)
        self.assertAlmostEqual(c, 1 / 3)

    def test_segment_homogeneity_pelt(self):
        results = self.analyzer.analyze_score(window_size=4.0, sigma=12.0)
        cp = self.analyzer.segment_homogeneity_pelt(results, penalty=0.05, min_size=2)
        self.assertIsInstance(cp, list)
        self.assertTrue(all(isinstance(i, int) for i in cp))


class TestTimbralHomogeneityAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FIXTURE_XML.is_file():
            raise unittest.SkipTest(f"Fixture not found: {FIXTURE_XML}")
        cls.analyzer = TimbralHomogeneityAnalyzer(score_path=str(FIXTURE_XML), time_step=0.5)

    def test_extract_timbral_features(self):
        feats = self.analyzer.extract_timbral_features(8.0, 4.0)
        self.assertIsNotNone(feats)
        self.assertIn("pitches", feats)
        self.assertIn("instruments", feats)
        self.assertIn("families", feats)
        self.assertIn("n_notes", feats)
        self.assertIn("n_instruments", feats)
        self.assertIn("string_events", feats)
        self.assertIn("string_overlap_mass", feats)
        self.assertIn("brass_events", feats)
        self.assertIn("brass_overlap_mass", feats)
        self.assertIn("flute_events", feats)
        self.assertIn("flute_overlap_mass", feats)
        self.assertIn("clarinet_events", feats)
        self.assertIn("clarinet_overlap_mass", feats)
        self.assertIn("double_reed_events", feats)
        self.assertIn("double_reed_overlap_mass", feats)
        self.assertIn("saxophone_events", feats)
        self.assertIn("saxophone_overlap_mass", feats)
        self.assertIn("percussion_events", feats)
        self.assertIn("percussion_overlap_mass", feats)
        self.assertIn("total_overlap_mass", feats)

    def test_compute_H_timbral_none(self):
        self.assertEqual(self.analyzer.compute_H_timbral(None), 0.5)

    def test_compute_H_timbral_one_instrument(self):
        feats = {"n_notes": 4, "n_instruments": 1, "n_families": 1, "pitches": np.array([60, 62, 64, 65])}
        H = self.analyzer.compute_H_timbral(feats)
        self.assertGreater(H, 0.7)
        self.assertLessEqual(H, 1.0)

    def test_compute_H_timbral_many_instruments(self):
        feats = {"n_notes": 10, "n_instruments": 10, "n_families": 5, "pitches": np.array([60 + i for i in range(10)])}
        H = self.analyzer.compute_H_timbral(feats)
        self.assertLess(H, 0.5)

    def test_analyze_timbral_returns_curves(self):
        results = self.analyzer.analyze_timbral(window_size=4.0)
        self.assertIn("t", results)
        self.assertIn("H_timbral", results)
        self.assertEqual(len(results["t"]), len(results["H_timbral"]))
        self.assertTrue(all(0 <= h <= 1 for h in results["H_timbral"]))


class TestNormalizePitchSpace(unittest.TestCase):
    def test_absolute_and_aliases(self):
        self.assertEqual(normalize_pitch_space("absolute"), "absolute")
        self.assertEqual(normalize_pitch_space(None), "absolute")
        self.assertEqual(normalize_pitch_space("pitch_class"), "pitch_class")
        self.assertEqual(normalize_pitch_space("chromatic"), "pitch_class")
        self.assertEqual(normalize_pitch_space("PC"), "pitch_class")


class TestNoteNameToMidiPs(unittest.TestCase):
    def test_a1(self):
        self.assertAlmostEqual(note_name_to_midi_ps("A1"), 33.0)

    def test_c4(self):
        self.assertAlmostEqual(note_name_to_midi_ps("C4"), 60.0)

    def test_e7(self):
        self.assertAlmostEqual(note_name_to_midi_ps("E7"), 100.0)


class TestRegisterUniformityAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FIXTURE_XML.is_file():
            raise unittest.SkipTest(f"Fixture not found: {FIXTURE_XML}")
        cls.analyzer = RegisterUniformityAnalyzer(
            score_path=str(FIXTURE_XML),
            register_low_ps=21.0,
            register_high_ps=88.0,
            time_step=0.5,
        )

    def test_compute_uniformity_empty(self):
        U = self.analyzer.compute_uniformity(np.array([]))
        self.assertTrue(np.isnan(U))

    def test_compute_uniformity_single_pitch(self):
        U = self.analyzer.compute_uniformity(np.array([60.0]))
        self.assertEqual(U, 0.0)

    def test_compute_uniformity_spread(self):
        pitches = np.linspace(30, 80, 20)
        U = self.analyzer.compute_uniformity(pitches)
        self.assertGreaterEqual(U, 0.0)
        self.assertLessEqual(U, 1.0)
        self.assertGreater(U, 0.5)

    def test_analyze_score_returns_curves(self):
        results = self.analyzer.analyze_score(window_size=4.0)
        self.assertIn("t", results)
        self.assertIn("U", results)
        self.assertEqual(len(results["t"]), len(results["U"]))
        for u in results["U"]:
            self.assertTrue(0 <= u <= 1 or (u != u), f"U must be in [0,1] or NaN, got {u}")


if __name__ == "__main__":
    unittest.main()
