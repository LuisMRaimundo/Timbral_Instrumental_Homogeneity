"""String-harmonic pitch interpretation (symbolic MusicXML / music21 only)."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from music21 import articulations, chord, interval, note, stream

from homogeneity_analyser.analyzers.harmonic_pitch import (
    HARMONIC_INTERVAL_TABLE_SOURCE,
    HARMONIC_PITCH_POLICY_CONSERVATIVE,
    HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
    HARMONIC_PITCH_POLICY_WRITTEN_AS_SOUNDING,
    infer_artificial_sounding_written_midi,
    match_artificial_harmonic_interval,
)
from homogeneity_analyser.analyzers.pitch_interpretation import (
    PITCH_INTERPRETATION_MUSICXML_SOUNDING,
    PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
    interpret_note_sounding_pitch_ps_list,
)
from homogeneity_analyser.analyzers.timbral_sounding_pitch import _note_or_part_transposition
from homogeneity_analyser.services.score_audit import build_symbolic_inspection_tables, build_vertical_sonority_audit

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"


def test_harmonic_interval_table_source_metadata() -> None:
    assert HARMONIC_INTERVAL_TABLE_SOURCE.get("evidence_type") == "string_harmonic_notation_reference"
    assert "Agatha Mallett" in (HARMONIC_INTERVAL_TABLE_SOURCE.get("source_name") or "")
    assert HARMONIC_INTERVAL_TABLE_SOURCE.get("source_status", "").startswith("practical notation chart")


def test_infer_artificial_octave() -> None:
    s, st, w = infer_artificial_sounding_written_midi(60.0, 72.0)  # C4 + touching C5
    assert st == "inferred_common_artificial"
    assert s == pytest.approx(72.0)
    _sw, _st, _w, rid, tiv = match_artificial_harmonic_interval(60.0, 72.0)
    assert rid == "octave"
    assert tiv == pytest.approx(12.0)


def test_infer_artificial_fifth_fourth_major_minor_third() -> None:
    s5, st5, _w5 = infer_artificial_sounding_written_midi(60.0, 67.0)  # C4 G4
    assert st5 == "inferred_common_artificial"
    assert s5 == pytest.approx(79.0)
    assert match_artificial_harmonic_interval(60.0, 67.0)[3] == "perfect_fifth"

    s4, st4, _ = infer_artificial_sounding_written_midi(60.0, 65.0)  # C4 F4
    assert st4 == "inferred_common_artificial"
    assert s4 == pytest.approx(84.0)

    s3, st3, w3 = infer_artificial_sounding_written_midi(60.0, 64.0)  # C4 E4
    assert st3 == "inferred_common_artificial"
    assert s3 == pytest.approx(88.0)
    assert "harmonic 5" in w3.lower() or "tempered" in w3.lower()

    s_m3, st_m3, w_m3 = infer_artificial_sounding_written_midi(60.0, 63.0)  # C4 Eb4
    assert st_m3 == "inferred_common_artificial"
    assert s_m3 == pytest.approx(91.0)
    assert "harmonic 6" in w_m3.lower() or "tempered" in w_m3.lower()


def test_explicit_sounding_natural_fixture() -> None:
    path = FIXTURE_DIR / "harmonic_sounding_e5.musicxml"
    score = _parse(path)
    _, ev, vert = build_symbolic_inspection_tables(score, harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE)
    row = next(r for r in ev if str(r.get("canonical_instrument")) == "violin")
    assert row["harmonic_sounding_status"] == "explicit"
    assert float(row["effective_sounding_midi"]) == pytest.approx(76.0)  # E5 concert for violin


def test_artificial_chord_cf_infer_policy_violin() -> None:
    path = FIXTURE_DIR / "harmonic_artificial_chord_cf.musicxml"
    score = _parse(path)
    _, ev, vert = build_symbolic_inspection_tables(
        score,
        harmonic_pitch_policy=HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
    )
    vrows = [r for r in ev if r.get("canonical_instrument") == "violin" and r.get("effective_sounding_midi") != ""]
    assert len(vrows) == 2
    for r in vrows:
        assert r["harmonic_sounding_status"] == "inferred_common_artificial"
        assert float(r["effective_sounding_midi"]) == pytest.approx(84.0)
        assert r.get("harmonic_interval_rule_id") == "perfect_fourth"
        assert float(r.get("harmonic_touching_interval_semitones") or 0) == pytest.approx(5.0)
        assert r.get("harmonic_pitch_policy") == HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL
    assert vert and vert[0].get("harmonic_unresolved_count") == 0


def test_artificial_chord_cf_cello() -> None:
    path = FIXTURE_DIR / "harmonic_artificial_chord_cf_cello.musicxml"
    score = _parse(path)
    _, ev, _ = build_symbolic_inspection_tables(
        score,
        harmonic_pitch_policy=HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
    )
    crows = [r for r in ev if r.get("canonical_instrument") == "cello"]
    assert len(crows) == 2
    for r in crows:
        assert float(r["effective_sounding_midi"]) == pytest.approx(72.0)
        assert r.get("harmonic_interval_rule_id") == "perfect_fourth"


def test_artificial_chord_cf_double_bass_fixture() -> None:
    path = FIXTURE_DIR / "harmonic_artificial_chord_cf_double_bass.musicxml"
    score = _parse(path)
    _, ev, _ = build_symbolic_inspection_tables(
        score,
        harmonic_pitch_policy=HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
    )
    brows = [r for r in ev if r.get("canonical_instrument") == "double bass"]
    assert len(brows) == 2
    for r in brows:
        assert float(r["harmonic_sounding_midi"]) == pytest.approx(60.0)
        assert float(r["effective_sounding_midi"]) == pytest.approx(60.0)


def test_double_bass_artificial_with_octave_transposer_mode() -> None:
    from music21 import instrument

    p = stream.Part()
    ins = instrument.Contrabass()
    ins.transposition = interval.Interval("-P8")
    p.insert(0, ins)
    ch = chord.Chord(["C2", "F2"])
    sh = articulations.StringHarmonic()
    sh.harmonicType = "artificial"
    ch.articulations = (sh,)
    p.insert(0, ch)
    sc = stream.Score()
    sc.insert(0, p)
    pits, meta = interpret_note_sounding_pitch_ps_list(
        ch,
        p,
        PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
        trans_resolver=_note_or_part_transposition,
        canonical_instrument="double bass",
        harmonic_pitch_policy=HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
    )
    assert pits[0] == pytest.approx(48.0)
    assert float(meta[0]["harmonic_sounding_midi"]) == pytest.approx(60.0)


def test_diamond_violin_conservative_unresolved() -> None:
    path = FIXTURE_DIR / "harmonic_diamond_violin.musicxml"
    score = _parse(path)
    _, ev, _ = build_symbolic_inspection_tables(score, harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE)
    row = next(r for r in ev if r.get("canonical_instrument") == "violin")
    assert row["harmonic_state"] == "harmonic_candidate"
    assert row["harmonic_type"] == "unknown"
    assert row["harmonic_sounding_status"] == "unresolved"
    assert float(row["effective_sounding_midi"]) == pytest.approx(69.0)  # A4 unchanged
    assert (
        str(row.get("harmonic_warning") or "")
        == "Diamond notehead on bowed string detected, but MusicXML does not specify whether this is sounding, base, "
        "or touching pitch."
    )


def test_natural_harmonic_without_sounding_is_candidate_unresolved() -> None:
    from music21 import instrument

    p = stream.Part()
    p.insert(0, instrument.Violin())
    n = note.Note("G4", quarterLength=1.0)
    sh = articulations.StringHarmonic()
    sh.harmonicType = "natural"
    n.articulations = (sh,)
    p.insert(0, n)
    sc = stream.Score()
    sc.insert(0, p)
    pits, meta = interpret_note_sounding_pitch_ps_list(
        n,
        p,
        PITCH_INTERPRETATION_MUSICXML_SOUNDING,
        trans_resolver=_note_or_part_transposition,
        canonical_instrument="violin",
        harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE,
    )
    assert meta[0]["harmonic_state"] == "harmonic_candidate"
    assert meta[0]["harmonic_type"] == "natural"
    assert meta[0]["harmonic_sounding_status"] == "unresolved"
    assert float(meta[0]["effective_sounding_midi"]) == pytest.approx(float(pits[0]))


def test_diamond_violin_written_as_sounding_policy() -> None:
    path = FIXTURE_DIR / "harmonic_diamond_violin.musicxml"
    score = _parse(path)
    _, ev, _ = build_symbolic_inspection_tables(score, harmonic_pitch_policy=HARMONIC_PITCH_POLICY_WRITTEN_AS_SOUNDING)
    row = next(r for r in ev if r.get("canonical_instrument") == "violin")
    assert row["harmonic_sounding_status"] == "written_as_sounding_policy"
    assert float(row["effective_sounding_midi"]) == pytest.approx(69.0)


def test_diamond_flute_not_harmonic_candidate() -> None:
    path = FIXTURE_DIR / "harmonic_diamond_flute.musicxml"
    score = _parse(path)
    _, ev, _ = build_symbolic_inspection_tables(score, harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE)
    row = next(r for r in ev if r.get("canonical_instrument") == "flute")
    assert row["harmonic_state"] == "none"
    assert "ignored" in str(row.get("harmonic_warning") or "").lower()


def test_diamond_snare_no_string_harmonic_inference() -> None:
    path = FIXTURE_DIR / "harmonic_diamond_snare.musicxml"
    score = _parse(path)
    _, ev, _ = build_symbolic_inspection_tables(score, harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE)
    row = next(r for r in ev if r.get("sounding_midi") != "unknown")
    assert row.get("harmonic_state") == "none"
    assert row.get("harmonic_detection_source") == "none"
    assert "ignored" in str(row.get("harmonic_warning") or "").lower()


def test_ruzicka_style_diamond_strings_fixture() -> None:
    from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer

    path = FIXTURE_DIR / "ruzicka_style_diamond_strings.musicxml"
    score = _parse(path)
    _, ev, vert = build_symbolic_inspection_tables(score, harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE)
    viol = next(r for r in ev if "violin" in str(r.get("canonical_instrument") or ""))
    vla = next(r for r in ev if str(r.get("canonical_instrument") or "") == "viola")
    assert viol["harmonic_state"] == "harmonic_candidate"
    assert vla["harmonic_state"] == "harmonic_candidate"
    assert viol.get("desk_group") == "5-6"
    assert viol.get("section_label")
    assert str(viol.get("raw_part_name") or "").lower().startswith("vnl")
    vert2 = build_vertical_sonority_audit(ev)
    assert vert2[0].get("harmonic_unresolved_count", 0) >= 1

    for r in ev:
        assert not str(r.get("canonical_instrument") or "").lower().startswith("vnl")

    an = SymbolicTIHomogeneityAnalyzer(
        music21_score=score,
        time_step=1.0,
        harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE,
    )
    feats = an.extract_hti_window(0.0, 4.0)
    assert feats is not None
    for evm in an.score_events:
        assert not str(evm.get("instrument") or "").lower().startswith("vnl")
    fam_d = dict(feats.get("family_distribution") or {})
    macro_d = dict(feats.get("macrofamily_distribution") or {})
    assert fam_d.get("other", 0.0) == 0.0
    assert macro_d.get("other", 0.0) == 0.0
    h_core, _comp, _aw = an.compute_H_TI(feats)
    assert math.isfinite(float(h_core))
    assert 0.0 <= float(h_core) <= 1.0


def test_vertical_sonorities_use_effective_sounding_after_harmonic_infer() -> None:
    path = FIXTURE_DIR / "harmonic_artificial_chord_cf.musicxml"
    score = _parse(path)
    _, ev, _ = build_symbolic_inspection_tables(
        score,
        harmonic_pitch_policy=HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
    )
    vert = build_vertical_sonority_audit(ev)
    assert vert
    mids = vert[0]["sounding_midi_values"]
    assert "84" in mids or "84.0" in mids


def test_vertical_sonorities_do_not_invent_sounding_for_unresolved_diamond() -> None:
    path = FIXTURE_DIR / "harmonic_diamond_violin.musicxml"
    score = _parse(path)
    _, ev, _ = build_symbolic_inspection_tables(score, harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE)
    vert = build_vertical_sonority_audit(ev)
    mids = vert[0]["sounding_midi_values"]
    assert "84" not in mids


def test_programmatic_chord_explicit_sounding() -> None:
    from music21 import instrument

    p = stream.Part()
    p.insert(0, instrument.Violin())
    ch = chord.Chord(["E5"])
    sh = articulations.StringHarmonic()
    sh.harmonicType = "natural"
    sh.pitchType = "sounding"
    ch.articulations = (sh,)
    p.insert(0, ch)
    sc = stream.Score()
    sc.insert(0, p)
    pits, meta = interpret_note_sounding_pitch_ps_list(
        ch,
        p,
        PITCH_INTERPRETATION_MUSICXML_SOUNDING,
        trans_resolver=_note_or_part_transposition,
        canonical_instrument="violin",
        harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE,
    )
    assert meta[0]["harmonic_sounding_status"] == "explicit"
    assert float(meta[0]["effective_sounding_midi"]) == pytest.approx(float(pits[0]))


def _parse(path: Path):
    from music21 import converter

    return converter.parse(str(path))
