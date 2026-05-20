"""H_TI ``technique_uniformity`` uses instrument-free ``technique_uniformity_key`` buckets."""

from __future__ import annotations

import math

import pytest
from music21 import articulations, expressions, instrument, meter, note, stream

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.technique_state import ORDINARY_DEFAULT_UNIFORMITY_KEY


def _hti_an(sc: stream.Score) -> SymbolicTIHomogeneityAnalyzer:
    return SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)


def _woodwind_trio_plain() -> stream.Score:
    sc = stream.Score()
    for cls in (instrument.Flute, instrument.Oboe, instrument.Clarinet):
        p = stream.Part()
        p.insert(0, cls())
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, note.Note("C5", quarterLength=4.0))
        sc.insert(0, p)
    return sc


def test_flute_oboe_clarinet_no_explicit_technique_uniformity_one() -> None:
    an = _hti_an(_woodwind_trio_plain())
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    assert float(f["instrument_uniformity"]) < 1.0
    assert f["technique_uniformity"] == pytest.approx(1.0)
    assert f["technique_coverage_status"] == "ordinary_default_uniform"
    dist = f["technique_state_distribution"]
    assert set(dist.keys()) == {ORDINARY_DEFAULT_UNIFORMITY_KEY}


def _brass_open_trio() -> stream.Score:
    sc = stream.Score()
    for cls in (instrument.Horn, instrument.Trumpet, instrument.Trombone):
        p = stream.Part()
        p.insert(0, cls())
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, note.Note("G4", quarterLength=4.0))
        sc.insert(0, p)
    return sc


def test_brass_open_uniform_technique_key_not_instrument_prefixed() -> None:
    an = _hti_an(_brass_open_trio())
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    assert f["technique_coverage_status"] == "ordinary_default_uniform"
    assert f["technique_uniformity"] == pytest.approx(1.0)
    dist = f["technique_state_distribution"]
    assert set(dist.keys()) == {ORDINARY_DEFAULT_UNIFORMITY_KEY}
    assert not any("horn" in k or "trumpet" in k for k in dist)


def _two_violins_arco_pizz() -> stream.Score:
    sc = stream.Score()
    p1 = stream.Part()
    p1.insert(0, instrument.Violin())
    p1.insert(0, meter.TimeSignature("4/4"))
    p1.insert(0, note.Note("C4", quarterLength=2.0))
    n_pizz = note.Note("C4", quarterLength=2.0)
    n_pizz.articulations = [articulations.Pizzicato()]
    p1.insert(2, n_pizz)
    p2 = stream.Part()
    p2.insert(0, instrument.Violin())
    p2.insert(0, meter.TimeSignature("4/4"))
    p2.insert(0, note.Note("D4", quarterLength=4.0))
    sc.insert(0, p1)
    sc.insert(0, p2)
    return sc


def test_arco_plus_pizzicato_explicit_mixed_lowers_technique_uniformity() -> None:
    an = _hti_an(_two_violins_arco_pizz())
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    assert f["technique_coverage_status"] == "explicit_mixed"
    assert float(f["technique_uniformity"]) < 1.0
    keys = set(f["technique_state_distribution"])
    assert ORDINARY_DEFAULT_UNIFORMITY_KEY in keys
    assert any("pizz" in k for k in keys)


def _sul_pont_plus_ordinario() -> stream.Score:
    sc = stream.Score()
    p1 = stream.Part()
    p1.insert(0, instrument.Violin())
    p1.insert(0, meter.TimeSignature("4/4"))
    p1.insert(0, expressions.TextExpression("sul pont"))
    p1.insert(0, note.Note("E4", quarterLength=2.0))
    p2 = stream.Part()
    p2.insert(0, instrument.Violin())
    p2.insert(0, meter.TimeSignature("4/4"))
    p2.insert(0, expressions.TextExpression("ordinario"))
    p2.insert(0, note.Note("F4", quarterLength=2.0))
    sc.insert(0, p1)
    sc.insert(0, p2)
    return sc


def test_sul_ponticello_and_ordinario_mixed_technique_uniformity() -> None:
    an = _hti_an(_sul_pont_plus_ordinario())
    f = an.extract_hti_window(1.0, 2.0)
    assert f is not None
    assert f["technique_coverage_status"] == "explicit_mixed"
    assert float(f["technique_uniformity"]) < 1.0


def test_technique_distribution_not_identical_to_instrument_distribution_keys() -> None:
    an = _hti_an(_woodwind_trio_plain())
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    inst_keys = set(f["instrument_distribution"])
    tech_keys = set(f["technique_state_distribution"])
    assert inst_keys != tech_keys or len(tech_keys) == 1


def test_technique_uniformity_identity_written_plus_explicit_not_instrument_columns() -> None:
    """Sanity: ``dominant_timbral_state`` is a technique uniformity bucket, not an instrument name."""
    an = _hti_an(_brass_open_trio())
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    dom = str(f.get("dominant_timbral_state") or "")
    assert dom == ORDINARY_DEFAULT_UNIFORMITY_KEY


def _clarinet_bass_clarinet_3_to_1_ql() -> stream.Score:
    sc = stream.Score()
    pc = stream.Part()
    pc.insert(0, instrument.Clarinet())
    pc.insert(0, meter.TimeSignature("4/4"))
    pc.insert(0, note.Note("C5", quarterLength=3.0))
    pbc = stream.Part()
    pbc.insert(0, instrument.BassClarinet())
    pbc.insert(0, meter.TimeSignature("4/4"))
    pbc.insert(0, note.Note("D5", quarterLength=1.0))
    sc.insert(0, pc)
    sc.insert(0, pbc)
    return sc


def test_clarinet_bass_clarinet_no_special_technique_decouples_from_instruments() -> None:
    """Overlap mass 3:1 ⇒ instrument_uniformity 0.625; technique layer stays neutral (one bucket)."""
    an = _hti_an(_clarinet_bass_clarinet_3_to_1_ql())
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    assert f["instrument_uniformity"] == pytest.approx(0.625)
    assert f["family_uniformity"] == pytest.approx(1.0)
    assert f["technique_uniformity"] == pytest.approx(1.0)
    assert f["technique_coverage_status"] == "ordinary_default_uniform"
    td = f["technique_state_distribution"]
    assert set(td.keys()) == {ORDINARY_DEFAULT_UNIFORMITY_KEY}
    assert td[ORDINARY_DEFAULT_UNIFORMITY_KEY] == pytest.approx(1.0)
    inst = f["instrument_distribution"]
    assert set(inst.keys()) != set(td.keys()) or len(inst) > 1


def test_hti_core_higher_when_technique_no_longer_tracks_instruments() -> None:
    """``H_TI_core`` uses a geometric mean: neutral technique (1.0) vs duplicated instrument keys (<1).

    Duplicating instrument keys in the technique slot raises the core.
    """
    an = _hti_an(_clarinet_bass_clarinet_3_to_1_ql())
    f = an.extract_hti_window(2.0, 4.0)
    assert f is not None
    h_actual, _, _ = an.compute_H_TI(f)
    f_dup = dict(f)
    f_dup["technique_uniformity"] = float(f["instrument_uniformity"])
    f_dup["technique_coverage_status"] = "explicit_mixed"
    h_dup, _, _ = an.compute_H_TI(f_dup)
    assert math.isfinite(float(h_actual)) and math.isfinite(float(h_dup))
    assert float(h_actual) > float(h_dup)
