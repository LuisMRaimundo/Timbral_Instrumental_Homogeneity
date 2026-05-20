"""Overlap-aware H(t) / U(t) behaviour (homogeneity + register analyzers)."""

from __future__ import annotations

import unittest

import numpy as np
from music21 import chord, instrument, meter, note, stream

from homogeneity_analyser.analyzers.common import overlap_quarter_length
from homogeneity_analyser.analyzers.homogeneity import HomogeneityAnalyzer
from homogeneity_analyser.analyzers.register import RegisterUniformityAnalyzer
from homogeneity_analyser.analyzers.timbral_sounding_pitch import sounding_pitch_ps_list


class TestOverlapQuarterLength(unittest.TestCase):
    def test_overlap_positive_only_when_intersecting(self) -> None:
        self.assertAlmostEqual(overlap_quarter_length(0.0, 4.0, 1.0, 3.0), 2.0)
        self.assertAlmostEqual(overlap_quarter_length(0.0, 0.5, 2.0, 4.0), 0.0)

    def test_tiny_clip(self) -> None:
        self.assertAlmostEqual(overlap_quarter_length(3.99, 4.02, 0.0, 4.0), 0.01)


class TestHomogeneityOverlapWeighting(unittest.TestCase):
    def test_long_note_contributes_more_pitch_mass_than_edge_clip(self) -> None:
        """Same two pitch classes; long overlap on one tone vs short clip should skew pitch PMF."""
        sc = stream.Score()
        p1 = stream.Part()
        p1.insert(0, instrument.Piano())
        m = stream.Measure(number=1)
        m.insert(0, meter.TimeSignature("4/4"))
        m.insert(0, note.Note("C4", quarterLength=4.0))
        m.insert(3.9375, note.Note("D4", quarterLength=0.0625))
        p1.append(m)
        sc.insert(0, p1)
        an = HomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        full = an.extract_features(2.0, 4.0)
        self.assertIsNotNone(full)
        assert full is not None
        c_idx = int(np.searchsorted(an.pitch_edges, 60.0, side="right") - 1)
        d_idx = int(np.searchsorted(an.pitch_edges, 62.0, side="right") - 1)
        self.assertGreater(full["pitch_pmf"][c_idx], full["pitch_pmf"][d_idx])

    def test_note_ending_just_after_window_start_has_small_weight(self) -> None:
        """Event mostly before the window contributes overlap only on the clipped segment."""
        sc = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Piano())
        p.insert(0, meter.TimeSignature("4/4"))
        p.append(note.Note("C4", quarterLength=1.0))
        sc.insert(0, p)
        an = HomogeneityAnalyzer(music21_score=sc, time_step=0.25)
        feats = an.extract_features(2.5, 4.0)
        self.assertIsNotNone(feats)
        assert feats is not None
        self.assertLess(feats["sounding_event_overlap_density"], 0.51)

    def test_density_keys_explicit(self) -> None:
        sc = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Piano())
        p.insert(0, meter.TimeSignature("4/4"))
        p.append(note.Note("C4", quarterLength=4.0))
        sc.insert(0, p)
        an = HomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        f = an.extract_features(2.0, 4.0)
        self.assertIsNotNone(f)
        assert f is not None
        self.assertIn("onset_event_density", f)
        self.assertIn("pitch_onset_density", f)
        self.assertIn("sounding_event_overlap_density", f)
        self.assertIn("sounding_pitch_overlap_density", f)
        self.assertAlmostEqual(f["density_scalar"], f["onset_event_density"])
        self.assertAlmostEqual(f["sounding_density"], f["sounding_event_overlap_density"])

    def test_extract_features_empty_window_returns_none(self) -> None:
        sc = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Piano())
        p.insert(0, meter.TimeSignature("4/4"))
        p.append(note.Note("C4", quarterLength=0.5))
        sc.insert(0, p)
        an = HomogeneityAnalyzer(music21_score=sc, time_step=0.25)
        self.assertIsNone(an.extract_features(50.0, 2.0))

    def test_chord_pitch_mass_conserved_equal_split(self) -> None:
        """Two chord tones share event overlap mass: sum of per-tone weights equals event overlap."""
        sc = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Piano())
        p.insert(0, meter.TimeSignature("4/4"))
        p.append(chord.Chord(["C4", "G4"], quarterLength=4.0))
        sc.insert(0, p)
        an = HomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        f = an.extract_features(2.0, 4.0)
        self.assertIsNotNone(f)
        assert f is not None
        self.assertAlmostEqual(float(f["pitch_pmf"].sum()), 1.0, places=6)
        self.assertAlmostEqual(f["sounding_pitch_overlap_density"], f["sounding_event_overlap_density"], places=6)


class TestRegisterOverlapWeighting(unittest.TestCase):
    def setUp(self) -> None:
        self.an = RegisterUniformityAnalyzer.__new__(RegisterUniformityAnalyzer)
        self.an.register_low = 48.0
        self.an.register_high = 84.0
        n_semitones = max(1, round(self.an.register_high - self.an.register_low) + 1)
        self.an._bin_edges = np.linspace(self.an.register_low - 0.5, self.an.register_high + 0.5, n_semitones + 1)
        self.an._n_bins = len(self.an._bin_edges) - 1
        self.an._max_entropy = float(np.log(max(1, self.an._n_bins)))

    def test_single_pitch_zero_with_weights(self) -> None:
        U = self.an.compute_uniformity(np.array([60.0]), np.array([4.0]))
        self.assertEqual(U, 0.0)

    def test_weighted_more_concentrated_than_uniform_weights(self) -> None:
        """Tiny mass on a second bin lowers entropy vs equal weighting on two bins."""
        ps = np.array([60.0, 72.0], dtype=float)
        u_equal = self.an.compute_uniformity(ps, np.array([1.0, 1.0]))
        u_skew = self.an.compute_uniformity(ps, np.array([10.0, 0.05]))
        self.assertLess(u_skew, u_equal)

    def test_empty_returns_nan(self) -> None:
        self.assertTrue(np.isnan(self.an.compute_uniformity(np.array([]))))

    def test_register_analyzer_end_to_end_weighted_changes_vs_flat(self) -> None:
        """Overlap-weighted U differs from applying unit weights to the same pitch list."""
        sc = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Piano())
        p.insert(0, meter.TimeSignature("4/4"))
        p.append(note.Note("C4", quarterLength=8.0))
        p.insert(7.9375, note.Note("E4", quarterLength=0.0625))
        sc.insert(0, p)
        reg = RegisterUniformityAnalyzer(
            score_path=None,
            register_low_ps=55.0,
            register_high_ps=65.0,
            time_step=0.25,
            music21_score=sc,
        )
        t_center = 4.0
        w = 8.0
        pitches, wts = reg._weighted_pitches_in_register(t_center, w)
        u_w = reg.compute_uniformity(pitches, wts)
        u_flat = reg.compute_uniformity(pitches, np.ones_like(pitches))
        self.assertEqual(pitches.size, 2)
        self.assertLess(u_w, u_flat)


class TestWrittenVsSoundingPitch(unittest.TestCase):
    def test_homogeneity_uses_written_ps_clarinet(self) -> None:
        """music21 flattened pitch.ps for transposing instruments is written pitch by default."""
        sc = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Clarinet())
        m = stream.Measure(number=1)
        m.insert(0, meter.TimeSignature("4/4"))
        m.insert(0, note.Note("C4", quarterLength=4.0))
        p.append(m)
        sc.insert(0, p)
        an = HomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        f = an.extract_features(2.0, 4.0)
        self.assertIsNotNone(f)
        assert f is not None
        idx = int(np.argmax(f["pitch_pmf"]))
        self.assertGreater(f["pitch_pmf"][idx], 0.5)
        self.assertLess(abs(float(an.pitch_centers[idx]) - 60.0), 1.01)
        n0 = p.flatten().notes[0]
        sounding = sounding_pitch_ps_list(n0, p)
        self.assertAlmostEqual(sounding[0], 58.0, places=0)
