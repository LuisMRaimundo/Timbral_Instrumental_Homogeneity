"""Unit tests for analysis_service."""
from __future__ import annotations

import csv
import io
import unittest
from pathlib import Path

import numpy as np

from homogeneity_analyser.services.analysis_service import (
    run_both_and_combine,
    run_homogeneity_analysis,
    run_register_uniformity_analysis,
    run_timbral_analysis,
)
from homogeneity_analyser.services.window_pipeline import align_series_nearest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"
EMPTY_NO_NOTES_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "empty_no_notes.xml"
SINGLE_NOTE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "single_note.xml"


class TestRunHomogeneityAnalysis(unittest.TestCase):
    def test_returns_structure(self):
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_homogeneity_analysis(str(FIXTURE_XML), {"time_step": 0.5, "window_size": 4.0, "sigma": 12.0})
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertIn("weighted geometric mean", out["summary"])
        self.assertIn("results", out)
        self.assertIn("plot_results", out)
        self.assertIn("summary", out)
        self.assertEqual(len(out["results"]["t"]), len(out["results"]["H"]))

    def test_single_aggregate(self):
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_homogeneity_analysis(str(FIXTURE_XML), {"single_aggregate": True, "window_size": 4.0})
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertEqual(len(out["results"]["t"]), 1)
        self.assertEqual(len(out["results"]["H"]), 1)

    def test_empty_score_returns_error(self):
        if not EMPTY_NO_NOTES_XML.is_file():
            self.skipTest("Fixture empty_no_notes.xml not found")
        out = run_homogeneity_analysis(str(EMPTY_NO_NOTES_XML), {"window_size": 4.0})
        self.assertIsNotNone(out.get("error"))
        self.assertIn("no notes", out["error"].lower() or "")

    def test_single_note_runs(self):
        if not SINGLE_NOTE_XML.is_file():
            self.skipTest("Fixture single_note.xml not found")
        out = run_homogeneity_analysis(str(SINGLE_NOTE_XML), {"time_step": 0.5, "window_size": 4.0})
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertGreaterEqual(len(out["results"]["H"]), 1)


class TestRunTimbralAnalysis(unittest.TestCase):
    def test_returns_structure(self):
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_timbral_analysis(str(FIXTURE_XML), {"time_step": 0.5, "window_size": 4.0})
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertIn("Part-name", out["summary"])
        self.assertIn("WARNING", out["summary"])
        self.assertIn("legacy diagnostic", out["summary"].lower())
        self.assertIn("results", out)
        self.assertIn("summary", out)
        self.assertIn("H_timbral", out["results"])
        self.assertEqual(len(out["results"]["t"]), len(out["results"]["H_timbral"]))
        self.assertIn("timbral_state_distribution", out["results"])
        self.assertIn("dominant_timbral_state", out["results"])
        self.assertIn("timbral_state_concentration", out["results"])


class TestRunBothAndCombine(unittest.TestCase):
    def test_combined_csv_includes_m_metrics(self):
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_both_and_combine(str(FIXTURE_XML), time_step=0.5, window_size=4.0, sigma=12.0)
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertIn("combined_csv_content", out)
        lines = out["combined_csv_content"].strip().split("\n")
        self.assertIn("dominant_timbral_state", lines[0])
        self.assertIn("t_quarterLength", lines[0])
        self.assertIn("H_timbral", lines[0])
        self.assertIn("H_cluster", lines[0])
        self.assertIn("H_orchestration_symbolic", lines[0])
        self.assertIn("H_notated_fusion_potential_dynamic", lines[0])
        self.assertGreater(len(lines), 1)
        rhead = csv.reader(io.StringIO(lines[0]))
        ncol = len(next(rhead))
        r = csv.reader(io.StringIO(lines[1]))
        parts = next(r)
        self.assertEqual(len(parts), ncol)
        cof_lines = (out.get("cluster_orch_fusion_diagnostics_csv_content") or "").strip().split("\n")
        self.assertIn("legacy_H_timbral", cof_lines[0])
        self.assertIn("H_fusion_acoustic_heuristic", cof_lines[0])
        self.assertIn("H_notated_fusion_potential_dynamic", cof_lines[0])
        self.assertIn("main_penalty_reason", cof_lines[0])
        self.assertGreater(len(cof_lines), 1)

    def test_invalid_path_returns_error(self):
        out = run_homogeneity_analysis("/nonexistent/file.xml", {"window_size": 4.0})
        self.assertIsNotNone(out.get("error"))


class TestAlignSeriesNearest(unittest.TestCase):
    def test_equal_time_grid(self):
        t = np.array([0.0, 1.0, 2.0], dtype=float)
        vals = ["a", "b", "c"]
        self.assertEqual(align_series_nearest(t, vals, t), vals)

    def test_nearest_label_on_finer_grid(self):
        t_from = np.array([0.0, 2.0], dtype=float)
        vals = ["low", "high"]
        t_to = np.array([0.0, 1.0, 2.0], dtype=float)
        out = align_series_nearest(t_from, vals, t_to)
        self.assertEqual(out, ["low", "low", "high"])


class TestRunRegisterUniformityAnalysis(unittest.TestCase):
    def test_returns_structure(self):
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_register_uniformity_analysis(
            str(FIXTURE_XML),
            {"time_step": 0.5, "window_size": 4.0, "register_low": "A1", "register_high": "E7"},
        )
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertIn("results", out)
        self.assertIn("summary", out)
        self.assertIn("t", out["results"])
        self.assertIn("U", out["results"])
        self.assertEqual(len(out["results"]["t"]), len(out["results"]["U"]))

    def test_register_bounds_note_names(self):
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_register_uniformity_analysis(
            str(FIXTURE_XML),
            {"register_low": "C4", "register_high": "C5", "window_size": 4.0},
        )
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertTrue(all(0 <= u <= 1 or u != u for u in out["results"]["U"]))

    def test_empty_score_returns_error(self):
        if not EMPTY_NO_NOTES_XML.is_file():
            self.skipTest("Fixture empty_no_notes.xml not found")
        out = run_register_uniformity_analysis(
            str(EMPTY_NO_NOTES_XML),
            {"window_size": 4.0, "register_low": "A1", "register_high": "E7"},
        )
        self.assertIsNotNone(out.get("error"))
        self.assertIn("no notes", out["error"].lower() or "")

    def test_invalid_register_returns_error(self):
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        out = run_register_uniformity_analysis(
            str(FIXTURE_XML),
            {"register_low": "", "register_high": "E7", "window_size": 4.0},
        )
        self.assertIsNotNone(out.get("error"))


if __name__ == "__main__":
    unittest.main()
