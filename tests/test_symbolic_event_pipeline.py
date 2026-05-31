"""Unit tests for symbolic score event pipeline modules."""

from __future__ import annotations

from music21 import instrument, meter, note, stream

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.symbolic_event_pipeline import build_symbolic_score_events
from homogeneity_analyser.analyzers.symbolic_instrument_resolve import effective_instrument_for_note
from homogeneity_analyser.analyzers.symbolic_score_analyzer import SymbolicScoreAnalyzer
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer


def _part_with_flute_piccolo() -> stream.Part:
    p = stream.Part(id="Fl2")
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, instrument.Flute())
    p.insert(0, note.Note("C4", quarterLength=1.0))
    p.insert(1.0, instrument.Piccolo())
    p.insert(1.0, note.Note("C4", quarterLength=1.0))
    p.makeMeasures(inPlace=True)
    return p


def _score_with_flute_piccolo() -> stream.Score:
    sc = stream.Score()
    sc.insert(0, _part_with_flute_piccolo())
    return sc


def _direct_events(sc: stream.Score) -> list:
    return build_symbolic_score_events(
        sc,
        pitch_interpretation_mode="musicxml_sounding",
        harmonic_pitch_policy="natural_only",
    )


def test_effective_instrument_for_note_matches_pipeline_events() -> None:
    part = _part_with_flute_piccolo()
    n0 = part.flatten().notes[0]
    n1 = part.flatten().notes[1]
    inst0, fam0, src0, _ = effective_instrument_for_note(n0, part)
    inst1, fam1, src1, _ = effective_instrument_for_note(n1, part)
    assert inst0 == "flute"
    assert inst1 == "piccolo"
    assert src1 == "note_context"
    assert fam0 == fam1


def test_symbolic_score_analyzer_events_match_direct_pipeline() -> None:
    sc = _score_with_flute_piccolo()
    direct = _direct_events(sc)
    via_base = SymbolicScoreAnalyzer(
        music21_score=sc,
        time_step=0.5,
        pitch_interpretation_mode="musicxml_sounding",
        harmonic_pitch_policy="natural_only",
    )
    assert len(direct) == len(via_base.score_events) == 2
    for a, b in zip(direct, via_base.score_events, strict=True):
        assert a["instrument"] == b["instrument"]
        assert a["pitches"] == b["pitches"]
        assert a["technique_uniformity_key"] == b["technique_uniformity_key"]


def test_hti_analyzer_does_not_subclass_timbral() -> None:
    assert not issubclass(SymbolicTIHomogeneityAnalyzer, TimbralHomogeneityAnalyzer)
    assert issubclass(SymbolicTIHomogeneityAnalyzer, SymbolicScoreAnalyzer)


def test_hti_and_timbral_analyzers_share_same_event_list() -> None:
    sc = _score_with_flute_piccolo()
    direct = _direct_events(sc)
    hti = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=0.5,
        pitch_interpretation_mode="musicxml_sounding",
        harmonic_pitch_policy="natural_only",
    )
    timbral = TimbralHomogeneityAnalyzer(
        music21_score=sc,
        time_step=0.5,
        pitch_interpretation_mode="musicxml_sounding",
        harmonic_pitch_policy="natural_only",
    )
    for events in (hti.score_events, timbral.score_events):
        assert len(direct) == len(events) == 2
        for a, b in zip(direct, events, strict=True):
            assert a["instrument"] == b["instrument"]
            assert a["pitches"] == b["pitches"]
            assert a["technique_uniformity_key"] == b["technique_uniformity_key"]
