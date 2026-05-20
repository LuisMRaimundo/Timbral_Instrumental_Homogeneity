"""Focused tests for saxophone-family symbolic H_timbral refinement."""

from __future__ import annotations

import unittest

import numpy as np
from music21 import expressions, note

from homogeneity_analyser.analyzers.saxophone_pairwise_timbral import pairwise_saxophone_homogeneity
from homogeneity_analyser.analyzers.saxophone_technique import (
    SAX_BREATHY,
    SAX_FLUTTER,
    SAX_GROWL,
    SAX_ORDINARIO,
    SAX_SLAP,
    SAX_SUBTONE,
    saxophone_technique_from_note,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_SAXOPHONES, FAMILY_STRINGS


def _se(
    instrument: str,
    pitch_ps: float,
    technique: str = SAX_ORDINARIO,
    overlap_ql: float = 1.0,
) -> dict:
    return {
        "instrument": instrument,
        "pitch": float(pitch_ps),
        "technique": technique,
        "overlap_ql": float(overlap_ql),
    }


class TestSaxophoneSubtypeHierarchy(unittest.TestCase):
    def test_alto_tenor_gt_alto_baritone(self):
        at = pairwise_saxophone_homogeneity([_se("alto saxophone", 72.0), _se("tenor saxophone", 68.0)])
        ab = pairwise_saxophone_homogeneity([_se("alto saxophone", 72.0), _se("baritone saxophone", 58.0)])
        self.assertGreater(at, ab)

    def test_tenor_baritone_gt_soprano_baritone(self):
        tb = pairwise_saxophone_homogeneity([_se("tenor saxophone", 65.0), _se("baritone saxophone", 55.0)])
        sb = pairwise_saxophone_homogeneity([_se("soprano saxophone", 74.0), _se("baritone saxophone", 55.0)])
        self.assertGreater(tb, sb)

    def test_baritone_bass_gt_soprano_bass(self):
        bb = pairwise_saxophone_homogeneity([_se("baritone saxophone", 55.0), _se("bass saxophone", 48.0)])
        sb = pairwise_saxophone_homogeneity([_se("soprano saxophone", 74.0), _se("bass saxophone", 45.0)])
        self.assertGreater(bb, sb)

    def test_soprano_alto_gt_soprano_bass(self):
        sa = pairwise_saxophone_homogeneity([_se("soprano saxophone", 72.0), _se("alto saxophone", 70.0)])
        sb = pairwise_saxophone_homogeneity([_se("soprano saxophone", 72.0), _se("bass saxophone", 45.0)])
        self.assertGreater(sa, sb)


class TestSaxophoneTessitura(unittest.TestCase):
    def test_same_alto_same_zone_gt_adjacent_gt_distant(self):
        same = pairwise_saxophone_homogeneity([_se("alto saxophone", 72.0), _se("alto saxophone", 72.0)])
        adj = pairwise_saxophone_homogeneity([_se("alto saxophone", 72.0), _se("alto saxophone", 78.0)])
        far = pairwise_saxophone_homogeneity([_se("alto saxophone", 60.0), _se("alto saxophone", 88.0)])
        self.assertGreater(same, adj)
        self.assertGreater(adj, far)

    def test_same_tenor_zones(self):
        same = pairwise_saxophone_homogeneity([_se("tenor saxophone", 65.0), _se("tenor saxophone", 66.0)])
        far = pairwise_saxophone_homogeneity([_se("tenor saxophone", 52.0), _se("tenor saxophone", 82.0)])
        self.assertGreater(same, far)

    def test_same_baritone_zones(self):
        same = pairwise_saxophone_homogeneity([_se("baritone saxophone", 55.0), _se("baritone saxophone", 56.0)])
        far = pairwise_saxophone_homogeneity([_se("baritone saxophone", 45.0), _se("baritone saxophone", 72.0)])
        self.assertGreater(same, far)

    def test_alto_mid_high_vs_alto_mid_baritone_mid(self):
        aa = pairwise_saxophone_homogeneity([_se("alto saxophone", 70.0), _se("alto saxophone", 82.0)])
        ab = pairwise_saxophone_homogeneity([_se("alto saxophone", 70.0), _se("baritone saxophone", 55.0)])
        self.assertGreater(aa, ab)


class TestSaxophoneTechniqueSensitivity(unittest.TestCase):
    def test_ord_pairs_beat_alternatives(self):
        base = (_se("alto saxophone", 72.0, SAX_ORDINARIO), _se("alto saxophone", 72.0, SAX_ORDINARIO))
        h0 = pairwise_saxophone_homogeneity(list(base))
        self.assertGreater(h0, pairwise_saxophone_homogeneity([base[0], _se("alto saxophone", 72.0, SAX_SUBTONE)]))
        self.assertGreater(h0, pairwise_saxophone_homogeneity([base[0], _se("alto saxophone", 72.0, SAX_GROWL)]))
        self.assertGreater(h0, pairwise_saxophone_homogeneity([base[0], _se("alto saxophone", 72.0, SAX_FLUTTER)]))
        self.assertGreater(h0, pairwise_saxophone_homogeneity([base[0], _se("alto saxophone", 72.0, SAX_SLAP)]))
        self.assertGreater(h0, pairwise_saxophone_homogeneity([base[0], _se("alto saxophone", 72.0, SAX_BREATHY)]))


class TestSaxophoneTechniqueParsing(unittest.TestCase):
    def test_growl_lyric(self):
        n = note.Note("D4")
        n.addLyric("growl")
        self.assertEqual(saxophone_technique_from_note(n, family=FAMILY_SAXOPHONES), SAX_GROWL)

    def test_subtone_expression(self):
        n = note.Note("E4")
        n.expressions.append(expressions.TextExpression("subtone"))
        self.assertEqual(saxophone_technique_from_note(n, family=FAMILY_SAXOPHONES), SAX_SUBTONE)

    def test_non_sax_returns_ordinario(self):
        n = note.Note("C4")
        n.addLyric("growl")
        self.assertEqual(saxophone_technique_from_note(n, family=FAMILY_STRINGS), SAX_ORDINARIO)


class TestMixedSaxophoneSonorities(unittest.TestCase):
    def test_pure_altos_gt_alto_tenor_gt_alto_baritone(self):
        pure = pairwise_saxophone_homogeneity([_se("alto saxophone", 72.0), _se("alto saxophone", 73.0)])
        at = pairwise_saxophone_homogeneity([_se("alto saxophone", 72.0), _se("tenor saxophone", 68.0)])
        ab = pairwise_saxophone_homogeneity([_se("alto saxophone", 72.0), _se("baritone saxophone", 58.0)])
        self.assertGreater(pure, at)
        self.assertGreater(at, ab)


class TestSaxophoneTimbralRegression(unittest.TestCase):
    def test_compute_H_timbral_without_saxophone_keys(self):
        ana = TimbralHomogeneityAnalyzer.__new__(TimbralHomogeneityAnalyzer)
        ana._timbral_config = {
            "weight_instrument": 0.65,
            "weight_register": 0.35,
            "family_bonus": 0.65,
            "register_ref_semitones": 3.0,
        }
        feats = {
            "n_notes": 3,
            "n_instruments": 2,
            "n_families": 2,
            "pitches": np.array([60.0, 64.0, 67.0], dtype=float),
        }
        H = TimbralHomogeneityAnalyzer.compute_H_timbral(ana, feats)
        self.assertGreater(H, 0.0)
        self.assertLessEqual(H, 1.0)


if __name__ == "__main__":
    unittest.main()
