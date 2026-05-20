"""Tests for percussion symbolic H_timbral subsystem."""

from __future__ import annotations

import unittest

import numpy as np
from music21 import expressions, note

from homogeneity_analyser.analyzers.percussion_pairwise_timbral import (
    pairwise_percussion_homogeneity,
    percussion_instrument_similarity,
)
from homogeneity_analyser.analyzers.percussion_technique import (
    PERC_BOWED,
    PERC_MALLET_HARD,
    PERC_ORDINARIO,
    PERC_ROLLED,
    PERC_SNARE_OFF,
    PERC_SNARE_ON,
    PERC_VIB_NO_PEDAL,
    PERC_VIB_PEDAL,
    percussion_technique_from_note,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_PERCUSSION, FAMILY_STRINGS


def _pe(inst: str, ps: float, tech: str = PERC_ORDINARIO, w: float = 1.0) -> dict:
    return {"instrument": inst, "pitch": float(ps), "technique": tech, "overlap_ql": w}


class TestPercussionMacroClassStructure(unittest.TestCase):
    def test_xylophone_marimba_gt_xylophone_cymbal(self):
        xm = pairwise_percussion_homogeneity([_pe("xylophone", 72.0), _pe("marimba", 65.0)])
        xc = pairwise_percussion_homogeneity([_pe("xylophone", 72.0), _pe("cymbal", 65.0)])
        self.assertGreater(xm, xc)

    def test_glock_crotales_gt_glock_bass_drum(self):
        gc = pairwise_percussion_homogeneity([_pe("glockenspiel", 80.0), _pe("crotales", 84.0)])
        gb = pairwise_percussion_homogeneity([_pe("glockenspiel", 80.0), _pe("bass drum", 40.0)])
        self.assertGreater(gc, gb)

    def test_bass_drum_tom_gt_snare_bass(self):
        bt = pairwise_percussion_homogeneity([_pe("bass drum", 40.0), _pe("tom-tom", 50.0)])
        sb = pairwise_percussion_homogeneity([_pe("snare drum", 55.0), _pe("bass drum", 40.0)])
        self.assertGreater(bt, sb)

    def test_gong_tamtam_gt_triangle_tamtam(self):
        gt = pairwise_percussion_homogeneity([_pe("gong", 48.0), _pe("tam-tam", 45.0)])
        tt = pairwise_percussion_homogeneity([_pe("triangle", 84.0), _pe("tam-tam", 45.0)])
        self.assertGreater(gt, tt)

    def test_glock_crotales_gt_glock_vibraphone(self):
        gc = pairwise_percussion_homogeneity([_pe("glockenspiel", 80.0), _pe("crotales", 84.0)])
        gv = pairwise_percussion_homogeneity([_pe("glockenspiel", 80.0), _pe("vibraphone", 70.0)])
        self.assertGreater(gc, gv)


class TestTimpaniSpecialCase(unittest.TestCase):
    def test_timpani_pair_gt_timpani_bass_drum(self):
        tt = pairwise_percussion_homogeneity([_pe("timpani", 55.0), _pe("timpani", 57.0)])
        tb = pairwise_percussion_homogeneity([_pe("timpani", 55.0), _pe("bass drum", 40.0)])
        self.assertGreater(tt, tb)

    def test_timpani_pair_gt_timpani_snare(self):
        tt = pairwise_percussion_homogeneity([_pe("timpani", 55.0), _pe("timpani", 56.0)])
        ts = pairwise_percussion_homogeneity([_pe("timpani", 55.0), _pe("snare drum", 60.0)])
        self.assertGreater(tt, ts)


class TestMetallicIdiophoneStructure(unittest.TestCase):
    def test_triangle_not_near_cymbal_as_generic_metal(self):
        tri_cym = percussion_instrument_similarity("triangle", "cymbal")
        cym_tam = percussion_instrument_similarity("cymbal", "tam-tam")
        self.assertGreater(cym_tam, tri_cym)


class TestPercussionTechniqueSensitivity(unittest.TestCase):
    def test_marimba_hard_soft_mallets(self):
        hh = pairwise_percussion_homogeneity(
            [_pe("marimba", 65.0, PERC_ORDINARIO), _pe("marimba", 66.0, PERC_ORDINARIO)]
        )
        hs = pairwise_percussion_homogeneity(
            [_pe("marimba", 65.0, PERC_ORDINARIO), _pe("marimba", 66.0, PERC_MALLET_HARD)]
        )
        self.assertGreater(hh, hs)

    def test_snare_on_vs_off(self):
        oo = pairwise_percussion_homogeneity(
            [_pe("snare drum", 55.0, PERC_SNARE_ON), _pe("snare drum", 55.0, PERC_SNARE_ON)]
        )
        ox = pairwise_percussion_homogeneity(
            [_pe("snare drum", 55.0, PERC_SNARE_ON), _pe("snare drum", 55.0, PERC_SNARE_OFF)]
        )
        self.assertGreater(oo, ox)

    def test_vibraphone_pedal_states(self):
        pp = pairwise_percussion_homogeneity(
            [_pe("vibraphone", 65.0, PERC_VIB_PEDAL), _pe("vibraphone", 66.0, PERC_VIB_PEDAL)]
        )
        pn = pairwise_percussion_homogeneity(
            [_pe("vibraphone", 65.0, PERC_VIB_PEDAL), _pe("vibraphone", 66.0, PERC_VIB_NO_PEDAL)]
        )
        self.assertGreater(pp, pn)

    def test_tamtam_struck_vs_bowed(self):
        ss = pairwise_percussion_homogeneity(
            [_pe("tam-tam", 45.0, PERC_ORDINARIO), _pe("tam-tam", 45.0, PERC_ORDINARIO)]
        )
        sb = pairwise_percussion_homogeneity([_pe("tam-tam", 45.0, PERC_ORDINARIO), _pe("tam-tam", 45.0, PERC_BOWED)])
        self.assertGreater(ss, sb)

    def test_cymbal_ordinario_vs_rolled(self):
        oo = pairwise_percussion_homogeneity([_pe("cymbal", 70.0, PERC_ORDINARIO), _pe("cymbal", 70.0, PERC_ORDINARIO)])
        or_ = pairwise_percussion_homogeneity([_pe("cymbal", 70.0, PERC_ORDINARIO), _pe("cymbal", 70.0, PERC_ROLLED)])
        self.assertGreater(oo, or_)


class TestPitchedVsUnpitchedHandling(unittest.TestCase):
    def test_marimba_pair_vs_marimba_bass_drum(self):
        mm = pairwise_percussion_homogeneity([_pe("marimba", 65.0), _pe("marimba", 67.0)])
        mb = pairwise_percussion_homogeneity([_pe("marimba", 65.0), _pe("bass drum", 40.0)])
        self.assertGreater(mm, mb)


class TestPercussionTechniqueParsing(unittest.TestCase):
    def test_roll_lyric(self):
        n = note.Note("C4")
        n.addLyric("roll")
        self.assertEqual(percussion_technique_from_note(n, family=FAMILY_PERCUSSION), PERC_ROLLED)

    def test_hard_mallet_expression(self):
        n = note.Note("D4")
        n.expressions.append(expressions.TextExpression("hard mallet"))
        self.assertEqual(percussion_technique_from_note(n, family=FAMILY_PERCUSSION), PERC_MALLET_HARD)

    def test_non_percussion_ignored(self):
        n = note.Note("E4")
        n.addLyric("roll")
        self.assertEqual(percussion_technique_from_note(n, family=FAMILY_STRINGS), PERC_ORDINARIO)


class TestPercussionTimbralRegression(unittest.TestCase):
    def test_compute_H_timbral_without_percussion_keys(self):
        ana = TimbralHomogeneityAnalyzer.__new__(TimbralHomogeneityAnalyzer)
        ana._timbral_config = {
            "weight_instrument": 0.65,
            "weight_register": 0.35,
            "family_bonus": 0.65,
            "register_ref_semitones": 3.0,
        }
        feats = {
            "n_notes": 2,
            "n_instruments": 2,
            "n_families": 2,
            "pitches": np.array([60.0, 64.0], dtype=float),
        }
        H = TimbralHomogeneityAnalyzer.compute_H_timbral(ana, feats)
        self.assertGreater(H, 0.0)
        self.assertLessEqual(H, 1.0)


if __name__ == "__main__":
    unittest.main()
