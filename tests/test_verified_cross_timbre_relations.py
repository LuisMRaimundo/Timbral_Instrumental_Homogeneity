"""Tests for bibliography-scoped verified cross-family timbral relations (``timbre_cross_relations``)."""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from homogeneity_analyser.analyzers.brass_technique import BRASS_OPEN
from homogeneity_analyser.analyzers.clarinet_technique import CLARINET_ORDINARIO
from homogeneity_analyser.analyzers.double_reed_pairwise_timbral import double_reed_pair_score
from homogeneity_analyser.analyzers.double_reed_technique import DR_ORDINARIO
from homogeneity_analyser.analyzers.flute_technique import FLUTE_ORDINARIO
from homogeneity_analyser.analyzers.percussion_technique import PERC_ORDINARIO
from homogeneity_analyser.analyzers.saxophone_technique import SAX_ORDINARIO
from homogeneity_analyser.analyzers.string_pairwise_timbral import is_bowed_orchestral_string
from homogeneity_analyser.analyzers.string_technique import TECH_ARCO
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.analyzers.timbre_cross_relations import (
    VERIFIED_CROSS_TIMBRAL_REGISTRY,
    verified_cross_timbral_boost,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OBOES,
    FAMILY_PERCUSSION,
    FAMILY_SAXOPHONES,
    FAMILY_STRINGS,
    get_timbral_config,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"


def _timbral_analyzer() -> TimbralHomogeneityAnalyzer:
    a = object.__new__(TimbralHomogeneityAnalyzer)
    a._timbral_config = get_timbral_config()
    return a


def _slice(
    instrument: str,
    family: str,
    pitch_ps: float,
    overlap_ql: float = 1.0,
) -> dict:
    return {
        "instrument": instrument,
        "family": family,
        "pitch": float(pitch_ps),
        "overlap_ql": float(overlap_ql),
    }


def _features_from_slices(timbral_note_slices: list[dict]) -> dict:
    """Minimal ``extract_timbral_features``-shaped dict for ``compute_H_timbral``."""
    total_overlap_mass = sum(float(s["overlap_ql"]) for s in timbral_note_slices)
    pitches = np.array([float(s["pitch"]) for s in timbral_note_slices], dtype=float)
    instruments = {str(s["instrument"]) for s in timbral_note_slices}
    families = {str(s["family"]) for s in timbral_note_slices}
    string_events: list[dict] = []
    string_ol = 0.0
    brass_events: list[dict] = []
    brass_ol = 0.0
    flute_events: list[dict] = []
    flute_ol = 0.0
    clarinet_events: list[dict] = []
    clar_ol = 0.0
    double_reed_events: list[dict] = []
    dr_ol = 0.0
    saxophone_events: list[dict] = []
    sax_ol = 0.0
    percussion_events: list[dict] = []
    perc_ol = 0.0
    for s in timbral_note_slices:
        inst = str(s["instrument"])
        fam = str(s["family"])
        ps = float(s["pitch"])
        ol = float(s["overlap_ql"])
        base = {"instrument": inst, "pitch": ps, "overlap_ql": ol}
        if fam == FAMILY_STRINGS and is_bowed_orchestral_string(inst):
            string_events.append({**base, "technique": TECH_ARCO})
            string_ol += ol
        elif fam == FAMILY_BRASS:
            brass_events.append({**base, "technique": BRASS_OPEN})
            brass_ol += ol
        elif fam == FAMILY_FLUTES:
            flute_events.append({**base, "technique": FLUTE_ORDINARIO})
            flute_ol += ol
        elif fam == FAMILY_CLARINETS:
            clarinet_events.append({**base, "technique": CLARINET_ORDINARIO})
            clar_ol += ol
        elif fam in (FAMILY_OBOES, FAMILY_BASSOONS):
            double_reed_events.append({**base, "family": fam, "technique": DR_ORDINARIO})
            dr_ol += ol
        elif fam == FAMILY_SAXOPHONES:
            saxophone_events.append({**base, "technique": SAX_ORDINARIO})
            sax_ol += ol
        elif fam == FAMILY_PERCUSSION:
            percussion_events.append({**base, "technique": PERC_ORDINARIO})
            perc_ol += ol
    reg_span = np.array([float(s["pitch"]) for s in timbral_note_slices], dtype=float)
    return {
        "pitches": pitches,
        "register_span_pitches": reg_span,
        "instruments": instruments,
        "families": families,
        "n_notes": len(timbral_note_slices),
        "n_instruments": len(instruments),
        "n_families": len(families),
        "string_events": string_events,
        "string_overlap_mass": string_ol,
        "brass_events": brass_events,
        "brass_overlap_mass": brass_ol,
        "flute_events": flute_events,
        "flute_overlap_mass": flute_ol,
        "clarinet_events": clarinet_events,
        "clarinet_overlap_mass": clar_ol,
        "double_reed_events": double_reed_events,
        "double_reed_overlap_mass": dr_ol,
        "saxophone_events": saxophone_events,
        "saxophone_overlap_mass": sax_ol,
        "percussion_events": percussion_events,
        "percussion_overlap_mass": perc_ol,
        "percussion_unpitched_overlap_mass": 0.0,
        "percussion_pitched_overlap_mass": 0.0,
        "total_overlap_mass": total_overlap_mass,
        "timbral_note_slices": list(timbral_note_slices),
    }


class TestDoubleReedOrderingAttested(unittest.TestCase):
    def test_oboe_bassoon_gt_oboe_clarinet_and_flute(self):
        ob_bn = double_reed_pair_score(
            "oboe", FAMILY_OBOES, 70.0, DR_ORDINARIO, "bassoon", FAMILY_BASSOONS, 58.0, DR_ORDINARIO
        )
        ob_cl = double_reed_pair_score(
            "oboe", FAMILY_OBOES, 70.0, DR_ORDINARIO, "b flat clarinet", FAMILY_CLARINETS, 70.0, DR_ORDINARIO
        )
        ob_fl = double_reed_pair_score(
            "oboe", FAMILY_OBOES, 70.0, DR_ORDINARIO, "flute", FAMILY_FLUTES, 72.0, DR_ORDINARIO
        )
        self.assertGreater(ob_bn, ob_cl)
        self.assertGreater(ob_bn, ob_fl)

    def test_oboe_english_horn_gt_oboe_bassoon(self):
        a = double_reed_pair_score(
            "oboe", FAMILY_OBOES, 72.0, DR_ORDINARIO, "cor anglais", FAMILY_OBOES, 65.0, DR_ORDINARIO
        )
        b = double_reed_pair_score(
            "oboe", FAMILY_OBOES, 72.0, DR_ORDINARIO, "bassoon", FAMILY_BASSOONS, 55.0, DR_ORDINARIO
        )
        self.assertGreater(a, b)

    def test_bassoon_contrabassoon_gt_oboe_bassoon(self):
        a = double_reed_pair_score(
            "bassoon", FAMILY_BASSOONS, 52.0, DR_ORDINARIO, "contrabassoon", FAMILY_BASSOONS, 45.0, DR_ORDINARIO
        )
        b = double_reed_pair_score(
            "oboe", FAMILY_OBOES, 72.0, DR_ORDINARIO, "bassoon", FAMILY_BASSOONS, 55.0, DR_ORDINARIO
        )
        self.assertGreater(a, b)


class TestTenorSaxClarinetNarrow(unittest.TestCase):
    def test_tenor_clarinet_boost_not_alto_clarinet(self):
        tm = 2.0
        tenor_slices = [
            _slice("tenor saxophone", FAMILY_SAXOPHONES, 68.0),
            _slice("b flat clarinet", FAMILY_CLARINETS, 70.0),
        ]
        alto_slices = [
            _slice("alto saxophone", FAMILY_SAXOPHONES, 65.0),
            _slice("b flat clarinet", FAMILY_CLARINETS, 70.0),
        ]
        self.assertGreater(
            verified_cross_timbral_boost(tenor_slices, tm),
            verified_cross_timbral_boost(alto_slices, tm),
        )

    def test_tenor_sax_not_generalized_to_baritone(self):
        tm = 2.0
        baritone_slices = [
            _slice("baritone saxophone", FAMILY_SAXOPHONES, 58.0),
            _slice("b flat clarinet", FAMILY_CLARINETS, 70.0),
        ]
        self.assertEqual(verified_cross_timbral_boost(baritone_slices, tm), 0.0)


class TestAltoSaxFrenchHorn(unittest.TestCase):
    def test_alto_sax_horn_gt_alto_sax_trumpet(self):
        an = _timbral_analyzer()
        horn_pair = _features_from_slices(
            [
                _slice("alto saxophone", FAMILY_SAXOPHONES, 68.0),
                _slice("horn", FAMILY_BRASS, 66.0),
            ]
        )
        tr_pair = _features_from_slices(
            [
                _slice("alto saxophone", FAMILY_SAXOPHONES, 68.0),
                _slice("trumpet", FAMILY_BRASS, 70.0),
            ]
        )
        self.assertGreater(an.compute_H_timbral(horn_pair), an.compute_H_timbral(tr_pair))


class TestTrumpetOboe(unittest.TestCase):
    def test_trumpet_oboe_gt_trumpet_flute_and_below_two_trumpets(self):
        an = _timbral_analyzer()
        to = _features_from_slices(
            [
                _slice("trumpet", FAMILY_BRASS, 72.0),
                _slice("oboe", FAMILY_OBOES, 74.0),
            ]
        )
        tf = _features_from_slices(
            [
                _slice("trumpet", FAMILY_BRASS, 72.0),
                _slice("flute", FAMILY_FLUTES, 74.0),
            ]
        )
        tt = _features_from_slices(
            [
                _slice("trumpet", FAMILY_BRASS, 72.0),
                _slice("trumpet", FAMILY_BRASS, 73.0),
            ]
        )
        h_to = an.compute_H_timbral(to)
        h_tf = an.compute_H_timbral(tf)
        h_tt = an.compute_H_timbral(tt)
        self.assertGreater(h_to, h_tf)
        self.assertGreater(h_tt, h_to)


class TestBassClarinetBassoon(unittest.TestCase):
    def test_bass_clarinet_bassoon_preferred_over_bb_or_trumpet(self):
        an = _timbral_analyzer()
        bb = _features_from_slices(
            [
                _slice("b flat clarinet", FAMILY_CLARINETS, 58.0),
                _slice("bassoon", FAMILY_BASSOONS, 50.0),
            ]
        )
        bc = _features_from_slices(
            [
                _slice("bass clarinet", FAMILY_CLARINETS, 52.0),
                _slice("bassoon", FAMILY_BASSOONS, 50.0),
            ]
        )
        bct = _features_from_slices(
            [
                _slice("bass clarinet", FAMILY_CLARINETS, 52.0),
                _slice("trumpet", FAMILY_BRASS, 70.0),
            ]
        )
        self.assertGreater(an.compute_H_timbral(bc), an.compute_H_timbral(bb))
        self.assertGreater(an.compute_H_timbral(bc), an.compute_H_timbral(bct))


class TestHornBassoon(unittest.TestCase):
    def test_horn_bassoon_gt_trumpet_bassoon(self):
        an = _timbral_analyzer()
        hb = _features_from_slices(
            [
                _slice("horn", FAMILY_BRASS, 60.0),
                _slice("bassoon", FAMILY_BASSOONS, 52.0),
            ]
        )
        tb = _features_from_slices(
            [
                _slice("trumpet", FAMILY_BRASS, 72.0),
                _slice("bassoon", FAMILY_BASSOONS, 52.0),
            ]
        )
        self.assertGreater(an.compute_H_timbral(hb), an.compute_H_timbral(tb))


class TestHighRegisterClarinetFlute(unittest.TestCase):
    def test_high_clarinet_flute_gt_low_clarinet_flute(self):
        an = _timbral_analyzer()
        hi = _features_from_slices(
            [
                _slice("b flat clarinet", FAMILY_CLARINETS, 78.0),
                _slice("flute", FAMILY_FLUTES, 76.0),
            ]
        )
        lo = _features_from_slices(
            [
                _slice("b flat clarinet", FAMILY_CLARINETS, 60.0),
                _slice("flute", FAMILY_FLUTES, 76.0),
            ]
        )
        self.assertGreater(an.compute_H_timbral(hi), an.compute_H_timbral(lo))

    def test_no_boost_when_clarinet_not_high(self):
        self.assertEqual(
            verified_cross_timbral_boost(
                [
                    _slice("b flat clarinet", FAMILY_CLARINETS, 65.0),
                    _slice("flute", FAMILY_FLUTES, 80.0),
                ],
                2.0,
            ),
            0.0,
        )


class TestSafetyNoSpeculativeCross(unittest.TestCase):
    def test_unrelated_pairs_zero_cross_boost(self):
        slices = [
            _slice("violin", FAMILY_STRINGS, 69.0),
            _slice("flute", FAMILY_FLUTES, 72.0),
        ]
        self.assertEqual(verified_cross_timbral_boost(slices, 2.0), 0.0)

    def test_registry_documents_natural_horn_relation(self):
        keys = [r.source_relation_key for r in VERIFIED_CROSS_TIMBRAL_REGISTRY]
        self.assertIn("natural_horn_cor_de_chasse_trumpet_bass_trumpet", keys)
        row = next(
            r
            for r in VERIFIED_CROSS_TIMBRAL_REGISTRY
            if r.source_relation_key == "natural_horn_cor_de_chasse_trumpet_bass_trumpet"
        )
        self.assertIn("natural horn", row.documentation_note.replace("`", "").lower())
        self.assertNotIn("unsupported", row.documentation_note.lower())

    def test_tenor_sax_e_flat_clarinet_no_cross_boost(self):
        tm = 2.0
        slices = [
            _slice("tenor saxophone", FAMILY_SAXOPHONES, 68.0),
            _slice("e flat clarinet", FAMILY_CLARINETS, 72.0),
        ]
        self.assertEqual(verified_cross_timbral_boost(slices, tm), 0.0)


class TestPipelineStillRuns(unittest.TestCase):
    def test_timbral_fixture(self):
        if not FIXTURE_XML.is_file():
            self.skipTest("Fixture not found")
        from homogeneity_analyser.services.analysis_service import run_timbral_analysis

        out = run_timbral_analysis(str(FIXTURE_XML), {"time_step": 0.5, "window_size": 4.0})
        self.assertIsNone(out.get("error"), out.get("error"))
        self.assertIn("H_timbral", out["results"])
