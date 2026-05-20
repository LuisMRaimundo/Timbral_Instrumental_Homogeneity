"""
Integration tests: H_timbral respects full timbral technique state (homogeneity vs identity).

Assumption tags in docstrings:
**confirmed musical convention** | **project-specific convention** |
**ambiguous but intentionally accepted** | **provisional / needs corpus validation**
"""

from __future__ import annotations

import pytest
from music21 import expressions, instrument, meter, note, stream

from homogeneity_analyser.analyzers.technique_state import timbral_state_concentration_from_distribution
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer


def _an(sc: stream.Score) -> TimbralHomogeneityAnalyzer:
    return TimbralHomogeneityAnalyzer(music21_score=sc)


def _h(an: TimbralHomogeneityAnalyzer, center: float = 2.0, width: float = 4.0) -> float:
    f = an.extract_timbral_features(center, width)
    return an.compute_H_timbral(f)


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


def _four_violins(dirs: tuple[str | None, str | None, str | None, str | None]) -> stream.Score:
    sc = stream.Score()
    for d in dirs:
        sc.append(_violin_part(d))
    return sc


def _clarinet_part(direction: str | None) -> stream.Part:
    p = stream.Part()
    p.insert(0, instrument.Clarinet())
    p.insert(0, meter.TimeSignature("4/4"))
    m = stream.Measure()
    if direction:
        m.insert(0, expressions.TextExpression(direction))
        m.insert(1, note.Note("D4", quarterLength=4.0))
    else:
        m.insert(0, note.Note("D4", quarterLength=4.0))
    p.append(m)
    return p


def _four_clarinets(dirs: tuple[str | None, str | None, str | None, str | None]) -> stream.Score:
    sc = stream.Score()
    for d in dirs:
        sc.append(_clarinet_part(d))
    return sc


def _flute_part(direction: str | None) -> stream.Part:
    p = stream.Part()
    p.insert(0, instrument.Flute())
    p.insert(0, meter.TimeSignature("4/4"))
    m = stream.Measure()
    if direction:
        m.insert(0, expressions.TextExpression(direction))
        m.insert(1, note.Note("C5", quarterLength=4.0))
    else:
        m.insert(0, note.Note("C5", quarterLength=4.0))
    p.append(m)
    return p


def _four_flutes(dirs: tuple[str | None, str | None, str | None, str | None]) -> stream.Score:
    sc = stream.Score()
    for d in dirs:
        sc.append(_flute_part(d))
    return sc


def _suspended_cymbal_part(direction: str | None) -> stream.Part:
    p = stream.Part()
    ins = instrument.Instrument()
    ins.instrumentName = "suspended cymbal"
    p.insert(0, ins)
    p.insert(0, meter.TimeSignature("4/4"))
    m = stream.Measure()
    if direction:
        m.insert(0, expressions.TextExpression(direction))
        m.insert(1, note.Note("C5", quarterLength=4.0))
    else:
        m.insert(0, note.Note("C5", quarterLength=4.0))
    p.append(m)
    return p


def _four_cymbals(dirs: tuple[str | None, str | None, str | None, str | None]) -> stream.Score:
    sc = stream.Score()
    for d in dirs:
        sc.append(_suspended_cymbal_part(d))
    return sc


@pytest.mark.parametrize(
    "mark,expect_sub",
    [
        (None, "open"),
        ("bouché", "stopped"),
        ("cuivré", "cuivre"),
    ],
)
def test_horn_uniform_brass_states_high_h_and_single_dominant_state(mark, expect_sub):
    """
    Classification: **confirmed musical convention** (uniform section technique reads as highly
    homogeneous); numeric floor **provisional / needs corpus validation**.
    """
    an = _an(_horn_score_4(mark))
    assert _h(an) > 0.82
    f = an.extract_timbral_features(2.0, 4.0)
    assert f is not None
    d = f["timbral_state_distribution"]
    assert len(d) == 1
    assert all(expect_sub in k for k in d)
    assert f["timbral_state_concentration"] == pytest.approx(1.0, abs=1e-6)
    assert expect_sub in (f["dominant_timbral_state"] or "")


def test_horn_two_open_two_stopped_lower_than_uniforms():
    """
    Classification: **project-specific convention** (mixed primary states reduce pairwise
    homogeneity vs uniform open or uniform stopped); margins **provisional / needs corpus validation**.
    """
    h_open = _h(_an(_horn_score_4(None)))
    h_st = _h(_an(_horn_score_4("bouché")))
    h_mix = _h(_an(_horn_score_mixed((None, None, "bouché", "bouché"))))
    assert h_mix < h_open - 0.02
    assert h_mix < h_st - 0.02
    f = _an(_horn_score_mixed((None, None, "bouché", "bouché"))).extract_timbral_features(2.0, 4.0)
    assert f is not None
    c = f["timbral_state_concentration"]
    assert c == pytest.approx(0.5, abs=0.06)


def test_horn_two_stopped_two_cuivre_lower_than_uniforms():
    """Classification: **project-specific convention** (mixed stopped vs cuivré like open+stopped)."""
    h_st = _h(_an(_horn_score_4("bouché")))
    h_cv = _h(_an(_horn_score_4("cuivré")))
    h_mix = _h(_an(_horn_score_mixed(("bouché", "bouché", "cuivré", "cuivré"))))
    assert h_mix < h_st - 0.02
    assert h_mix < h_cv - 0.02


def test_violin_uniform_arco_and_sul_pont_high_mixed_lower():
    """
    Classification: **confirmed musical convention** (uniform contact/playing state vs mixed);
    thresholds **provisional / needs corpus validation**.
    """
    h_arco = _h(_an(_four_violins((None, None, None, None))))
    h_sp = _h(_an(_four_violins(("sul pont.",) * 4)))
    h_mix = _h(_an(_four_violins((None, None, "sul pont.", "sul pont."))))
    assert h_arco > 0.82
    assert h_sp > 0.82
    assert h_mix < h_arco - 0.02
    assert h_mix < h_sp - 0.02


def test_violin_sul_pont_con_sord_distinct_signature_from_sul_pont_senza():
    """
    Classification: **confirmed musical convention** (mute + contact are orthogonal dimensions);
    H may both be high for uniform sections, but timbral state ids must differ (**homogeneity vs identity**).
    """
    sc_a = stream.Score()
    for _ in range(4):
        p = stream.Part()
        p.insert(0, instrument.Violin())
        p.insert(0, meter.TimeSignature("4/4"))
        m = stream.Measure()
        m.insert(0, expressions.TextExpression("con sord."))
        m.insert(0, expressions.TextExpression("sul pont."))
        m.insert(1, note.Note("G4", quarterLength=4.0))
        p.append(m)
        sc_a.append(p)
    sc_b = stream.Score()
    for _ in range(4):
        p = stream.Part()
        p.insert(0, instrument.Violin())
        p.insert(0, meter.TimeSignature("4/4"))
        m = stream.Measure()
        m.insert(0, expressions.TextExpression("sul pont."))
        m.insert(1, note.Note("G4", quarterLength=4.0))
        p.append(m)
        sc_b.append(p)
    fa = _an(sc_a).extract_timbral_features(2.0, 4.0)
    fb = _an(sc_b).extract_timbral_features(2.0, 4.0)
    assert fa and fb
    assert fa["dominant_timbral_state"] != fb["dominant_timbral_state"]
    dom_a = str(fa["dominant_timbral_state"] or "")
    keys_a = "".join(fa["timbral_state_distribution"])
    assert "muted" in dom_a or "muted" in keys_a
    assert "sul_pont" in dom_a or "sul_pont" in keys_a
    dom_b = str(fb["dominant_timbral_state"] or "")
    keys_b = "".join(fb["timbral_state_distribution"])
    assert "sul_pont" in dom_b or "sul_pont" in keys_b
    assert "muted" not in dom_b and "muted" not in keys_b


def test_clarinet_uniform_ordinary_and_slap_high_mixed_lower():
    """Classification: **project-specific convention** (slap vs ordinario pairwise gap)."""
    h_o = _h(_an(_four_clarinets((None,) * 4)))
    h_s = _h(_an(_four_clarinets(("slap tongue",) * 4)))
    h_m = _h(_an(_four_clarinets((None, None, "slap tongue", "slap tongue"))))
    assert h_o > 0.78
    assert h_s > 0.78
    assert h_m < min(h_o, h_s) - 0.02


def test_flute_uniform_air_high_mixed_ordinary_air_lower():
    """Classification: **project-specific convention** (air_sound lane vs ordinario)."""
    h_air = _h(_an(_four_flutes(("air sound",) * 4)))
    h_o = _h(_an(_four_flutes((None,) * 4)))
    h_m = _h(_an(_four_flutes((None, None, "air sound", "air sound"))))
    assert h_air > 0.78
    assert h_o > 0.78
    assert h_m < min(h_o, h_air) - 0.02


def test_cymbal_uniform_let_ring_and_mixed_with_damped():
    """Classification: **confirmed musical convention** (damped vs let ring as distinct resonance)."""
    h_lr = _h(_an(_four_cymbals(("let ring",) * 4)))
    h_m = _h(_an(_four_cymbals(("let ring", "let ring", "damped", "damped"))))
    assert h_lr > 0.75
    assert h_m < h_lr - 0.02


def test_analyze_timbral_series_includes_state_audit_fields():
    """
    Classification: **project-specific convention** (time series bundles overlap-weighted
    ``timbral_state_distribution`` + concentration for audit / JSON export).
    """
    an = _an(_horn_score_mixed((None, None, "bouché", "bouché")))
    ts = an.analyze_timbral(window_size=4.0)
    assert "timbral_state_distribution" in ts
    assert "dominant_timbral_state" in ts
    assert "timbral_state_concentration" in ts
    assert len(ts["timbral_state_distribution"]) == len(ts["t"])
    assert len(ts["dominant_timbral_state"]) == len(ts["t"])
    assert len(ts["timbral_state_concentration"]) == len(ts["t"])


def test_timbral_events_carry_technique_state_and_timing_fields():
    """Classification: **project-specific convention** (event schema for downstream audit)."""
    an = _an(_horn_score_4("cuivré"))
    assert len(an._events) == 4
    for ev in an._events:
        assert "technique_state" in ev and isinstance(ev["technique_state"], dict)
        assert "technique_state_id" in ev
        assert "onset" in ev and "note_end" in ev
        assert ev["onset"] == ev["offset"]
        assert ev["note_end"] == ev["end"]
        assert ev["duration_ql"] == pytest.approx(ev["end"] - ev["offset"])
        assert "family" in ev and "instrument" in ev


def test_concentration_two_equal_masses():
    """Classification: **project-specific convention** (Herfindahl on overlap masses)."""
    dist = {"horn|open": 2.0, "horn|stopped": 2.0}
    assert timbral_state_concentration_from_distribution(dist) == pytest.approx(0.5)
