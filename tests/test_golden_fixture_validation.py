"""
Golden-fixture validation: small MusicXML scores + qualitative H_TI / symbolic invariants.

Prefer robust inequalities over fragile exact ``H_TI_core`` scalars unless the score is
minimal and the geometry of the metric is obvious (e.g. register spread vs unison).
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from music21 import converter

from homogeneity_analyser.analyzers.harmonic_pitch import (
    HARMONIC_PITCH_POLICY_CONSERVATIVE,
    HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
)
from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.analyzers.pitch_interpretation import (
    PITCH_INTERPRETATION_MUSICXML_SOUNDING,
    PITCH_INTERPRETATION_XML_AS_REAL,
)
from homogeneity_analyser.analyzers.technique_state import ORDINARY_DEFAULT_UNIFORMITY_KEY
from homogeneity_analyser.services.score_audit import build_symbolic_inspection_tables, build_vertical_sonority_audit
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_STRINGS,
    get_instrument_and_family,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"


def _load(name: str):
    path = FIXTURE_DIR / name
    if not path.is_file():
        pytest.skip(f"missing fixture {name}")
    return converter.parse(str(path))


def _hti_core_window(score, *, t0: float = 0.0, t1: float = 4.0, **kwargs) -> tuple[float, dict]:
    """Return ``(H_TI_core, feats)`` for one window (``feats`` may be ``None``)."""
    an = SymbolicTIHomogeneityAnalyzer(music21_score=score, time_step=1.0, **kwargs)
    feats = an.extract_hti_window(t0, t1)
    if feats is None:
        return float("nan"), {}
    h, _comp, _aw = an.compute_H_TI(feats)
    return float(h), feats


def _first_event_instruments(score) -> list[tuple[str, str, str]]:
    """(canonical_instrument, family, macrofamily) for each timbral event (order as built)."""
    an = SymbolicTIHomogeneityAnalyzer(music21_score=score, time_step=1.0)
    out: list[tuple[str, str, str]] = []
    for ev in an.score_events:
        inst = str(ev.get("instrument") or "")
        fam = str(ev.get("family") or "")
        macro = macrofamily_from_instrumental_subfamily(fam)
        out.append((inst, fam, macro))
    return out


class TestGoldenTaxonomyAndMacrofamily:
    def test_two_violins_canonical_and_string_macro(self) -> None:
        sc = _load("golden_two_violins_unison_c5.musicxml")
        rows = _first_event_instruments(sc)
        assert len(rows) == 2
        for inst, fam, macro in rows:
            assert inst == "violin"
            assert fam == FAMILY_STRINGS
            assert macro == macrofamily_from_instrumental_subfamily(fam)

    def test_violin_viola_distinct_canonical_same_string_family(self) -> None:
        sc = _load("golden_violin_viola_unison_c5.musicxml")
        rows = _first_event_instruments(sc)
        insts = {r[0] for r in rows}
        fams = {r[1] for r in rows}
        assert insts == {"violin", "viola"}
        assert fams == {FAMILY_STRINGS}

    def test_violin_flute_cross_family(self) -> None:
        sc = _load("golden_violin_flute_unison_c5.musicxml")
        rows = _first_event_instruments(sc)
        insts = {r[0] for r in rows}
        fams = {r[1] for r in rows}
        assert insts == {"violin", "flute"}
        assert FAMILY_STRINGS in fams and FAMILY_FLUTES in fams

    def test_part_name_mapping_clarinet(self) -> None:
        c_inst, fam = get_instrument_and_family("Clarinet in Bb")
        assert c_inst == "b flat clarinet"
        assert fam == FAMILY_CLARINETS


class TestGoldenPitchInterpretationAndMicrotone:
    def test_clarinet_sounding_vs_xml_as_real_differs(self) -> None:
        sc = _load("golden_clarinet_c5_written.musicxml")
        _, ev_sound, _ = build_symbolic_inspection_tables(
            sc, pitch_interpretation_mode=PITCH_INTERPRETATION_MUSICXML_SOUNDING
        )
        _, ev_real, _ = build_symbolic_inspection_tables(sc, pitch_interpretation_mode=PITCH_INTERPRETATION_XML_AS_REAL)
        assert ev_sound and ev_real
        s0 = float(ev_sound[0]["effective_sounding_midi"])
        r0 = float(ev_real[0]["effective_sounding_midi"])
        assert s0 != pytest.approx(r0)

    def test_violin_half_sharp_effective_written_midi(self) -> None:
        sc = _load("golden_violin_half_sharp.musicxml")
        _, ev, _ = build_symbolic_inspection_tables(sc)
        row = next(r for r in ev if str(r.get("canonical_instrument") or "") == "violin")
        assert float(row["effective_written_midi"]) == pytest.approx(72.5)


class TestGoldenHarmonics:
    def test_diamond_conservative_unresolved_warning(self) -> None:
        sc = _load("harmonic_diamond_violin.musicxml")
        _, ev, _ = build_symbolic_inspection_tables(sc, harmonic_pitch_policy=HARMONIC_PITCH_POLICY_CONSERVATIVE)
        row = next(r for r in ev if str(r.get("canonical_instrument") or "") == "violin")
        assert row.get("harmonic_sounding_status") == "unresolved"
        warn = str(row.get("harmonic_warning") or "")
        assert warn
        assert "diamond" in warn.lower() or "sounding" in warn.lower()

    def test_artificial_infer_policy_resolves_vertical(self) -> None:
        sc = _load("harmonic_artificial_chord_cf.musicxml")
        _, ev, _ = build_symbolic_inspection_tables(
            sc,
            harmonic_pitch_policy=HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
        )
        vert = build_vertical_sonority_audit(ev)
        assert vert
        assert int(vert[0].get("harmonic_unresolved_count") or 0) == 0


class TestGoldenTechniqueUniformityKey:
    def test_plain_two_violins_all_default_technique_key(self) -> None:
        sc = _load("golden_two_violins_unison_c5.musicxml")
        an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        keys = {str(ev.get("technique_uniformity_key") or "") for ev in an.score_events}
        assert keys == {ORDINARY_DEFAULT_UNIFORMITY_KEY}

    def test_sul_pont_text_fixture_explicit_mixed_lowers_technique_uniformity(self) -> None:
        sc = _load("golden_two_violins_sul_pont_ordinario.musicxml")
        feats = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0).extract_hti_window(0.0, 4.0)
        assert feats is not None
        assert feats["technique_coverage_status"] == "explicit_mixed"
        assert float(feats["technique_uniformity"]) < 1.0
        dist = feats["technique_state_distribution"]
        assert ORDINARY_DEFAULT_UNIFORMITY_KEY in dist
        assert any("pont" in k.lower() or "sul" in k.lower() for k in dist)


class TestGoldenHTiQualitative:
    def test_close_register_unison_trombones_higher_hti_than_chromatic_spread(self) -> None:
        dense = _load("golden_four_trombones_unison_c.musicxml")
        sparse = _load("four_trombones_pp_crescendo_whole.musicxml")
        h_dense, f_dense = _hti_core_window(dense)
        h_sparse, f_sparse = _hti_core_window(sparse)
        assert math.isfinite(h_dense) and math.isfinite(h_sparse)
        assert h_dense > h_sparse
        assert float(f_dense["register_span_semitones"]) < float(f_sparse["register_span_semitones"])

    def test_same_instrument_pair_beats_cross_family_pair_on_hti(self) -> None:
        two_vn = _load("golden_two_violins_unison_c5.musicxml")
        vn_va = _load("golden_violin_viola_unison_c5.musicxml")
        vn_fl = _load("golden_violin_flute_unison_c5.musicxml")
        h_vv, _ = _hti_core_window(two_vn)
        h_vva, _ = _hti_core_window(vn_va)
        h_vnf, _ = _hti_core_window(vn_fl)
        assert math.isfinite(h_vv) and math.isfinite(h_vva) and math.isfinite(h_vnf)
        assert h_vv > h_vva
        assert h_vva > h_vnf

    def test_no_explicit_technique_implies_technique_uniformity_one(self) -> None:
        sc = _load("golden_two_violins_unison_c5.musicxml")
        _h, feats = _hti_core_window(sc)
        assert feats["technique_coverage_status"] == "ordinary_default_uniform"
        assert float(feats["technique_uniformity"]) == pytest.approx(1.0)
