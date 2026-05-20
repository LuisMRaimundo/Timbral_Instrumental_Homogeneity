"""Regression tests for timbral correction pass (sounding pitch, notation context, percussion register)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from music21 import expressions, instrument, meter, note, stream

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.analyzers.percussion_ontology import PitchStatus, get_percussion_meta
from homogeneity_analyser.analyzers.string_technique import TECH_PIZZ, string_technique_from_note
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.analyzers.timbral_sounding_pitch import sounding_pitch_ps_list
from homogeneity_analyser.analyzers.timbre_cross_relations import verified_cross_timbral_boost
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_PERCUSSION,
    get_timbral_config,
)


def _timbral_analyzer_from_score(sc: stream.Score) -> TimbralHomogeneityAnalyzer:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "score.musicxml"
        sc.write("musicxml", fp=str(path))
        return TimbralHomogeneityAnalyzer(str(path))


class TestSoundingPitchTimbral(unittest.TestCase):
    def test_bb_clarinet_written_c_sounds_bb(self):
        p = stream.Part()
        p.insert(0, instrument.Clarinet())
        p.append(note.Note("C4"))
        n = p.flatten().notes[0]
        ps = sounding_pitch_ps_list(n, p)
        self.assertEqual(len(ps), 1)
        self.assertAlmostEqual(ps[0], 58.0, places=3)

    def test_alto_sax_written_c_sounds_eb_below(self):
        p = stream.Part()
        p.insert(0, instrument.AltoSaxophone())
        p.append(note.Note("C4"))
        n = p.flatten().notes[0]
        ps = sounding_pitch_ps_list(n, p)
        self.assertAlmostEqual(ps[0], 51.0, places=3)

    def test_piccolo_transposes_octave(self):
        p = stream.Part()
        p.insert(0, instrument.Piccolo())
        p.append(note.Note("C5"))
        n = p.flatten().notes[0]
        ps = sounding_pitch_ps_list(n, p)
        self.assertGreater(ps[0], float(n.pitch.ps))

    def test_timbral_events_use_sounding_pitch(self):
        sc = stream.Score()
        p = stream.Part()
        p.insert(0, instrument.Clarinet())
        p.insert(0, meter.TimeSignature("4/4"))
        p.append(note.Note("C4", quarterLength=4.0))
        sc.append(p)
        a = _timbral_analyzer_from_score(sc)
        ev = a._events
        self.assertEqual(len(ev), 1)
        self.assertAlmostEqual(ev[0]["pitches"][0], 58.0, places=2)


class TestNotationContextTechnique(unittest.TestCase):
    def test_measure_text_expression_pizz(self):
        m = stream.Measure()
        m.number = 1
        m.insert(0, expressions.TextExpression("pizz."))
        m.insert(1, note.Note("G3", quarterLength=1.0))
        n = m.notes[0]
        blob = notation_text_context_for_note(n)
        self.assertIn("pizz", blob)
        self.assertEqual(string_technique_from_note(n), TECH_PIZZ)


class TestCrossRelationNarrowing(unittest.TestCase):
    def test_high_clarinet_flute_excludes_bass_clarinet(self):
        tm = 2.0
        bass_pair = [
            {"instrument": "bass clarinet", "family": FAMILY_CLARINETS, "pitch": 78.0, "overlap_ql": 1.0},
            {"instrument": "flute", "family": FAMILY_FLUTES, "pitch": 76.0, "overlap_ql": 1.0},
        ]
        sop_pair = [
            {"instrument": "b flat clarinet", "family": FAMILY_CLARINETS, "pitch": 78.0, "overlap_ql": 1.0},
            {"instrument": "flute", "family": FAMILY_FLUTES, "pitch": 76.0, "overlap_ql": 1.0},
        ]
        self.assertEqual(verified_cross_timbral_boost(bass_pair, tm), 0.0)
        self.assertGreater(verified_cross_timbral_boost(sop_pair, tm), 0.0)

    def test_natural_horn_trumpet_narrow_not_modern_horn(self):
        tm = 2.0
        hist = [
            {"instrument": "natural horn", "family": FAMILY_BRASS, "pitch": 62.0, "overlap_ql": 1.0},
            {"instrument": "trumpet", "family": FAMILY_BRASS, "pitch": 65.0, "overlap_ql": 1.0},
        ]
        modern = [
            {"instrument": "horn", "family": FAMILY_BRASS, "pitch": 62.0, "overlap_ql": 1.0},
            {"instrument": "trumpet", "family": FAMILY_BRASS, "pitch": 65.0, "overlap_ql": 1.0},
        ]
        self.assertGreater(verified_cross_timbral_boost(hist, tm), 0.0)
        self.assertEqual(verified_cross_timbral_boost(modern, tm), 0.0)


class TestPercussionRegisterHandling(unittest.TestCase):
    def _feat(self, slices: list[dict]) -> dict:
        """Minimal features for compute_H_timbral percussion register branch."""
        tot = sum(float(s["ol"]) for s in slices)
        pitches = [float(s["p"]) for s in slices]
        pe = [
            {
                "instrument": s["i"],
                "pitch": float(s["p"]),
                "technique": "ordinario",
                "overlap_ql": float(s["ol"]),
            }
            for s in slices
        ]
        pm = tot
        pun = sum(float(s["ol"]) for s in slices if get_percussion_meta(s["i"]).pitch_status == PitchStatus.UNPITCHED)
        pp = sum(
            float(s["ol"])
            for s in slices
            if get_percussion_meta(s["i"]).pitch_status in (PitchStatus.PITCHED, PitchStatus.QUASI_PITCHED)
        )
        reg_span = [float(s["p"]) for s in slices if get_percussion_meta(s["i"]).pitch_status != PitchStatus.UNPITCHED]
        return {
            "pitches": np.array(pitches, dtype=float),
            "register_span_pitches": np.array(reg_span, dtype=float) if reg_span else np.array([], dtype=float),
            "instruments": {s["i"] for s in slices},
            "families": {FAMILY_PERCUSSION},
            "n_notes": len(slices),
            "n_instruments": len({s["i"] for s in slices}),
            "n_families": 1,
            "string_events": [],
            "string_overlap_mass": 0.0,
            "brass_events": [],
            "brass_overlap_mass": 0.0,
            "flute_events": [],
            "flute_overlap_mass": 0.0,
            "clarinet_events": [],
            "clarinet_overlap_mass": 0.0,
            "double_reed_events": [],
            "double_reed_overlap_mass": 0.0,
            "saxophone_events": [],
            "saxophone_overlap_mass": 0.0,
            "percussion_events": pe,
            "percussion_overlap_mass": pm,
            "percussion_unpitched_overlap_mass": pun,
            "percussion_pitched_overlap_mass": pp,
            "total_overlap_mass": tot,
            "timbral_note_slices": [
                {
                    "instrument": s["i"],
                    "family": FAMILY_PERCUSSION,
                    "pitch": float(s["p"]),
                    "overlap_ql": float(s["ol"]),
                }
                for s in slices
            ],
        }

    def test_unpitched_pair_not_driven_by_absurd_pitch_span(self):
        an = object.__new__(TimbralHomogeneityAnalyzer)
        an._timbral_config = get_timbral_config()
        # Snare + bass drum with wildly different placeholder MIDI ps (if any); unpitched excluded from span.
        f = self._feat(
            [
                {"i": "snare drum", "p": 60.0, "ol": 1.0},
                {"i": "bass drum", "p": 40.0, "ol": 1.0},
            ]
        )
        h = an.compute_H_timbral(f)
        self.assertGreater(h, 0.45)

    def test_xylo_marimba_uses_pitch_span(self):
        an = object.__new__(TimbralHomogeneityAnalyzer)
        an._timbral_config = get_timbral_config()
        f = self._feat(
            [
                {"i": "xylophone", "p": 72.0, "ol": 1.0},
                {"i": "marimba", "p": 60.0, "ol": 1.0},
            ]
        )
        h = an.compute_H_timbral(f)
        self.assertGreater(h, 0.42)

    def test_timpani_only_span_sensible(self):
        an = object.__new__(TimbralHomogeneityAnalyzer)
        an._timbral_config = get_timbral_config()
        f = self._feat(
            [
                {"i": "timpani", "p": 50.0, "ol": 1.0},
                {"i": "timpani", "p": 56.0, "ol": 1.0},
            ]
        )
        h = an.compute_H_timbral(f)
        self.assertGreater(h, 0.55)

    def test_mixed_pitched_and_unpitched_percussion(self):
        an = object.__new__(TimbralHomogeneityAnalyzer)
        an._timbral_config = get_timbral_config()
        f = self._feat(
            [
                {"i": "snare drum", "p": 60.0, "ol": 1.0},
                {"i": "timpani", "p": 52.0, "ol": 1.0},
            ]
        )
        h = an.compute_H_timbral(f)
        self.assertGreater(h, 0.35)
