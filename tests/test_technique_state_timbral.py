"""
Technique-state tracking and H_timbral behaviour (symbolic MusicXML / music21).

Assumption tags (see also ``test_audit_rigorous_timbral`` module docstring):
**confirmed musical convention** | **project-specific convention** |
**ambiguous but intentionally accepted** | **provisional / needs corpus validation**
"""

from __future__ import annotations

import pytest

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
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BRASS, FAMILY_CLARINETS, FAMILY_STRINGS


def _analyzer_from_score(sc: stream.Score) -> TimbralHomogeneityAnalyzer:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "score.musicxml"
        sc.write("musicxml", fp=str(path))
        return TimbralHomogeneityAnalyzer(str(path))


def _horn_part(mark: str | None) -> stream.Part:
    p = stream.Part()
    p.insert(0, instrument.Horn())
    p.insert(0, meter.TimeSignature("4/4"))
    m = stream.Measure()
    if mark:
        m.insert(0, expressions.TextExpression(mark))
        m.insert(1, note.Note("F4", quarterLength=4.0))
    else:
        m.insert(0, note.Note("F4", quarterLength=4.0))
    p.append(m)
    return p


def _horn_score_4(mark: str | None) -> stream.Score:
    sc = stream.Score()
    for _ in range(4):
        sc.append(_horn_part(mark))
    return sc


def _horn_score_mixed(marks: tuple[str | None, str | None, str | None, str | None]) -> stream.Score:
    sc = stream.Score()
    for mk in marks:
        sc.append(_horn_part(mk))
    return sc


def _h_center(an: TimbralHomogeneityAnalyzer, center: float = 2.0, width: float = 4.0) -> float:
    f = an.extract_timbral_features(center, width)
    return an.compute_H_timbral(f)


@pytest.mark.parametrize(
    "raw,needle",
    [
        ("Bouché", "bouche"),
        ("gestopft", "gestopft"),
        ("sons bouchés", "sons bouch"),
        ("cuivré", "cuivre"),
    ],
)
def test_normalize_technique_text_brass_aliases(raw, needle):
    """Classification: **confirmed musical convention** (common FR/DE/EN direction wording for brass)."""
    n = normalize_technique_text(raw)
    assert needle in n


def test_text_to_horn_stopped_state_id():
    """Classification: **confirmed musical convention** (bouché / stopped horn family)."""
    ctx = TechniqueStateContext(family=FAMILY_BRASS, instrument="horn")
    apply_persistent_text("bouché", ctx)
    n = note.Note("F4")
    st = merge_note_technique_state(ctx, n, instrument="horn", family=FAMILY_BRASS)
    assert technique_state_id("horn", FAMILY_BRASS, st) == "horn|stopped"


def test_text_to_horn_cuivre_state_id():
    """Classification: **confirmed musical convention** (cuivré / brassy bell-up family)."""
    ctx = TechniqueStateContext(family=FAMILY_BRASS, instrument="horn")
    apply_persistent_text("cuivré", ctx)
    n = note.Note("F4")
    st = merge_note_technique_state(ctx, n, instrument="horn", family=FAMILY_BRASS)
    assert technique_state_id("horn", FAMILY_BRASS, st) == "horn|cuivre"


def test_senza_sord_does_not_clear_stopped_primary():
    """
    Classification: **ambiguous but intentionally accepted**. 'Senza sord.' is primarily a mute directive;
    it does not cancel hand-stopped horn here (some scores might bundle both; this parser keeps primary).
    """
    ctx = TechniqueStateContext(family=FAMILY_BRASS, instrument="horn")
    apply_persistent_text("bouché", ctx)
    apply_persistent_text("senza sord.", ctx)
    assert ctx.brass_primary == "stopped"
    assert ctx.brass_mute == "none"


def test_brass_uniform_states_high_h_and_single_distribution():
    """
    Classification: **provisional / needs corpus validation** (numeric floor 0.85 and window centre 2.0 /
    width 4.0 are regression anchors, not music-theory constants).
    """
    h_open = _h_center(_analyzer_from_score(_horn_score_4(None)))
    h_st = _h_center(_analyzer_from_score(_horn_score_4("bouché")))
    h_cv = _h_center(_analyzer_from_score(_horn_score_4("cuivré")))
    assert h_open > 0.85
    assert h_st > 0.85
    assert h_cv > 0.85
    for mk, key in ((None, "horn|open"), ("bouché", "horn|stopped"), ("cuivré", "horn|cuivre")):
        an = _analyzer_from_score(_horn_score_4(mk))
        f = an.extract_timbral_features(2.0, 4.0)
        dist = f["timbral_state_distribution"]
        assert len(dist) == 1
        assert key in dist


def test_brass_mixed_open_stopped_lower_h():
    """
    Classification: **project-specific convention** (homogeneity model should rank mixed states below uniform);
    margin 0.02 is **provisional / needs corpus validation**.
    """
    h_open = _h_center(_analyzer_from_score(_horn_score_4(None)))
    h_st = _h_center(_analyzer_from_score(_horn_score_4("bouché")))
    h_mix = _h_center(_analyzer_from_score(_horn_score_mixed((None, None, "bouché", "bouché"))))
    assert h_mix < h_open - 0.02
    assert h_mix < h_st - 0.02
    f = _analyzer_from_score(_horn_score_mixed((None, None, "bouché", "bouché"))).extract_timbral_features(2.0, 4.0)
    d = f["timbral_state_distribution"]
    assert "horn|open" in d and "horn|stopped" in d


def test_brass_mixed_stopped_cuivre_lower_than_uniform():
    """Classification: **project-specific convention** (same ranking idea); margin **provisional**."""
    h_st = _h_center(_analyzer_from_score(_horn_score_4("bouché")))
    h_cv = _h_center(_analyzer_from_score(_horn_score_4("cuivré")))
    h_mix = _h_center(_analyzer_from_score(_horn_score_mixed(("bouché", "bouché", "cuivré", "cuivré"))))
    assert h_mix < h_st - 0.02
    assert h_mix < h_cv - 0.02


def _violin_part(direction: str | None) -> stream.Part:
    p = stream.Part()
    p.insert(0, instrument.Violin())
    p.insert(0, meter.TimeSignature("4/4"))
    m = stream.Measure()
    if direction:
        m.insert(0, expressions.TextExpression(direction))
        m.insert(1, note.Note("G4", quarterLength=4.0))
    else:
        m.insert(0, note.Note("G4", quarterLength=4.0))
    p.append(m)
    return p


def _four_violins(dir4: tuple[str | None, str | None, str | None, str | None]) -> stream.Score:
    sc = stream.Score()
    for d in dir4:
        sc.append(_violin_part(d))
    return sc


def test_string_uniform_and_mixed_homogeneity():
    """
    Classification: **project-specific convention** (mixed < uniform); threshold 0.82 **provisional /
    needs corpus validation**. Bare parts imply arco when no pizz. text — **ambiguous but intentionally accepted**.
    """
    h_arco = _h_center(_analyzer_from_score(_four_violins((None, None, None, None))))
    h_sp = _h_center(_analyzer_from_score(_four_violins(("sul pont.",) * 4)))
    h_mix = _h_center(_analyzer_from_score(_four_violins((None, None, "sul pont.", "sul pont."))))
    assert h_arco > 0.82
    assert h_sp > 0.82
    assert h_mix < h_arco - 0.02
    assert h_mix < h_sp - 0.02


def test_stateful_pizz_persists_until_arco():
    """Classification: **confirmed musical convention** (pizz. persists until arco / ord. in orchestral practice)."""
    p = stream.Part()
    p.insert(0, instrument.Violin())
    p.insert(0, meter.TimeSignature("4/4"))
    m1 = stream.Measure()
    m1.insert(0, expressions.TextExpression("pizz."))
    m1.insert(1, note.Note("G4", quarterLength=1.0))
    m2 = stream.Measure()
    m2.insert(0, note.Note("A4", quarterLength=1.0))
    p.append(m1)
    p.append(m2)
    sc = stream.Score()
    sc.append(p)
    an = _analyzer_from_score(sc)
    ev = an._events
    assert len(ev) == 2
    assert ev[0]["technique_state_id"].startswith("violin|") and "pizz" in ev[0]["technique_state_id"]
    assert ev[1]["technique_state_id"].startswith("violin|") and "pizz" in ev[1]["technique_state_id"]


def test_stateful_sul_pont_persists():
    """Classification: **confirmed musical convention** (sul pont. as persistent contact until cancelled)."""
    p = stream.Part()
    p.insert(0, instrument.Violin())
    p.insert(0, meter.TimeSignature("4/4"))
    m1 = stream.Measure()
    m1.insert(0, expressions.TextExpression("sul pont."))
    m1.insert(1, note.Note("G4", quarterLength=1.0))
    m2 = stream.Measure()
    m2.insert(0, note.Note("A4", quarterLength=1.0))
    p.append(m1)
    p.append(m2)
    sc = stream.Score()
    sc.append(p)
    an = _analyzer_from_score(sc)
    ev = an._events
    assert "sul_pont" in ev[0]["technique_state_id"]
    assert "sul_pont" in ev[1]["technique_state_id"]


def test_senza_vibrato_cancels_before_generic_vibrato():
    """Regression: ``senza vibrato`` contains ``vibrato``; negation must match first."""
    ctx = TechniqueStateContext(family=FAMILY_CLARINETS, instrument="clarinet")
    apply_persistent_text("senza vibrato", ctx)
    assert ctx.wind_lane == "ordinario"


def test_molto_flautando_sets_pressure_not_flautando_contact():
    ctx = TechniqueStateContext(family=FAMILY_STRINGS, instrument="violin")
    apply_persistent_text("molto flautando", ctx)
    assert ctx.str_pressure == "molto_flautando"
    assert ctx.str_contact == "ordinary"


def test_string_ordinario_clears_harmonic():
    ctx = TechniqueStateContext(family=FAMILY_STRINGS, instrument="violin")
    apply_persistent_text("natural harmonic", ctx)
    assert ctx.str_harmonic == "natural_harmonic"
    apply_persistent_text("ord.", ctx)
    assert ctx.str_harmonic == "none"
