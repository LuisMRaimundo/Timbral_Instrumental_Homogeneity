"""
Per-note instrument resolution for orchestral doublings (``timbral.TimbralHomogeneityAnalyzer``).

Uses in-memory ``music21`` scores via ``music21_score=`` because MusicXML round-trip often
drops mid-part ``Instrument`` inserts.

**Project-specific convention:** ``instrument_source`` tagging (``note_context`` vs part fallbacks).
"""

from __future__ import annotations

from music21 import instrument, meter, note, stream

from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OBOES,
    FAMILY_PERCUSSION,
)


def _score_with_part(part: stream.Part) -> stream.Score:
    sc = stream.Score()
    sc.insert(0, part)
    return sc


def test_flute_then_piccolo_different_canonical_and_sounding_pitch():
    p = stream.Part(id="Fl2")
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Flute())
    p.insert(0, note.Note("C4", quarterLength=1.0))
    p.insert(1.0, instrument.Piccolo())
    p.insert(1.0, note.Note("C4", quarterLength=1.0))
    p.makeMeasures(inPlace=True)

    an = TimbralHomogeneityAnalyzer(music21_score=_score_with_part(p), time_step=0.5)
    ev = [e for e in an._events if e["offset"] in (0.0, 1.0)]
    assert len(ev) == 2
    assert ev[0]["instrument"] == "flute"
    assert ev[1]["instrument"] == "piccolo"
    assert ev[1]["instrument_source"] == "note_context"
    assert ev[0]["pitches"] != ev[1]["pitches"]  # piccolo transposes sounding octave up


def test_oboe_then_cor_anglais():
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Oboe())
    p.insert(0, note.Note("A4", quarterLength=1.0))
    p.insert(1.0, instrument.EnglishHorn())
    p.insert(1.0, note.Note("G4", quarterLength=1.0))
    p.makeMeasures(inPlace=True)

    an = TimbralHomogeneityAnalyzer(music21_score=_score_with_part(p), time_step=0.5)
    ev = sorted([e for e in an._events], key=lambda e: e["offset"])
    assert ev[0]["instrument"] == "oboe"
    assert ev[0]["family"] == FAMILY_OBOES
    assert ev[1]["instrument"] == "cor anglais"
    assert ev[1]["family"] == FAMILY_OBOES
    assert ev[1]["instrument_source"] == "note_context"


def test_bassoon_then_contrabassoon():
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Bassoon())
    p.insert(0, note.Note("B3", quarterLength=1.0))
    p.insert(1.0, instrument.Contrabassoon())
    p.insert(1.0, note.Note("A2", quarterLength=1.0))
    p.makeMeasures(inPlace=True)

    an = TimbralHomogeneityAnalyzer(music21_score=_score_with_part(p), time_step=0.5)
    ev = sorted([e for e in an._events], key=lambda e: e["offset"])
    assert ev[0]["instrument"] == "bassoon"
    assert ev[1]["instrument"] == "contrabassoon"
    assert ev[0]["family"] == FAMILY_BASSOONS
    assert ev[1]["family"] == FAMILY_BASSOONS


def test_clarinet_then_bass_clarinet():
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Clarinet())
    p.insert(0, note.Note("D4", quarterLength=1.0))
    p.insert(1.0, instrument.BassClarinet())
    p.insert(1.0, note.Note("D3", quarterLength=1.0))
    p.makeMeasures(inPlace=True)

    an = TimbralHomogeneityAnalyzer(music21_score=_score_with_part(p), time_step=0.5)
    ev = sorted([e for e in an._events], key=lambda e: e["offset"])
    assert ev[0]["instrument"] == "clarinet"
    assert ev[0]["family"] == FAMILY_CLARINETS
    assert ev[1]["instrument"] == "bass clarinet"
    assert ev[1]["family"] == FAMILY_CLARINETS


def test_percussion_glockenspiel_then_cymbals_not_generic_percussion():
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Glockenspiel())
    p.insert(0, note.Note("C5", quarterLength=1.0))
    p.insert(1.0, instrument.Cymbals())
    p.insert(1.0, note.Note("D5", quarterLength=1.0))
    p.makeMeasures(inPlace=True)

    an = TimbralHomogeneityAnalyzer(music21_score=_score_with_part(p), time_step=0.5)
    ev = sorted([e for e in an._events], key=lambda e: e["offset"])
    assert ev[0]["instrument"] == "glockenspiel"
    assert ev[1]["instrument"] == "cymbal"
    assert ev[0]["family"] == FAMILY_PERCUSSION
    assert ev[1]["family"] == FAMILY_PERCUSSION
    assert "percussion" not in (ev[0]["instrument"], ev[1]["instrument"])


def test_single_flute_part_preserves_part_level_resolution():
    p = stream.Part(id="Fl1")
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Flute())
    p.insert(0, note.Note("C4", quarterLength=1.0))
    p.insert(1.0, note.Note("D4", quarterLength=1.0))
    p.makeMeasures(inPlace=True)

    an = TimbralHomogeneityAnalyzer(music21_score=_score_with_part(p), time_step=0.5)
    ev = an._events
    assert len(ev) == 2
    assert all(e["instrument"] == "flute" for e in ev)
    assert all(e["family"] == FAMILY_FLUTES for e in ev)
    assert {e["instrument_source"] for e in ev} <= {"part_context", "part_name_fallback"}


def test_timbral_note_slices_include_instrument_source():
    p = stream.Part()
    p.insert(0, instrument.Flute())
    p.insert(0, note.Note("C4", quarterLength=1.0))
    p.makeMeasures(inPlace=True)
    an = TimbralHomogeneityAnalyzer(music21_score=_score_with_part(p), time_step=0.5)
    feats = an.extract_timbral_features(0.5, 2.0)
    assert feats and feats["timbral_note_slices"]
    assert "instrument_source" in feats["timbral_note_slices"][0]


def test_H_timbral_sees_two_instruments_after_flute_piccolo_doubling():
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Flute())
    p.insert(0, note.Note("C4", quarterLength=1.0))
    p.insert(1.0, instrument.Piccolo())
    p.insert(1.0, note.Note("D4", quarterLength=1.0))
    p.makeMeasures(inPlace=True)

    an = TimbralHomogeneityAnalyzer(music21_score=_score_with_part(p), time_step=0.25)
    feats = an.extract_timbral_features(1.0, 2.5)
    assert feats is not None
    assert feats["n_instruments"] == 2
    assert "flute" in feats["instruments"] and "piccolo" in feats["instruments"]
