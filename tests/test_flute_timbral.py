"""Focused tests for flute-family symbolic H_timbral refinement."""

from __future__ import annotations

import unittest

import numpy as np
from music21 import articulations, expressions, note

from homogeneity_analyser.analyzers.flute_pairwise_timbral import pairwise_flute_homogeneity
from homogeneity_analyser.analyzers.flute_technique import (
    FLUTE_BREATHY,
    FLUTE_FLUTTER,
    FLUTE_HARMONIC,
    FLUTE_ORDINARIO,
    FLUTE_WHISTLE,
    flute_technique_from_note,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_FLUTES


def _fe(
    instrument: str,
    pitch_ps: float,
    technique: str = FLUTE_ORDINARIO,
    overlap_ql: float = 1.0,
) -> dict:
    return {
        "instrument": instrument,
        "pitch": float(pitch_ps),
        "technique": technique,
        "overlap_ql": float(overlap_ql),
    }


class TestFluteSubtypeHierarchy(unittest.TestCase):
    def test_flute_alto_vs_flute_piccolo(self):
        ctrl = (_fe("flute", 76.0), _fe("alto flute", 72.0))
        alt = (_fe("flute", 76.0), _fe("piccolo", 88.0))
        self.assertGreater(pairwise_flute_homogeneity(list(ctrl)), pairwise_flute_homogeneity(list(alt)))

    def test_alto_bass_vs_alto_piccolo(self):
        ctrl = (_fe("alto flute", 70.0), _fe("bass flute", 55.0))
        alt = (_fe("alto flute", 70.0), _fe("piccolo", 88.0))
        self.assertGreater(pairwise_flute_homogeneity(list(ctrl)), pairwise_flute_homogeneity(list(alt)))

    def test_bass_piccolo_among_lowest(self):
        bass_pic = pairwise_flute_homogeneity([_fe("bass flute", 50.0), _fe("piccolo", 90.0)])
        flute_alto = pairwise_flute_homogeneity([_fe("flute", 76.0), _fe("alto flute", 72.0)])
        self.assertLess(bass_pic, flute_alto)


class TestFluteTessituraSensitivity(unittest.TestCase):
    def test_same_flute_same_zone_highest_then_adjacent_then_distant(self):
        same = pairwise_flute_homogeneity([_fe("flute", 75.0), _fe("flute", 75.0)])
        adj = pairwise_flute_homogeneity([_fe("flute", 75.0), _fe("flute", 82.0)])
        far = pairwise_flute_homogeneity([_fe("flute", 62.0), _fe("flute", 94.0)])
        self.assertGreater(same, adj)
        self.assertGreater(adj, far)

    def test_alto_flute_tessitura_order(self):
        same = pairwise_flute_homogeneity([_fe("alto flute", 68.0), _fe("alto flute", 68.0)])
        far = pairwise_flute_homogeneity([_fe("alto flute", 55.0), _fe("alto flute", 86.0)])
        self.assertGreater(same, far)

    def test_piccolo_tessitura_order(self):
        same = pairwise_flute_homogeneity([_fe("piccolo", 88.0), _fe("piccolo", 88.0)])
        far = pairwise_flute_homogeneity([_fe("piccolo", 74.0), _fe("piccolo", 102.0)])
        self.assertGreater(same, far)

    def test_flute_high_mid_closer_than_flute_high_bass_high(self):
        a = pairwise_flute_homogeneity([_fe("flute", 88.0), _fe("flute", 72.0)])
        b = pairwise_flute_homogeneity([_fe("flute", 88.0), _fe("bass flute", 62.0)])
        self.assertGreater(a, b)


class TestFluteTechniqueSensitivity(unittest.TestCase):
    def test_ord_pairs_beat_mixed_techniques(self):
        base = (_fe("flute", 76.0, FLUTE_ORDINARIO), _fe("flute", 76.0, FLUTE_ORDINARIO))
        h0 = pairwise_flute_homogeneity(list(base))
        self.assertGreater(h0, pairwise_flute_homogeneity([base[0], _fe("flute", 76.0, FLUTE_BREATHY)]))
        self.assertGreater(h0, pairwise_flute_homogeneity([base[0], _fe("flute", 76.0, FLUTE_FLUTTER)]))
        self.assertGreater(h0, pairwise_flute_homogeneity([base[0], _fe("flute", 76.0, FLUTE_HARMONIC)]))
        self.assertGreater(h0, pairwise_flute_homogeneity([base[0], _fe("flute", 76.0, FLUTE_WHISTLE)]))


class TestFluteTechniqueParsing(unittest.TestCase):
    def test_flutter_from_lyric(self):
        n = note.Note("G4")
        n.addLyric("flutter tongue")
        self.assertEqual(flute_technique_from_note(n, family=FAMILY_FLUTES), FLUTE_FLUTTER)

    def test_harmonic_articulation(self):
        # `Harmonic` articulation in MusicXML/music21 is a **notational** flag; it implies written
        # harmonics in many scores but is not a guarantee of sounding behaviour without further context.
        n = note.Note("A4")
        n.articulations.append(articulations.Harmonic())
        self.assertEqual(flute_technique_from_note(n, family=FAMILY_FLUTES), FLUTE_HARMONIC)

    def test_whistle_from_expression(self):
        n = note.Note("C5")
        n.expressions.append(expressions.TextExpression("whistle tone"))
        self.assertEqual(flute_technique_from_note(n, family=FAMILY_FLUTES), FLUTE_WHISTLE)

    def test_non_flute_family_returns_ordinario(self):
        n = note.Note("D4")
        n.addLyric("flutter")
        self.assertEqual(flute_technique_from_note(n, family="strings"), FLUTE_ORDINARIO)


class TestMixedFluteSonorities(unittest.TestCase):
    def test_pure_two_flutes_vs_flute_alto_vs_flute_piccolo(self):
        pure = pairwise_flute_homogeneity([_fe("flute", 75.0), _fe("flute", 76.0)])
        fa = pairwise_flute_homogeneity([_fe("flute", 75.0), _fe("alto flute", 72.0)])
        fp = pairwise_flute_homogeneity([_fe("flute", 75.0), _fe("piccolo", 88.0)])
        self.assertGreater(pure, fa)
        self.assertGreater(fa, fp)

    def test_alto_bass_more_homogeneous_than_flute_piccolo(self):
        ab = pairwise_flute_homogeneity([_fe("alto flute", 70.0), _fe("bass flute", 55.0)])
        fp = pairwise_flute_homogeneity([_fe("flute", 76.0), _fe("piccolo", 88.0)])
        self.assertGreater(ab, fp)


class TestFluteTimbralRegression(unittest.TestCase):
    def test_compute_H_timbral_without_flute_keys_unchanged_path(self):
        ana = TimbralHomogeneityAnalyzer.__new__(TimbralHomogeneityAnalyzer)
        ana._timbral_config = {
            "weight_instrument": 0.65,
            "weight_register": 0.35,
            "family_bonus": 0.65,
            "register_ref_semitones": 3.0,
        }
        feats = {
            "n_notes": 4,
            "n_instruments": 2,
            "n_families": 2,
            "pitches": np.array([60.0, 64.0, 67.0, 72.0], dtype=float),
        }
        H = TimbralHomogeneityAnalyzer.compute_H_timbral(ana, feats)
        self.assertGreater(H, 0.0)
        self.assertLessEqual(H, 1.0)


if __name__ == "__main__":
    unittest.main()
