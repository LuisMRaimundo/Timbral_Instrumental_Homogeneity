"""Pitch interpretation modes and microtonal effective alter (H_TI pitch evidence layer)."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest
from music21 import instrument, meter, note, stream

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.pitch_interpretation import (
    PITCH_INTERPRETATION_IGNORE_OCTAVE,
    PITCH_INTERPRETATION_MODES,
    PITCH_INTERPRETATION_MUSICXML_SOUNDING,
    PITCH_INTERPRETATION_XML_AS_REAL,
    PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
    compute_effective_alter,
    interpret_pitch_tone,
    transpose_reduced_to_chromatic_band,
)
from homogeneity_analyser.analyzers.timbral_sounding_pitch import _note_or_part_transposition
from homogeneity_analyser.services.analysis_service import run_symbolic_ti_homogeneity_analysis
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS
from homogeneity_analyser.services.param_validation import AnalysisParameterError, validate_hti_params
from homogeneity_analyser.services.score_audit import build_symbolic_inspection_tables, build_vertical_sonority_audit
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BASSOONS, get_instrument_and_family


def _mock_pitch(alter, acc_full_name: str):
    acc = SimpleNamespace(fullName=acc_full_name, name=acc_full_name, unicode=None)
    return SimpleNamespace(alter=alter, accidental=acc)


def test_compute_effective_alter_quarter_sharp_alter_zero():
    p = _mock_pitch(0, "half-sharp")
    b = compute_effective_alter(p)
    assert b["effective_alter"] == pytest.approx(0.5)
    assert b["microtonal_accidental_status"] == "inferred_from_text"
    assert b["microtonal_accidental_detected"] is True


def test_compute_effective_alter_quarter_flat_alter_zero():
    p = _mock_pitch(0, "half-flat")
    b = compute_effective_alter(p)
    assert b["effective_alter"] == pytest.approx(-0.5)


def test_compute_effective_alter_three_quarters_sharp():
    p = _mock_pitch(0, "one-and-a-half-sharp")
    b = compute_effective_alter(p)
    assert b["effective_alter"] == pytest.approx(1.5)


def test_compute_effective_alter_explicit_fraction_not_doubled():
    acc = SimpleNamespace(fullName="half-sharp", name="half-sharp", unicode=None)
    p = SimpleNamespace(alter=0.5, accidental=acc)
    b = compute_effective_alter(p)
    assert b["effective_alter"] == pytest.approx(0.5)
    assert b["microtonal_accidental_status"] == "explicit_alter"


def test_compute_effective_alter_natural_not_microtonal():
    p = _mock_pitch(0, "natural")
    b = compute_effective_alter(p)
    assert b["effective_alter"] == pytest.approx(0.0)
    assert b["microtonal_accidental_detected"] is False
    assert b["microtonal_accidental_status"] == "explicit_natural"


def test_compute_effective_alter_unknown_accidental():
    p = _mock_pitch(0, "custom-weird-sign")
    b = compute_effective_alter(p)
    assert b["microtonal_accidental_status"] == "unknown"
    assert b["effective_alter"] == pytest.approx(0.0)
    assert b["microtonal_accidental_detected"] is False


def test_transpose_reduced_to_chromatic_band():
    assert transpose_reduced_to_chromatic_band(12.0) == pytest.approx(0.0)
    assert transpose_reduced_to_chromatic_band(-12.0) == pytest.approx(0.0)
    assert transpose_reduced_to_chromatic_band(14.0) == pytest.approx(2.0)
    assert transpose_reduced_to_chromatic_band(-14.0) == pytest.approx(-2.0)


def _tiny_score_clarinet_and_flute():
    """Bb clarinet on C4 + flute on C4 (same written, different sounding when transposed)."""
    cl = stream.Part(id="Cl")
    cl.insert(0, meter.TimeSignature("4/4"))
    cl.insert(0, instrument.Clarinet())
    cl.append(note.Note("C4", quarterLength=4.0))
    fl = stream.Part(id="Fl")
    fl.insert(0, meter.TimeSignature("4/4"))
    fl.insert(0, instrument.Flute())
    fl.append(note.Note("C4", quarterLength=4.0))
    return stream.Score([cl, fl])


def test_xml_pitch_as_real_vs_musicxml_sounding_register_span():
    sc = _tiny_score_clarinet_and_flute()
    a_sound = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_MUSICXML_SOUNDING,
    )
    a_real = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL,
    )
    w = 4.0
    f_s = a_sound.extract_hti_window(2.0, w)
    f_r = a_real.extract_hti_window(2.0, w)
    assert f_s is not None and f_r is not None
    assert f_s["register_span_semitones"] != f_r["register_span_semitones"]


def test_ignore_octave_transpositions_only_vs_full():
    from music21 import interval

    sc = _tiny_score_clarinet_and_flute()
    # Force a pure-octave transposition on the clarinet part for this test.
    cl_ins = sc.parts[0].getInstrument(returnDefault=True)
    cl_ins.transposition = interval.Interval(-12)
    a_full = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_MUSICXML_SOUNDING,
    )
    a_ig = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_IGNORE_OCTAVE,
    )
    w = 4.0
    f_full = a_full.extract_hti_window(2.0, w)
    f_ig = a_ig.extract_hti_window(2.0, w)
    assert f_full is not None and f_ig is not None
    assert f_full["register_span_semitones"] != f_ig["register_span_semitones"]


def test_contrabassoon_octave_xml_as_real_matches_written():
    from music21 import interval

    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    cb = instrument.Contrabassoon()
    cb.transposition = interval.Interval(-12)
    p.insert(0, cb)
    p.append(note.Note("C3", quarterLength=4.0))
    n0 = p.flatten().notes[0]
    trans = _note_or_part_transposition(n0, p)
    assert trans is not None
    m_sound = interpret_pitch_tone(n0.pitch, trans, mode=PITCH_INTERPRETATION_MUSICXML_SOUNDING)
    m_real = interpret_pitch_tone(n0.pitch, trans, mode=PITCH_INTERPRETATION_XML_AS_REAL)
    assert m_real["effective_sounding_midi"] == pytest.approx(m_real["effective_written_midi"])
    assert m_sound["effective_sounding_midi"] != pytest.approx(m_real["effective_sounding_midi"])


def test_symbolic_inspection_event_audit_pitch_columns():
    sc = _tiny_score_clarinet_and_flute()
    _, ev, _ = build_symbolic_inspection_tables(sc, pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL)
    assert ev
    assert all(str(r.get("pitch_interpretation_mode") or "") == PITCH_INTERPRETATION_XML_AS_REAL for r in ev)
    assert "effective_sounding_midi" in ev[0]
    assert "accidental_text" in ev[0]


def test_half_sharp_c5_effective_sounding_midi():
    from music21 import pitch

    n = note.Note("C5")
    n.pitch.accidental = pitch.Accidental("half-sharp")
    m = interpret_pitch_tone(n.pitch, None, mode=PITCH_INTERPRETATION_XML_AS_REAL)
    assert m["effective_written_midi"] == pytest.approx(72.5)
    assert m["effective_sounding_midi"] == pytest.approx(72.5)
    assert m["effective_written_midi"] + m["total_transpose_applied"] == pytest.approx(m["effective_sounding_midi"])


def test_half_sharp_a6_effective_sounding_midi():
    from music21 import pitch

    n = note.Note("A6")
    n.pitch.accidental = pitch.Accidental("half-sharp")
    m = interpret_pitch_tone(n.pitch, None, mode=PITCH_INTERPRETATION_XML_AS_REAL)
    assert m["effective_written_midi"] == pytest.approx(93.5)
    assert m["effective_sounding_midi"] == pytest.approx(93.5)
    assert m["effective_written_midi"] + m["total_transpose_applied"] == pytest.approx(m["effective_sounding_midi"])


def test_vertical_sonorities_fractional_midi_when_microtonal():
    from music21 import pitch

    p1 = stream.Part()
    p1.insert(0, meter.TimeSignature("4/4"))
    p1.insert(0, instrument.Flute())
    p1.append(note.Note("C4", quarterLength=4.0))
    p2 = stream.Part()
    p2.insert(0, meter.TimeSignature("4/4"))
    p2.insert(0, instrument.Flute())
    n2 = note.Note("C4", quarterLength=4.0)
    n2.pitch.accidental = pitch.Accidental("half-sharp")
    p2.append(n2)
    sc = stream.Score([p1, p2])
    _, ev, _ = build_symbolic_inspection_tables(sc, pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL)
    vert = build_vertical_sonority_audit(ev)
    assert vert
    sm = vert[0].get("sounding_midi_values") or ""
    assert "60.5" in str(sm) or ", 60.5" in str(sm) or str(sm).startswith("60.5")


def test_register_span_reflects_half_semitone_between_microtonal_and_natural():
    from music21 import pitch

    p1 = stream.Part()
    p1.insert(0, meter.TimeSignature("4/4"))
    p1.insert(0, instrument.Flute())
    p1.append(note.Note("C4", quarterLength=4.0))
    p2 = stream.Part()
    p2.insert(0, meter.TimeSignature("4/4"))
    p2.insert(0, instrument.Flute())
    n2 = note.Note("C4", quarterLength=4.0)
    n2.pitch.accidental = pitch.Accidental("half-sharp")
    p2.append(n2)
    sc = stream.Score([p1, p2])
    an = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL,
    )
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    assert float(f["register_span_semitones"]) == pytest.approx(0.5)


def test_contrafagote_maps_to_contrabassoon():
    for raw in ("contra fagote", "contrafagote", "Contra Fagote"):
        c, fam = get_instrument_and_family(raw)
        assert c == "contrabassoon"
        assert fam == FAMILY_BASSOONS


def test_plain_score_no_explicit_technique_not_explicit_mixed():
    sc = stream.Score()
    for i in range(4):
        p = stream.Part(id=f"P{i}")
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, instrument.Violin())
        p.append(note.Note("C4", quarterLength=1.0))
        sc.insert(0, p)
    an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=0.25)
    f = an.extract_hti_window(0.5, 2.0)
    assert f is not None
    assert f["technique_coverage_status"] != "explicit_mixed"


def test_vertical_sonorities_use_effective_sounding_midi():
    sc = _tiny_score_clarinet_and_flute()
    _, ev, _ = build_symbolic_inspection_tables(sc, pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL)
    vert = build_vertical_sonority_audit(ev)
    assert vert
    v0 = vert[0]
    assert "register_span_semitones" in v0
    assert not (isinstance(v0["register_span_semitones"], float) and math.isnan(float(v0["register_span_semitones"])))


def test_validate_hti_params_rejects_bad_pitch_mode():
    with pytest.raises(AnalysisParameterError):
        validate_hti_params({**DEFAULT_HTI_PARAMS, "pitch_interpretation_mode": "not_a_mode"})


def test_validate_hti_params_rejects_bad_harmonic_pitch_policy():
    with pytest.raises(AnalysisParameterError):
        validate_hti_params({**DEFAULT_HTI_PARAMS, "harmonic_pitch_policy": "aggressive"})


def test_pitch_mode_hybrid_in_tuple_and_validation():
    assert PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS in PITCH_INTERPRETATION_MODES
    validate_hti_params(
        {
            **DEFAULT_HTI_PARAMS,
            "pitch_interpretation_mode": PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
        }
    )


def _hybrid_real_pitch_octave_fixture_score() -> stream.Score:
    from music21 import interval, pitch

    def mk(name: str, ins: instrument.Instrument, n: note.Note) -> stream.Part:
        p = stream.Part()
        p.partName = name
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, ins)
        p.append(n)
        return p

    sc = stream.Score()
    n1 = note.Note("A6", quarterLength=4.0)
    n1.pitch.accidental = pitch.Accidental("half-sharp")
    sc.insert(0, mk("Cl", instrument.Clarinet(), n1))
    n2 = note.Note("F5", quarterLength=4.0)
    n2.pitch.accidental = pitch.Accidental("half-sharp")
    sc.insert(0, mk("Bcl", instrument.BassClarinet(), n2))
    n3 = note.Note("F5", quarterLength=4.0)
    n3.pitch.accidental = pitch.Accidental("half-sharp")
    sc.insert(0, mk("Hn", instrument.Horn(), n3))
    sc.insert(0, mk("Tpt", instrument.Trumpet(), note.Note("C#6", quarterLength=4.0)))
    cb = instrument.Contrabassoon()
    cb.transposition = interval.Interval(-12)
    sc.insert(0, mk("Cfg", cb, note.Note("C#2", quarterLength=4.0)))
    sc.insert(0, mk("Cb", instrument.Contrabass(), note.Note("C2", quarterLength=4.0)))
    return sc


def test_hybrid_mode_expected_midis_and_transpose_audit():
    sc = _hybrid_real_pitch_octave_fixture_score()
    an = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
    )
    by_inst: dict[str, dict] = {}
    for ev in an.score_events:
        pm0 = (ev.get("pitch_tone_metadata") or [{}])[0]
        by_inst[str(ev["instrument"])] = pm0

    cl = by_inst["clarinet"]
    assert cl["effective_written_midi"] == pytest.approx(93.5)
    assert cl["total_transpose_applied"] == pytest.approx(0.0)
    assert cl["effective_sounding_midi"] == pytest.approx(93.5)
    assert cl["chromatic_transpose_detected"] == pytest.approx(-2.0)
    assert cl["chromatic_transpose_applied"] == pytest.approx(0.0)

    bcl = by_inst["bass clarinet"]
    assert bcl["effective_written_midi"] == pytest.approx(77.5)
    assert bcl["total_transpose_applied"] == pytest.approx(0.0)
    assert bcl["effective_sounding_midi"] == pytest.approx(77.5)

    hn = by_inst["horn"]
    assert hn["effective_written_midi"] == pytest.approx(77.5)
    assert hn["total_transpose_applied"] == pytest.approx(0.0)
    assert hn["effective_sounding_midi"] == pytest.approx(77.5)

    tpt = by_inst["trumpet"]
    assert tpt["effective_written_midi"] == pytest.approx(85.0)
    assert tpt["total_transpose_applied"] == pytest.approx(0.0)
    assert tpt["effective_sounding_midi"] == pytest.approx(85.0)

    cfg = by_inst["contrabassoon"]
    assert cfg["effective_written_midi"] == pytest.approx(37.0)
    assert cfg["octave_transpose_applied"] == pytest.approx(-12.0)
    assert cfg["total_transpose_applied"] == pytest.approx(-12.0)
    assert cfg["effective_sounding_midi"] == pytest.approx(25.0)

    dbs = by_inst["double bass"]
    assert dbs["effective_written_midi"] == pytest.approx(36.0)
    assert dbs["octave_transpose_applied"] == pytest.approx(-12.0)
    assert dbs["total_transpose_applied"] == pytest.approx(-12.0)
    assert dbs["effective_sounding_midi"] == pytest.approx(24.0)

    for ev in an.score_events:
        pm0 = (ev.get("pitch_tone_metadata") or [{}])[0]
        ew = float(pm0["effective_written_midi"])
        tot = float(pm0["total_transpose_applied"])
        es = float(pm0["effective_sounding_midi"])
        assert ew + tot == pytest.approx(es)


def test_hybrid_register_span_about_sixty_nine_point_five():
    sc = _hybrid_real_pitch_octave_fixture_score()
    an = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
    )
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    assert float(f["register_span_semitones"]) == pytest.approx(69.5)


def test_hybrid_register_span_exceeds_xml_as_real_only():
    sc = _hybrid_real_pitch_octave_fixture_score()
    a_xml = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL,
    )
    a_hy = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
    )
    fx = a_xml.extract_hti_window(2.0, 4.0)
    fh = a_hy.extract_hti_window(2.0, 4.0)
    assert fx is not None and fh is not None
    assert float(fh["register_span_semitones"]) > float(fx["register_span_semitones"])


def test_ignore_octave_mode_octave_not_in_applied_columns():
    from music21 import interval

    trans = interval.Interval(-12)
    m = interpret_pitch_tone(
        note.Note("C4").pitch,
        trans,
        mode=PITCH_INTERPRETATION_IGNORE_OCTAVE,
        canonical_instrument="double bass",
    )
    assert m["octave_transpose_detected"] == pytest.approx(-12.0)
    assert m["octave_transpose_applied"] == pytest.approx(0.0)
    assert m["total_transpose_applied"] == pytest.approx(0.0)
    assert m["effective_sounding_midi"] == pytest.approx(m["effective_written_midi"])


def test_vertical_and_json_series_use_hybrid_sounding_midis():
    import tempfile
    from pathlib import Path

    sc = _hybrid_real_pitch_octave_fixture_score()
    _, ev, _ = build_symbolic_inspection_tables(
        sc,
        pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
    )
    vert = build_vertical_sonority_audit(ev)
    assert vert
    assert float(vert[0]["register_span_semitones"]) == pytest.approx(69.5)
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "hybrid_pitch.xml"
        sc.write("musicxml", fp=str(p))
        out = run_symbolic_ti_homogeneity_analysis(
            str(p),
            {
                **DEFAULT_HTI_PARAMS,
                "pitch_interpretation_mode": PITCH_INTERPRETATION_XML_AS_REAL_WITH_OCTAVE_TRANSPOSERS,
                "time_step": 1.0,
                "window_size": 4.0,
            },
        )
        assert not out.get("error")
        rs = out["results"]["register_span_semitones"]
        vals = [float(x) for x in rs if isinstance(x, int | float) and math.isfinite(float(x))]
        assert vals
        assert min(abs(v - 69.5) for v in vals) < 1e-3


def test_run_symbolic_ti_homogeneity_analysis_includes_pitch_mode_in_parameters():
    from pathlib import Path

    here = Path(__file__).resolve().parent
    xml = here / "fixtures" / "musicxml" / "four_trombones_pp_crescendo_whole.musicxml"
    if not xml.is_file():
        pytest.skip("fixture four_trombones_pp_crescendo_whole.musicxml missing")
    out = run_symbolic_ti_homogeneity_analysis(
        str(xml),
        {**DEFAULT_HTI_PARAMS, "pitch_interpretation_mode": PITCH_INTERPRETATION_XML_AS_REAL},
    )
    assert not out.get("error")
    assert out["parameters"]["pitch_interpretation_mode"] == PITCH_INTERPRETATION_XML_AS_REAL
    res = out["results"]
    assert res["pitch_interpretation_mode"][0] == PITCH_INTERPRETATION_XML_AS_REAL
