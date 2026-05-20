"""
Rigorous audit-style tests: taxonomy safety, technique-state parsing, persistence, H_timbral outputs.

Musical / policy assumption tags (use on any test that embeds a non-obvious scoring choice):

- **confirmed musical convention** — widely used in orchestral parts / pedagogy (still symbolic-only here).
- **project-specific convention** — deliberate Homogeneity_analyser rule (taxonomy, IDs, API), not universal law.
- **ambiguous but intentionally accepted** — multiple real-world readings exist; this test locks the chosen one.
- **provisional / needs corpus validation** — reasonable default; should be checked against a wider MusicXML corpus.

Symbolic input only (music21 / MusicXML); no PDF or image “recognition”.
"""

from __future__ import annotations

import pytest

import copy
import tempfile
from pathlib import Path

from music21 import expressions, instrument, meter, note, stream

from homogeneity_analyser.analyzers.technique_state import (
    TechniqueStateContext,
    apply_persistent_text,
    merge_note_technique_state,
    normalize_technique_text,
    technique_state_id,
)
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OTHER,
    FAMILY_PERCUSSION,
    FAMILY_STRINGS,
    FAMILY_VOICE,
    get_alias_collision_log,
    get_instrument_and_family,
)

ALLOWED_ALIAS_COLLISION_KEYS: frozenset[str] = frozenset()


def _analyzer_from_score(sc: stream.Score) -> TimbralHomogeneityAnalyzer:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "score.musicxml"
        sc.write("musicxml", fp=str(path))
        return TimbralHomogeneityAnalyzer(str(path))


def test_alias_collision_log_only_allowlisted():
    """Classification: **project-specific convention** (alias collision policy for taxonomy builds)."""
    for row in get_alias_collision_log():
        assert row[0] in ALLOWED_ALIAS_COLLISION_KEYS, row


@pytest.mark.parametrize(
    "raw,canon,fam",
    [
        # Conservative fallback: not a tin-whistle alias inside a longer phrase.
        ("jet whistle", "jet whistle", FAMILY_OTHER),
        ("clarinetto", "clarinetto", FAMILY_OTHER),
        ("cornett", "cornett", FAMILY_BRASS),
        # "cornetto" → modern cornet (PT/IT naming). Historical cornett is "cornett"; scores may still use
        # "cornetto" for early music — disambiguation is by part naming practice, not score analysis here.
        ("cornetto", "cornet", FAMILY_BRASS),
        ("classical guitar", "guitar", FAMILY_STRINGS),
    ],
)
def test_taxonomy_no_unsafe_substring_instrument_matches(raw, canon, fam):
    """
    Classification (per case): **ambiguous but intentionally accepted** (jet whistle, clarinetto → unknown);
    **project-specific convention** (cornetto→cornet; cornett kept); **confirmed musical convention**
    (classical guitar → guitar, not clarinet substring).
    """
    inst, got_fam = get_instrument_and_family(raw)
    assert inst == canon
    assert got_fam == fam


@pytest.mark.parametrize(
    "a,b",
    [
        ("bouché", "bouche"),
        ("BOUCHÉ", "bouche"),
        ("bouchés", "bouches"),
        ("sul pont.", "sul pont"),
        ("sul-pont.", "sul pont"),
        ("Sul Ponticello", "sul ponticello"),
        ("fl.", "fl"),
        ("FL", "fl"),
        ("flauta", "flauta"),
        ("Flauta", "flauta"),
        ("órgão", "orgao"),
        ("orgao", "orgao"),
        ("Org.", "org"),
    ],
)
def test_technique_text_normalisation_equivalence_branches(a, b):
    """Classification: **project-specific convention** (normalisation contract for technique strings)."""
    assert normalize_technique_text(a) == normalize_technique_text(b)


def test_decomposed_accent_normalisation_still_matches():
    """Classification: **project-specific convention** (NFD vs composed accents must normalise identically here)."""
    s = "bouche\u0301s"
    assert normalize_technique_text(s) == normalize_technique_text("bouchés")


def test_brass_plus_stopped_only_as_isolated_plus_sign():
    """
    Classification: **ambiguous but intentionally accepted**. In universal notation, '+' is not always
    stopped horn; here it means stopped **only** when parsed as brass technique text (this test) or the
    same `_apply_brass_direction` path in full scores — not in arbitrary non-brass strings (e.g. 'a + b').
    """
    ctx = TechniqueStateContext(family=FAMILY_BRASS, instrument="horn")
    apply_persistent_text("a + b", ctx)
    assert ctx.brass_primary == "open"
    ctx2 = TechniqueStateContext(family=FAMILY_BRASS, instrument="horn")
    apply_persistent_text("+", ctx2)
    assert ctx2.brass_primary == "stopped"


def test_clarinet_bisbigliando_distinct_lane_from_multiphonic():
    """
    Classification: **ambiguous but intentionally accepted**. Composers and texts blur bisbigliando vs
    multiphonic; this project keeps separate lanes for timbral distribution clarity.
    """
    ctx = TechniqueStateContext(family=FAMILY_CLARINETS, instrument="clarinet")
    apply_persistent_text("bisbigliando", ctx)
    st = merge_note_technique_state(ctx, note.Note("D4"), instrument="clarinet", family=FAMILY_CLARINETS)
    assert "bisbigliando" in technique_state_id("clarinet", FAMILY_CLARINETS, st)
    ctx2 = TechniqueStateContext(family=FAMILY_CLARINETS, instrument="clarinet")
    apply_persistent_text("multiphonic", ctx2)
    st2 = merge_note_technique_state(ctx2, note.Note("D4"), instrument="clarinet", family=FAMILY_CLARINETS)
    assert "multiphonic" in technique_state_id("clarinet", FAMILY_CLARINETS, st2)


def test_flute_jet_whistle_lane():
    """Classification: **confirmed musical convention** (standard extended technique label 'jet whistle')."""
    ctx = TechniqueStateContext(family=FAMILY_FLUTES, instrument="flute")
    apply_persistent_text("jet whistle", ctx)
    st = merge_note_technique_state(ctx, note.Note("C5"), instrument="flute", family=FAMILY_FLUTES)
    assert "jet_whistle" in technique_state_id("flute", FAMILY_FLUTES, st)


def test_percussion_superball_beater():
    """Classification: **provisional / needs corpus validation** (beater taxonomy and wording in scores)."""
    ctx = TechniqueStateContext(family=FAMILY_PERCUSSION, instrument="percussion")
    apply_persistent_text("superball", ctx)
    st = ctx.to_state()
    assert st.beater == "superball"
    assert "superball" in technique_state_id("percussion", FAMILY_PERCUSSION, st)


def test_suspended_cymbal_resonance_in_technique_state_id():
    """Classification: **confirmed musical convention** (let ring / damping directions on cymbals)."""
    ctx = TechniqueStateContext(family=FAMILY_PERCUSSION, instrument="suspended cymbal")
    apply_persistent_text("let ring", ctx)
    st = merge_note_technique_state(ctx, note.Note("C4"), instrument="suspended cymbal", family=FAMILY_PERCUSSION)
    tid = technique_state_id("suspended cymbal", FAMILY_PERCUSSION, st)
    assert "let_ring" in tid


def test_violin_diamond_notehead_harmonic_heuristic():
    """
    Symbolic heuristic (not guaranteed truth): diamond noteheads are often used for string harmonics,
    but editors vary; this only reflects music21 notehead + our merge rules, not acoustic verification.
    """
    ctx = TechniqueStateContext(family=FAMILY_STRINGS, instrument="violin")
    n = note.Note("G4")
    n.notehead = "diamond"
    st = merge_note_technique_state(copy.copy(ctx), n, instrument="violin", family=FAMILY_STRINGS)
    tid = technique_state_id("violin", FAMILY_STRINGS, st)
    assert "harmonic" in tid


def test_string_battuto_alone_not_col_legno():
    """
    Classification: **confirmed musical convention**. 'Battuto' alone is ambiguous; col legno battuto is
    not implied without 'col legno' / 'legno …' phrasing in this project's parser.
    """
    ctx = TechniqueStateContext(family="strings", instrument="violin")
    ctx.family = "strings"
    apply_persistent_text("battuto", ctx)
    st = merge_note_technique_state(ctx, note.Note("G4"), instrument="violin", family="strings")
    assert "col_legno" not in technique_state_id("violin", "strings", st)


def test_horn_stopped_then_open_persistence_five_notes():
    """
    Classification: **confirmed musical convention** (text directions persist until contradicted), with
    **provisional / needs corpus validation** on exact same-offset ordering when exported via MusicXML.
    """
    p = stream.Part()
    p.insert(0, instrument.Horn())
    p.insert(0, meter.TimeSignature("4/4"))
    m1 = stream.Measure()
    m1.insert(0, expressions.TextExpression("bouché"))
    m1.insert(0, note.Note("F4", quarterLength=4.0))
    m2 = stream.Measure()
    m2.insert(0, note.Note("F4", quarterLength=4.0))
    m3 = stream.Measure()
    m3.insert(0, note.Note("F4", quarterLength=4.0))
    m4 = stream.Measure()
    m4.insert(0, expressions.TextExpression("open"))
    m4.insert(0, note.Note("F4", quarterLength=4.0))
    m5 = stream.Measure()
    m5.insert(0, note.Note("F4", quarterLength=4.0))
    p.append(m1)
    p.append(m2)
    p.append(m3)
    p.append(m4)
    p.append(m5)
    sc = stream.Score()
    sc.append(p)
    an = _analyzer_from_score(sc)
    ev = an._events
    assert len(ev) == 5
    for i in range(3):
        assert "stopped" in ev[i]["technique_state_id"]
    for i in range(3, 5):
        assert "open" in ev[i]["technique_state_id"]


def test_trumpet_mute_persistence_con_sord_senza_unit_context():
    """Classification: **confirmed musical convention** (con sord. / senza sord. as mute state text)."""
    ctx = TechniqueStateContext(family=FAMILY_BRASS, instrument="trumpet")
    apply_persistent_text("con sord.", ctx)
    n = note.Note("C5")
    st1 = merge_note_technique_state(copy.copy(ctx), n, instrument="trumpet", family=FAMILY_BRASS)
    st2 = merge_note_technique_state(copy.copy(ctx), n, instrument="trumpet", family=FAMILY_BRASS)
    assert "muted" in technique_state_id("trumpet", FAMILY_BRASS, st1).lower()
    assert technique_state_id("trumpet", FAMILY_BRASS, st1) == technique_state_id("trumpet", FAMILY_BRASS, st2)
    apply_persistent_text("senza sord.", ctx)
    st3 = merge_note_technique_state(copy.copy(ctx), n, instrument="trumpet", family=FAMILY_BRASS)
    tid = technique_state_id("trumpet", FAMILY_BRASS, st3)
    assert "muted_generic" not in tid


def test_timbral_window_output_keys_and_time_series():
    """Classification: **project-specific convention** (feature keys and time-series shape of H_timbral)."""
    sc = stream.Score()
    for _ in range(4):
        p = stream.Part()
        p.insert(0, instrument.Horn())
        p.insert(0, meter.TimeSignature("4/4"))
        m = stream.Measure()
        m.insert(0, note.Note("F4", quarterLength=4.0))
        p.append(m)
        sc.append(p)
    an = _analyzer_from_score(sc)
    f = an.extract_timbral_features(2.0, 4.0)
    assert f is not None
    assert "timbral_state_distribution" in f
    assert "dominant_timbral_state" in f
    assert "timbral_state_concentration" in f
    h = an.compute_H_timbral(f)
    assert 0.0 <= h <= 1.0
    ts = an.analyze_timbral(window_size=4.0)
    assert "H_timbral" in ts and "t" in ts
    assert len(ts["H_timbral"]) == len(ts["t"])
    assert "timbral_state_distribution" in ts
    assert "dominant_timbral_state" in ts
    assert "timbral_state_concentration" in ts
    assert len(ts["timbral_state_distribution"]) == len(ts["t"])


def test_ambiguous_voice_labels_not_mapped_to_winds():
    """
    Project-specific convention: bare "alto", "tenor", "baritone" (no "saxophone" / "flute" / etc.) are
    treated as **voice** roles, not as instrumental aliases — avoids mapping e.g. "Alto" wind parts
    without clearer part names. Use "alto saxophone", "alto flute", etc. when that is what you mean.
    """
    inst_a, fam_a = get_instrument_and_family("alto")
    inst_t, fam_t = get_instrument_and_family("tenor")
    inst_b, fam_b = get_instrument_and_family("baritone")
    assert fam_a == FAMILY_VOICE
    assert fam_t == FAMILY_VOICE
    assert fam_b == FAMILY_VOICE
    assert inst_a == "alto"
    assert inst_t == "tenor"
    assert inst_b == "baritone"
