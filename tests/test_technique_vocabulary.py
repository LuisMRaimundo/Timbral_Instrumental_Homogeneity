"""
Unit tests for :mod:`homogeneity_analyser.analyzers.technique_state` symbolic vocabulary
(MusicXML / music21 text and articulations only).

Assumption tags (per test docstring):
**confirmed musical convention** | **project-specific convention** |
**ambiguous but intentionally accepted** | **provisional / needs corpus validation**
"""

from __future__ import annotations

import copy

from music21 import note

from homogeneity_analyser.analyzers.clarinet_technique import (
    CLARINET_BISBIGLIANDO,
    CLARINET_MULTIPHONIC,
    clarinet_technique_from_note,
)
from homogeneity_analyser.analyzers.flute_technique import (
    FLUTE_JET_WHISTLE,
    FLUTE_UNKNOWN,
    flute_technique_from_note,
)
from homogeneity_analyser.analyzers.technique_state import (
    TechniqueStateContext,
    apply_persistent_text,
    merge_note_technique_state,
    technique_state_id,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_PERCUSSION,
    FAMILY_STRINGS,
)


def test_brass_cuivre_horn_state():
    """Classification: **confirmed musical convention** (cuivré / bell-up brass colour on horn)."""
    ctx = TechniqueStateContext(family=FAMILY_BRASS, instrument="horn")
    apply_persistent_text("cuivré horn", ctx)
    st = merge_note_technique_state(ctx, note.Note("F4"), instrument="horn", family=FAMILY_BRASS)
    assert st.primary == "cuivre"
    assert "cuivre" in technique_state_id("horn", FAMILY_BRASS, st)


def test_brass_isolated_plus_stopped_horn():
    """Classification: **confirmed musical convention** ('+' as stopped horn in isolated brass directions)."""
    ctx = TechniqueStateContext(family=FAMILY_BRASS, instrument="horn")
    apply_persistent_text("+", ctx)
    assert ctx.brass_primary == "stopped"


def test_brass_plus_inside_unrelated_text_not_stopped():
    """
    Classification: **project-specific convention**. Only an isolated '+' token (after normalisation)
    denotes stopped horn; '+' embedded in other wording does not.
    """
    ctx = TechniqueStateContext(family=FAMILY_BRASS, instrument="horn")
    apply_persistent_text("2 + 2 = 4", ctx)
    assert ctx.brass_primary == "open"


def test_wind_jet_whistle_distinct_from_whistle_tone():
    """Classification: **confirmed musical convention** (jet whistle vs ordinary whistle tone as distinct labels)."""
    ctx_j = TechniqueStateContext(family=FAMILY_FLUTES, instrument="flute")
    apply_persistent_text("jet whistle", ctx_j)
    assert ctx_j.wind_lane == "jet_whistle"
    ctx_w = TechniqueStateContext(family=FAMILY_FLUTES, instrument="flute")
    apply_persistent_text("whistle tone", ctx_w)
    assert ctx_w.wind_lane == "whistle_tone"


def test_clarinet_bisbigliando_keyword_distinct_from_multiphonic():
    """
    Classification: **confirmed musical convention** (bisbigliando is its own extended technique class);
    keyword helper must not collapse it into multiphonic.
    """
    n2 = note.Note("D4")
    n2.lyric = "bisbigliando"
    assert clarinet_technique_from_note(n2, family=FAMILY_CLARINETS) == CLARINET_BISBIGLIANDO
    n3 = note.Note("D4")
    n3.lyric = "multiphonic"
    assert clarinet_technique_from_note(n3, family=FAMILY_CLARINETS) == CLARINET_MULTIPHONIC


def test_flute_a2_not_ordinario_from_keywords():
    """
    Classification: **confirmed musical convention**. 'a2' marks both players (or similar ensemble marking);
    it must not be read as an airy / open-flute reset via flute keyword heuristics.
    """
    n = note.Note("C5")
    n.lyric = "a2"
    assert flute_technique_from_note(n, family=FAMILY_FLUTES) == FLUTE_UNKNOWN


def test_flute_jet_whistle_keyword_before_whistle_tone(monkeypatch):
    """Classification: **confirmed musical convention** (jet whistle must win over generic whistle parsing)."""

    def _blob_jet(_n):
        return "jet whistle"

    monkeypatch.setattr(
        "homogeneity_analyser.analyzers.flute_technique.notation_text_context_for_note",
        _blob_jet,
    )
    n = note.Note("C5")
    assert flute_technique_from_note(n, family=FAMILY_FLUTES) == FLUTE_JET_WHISTLE


def test_string_battuto_alone_not_col_legno_vocabulary():
    """
    Classification: **confirmed musical convention**. Bare 'battuto' is not col legno without
    'col legno' / 'legno' wording (**ambiguous but intentionally accepted** parser boundary).
    """
    ctx = TechniqueStateContext(family=FAMILY_STRINGS, instrument="violin")
    apply_persistent_text("battuto", ctx)
    st = merge_note_technique_state(ctx, note.Note("G4"), instrument="violin", family=FAMILY_STRINGS)
    assert st.excitation != "col_legno_battuto"
    assert "col_legno" not in technique_state_id("violin", FAMILY_STRINGS, st)


def test_string_col_legno_bare_defaults_to_battuto():
    """
    Classification: **ambiguous but intentionally accepted**. Unqualified 'col legno' is mapped to
    col legno battuto as a practical default until a score-specific cue appears.
    """
    ctx = TechniqueStateContext(family=FAMILY_STRINGS, instrument="violin")
    apply_persistent_text("col legno", ctx)
    st = merge_note_technique_state(ctx, note.Note("G4"), instrument="violin", family=FAMILY_STRINGS)
    assert st.excitation == "col_legno_battuto"


def test_string_diamond_notehead_harmonic_heuristic():
    """
    Classification: **provisional / needs corpus validation**. Diamond noteheads often indicate harmonics
    in string parts, but editors differ; this is the documented music21 notehead heuristic only.
    """
    ctx = TechniqueStateContext(family=FAMILY_STRINGS, instrument="violin")
    n = note.Note("G4")
    n.notehead = "diamond"
    st = merge_note_technique_state(copy.copy(ctx), n, instrument="violin", family=FAMILY_STRINGS)
    assert "harmonic" in technique_state_id("violin", FAMILY_STRINGS, st)


def test_percussion_superball_let_ring_damped_vocabulary():
    """Classification: **provisional / needs corpus validation** (free-text beater / resonance wording)."""
    ctx_sb = TechniqueStateContext(family=FAMILY_PERCUSSION, instrument="marimba")
    apply_persistent_text("superball", ctx_sb)
    assert ctx_sb.to_state().beater == "superball"

    ctx_lr = TechniqueStateContext(family=FAMILY_PERCUSSION, instrument="suspended cymbal")
    apply_persistent_text("let ring", ctx_lr)
    assert ctx_lr.to_state().resonance == "let_ring"

    ctx_dm = TechniqueStateContext(family=FAMILY_PERCUSSION, instrument="cymbal")
    apply_persistent_text("damped", ctx_dm)
    assert ctx_dm.to_state().resonance == "damped"


def test_wind_a2_direction_text_is_no_op_for_lane():
    """
    Classification: **confirmed musical convention** ('a2' as ensemble marking, not a timbral air cue).
    """
    ctx = TechniqueStateContext(family=FAMILY_FLUTES, instrument="flute")
    ctx.wind_lane = "flutter"
    apply_persistent_text("a2", ctx)
    assert ctx.wind_lane == "flutter"
