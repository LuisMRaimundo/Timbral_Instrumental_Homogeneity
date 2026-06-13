"""
Musicological plausibility contracts for symbolic H_TI / H_TI_core.

Score-derived ordinal expectations on controlled music21 textures: instrument identity,
family/subfamily coherence, technique uniformity, register compactness, dynamic separation
from H_TI_core, sliding-window ranking stability, and export alias consistency.

Tests only. Not perceptual or acoustic validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from music21 import converter, dynamics, expressions, instrument as m21inst, meter, note, stream

from homogeneity_analyser.analyzers.hti import HTI_CSV_COLUMNS, SymbolicTIHomogeneityAnalyzer, hti_csv_row_dict
from homogeneity_analyser.analyzers.hti_adaptive_windows import HTI_EDGE_DROP, HTI_EDGE_INCLUDE, HTI_EDGE_MARK
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_CLARINETS, FAMILY_STRINGS

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"
_TOL = {"abs": 1e-9, "rel": 1e-9}
_WINDOW_CENTER = 2.0
_WINDOW_SIZE = 4.0


def _load_fixture(name: str):
    path = FIXTURE_DIR / name
    if not path.is_file():
        pytest.skip(f"missing fixture {name}")
    return converter.parse(str(path))


def _sustained_part(
    inst: m21inst.Instrument,
    *,
    written_pitch: str = "C5",
    dynamic: str | None = None,
    technique_mark: str | None = None,
) -> stream.Part:
    p = stream.Part()
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, inst)
    m = stream.Measure()
    offset = 0
    if dynamic is not None:
        m.insert(offset, dynamics.Dynamic(dynamic))
        offset += 1
    if technique_mark is not None:
        m.insert(offset, expressions.TextExpression(technique_mark))
        offset += 1
    m.insert(offset, note.Note(written_pitch, quarterLength=4.0))
    p.append(m)
    return p


def _score_from_parts(*parts: stream.Part) -> stream.Score:
    sc = stream.Score()
    for part in parts:
        sc.append(part)
    return sc


def _hti_analyzer(sc: stream.Score) -> SymbolicTIHomogeneityAnalyzer:
    return SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)


def _window_core_and_feats(
    sc: stream.Score,
    *,
    center: float = _WINDOW_CENTER,
    window: float = _WINDOW_SIZE,
) -> tuple[float, dict]:
    an = _hti_analyzer(sc)
    feats = an.extract_hti_window(center, window)
    if feats is None:
        return float("nan"), {}
    h_core, _, _ = an.compute_H_TI(feats)
    return float(h_core), feats


def _interior_core(sc: stream.Score, *, edge_policy: str = HTI_EDGE_MARK) -> float:
    an = _hti_analyzer(sc)
    results = an.analyze_hti(_WINDOW_SIZE, edge_policy=edge_policy)
    index = 2
    return float(results["H_TI_core"][index])


# ---------------------------------------------------------------------------
# A. Instrument identity plausibility
# ---------------------------------------------------------------------------


def test_same_clarinet_section_more_homogeneous_than_clarinet_trumpet_violin_mix() -> None:
    uniform = _score_from_parts(*[_sustained_part(m21inst.Clarinet()) for _ in range(4)])
    mixed = _score_from_parts(
        _sustained_part(m21inst.Clarinet()),
        _sustained_part(m21inst.Trumpet()),
        _sustained_part(m21inst.Violin()),
    )
    h_uniform, _ = _window_core_and_feats(uniform)
    h_mixed, _ = _window_core_and_feats(mixed)
    assert h_uniform > h_mixed


def test_two_violins_unison_not_below_violin_flute_cross_section() -> None:
    same_strings = _load_fixture("golden_two_violins_unison_c5.musicxml")
    cross_section = _load_fixture("golden_violin_flute_unison_c5.musicxml")
    h_same, _ = _window_core_and_feats(same_strings)
    h_cross, _ = _window_core_and_feats(cross_section)
    assert h_same >= h_cross
    assert h_same == pytest.approx(1.0, **_TOL)


def test_duplicate_clarinets_closer_than_cross_family_instrumentation() -> None:
    doubled = _score_from_parts(*[_sustained_part(m21inst.Clarinet()) for _ in range(2)])
    cross = _score_from_parts(
        _sustained_part(m21inst.Clarinet()),
        _sustained_part(m21inst.Horn()),
        _sustained_part(m21inst.Violin()),
    )
    h_doubled, f_d = _window_core_and_feats(doubled)
    h_cross, f_c = _window_core_and_feats(cross)
    assert h_doubled > h_cross
    assert f_d["instrument_uniformity"] > f_c["instrument_uniformity"]


# ---------------------------------------------------------------------------
# B. Family and subfamily plausibility
# ---------------------------------------------------------------------------


def test_same_family_flute_section_more_homogeneous_than_flute_horn_violin() -> None:
    woodwind_section = _score_from_parts(*[_sustained_part(m21inst.Flute()) for _ in range(4)])
    cross_family = _score_from_parts(
        _sustained_part(m21inst.Flute()),
        _sustained_part(m21inst.Flute()),
        _sustained_part(m21inst.Horn()),
        _sustained_part(m21inst.Violin()),
    )
    h_section, _ = _window_core_and_feats(woodwind_section)
    h_cross, _ = _window_core_and_feats(cross_family)
    assert h_section > h_cross
    assert h_section == pytest.approx(1.0, **_TOL)


def test_uniform_bb_clarinets_more_homogeneous_than_bb_plus_bass_clarinet() -> None:
    uniform_bb = _score_from_parts(*[_sustained_part(m21inst.Clarinet()) for _ in range(4)])
    subfamily_mix = _score_from_parts(
        *[_sustained_part(m21inst.Clarinet()) for _ in range(3)],
        _sustained_part(m21inst.BassClarinet()),
    )
    h_uniform, f_u = _window_core_and_feats(uniform_bb)
    h_mix, f_m = _window_core_and_feats(subfamily_mix)
    assert h_uniform > h_mix
    assert f_u["instrument_uniformity"] == pytest.approx(1.0, **_TOL)
    assert float(f_m["instrument_uniformity"]) < 1.0


def test_known_clarinet_section_not_below_unknown_other_instrument_texture() -> None:
    coherent = _score_from_parts(*[_sustained_part(m21inst.Clarinet()) for _ in range(4)])
    unknown = m21inst.Instrument()
    unknown.instrumentName = "Mystery Widget XYZ"
    diluted = _score_from_parts(
        *[_sustained_part(m21inst.Clarinet()) for _ in range(2)],
        _sustained_part(unknown),
        _sustained_part(unknown),
    )
    h_coherent, f_c = _window_core_and_feats(coherent)
    h_diluted, f_d = _window_core_and_feats(diluted)
    assert h_coherent > h_diluted
    assert f_c["family_uniformity"] == pytest.approx(1.0, **_TOL)
    assert float(f_d["family_uniformity"]) < 1.0


# ---------------------------------------------------------------------------
# C. Technique plausibility
# ---------------------------------------------------------------------------


def _horn_score_uniform_technique(mark: str) -> stream.Score:
    return _score_from_parts(*[_sustained_part(m21inst.Horn(), technique_mark=mark) for _ in range(4)])


def _horn_score_alternating_techniques() -> stream.Score:
    marks = ("stopped", "open", "stopped", "open")
    return _score_from_parts(*[_sustained_part(m21inst.Horn(), technique_mark=m) for m in marks])


def test_same_horn_technique_more_homogeneous_than_mixed_stopped_open() -> None:
    uniform = _horn_score_uniform_technique("stopped")
    mixed = _horn_score_alternating_techniques()
    h_uniform, f_u = _window_core_and_feats(uniform)
    h_mixed, f_m = _window_core_and_feats(mixed)
    assert h_uniform > h_mixed
    assert f_u["technique_uniformity"] == pytest.approx(1.0, **_TOL)
    assert f_m["technique_coverage_status"] == "explicit_mixed"
    assert float(f_m["technique_uniformity"]) < 1.0


def test_technique_mix_lowers_technique_component_without_corrupting_family_identity() -> None:
    uniform = _horn_score_uniform_technique("open")
    mixed = _horn_score_alternating_techniques()
    _, f_u = _window_core_and_feats(uniform)
    _, f_m = _window_core_and_feats(mixed)
    assert f_u["family_uniformity"] == pytest.approx(f_m["family_uniformity"], **_TOL)
    assert f_u["instrument_uniformity"] == pytest.approx(f_m["instrument_uniformity"], **_TOL)
    assert float(f_m["technique_uniformity"]) < float(f_u["technique_uniformity"])


def test_clarinet_breathy_vs_ordinario_reduces_technique_uniformity() -> None:
    ordinary = _score_from_parts(
        _sustained_part(m21inst.Clarinet()),
        _sustained_part(m21inst.Clarinet(), technique_mark="breathy"),
    )
    uniform = _score_from_parts(*[_sustained_part(m21inst.Clarinet()) for _ in range(2)])
    h_ord, f_ord = _window_core_and_feats(ordinary)
    h_uni, f_uni = _window_core_and_feats(uniform)
    assert h_uni > h_ord
    assert float(f_ord["technique_uniformity"]) < float(f_uni["technique_uniformity"])


# ---------------------------------------------------------------------------
# D. Register plausibility
# ---------------------------------------------------------------------------


def test_compact_unison_register_more_homogeneous_than_octave_spread() -> None:
    compact = _score_from_parts(
        _sustained_part(m21inst.Violin(), written_pitch="C4"),
        _sustained_part(m21inst.Violin(), written_pitch="C4"),
    )
    spread = _score_from_parts(
        _sustained_part(m21inst.Violin(), written_pitch="C3"),
        _sustained_part(m21inst.Violin(), written_pitch="C5"),
    )
    h_compact, f_c = _window_core_and_feats(compact)
    h_spread, f_s = _window_core_and_feats(spread)
    assert h_compact > h_spread
    assert f_c["register_span_semitones"] == pytest.approx(0.0, **_TOL)
    assert float(f_s["register_span_semitones"]) > float(f_c["register_span_semitones"])


def test_clarinet_written_unison_uses_sounding_pitch_for_register_coherence() -> None:
    sounding_unison = _score_from_parts(
        _sustained_part(m21inst.Clarinet(), written_pitch="C4"),
        _sustained_part(m21inst.Clarinet(), written_pitch="C4"),
    )
    written_step_apart = _score_from_parts(
        _sustained_part(m21inst.Clarinet(), written_pitch="C4"),
        _sustained_part(m21inst.Clarinet(), written_pitch="D4"),
    )
    h_unison, f_u = _window_core_and_feats(sounding_unison)
    h_step, f_s = _window_core_and_feats(written_step_apart)
    assert h_unison > h_step
    assert f_u["register_span_semitones"] == pytest.approx(0.0, **_TOL)
    assert float(f_s["register_span_semitones"]) > 0.0


def test_transposing_clarinets_same_concert_pitch_register_compactness_high() -> None:
    """Written C4 on both B♭ clarinets → identical concert sounding register."""
    sc = _score_from_parts(
        _sustained_part(m21inst.Clarinet(), written_pitch="C4"),
        _sustained_part(m21inst.Clarinet(), written_pitch="C4"),
    )
    an = _hti_analyzer(sc)
    assert len(an._events) == 2
    assert an._events[0]["pitches"] == an._events[1]["pitches"]
    h_core, feats = _window_core_and_feats(sc)
    assert h_core == pytest.approx(1.0, **_TOL)
    assert feats["register_span_semitones"] == pytest.approx(0.0, **_TOL)


# ---------------------------------------------------------------------------
# E. Dynamics / notation-context plausibility
# ---------------------------------------------------------------------------


def test_uniform_dynamics_do_not_reduce_h_ti_core_relative_to_mixed_dynamics() -> None:
    uniform = _score_from_parts(
        _sustained_part(m21inst.Violin(), dynamic="mf"),
        _sustained_part(m21inst.Violin(), dynamic="mf"),
    )
    divergent = _score_from_parts(
        _sustained_part(m21inst.Violin(), dynamic="pp"),
        _sustained_part(m21inst.Violin(), dynamic="ff"),
    )
    h_uniform, f_u = _window_core_and_feats(uniform)
    h_divergent, f_d = _window_core_and_feats(divergent)
    assert h_uniform == pytest.approx(h_divergent, **_TOL)
    assert f_u["notated_dynamic_coherence"] == pytest.approx(1.0, **_TOL)
    assert float(f_d["notated_dynamic_coherence"]) < 1.0
    assert f_d["dynamic_divergence_detected"] is True


def test_pp_and_ff_uniform_textures_share_h_ti_core() -> None:
    pp = _score_from_parts(
        _sustained_part(m21inst.Violin(), dynamic="pp"),
        _sustained_part(m21inst.Violin(), dynamic="pp"),
    )
    ff = _score_from_parts(
        _sustained_part(m21inst.Violin(), dynamic="ff"),
        _sustained_part(m21inst.Violin(), dynamic="ff"),
    )
    h_pp, f_pp = _window_core_and_feats(pp)
    h_ff, f_ff = _window_core_and_feats(ff)
    assert h_pp == pytest.approx(h_ff, **_TOL)
    assert f_pp["dominant_dynamic"] == "pp"
    assert f_ff["dominant_dynamic"] == "ff"


def test_dynamic_layer_separate_from_core_on_analyze_series() -> None:
    sc = _score_from_parts(
        _sustained_part(m21inst.Flute(), dynamic="pp"),
        _sustained_part(m21inst.Flute(), dynamic="pp"),
    )
    an = _hti_analyzer(sc)
    results = an.analyze_hti(_WINDOW_SIZE)
    idx = 2
    assert results["H_TI_core"][idx] == pytest.approx(results["H_TI"][idx], **_TOL)
    assert results["soft_blend_potential"][idx] is not None


# ---------------------------------------------------------------------------
# F. Sliding-window plausibility
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("edge_policy", (HTI_EDGE_INCLUDE, HTI_EDGE_MARK, HTI_EDGE_DROP))
def test_homogeneous_violin_pair_ranks_above_violin_flute_under_edge_policies(edge_policy: str) -> None:
    uniform = _load_fixture("golden_two_violins_unison_c5.musicxml")
    mixed = _load_fixture("golden_violin_flute_unison_c5.musicxml")
    h_uniform = _interior_core(uniform, edge_policy=edge_policy)
    h_mixed = _interior_core(mixed, edge_policy=edge_policy)
    assert h_uniform > h_mixed


def test_edge_partial_flags_are_diagnostic_without_inverting_interior_ranking() -> None:
    uniform = _load_fixture("golden_two_violins_unison_c5.musicxml")
    mixed = _load_fixture("golden_violin_flute_unison_c5.musicxml")
    an_u = _hti_analyzer(uniform)
    an_m = _hti_analyzer(mixed)
    ru = an_u.analyze_hti(_WINDOW_SIZE, edge_policy=HTI_EDGE_MARK)
    rm = an_m.analyze_hti(_WINDOW_SIZE, edge_policy=HTI_EDGE_MARK)
    assert ru["edge_window"][0] is True
    assert float(ru["H_TI_core"][0]) == pytest.approx(float(ru["H_TI_core"][2]), **_TOL)
    assert float(ru["H_TI_core"][2]) > float(rm["H_TI_core"][2])


def test_stable_clarinet_section_interior_window_stays_high() -> None:
    sc = _score_from_parts(*[_sustained_part(m21inst.Clarinet()) for _ in range(4)])
    results = _hti_analyzer(sc).analyze_hti(_WINDOW_SIZE)
    assert results["H_TI_core"][2] == pytest.approx(1.0, **_TOL)
    assert results["hti_comparability_class"][2] == "full_4_component"


# ---------------------------------------------------------------------------
# G. Export plausibility
# ---------------------------------------------------------------------------


def test_export_row_preserves_homogeneity_ranking_between_textures() -> None:
    uniform = _load_fixture("golden_two_violins_unison_c5.musicxml")
    mixed = _load_fixture("golden_violin_flute_unison_c5.musicxml")
    ru = _hti_analyzer(uniform).analyze_hti(_WINDOW_SIZE)
    rm = _hti_analyzer(mixed).analyze_hti(_WINDOW_SIZE)
    idx = 2
    row_u = {
        "H_TI": ru["H_TI"][idx],
        "H_TI_core": ru["H_TI_core"][idx],
        "H_TI_strict": ru["H_TI_strict"][idx],
        "t_quarterLength": ru["t"][idx],
        "hti_comparability_class": ru["hti_comparability_class"][idx],
        "edge_window": ru["edge_window"][idx],
        "instrument_uniformity": ru["instrument_uniformity"][idx],
        "family_uniformity": ru["family_uniformity"][idx],
        "technique_uniformity": ru["technique_uniformity"][idx],
        "register_proximity": ru["register_proximity"][idx],
    }
    row_m = {
        "H_TI": rm["H_TI"][idx],
        "H_TI_core": rm["H_TI_core"][idx],
        "H_TI_strict": rm["H_TI_strict"][idx],
        "t_quarterLength": rm["t"][idx],
        "hti_comparability_class": rm["hti_comparability_class"][idx],
        "edge_window": rm["edge_window"][idx],
        "instrument_uniformity": rm["instrument_uniformity"][idx],
        "family_uniformity": rm["family_uniformity"][idx],
        "technique_uniformity": rm["technique_uniformity"][idx],
        "register_proximity": rm["register_proximity"][idx],
    }
    out_u = hti_csv_row_dict(row_u)
    out_m = hti_csv_row_dict(row_m)
    assert float(out_u["H_TI_core"]) > float(out_m["H_TI_core"])
    assert out_u["H_TI"] == out_u["H_TI_strict"]
    assert out_m["H_TI"] == out_m["H_TI_strict"]


def test_export_registry_includes_core_aliases_and_window_diagnostics() -> None:
    required = (
        "H_TI",
        "H_TI_core",
        "H_TI_strict",
        "hti_comparability_class",
        "edge_window",
        "window_coverage_ratio",
        "instrument_uniformity",
        "instrumental_subfamily_uniformity",
        "technique_uniformity",
        "register_proximity",
        "notated_dynamic_coherence",
        "dynamic_interpretation_label",
    )
    for key in required:
        assert key in HTI_CSV_COLUMNS
