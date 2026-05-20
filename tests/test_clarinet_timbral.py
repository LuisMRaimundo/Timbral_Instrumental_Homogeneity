"""Focused tests for clarinet-family symbolic H_timbral refinement."""

from __future__ import annotations

import unittest

import numpy as np
from music21 import expressions, note

from homogeneity_analyser.analyzers.clarinet_pairwise_timbral import pairwise_clarinet_homogeneity
from homogeneity_analyser.analyzers.clarinet_technique import (
    CLARINET_BREATHY,
    CLARINET_FLUTTER,
    CLARINET_MULTIPHONIC,
    CLARINET_ORDINARIO,
    CLARINET_SLAP,
    clarinet_technique_from_note,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_CLARINETS


def _ce(
    instrument: str,
    pitch_ps: float,
    technique: str = CLARINET_ORDINARIO,
    overlap_ql: float = 1.0,
) -> dict:
    return {
        "instrument": instrument,
        "pitch": float(pitch_ps),
        "technique": technique,
        "overlap_ql": float(overlap_ql),
    }


class TestClarinetSubtypeHierarchy(unittest.TestCase):
    def test_a_clarinet_plus_bb_higher_than_bb_plus_eflat(self):
        a_bb = pairwise_clarinet_homogeneity([_ce("a clarinet", 72.0), _ce("b flat clarinet", 72.0)])
        bb_eb = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("e flat clarinet", 72.0)])
        self.assertGreater(a_bb, bb_eb)

    def test_a_bb_higher_than_bb_bass(self):
        a_bb = pairwise_clarinet_homogeneity([_ce("a clarinet", 72.0), _ce("b flat clarinet", 72.0)])
        bb_bass = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("bass clarinet", 52.0)])
        self.assertGreater(a_bb, bb_bass)

    def test_bb_c_less_than_a_bb(self):
        a_bb = pairwise_clarinet_homogeneity([_ce("a clarinet", 72.0), _ce("b flat clarinet", 72.0)])
        bb_c = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("c clarinet", 72.0)])
        self.assertGreater(a_bb, bb_c)

    def test_bass_contra_higher_than_bb_contra(self):
        bc = pairwise_clarinet_homogeneity([_ce("bass clarinet", 50.0), _ce("contrabass clarinet", 42.0)])
        bb_cb = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("contrabass clarinet", 40.0)])
        self.assertGreater(bc, bb_cb)

    def test_eb_bass_among_lowest(self):
        eb_bass = pairwise_clarinet_homogeneity([_ce("e flat clarinet", 74.0), _ce("bass clarinet", 48.0)])
        a_bb = pairwise_clarinet_homogeneity([_ce("a clarinet", 72.0), _ce("b flat clarinet", 72.0)])
        self.assertLess(eb_bass, a_bb)


class TestClarinetRegisterZones(unittest.TestCase):
    def test_same_bb_same_pitch_highest_then_adjacent_then_distant(self):
        same = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("b flat clarinet", 72.0)])
        adj = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 70.0), _ce("b flat clarinet", 76.0)])
        far = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 58.0), _ce("b flat clarinet", 88.0)])
        self.assertGreater(same, adj)
        self.assertGreater(adj, far)

    def test_chalumeau_clarion_altissimo_chain(self):
        ch_ch = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 62.0), _ce("b flat clarinet", 64.0)])
        ch_cl = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 62.0), _ce("b flat clarinet", 72.0)])
        ch_alt = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 62.0), _ce("b flat clarinet", 86.0)])
        self.assertGreater(ch_ch, ch_cl)
        self.assertGreater(ch_cl, ch_alt)

    def test_bass_clarinet_relative_zones(self):
        same = pairwise_clarinet_homogeneity([_ce("bass clarinet", 50.0), _ce("bass clarinet", 51.0)])
        far = pairwise_clarinet_homogeneity([_ce("bass clarinet", 42.0), _ce("bass clarinet", 72.0)])
        self.assertGreater(same, far)

    def test_bb_chal_clar_more_homogeneous_than_bb_chal_bass_unrelated(self):
        bb_pair = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 62.0), _ce("b flat clarinet", 74.0)])
        bb_bass = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 62.0), _ce("bass clarinet", 48.0)])
        self.assertGreater(bb_pair, bb_bass)


class TestClarinetTechniqueSensitivity(unittest.TestCase):
    def test_ord_pairs_beat_mixed(self):
        base = (_ce("b flat clarinet", 72.0, CLARINET_ORDINARIO), _ce("b flat clarinet", 72.0, CLARINET_ORDINARIO))
        h0 = pairwise_clarinet_homogeneity(list(base))
        self.assertGreater(h0, pairwise_clarinet_homogeneity([base[0], _ce("b flat clarinet", 72.0, CLARINET_FLUTTER)]))
        self.assertGreater(h0, pairwise_clarinet_homogeneity([base[0], _ce("b flat clarinet", 72.0, CLARINET_BREATHY)]))
        self.assertGreater(h0, pairwise_clarinet_homogeneity([base[0], _ce("b flat clarinet", 72.0, CLARINET_SLAP)]))
        self.assertGreater(
            h0, pairwise_clarinet_homogeneity([base[0], _ce("b flat clarinet", 72.0, CLARINET_MULTIPHONIC)])
        )


class TestClarinetTechniqueParsing(unittest.TestCase):
    def test_flutter_from_lyric(self):
        n = note.Note("G4")
        n.addLyric("flutter tongue")
        self.assertEqual(clarinet_technique_from_note(n, family=FAMILY_CLARINETS), CLARINET_FLUTTER)

    def test_multiphonic_from_expression(self):
        n = note.Note("B4")
        n.expressions.append(expressions.TextExpression("multiphonic"))
        self.assertEqual(clarinet_technique_from_note(n, family=FAMILY_CLARINETS), CLARINET_MULTIPHONIC)

    def test_non_clarinet_family_returns_ordinario(self):
        n = note.Note("C4")
        n.addLyric("multiphonic")
        self.assertEqual(clarinet_technique_from_note(n, family="strings"), CLARINET_ORDINARIO)


class TestMixedClarinetSonorities(unittest.TestCase):
    def test_pure_bb_then_bb_a_then_bb_bass_then_bb_eb(self):
        pure = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("b flat clarinet", 73.0)])
        bb_a = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("a clarinet", 72.0)])
        bb_bass = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("bass clarinet", 52.0)])
        bb_eb = pairwise_clarinet_homogeneity([_ce("b flat clarinet", 72.0), _ce("e flat clarinet", 72.0)])
        self.assertGreater(pure, bb_a)
        self.assertGreater(bb_a, bb_bass)
        self.assertGreater(bb_bass, bb_eb)


class TestClarinetTimbralRegression(unittest.TestCase):
    def test_compute_H_timbral_without_clarinet_keys(self):
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
