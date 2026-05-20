"""
Chronological persistent technique state vs same-measure text safety.

**Project-specific convention:** ``notation_text_context_for_note(..., measure_text="prior")`` uses
strict offsets; ``timbral`` uses ``measure_text="none"`` and relies on ``iter_timbral_elements``.
"""

from __future__ import annotations

from music21 import expressions, instrument, note, stream

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.analyzers.technique_state import (
    TechniqueStateContext,
    apply_persistent_text,
    merge_note_technique_state,
    technique_state_id,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BRASS


def _sc(part: stream.Part) -> stream.Score:
    s = stream.Score()
    s.insert(0, part)
    return s


def test_horn_bouche_persists_until_open():
    p = stream.Part()
    p.insert(0, instrument.Horn())
    m = stream.Measure()
    m.insert(0, expressions.TextExpression("bouché"))
    m.insert(0, note.Note("F4", quarterLength=1.0))
    m.insert(1.0, note.Note("G4", quarterLength=1.0))
    m.insert(2.0, note.Note("A4", quarterLength=1.0))
    m.insert(3.0, expressions.TextExpression("open"))
    m.insert(3.0, note.Note("B4", quarterLength=1.0))
    m.insert(4.0, note.Note("C5", quarterLength=1.0))
    p.insert(0, m)

    an = TimbralHomogeneityAnalyzer(music21_score=_sc(p), time_step=0.25)
    ids = [e["technique_state_id"] for e in an._events]
    assert ids[0] == "horn|stopped"
    assert ids[1] == "horn|stopped"
    assert ids[2] == "horn|stopped"
    assert ids[3] == "horn|open"
    assert ids[4] == "horn|open"


def test_violin_pizz_persists_until_arco():
    p = stream.Part()
    p.insert(0, instrument.Violin())
    m = stream.Measure()
    m.insert(0, expressions.TextExpression("pizz."))
    m.insert(0, note.Note("G3", quarterLength=1.0))
    m.insert(1.0, note.Note("A3", quarterLength=1.0))
    m.insert(2.0, expressions.TextExpression("arco"))
    m.insert(2.0, note.Note("B3", quarterLength=1.0))
    m.insert(3.0, note.Note("C4", quarterLength=1.0))
    p.insert(0, m)

    an = TimbralHomogeneityAnalyzer(music21_score=_sc(p), time_step=0.25)
    ids = [e["technique_state_id"] for e in an._events]
    assert all("pizz" in x for x in ids[:2])
    assert all("arco" in x and "pizz" not in x for x in ids[2:])


def test_violin_sul_pont_persists_until_ord():
    p = stream.Part()
    p.insert(0, instrument.Violin())
    m = stream.Measure()
    m.insert(0, expressions.TextExpression("sul pont."))
    m.insert(0, note.Note("D4", quarterLength=1.0))
    m.insert(1.0, note.Note("E4", quarterLength=1.0))
    m.insert(2.0, expressions.TextExpression("ord."))
    m.insert(2.0, note.Note("F4", quarterLength=1.0))
    m.insert(3.0, note.Note("G4", quarterLength=1.0))
    p.insert(0, m)

    an = TimbralHomogeneityAnalyzer(music21_score=_sc(p), time_step=0.25)
    ids = [e["technique_state_id"] for e in an._events]
    assert all("sul_pont" in x for x in ids[:2])
    assert all("sul_pont" not in x for x in ids[2:])


def test_trumpet_con_sord_senza_sord_persistence():
    p = stream.Part()
    p.insert(0, instrument.Trumpet())
    m = stream.Measure()
    m.insert(0, expressions.TextExpression("con sord."))
    m.insert(0, note.Note("C5", quarterLength=1.0))
    m.insert(1.0, note.Note("D5", quarterLength=1.0))
    m.insert(2.0, expressions.TextExpression("senza sord."))
    m.insert(2.0, note.Note("E5", quarterLength=1.0))
    m.insert(3.0, note.Note("F5", quarterLength=1.0))
    p.insert(0, m)

    an = TimbralHomogeneityAnalyzer(music21_score=_sc(p), time_step=0.25)
    ids = [e["technique_state_id"] for e in an._events]
    assert all("muted" in x or "open" in x for x in ids)
    assert all("muted_generic" in x for x in ids[:2])
    assert all("muted_generic" not in x for x in ids[2:])


def test_same_measure_later_direction_not_retroactive_in_notation_blob():
    m = stream.Measure()
    m.insert(0, note.Note("C4", quarterLength=1.0))
    m.insert(2.0, expressions.TextExpression("pizz."))
    n_early = m.notes[0]
    blob_prior = notation_text_context_for_note(n_early, measure_text="prior")
    assert "pizz" not in blob_prior
    blob_legacy = notation_text_context_for_note(n_early, measure_text="legacy")
    assert "pizz" in blob_legacy


def test_trumpet_harmon_stem_out_state_id():
    c = TechniqueStateContext(family=FAMILY_BRASS, instrument="trumpet")
    apply_persistent_text("harmon mute stem out", c)
    st = merge_note_technique_state(c, note.Note("C5"), instrument="trumpet", family=FAMILY_BRASS)
    tid = technique_state_id("trumpet", FAMILY_BRASS, st)
    assert tid == "trumpet|harmon_mute|stem_out"


def test_violin_note_local_expression_does_not_persist_to_next_note():
    """Note-only ``TextExpression`` (``measure_text='none'``) must not advance timeline context."""
    p = stream.Part()
    p.insert(0, instrument.Violin())
    m = stream.Measure()
    n1 = note.Note("G3", quarterLength=1.0)
    n1.expressions.append(expressions.TextExpression("sul tasto"))
    m.insert(0, n1)
    m.insert(1.0, note.Note("A3", quarterLength=1.0))
    p.insert(0, m)

    an = TimbralHomogeneityAnalyzer(music21_score=_sc(p), time_step=0.25)
    ids = [e["technique_state_id"] for e in an._events]
    assert any(x in ids[0] for x in ("sul_tasto", "molto_sul_tasto"))
    assert all(x not in ids[1] for x in ("sul_tasto", "molto_sul_tasto"))
