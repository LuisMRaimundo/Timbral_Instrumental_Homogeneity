"""Focused tests for double-reed symbolic H_timbral refinement."""

from __future__ import annotations

import unittest

import numpy as np
from music21 import expressions, note

from homogeneity_analyser.analyzers.double_reed_pairwise_timbral import (
    double_reed_pair_score,
    pairwise_double_reed_homogeneity,
)
from homogeneity_analyser.analyzers.double_reed_technique import (
    DR_FLUTTER,
    DR_MULTIPHONIC,
    DR_ORDINARIO,
    double_reed_technique_from_note,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OBOES,
    FAMILY_STRINGS,
)


def _de(
    instrument: str,
    pitch_ps: float,
    technique: str = DR_ORDINARIO,
    overlap_ql: float = 1.0,
    family: str = FAMILY_OBOES,
) -> dict:
    return {
        "instrument": instrument,
        "family": family,
        "pitch": float(pitch_ps),
        "technique": technique,
        "overlap_ql": float(overlap_ql),
    }


class TestDoubleReedInternalHierarchy(unittest.TestCase):
    def test_oboe_english_horn_gt_oboe_bassoon(self):
        a = pairwise_double_reed_homogeneity(
            [_de("oboe", 72.0, family=FAMILY_OBOES), _de("cor anglais", 65.0, family=FAMILY_OBOES)]
        )
        b = pairwise_double_reed_homogeneity(
            [_de("oboe", 72.0, family=FAMILY_OBOES), _de("bassoon", 55.0, family=FAMILY_BASSOONS)]
        )
        self.assertGreater(a, b)

    def test_bassoon_contrabassoon_gt_oboe_bassoon(self):
        a = pairwise_double_reed_homogeneity(
            [_de("bassoon", 52.0, family=FAMILY_BASSOONS), _de("contrabassoon", 45.0, family=FAMILY_BASSOONS)]
        )
        b = pairwise_double_reed_homogeneity(
            [_de("oboe", 72.0, family=FAMILY_OBOES), _de("bassoon", 55.0, family=FAMILY_BASSOONS)]
        )
        self.assertGreater(a, b)

    def test_oboe_contrabassoon_lt_oboe_bassoon(self):
        a = pairwise_double_reed_homogeneity(
            [_de("oboe", 72.0, family=FAMILY_OBOES), _de("contrabassoon", 42.0, family=FAMILY_BASSOONS)]
        )
        b = pairwise_double_reed_homogeneity(
            [_de("oboe", 72.0, family=FAMILY_OBOES), _de("bassoon", 55.0, family=FAMILY_BASSOONS)]
        )
        self.assertLess(a, b)


class TestDoubleReedVsNonDoubleReed(unittest.TestCase):
    def test_oboe_bassoon_gt_oboe_clarinet(self):
        dr = double_reed_pair_score(
            "oboe",
            FAMILY_OBOES,
            70.0,
            DR_ORDINARIO,
            "bassoon",
            FAMILY_BASSOONS,
            58.0,
            DR_ORDINARIO,
        )
        mx = double_reed_pair_score(
            "oboe",
            FAMILY_OBOES,
            70.0,
            DR_ORDINARIO,
            "clarinet",
            FAMILY_CLARINETS,
            70.0,
            DR_ORDINARIO,
        )
        self.assertGreater(dr, mx)

    def test_oboe_bassoon_gt_oboe_flute(self):
        dr = double_reed_pair_score(
            "oboe",
            FAMILY_OBOES,
            70.0,
            DR_ORDINARIO,
            "bassoon",
            FAMILY_BASSOONS,
            58.0,
            DR_ORDINARIO,
        )
        fl = double_reed_pair_score(
            "oboe",
            FAMILY_OBOES,
            70.0,
            DR_ORDINARIO,
            "flute",
            FAMILY_FLUTES,
            70.0,
            DR_ORDINARIO,
        )
        self.assertGreater(dr, fl)

    def test_bassoon_contra_gt_bassoon_flute(self):
        dr = double_reed_pair_score(
            "bassoon",
            FAMILY_BASSOONS,
            52.0,
            DR_ORDINARIO,
            "contrabassoon",
            FAMILY_BASSOONS,
            45.0,
            DR_ORDINARIO,
        )
        fl = double_reed_pair_score(
            "bassoon",
            FAMILY_BASSOONS,
            52.0,
            DR_ORDINARIO,
            "flute",
            FAMILY_FLUTES,
            60.0,
            DR_ORDINARIO,
        )
        self.assertGreater(dr, fl)


class TestDoubleReedRegister(unittest.TestCase):
    def test_same_oboe_same_zone_gt_distant(self):
        same = pairwise_double_reed_homogeneity([_de("oboe", 72.0), _de("oboe", 72.0)])
        far = pairwise_double_reed_homogeneity([_de("oboe", 60.0), _de("oboe", 90.0)])
        self.assertGreater(same, far)

    def test_same_bassoon_zones(self):
        same = pairwise_double_reed_homogeneity(
            [_de("bassoon", 52.0, family=FAMILY_BASSOONS), _de("bassoon", 53.0, family=FAMILY_BASSOONS)]
        )
        far = pairwise_double_reed_homogeneity(
            [_de("bassoon", 40.0, family=FAMILY_BASSOONS), _de("bassoon", 72.0, family=FAMILY_BASSOONS)]
        )
        self.assertGreater(same, far)

    def test_same_contrabassoon_zones(self):
        same = pairwise_double_reed_homogeneity(
            [
                _de("contrabassoon", 45.0, family=FAMILY_BASSOONS),
                _de("contrabassoon", 46.0, family=FAMILY_BASSOONS),
            ]
        )
        far = pairwise_double_reed_homogeneity(
            [
                _de("contrabassoon", 35.0, family=FAMILY_BASSOONS),
                _de("contrabassoon", 58.0, family=FAMILY_BASSOONS),
            ]
        )
        self.assertGreater(same, far)


class TestMixedDoubleReedSonorities(unittest.TestCase):
    def test_pure_oboes_gt_oboe_cor_gt_oboe_bassoon(self):
        pure = pairwise_double_reed_homogeneity([_de("oboe", 72.0), _de("oboe", 73.0)])
        oc = pairwise_double_reed_homogeneity([_de("oboe", 72.0), _de("cor anglais", 65.0)])
        ob = pairwise_double_reed_homogeneity(
            [_de("oboe", 72.0, family=FAMILY_OBOES), _de("bassoon", 55.0, family=FAMILY_BASSOONS)]
        )
        self.assertGreater(pure, oc)
        self.assertGreater(oc, ob)

    def test_bassoon_contra_gt_oboe_contra(self):
        bc = pairwise_double_reed_homogeneity(
            [_de("bassoon", 52.0, family=FAMILY_BASSOONS), _de("contrabassoon", 45.0, family=FAMILY_BASSOONS)]
        )
        oc = pairwise_double_reed_homogeneity(
            [_de("oboe", 72.0, family=FAMILY_OBOES), _de("contrabassoon", 42.0, family=FAMILY_BASSOONS)]
        )
        self.assertGreater(bc, oc)


class TestDoubleReedTechniqueParsing(unittest.TestCase):
    def test_flutter_lyric(self):
        n = note.Note("A4")
        n.addLyric("flutter tongue")
        self.assertEqual(double_reed_technique_from_note(n, family=FAMILY_OBOES), DR_FLUTTER)

    def test_multiphonic_expression(self):
        n = note.Note("G4")
        n.expressions.append(expressions.TextExpression("multiphonic"))
        self.assertEqual(double_reed_technique_from_note(n, family=FAMILY_BASSOONS), DR_MULTIPHONIC)

    def test_strings_ignored(self):
        n = note.Note("C4")
        n.addLyric("flutter")
        self.assertEqual(double_reed_technique_from_note(n, family=FAMILY_STRINGS), DR_ORDINARIO)


class TestDoubleReedTimbralRegression(unittest.TestCase):
    def test_compute_H_timbral_without_double_reed_keys(self):
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
