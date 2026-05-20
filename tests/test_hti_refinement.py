"""H_TI refinements: taxonomy, dynamics ordinal, technique coverage, dynamic conditioning layer."""

from __future__ import annotations

import math

import numpy as np
import pytest
from music21 import expressions, instrument, meter, note, stream

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.hti_dynamic_conditioning import (
    attach_dynamic_conditioning_for_window,
    pick_dynamic_interpretation_label,
)
from homogeneity_analyser.analyzers.hti_dynamics import aggregate_notated_dynamics_for_window, dynamic_level_ordinal_01
from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.analyzers.technique_state import TechniqueState, technique_state_default_like
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_STRINGS,
)


def _attach(feats: dict, h_core: float, *, contrib=None, inst=None, fam=None, macro=None, pits=None, span=0.0) -> None:
    attach_dynamic_conditioning_for_window(
        feats,
        h_core,
        contrib or [],
        inst or {"solo": 1.0},
        fam or {"solo_fam": 1.0},
        macro or {"woodwinds": 1.0},
        pits if pits is not None else [60.0],
        float(span),
    )


def test_macrofamily_maps_subfamily() -> None:
    assert macrofamily_from_instrumental_subfamily(FAMILY_STRINGS) == "strings"
    assert macrofamily_from_instrumental_subfamily(FAMILY_CLARINETS) == "woodwinds"
    assert macrofamily_from_instrumental_subfamily(FAMILY_BRASS) == "brass"


def test_dynamic_coherence_single_level_is_one() -> None:
    def _ol(_e, _a, _b):
        return 1.0

    out = aggregate_notated_dynamics_for_window([{"dynamic_mark": "pp", "hairpin": "none"}], _ol, 0.0, 4.0)
    assert out["notated_dynamic_coherence"] == pytest.approx(1.0)
    assert out["dominant_dynamic"] == "pp"
    assert out["dynamic_coverage_status"] in ("explicit", "partial")


def test_dynamic_coherence_mixed_levels_below_one() -> None:
    def _ol(_e, _a, _b):
        return 1.0

    ev = [
        {"dynamic_mark": "pp", "hairpin": "none"},
        {"dynamic_mark": "ff", "hairpin": "none"},
    ]
    out = aggregate_notated_dynamics_for_window(ev, _ol, 0.0, 4.0)
    assert out["notated_dynamic_coherence"] < 1.0
    assert out["dynamic_divergence_detected"] is True


def test_pp_ordinal_below_ff() -> None:
    assert (dynamic_level_ordinal_01("pp") or 0) < (dynamic_level_ordinal_01("ff") or 0)


def test_register_span_uses_all_listed_pitch_classes() -> None:
    pitches = [60.0, 67.0, 64.0]
    arr = np.asarray(pitches, dtype=float)
    assert float(np.ptp(arr)) == pytest.approx(7.0)


def test_technique_default_like_detection() -> None:
    wind_plain = TechniqueState(family=FAMILY_FLUTES, instrument="flute", primary="ordinario")
    assert technique_state_default_like(wind_plain)
    horn_open = TechniqueState(family=FAMILY_BRASS, instrument="horn", primary="open")
    assert technique_state_default_like(horn_open)
    horn_stopped = TechniqueState(family=FAMILY_BRASS, instrument="horn", primary="stopped")
    assert not technique_state_default_like(horn_stopped)


def test_soft_blend_and_projection_risk_monotone() -> None:
    feats: dict = {
        "notated_dynamic_level_distribution": {"pp": 1.0},
        "notated_dynamic_coherence": 1.0,
        "dominant_dynamic": "pp",
        "dynamic_intensity_ordinal": 0.16,
        "dynamic_softness": 0.84,
        "dynamic_coverage_status": "explicit",
        "crescendo_active": False,
        "diminuendo_active": False,
        "dynamic_divergence_detected": False,
        "instrumental_subfamily_uniformity": 0.9,
        "family_uniformity": 0.9,
        "n_instruments": 3,
        "n_families": 1,
        "n_macrofamilies": 1,
    }
    _attach(
        feats, 0.7, inst={"a": 0.5, "b": 0.5}, fam={"fam": 1.0}, macro={"woodwinds": 1.0}, pits=[60.0, 62.0], span=2.0
    )
    assert feats["soft_blend_potential"] == pytest.approx(0.7 * 1.0 * 0.84, rel=1e-4)
    assert feats["family_heterogeneity"] == pytest.approx(0.1, rel=1e-4)
    assert math.isfinite(float(feats["projection_divergence_risk"]))


def test_ff_brass_projection_risk_high() -> None:
    feats: dict = {
        "notated_dynamic_coherence": 0.5,
        "dominant_dynamic": "ff",
        "dynamic_intensity_ordinal": 0.88,
        "dynamic_softness": 0.12,
        "dynamic_coverage_status": "explicit",
        "crescendo_active": False,
        "diminuendo_active": False,
        "dynamic_divergence_detected": True,
        "instrumental_subfamily_uniformity": 0.5,
        "family_uniformity": 0.5,
        "n_instruments": 4,
        "n_families": 1,
        "n_macrofamilies": 1,
    }
    contrib = [
        ({"instrument": "trumpet", "family": FAMILY_BRASS, "technique_state_id": "a", "dynamic_mark": "ff"}, 1.0),
        ({"instrument": "trombone", "family": FAMILY_BRASS, "technique_state_id": "b", "dynamic_mark": "ff"}, 1.0),
    ]
    inst_m = {"trumpet": 1.0, "trombone": 1.0}
    fam_m = {FAMILY_BRASS: 2.0}
    macro_m = {"brass": 2.0}
    _attach(feats, 0.55, contrib=contrib, inst=inst_m, fam=fam_m, macro=macro_m, pits=[60.0, 55.0], span=12.0)
    assert float(feats["projection_divergence_risk"]) > 0.25


def test_insufficient_dynamic_evidence_label() -> None:
    feats: dict = {
        "notated_dynamic_coherence": float("nan"),
        "dynamic_intensity_ordinal": float("nan"),
        "dynamic_softness": float("nan"),
        "dynamic_coverage_status": "unavailable",
        "crescendo_active": False,
        "diminuendo_active": False,
        "dynamic_divergence_detected": False,
        "instrumental_subfamily_uniformity": 0.8,
        "family_uniformity": 0.8,
        "n_instruments": 1,
        "n_families": 1,
        "n_macrofamilies": 1,
    }
    _attach(feats, 0.9)
    assert feats["dynamic_interpretation_label"] == "insufficient_dynamic_evidence"


def test_cross_family_masked_tonal_mass_label() -> None:
    feats: dict = {
        "notated_dynamic_coherence": 0.55,
        "dominant_dynamic": "fff",
        "dynamic_intensity_ordinal": 0.96,
        "dynamic_softness": 0.04,
        "dynamic_coverage_status": "explicit",
        "crescendo_active": False,
        "diminuendo_active": False,
        "dynamic_divergence_detected": False,
        "instrumental_subfamily_uniformity": 0.2,
        "family_uniformity": 0.2,
        "n_instruments": 6,
        "n_families": 3,
        "n_macrofamilies": 3,
    }
    contrib = [
        ({"instrument": "trumpet", "family": FAMILY_BRASS, "technique_state_id": "t1", "dynamic_mark": "fff"}, 1.0),
        ({"instrument": "violin", "family": FAMILY_STRINGS, "technique_state_id": "t2", "dynamic_mark": "fff"}, 1.0),
        ({"instrument": "flute", "family": "flutes", "technique_state_id": "t3", "dynamic_mark": "fff"}, 1.0),
    ]
    _attach(
        feats,
        0.65,
        contrib=contrib,
        inst={"trumpet": 1.0, "violin": 1.0, "flute": 1.0},
        fam={FAMILY_BRASS: 1.0, FAMILY_STRINGS: 1.0, "flutes": 1.0},
        macro={"brass": 1.0, "strings": 1.0, "woodwinds": 1.0},
        pits=[55.0, 60.0, 72.0],
        span=20.0,
    )
    assert feats["dynamic_interpretation_label"] == "cross_family_masked_tonal_mass_risk"


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


def _hti_an(sc: stream.Score) -> SymbolicTIHomogeneityAnalyzer:
    return SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)


def test_hti_four_horns_same_explicit_technique_uniformity_one() -> None:
    an = _hti_an(_horn_score_4("stopped"))
    feats = an.extract_hti_window(2.0, 4.0)
    assert feats is not None
    assert feats["technique_uniformity"] == pytest.approx(1.0)
    assert feats["technique_coverage_status"] == "explicit_uniform"


def test_hti_mixed_horn_techniques_uniformity_below_one() -> None:
    an = _hti_an(_horn_score_mixed(("stopped", "open", "stopped", "open")))
    feats = an.extract_hti_window(2.0, 4.0)
    assert feats is not None
    assert feats["technique_coverage_status"] == "explicit_mixed"
    assert float(feats["technique_uniformity"]) < 1.0


def test_hti_no_technique_ids_technique_term_dropped_from_mean() -> None:
    sc = _horn_score_4(None)
    an = _hti_an(sc)
    an._events = [
        {
            "offset": 0.0,
            "end": 4.0,
            "instrument": "horn",
            "family": FAMILY_BRASS,
            "technique_state_id": "",
            "technique_state": {},
            "pitches": [65.0],
            "dynamic_mark": "",
            "hairpin": "none",
        }
    ]
    feats = an.extract_hti_window(2.0, 4.0)
    assert feats is not None
    assert feats["technique_coverage_status"] == "unavailable"
    assert not math.isfinite(float(feats["technique_uniformity"]))
    h, diag, renorm = an.compute_H_TI(feats)
    assert "technique_uniformity" not in diag["components"]
    assert "technique_uniformity" not in renorm


def test_pick_brass_soft_convergence() -> None:
    feats = {
        "dynamic_coverage_status": "explicit",
        "string_technique_state_mixed": False,
        "n_macrofamilies": 1,
        "brass_family_active": True,
        "clarinet_family_active": False,
        "dominant_dynamic": "pp",
        "dynamic_intensity_ordinal": 0.16,
        "masked_tonal_mass_risk": 0.1,
        "projection_divergence_risk": 0.05,
        "transparent_blend_potential": 0.1,
        "same_family_mixed_instrument_mass": 0.25,
        "percussion_overlap_fraction": 0.0,
        "non_percussion_sustained_overlap_fraction": 1.0,
        "string_family_active": False,
    }
    assert pick_dynamic_interpretation_label(feats) == "soft_brass_intra_family_convergence_potential"


def test_pick_brass_projection_divergence() -> None:
    feats = {
        "dynamic_coverage_status": "explicit",
        "string_technique_state_mixed": False,
        "n_macrofamilies": 1,
        "brass_family_active": True,
        "clarinet_family_active": False,
        "dominant_dynamic": "ff",
        "dynamic_intensity_ordinal": 0.88,
        "masked_tonal_mass_risk": 0.2,
        "projection_divergence_risk": 0.55,
        "transparent_blend_potential": 0.05,
        "same_family_mixed_instrument_mass": 0.4,
        "bright_brass_overlap_fraction": 0.5,
        "percussion_overlap_fraction": 0.0,
        "non_percussion_sustained_overlap_fraction": 1.0,
        "string_family_active": False,
        "masking_context_weight": 0.35,
    }
    assert pick_dynamic_interpretation_label(feats) == "brass_projection_divergence_risk"


def test_pick_clarinet_soft_and_bright() -> None:
    soft = {
        "dynamic_coverage_status": "explicit",
        "string_technique_state_mixed": False,
        "n_macrofamilies": 1,
        "brass_family_active": False,
        "clarinet_family_active": True,
        "flute_family_active": False,
        "double_reed_family_active": False,
        "dominant_dynamic": "pp",
        "dynamic_intensity_ordinal": 0.16,
        "masked_tonal_mass_risk": 0.05,
        "projection_divergence_risk": 0.02,
        "transparent_blend_potential": 0.2,
        "same_family_mixed_instrument_mass": 0.0,
        "percussion_overlap_fraction": 0.0,
        "non_percussion_sustained_overlap_fraction": 1.0,
        "string_family_active": False,
    }
    assert pick_dynamic_interpretation_label(soft) == "clarinet_soft_blend_potential"
    bright = {**soft, "dominant_dynamic": "ff", "dynamic_intensity_ordinal": 0.88, "projection_divergence_risk": 0.6}
    assert pick_dynamic_interpretation_label(bright) == "clarinet_bright_projection_salience"


def test_pick_flute_labels() -> None:
    base = {
        "dynamic_coverage_status": "explicit",
        "string_technique_state_mixed": False,
        "n_macrofamilies": 1,
        "brass_family_active": False,
        "clarinet_family_active": False,
        "flute_family_active": True,
        "double_reed_family_active": False,
        "masked_tonal_mass_risk": 0.05,
        "projection_divergence_risk": 0.02,
        "transparent_blend_potential": 0.2,
        "same_family_mixed_instrument_mass": 0.0,
        "percussion_overlap_fraction": 0.0,
        "non_percussion_sustained_overlap_fraction": 1.0,
        "string_family_active": False,
    }
    low = {**base, "dominant_dynamic": "pp", "dynamic_intensity_ordinal": 0.16}
    assert pick_dynamic_interpretation_label(low) == "flute_soft_blend_potential"
    hi = {**base, "dominant_dynamic": "ff", "dynamic_intensity_ordinal": 0.88}
    assert pick_dynamic_interpretation_label(hi) == "flute_moderate_projection_salience"


def test_pick_double_reed_labels() -> None:
    base = {
        "dynamic_coverage_status": "explicit",
        "string_technique_state_mixed": False,
        "n_macrofamilies": 1,
        "brass_family_active": False,
        "clarinet_family_active": False,
        "flute_family_active": False,
        "double_reed_family_active": True,
        "masked_tonal_mass_risk": 0.05,
        "projection_divergence_risk": 0.02,
        "transparent_blend_potential": 0.2,
        "same_family_mixed_instrument_mass": 0.0,
        "percussion_overlap_fraction": 0.0,
        "non_percussion_sustained_overlap_fraction": 1.0,
        "string_family_active": False,
    }
    assert pick_dynamic_interpretation_label({**base, "dominant_dynamic": "p", "dynamic_intensity_ordinal": 0.3}) == (
        "double_reed_soft_blend_potential"
    )
    assert pick_dynamic_interpretation_label({**base, "dominant_dynamic": "ff", "dynamic_intensity_ordinal": 0.88}) == (
        "double_reed_projection_salience"
    )


def test_same_instruments_pp_vs_ff_soft_blend() -> None:
    """H_TI_core unchanged by dynamics; soft_blend_potential tracks softness × coherence."""
    base_dyn_pp = {
        "notated_dynamic_coherence": 1.0,
        "dominant_dynamic": "pp",
        "dynamic_intensity_ordinal": 0.16,
        "dynamic_softness": 0.84,
        "dynamic_coverage_status": "explicit",
        "crescendo_active": False,
        "diminuendo_active": False,
        "dynamic_divergence_detected": False,
        "notated_dynamic_level_distribution": {"pp": 1.0},
        "instrumental_subfamily_uniformity": 1.0,
        "family_uniformity": 1.0,
        "n_instruments": 1,
        "n_families": 1,
        "n_macrofamilies": 1,
    }
    f_pp = dict(base_dyn_pp)
    _attach(f_pp, 0.95, inst={"vn": 1.0}, fam={FAMILY_STRINGS: 1.0}, macro={"strings": 1.0}, pits=[60.0], span=0.0)
    f_ff = dict(base_dyn_pp)
    f_ff.update(
        {
            "dominant_dynamic": "ff",
            "dynamic_intensity_ordinal": 0.88,
            "dynamic_softness": 0.12,
            "notated_dynamic_level_distribution": {"ff": 1.0},
        }
    )
    _attach(f_ff, 0.95, inst={"vn": 1.0}, fam={FAMILY_STRINGS: 1.0}, macro={"strings": 1.0}, pits=[60.0], span=0.0)
    assert f_pp["soft_blend_potential"] > f_ff["soft_blend_potential"]
    assert f_ff["projection_divergence_risk"] > f_pp["projection_divergence_risk"]


def test_tuba_ff_projection_weight_dampened_vs_trumpet_trombone() -> None:
    feats_tuba: dict = {
        "notated_dynamic_coherence": 1.0,
        "dominant_dynamic": "ff",
        "dynamic_intensity_ordinal": 0.88,
        "dynamic_softness": 0.12,
        "dynamic_coverage_status": "explicit",
        "crescendo_active": False,
        "diminuendo_active": False,
        "dynamic_divergence_detected": False,
        "instrumental_subfamily_uniformity": 0.5,
        "family_uniformity": 0.5,
        "n_instruments": 2,
        "n_families": 1,
        "n_macrofamilies": 1,
    }
    ct_tuba = [({"instrument": "tuba", "family": FAMILY_BRASS, "technique_state_id": "a", "dynamic_mark": "ff"}, 1.0)]
    ct_tt = [
        ({"instrument": "trumpet", "family": FAMILY_BRASS, "technique_state_id": "a", "dynamic_mark": "ff"}, 1.0),
        ({"instrument": "trombone", "family": FAMILY_BRASS, "technique_state_id": "b", "dynamic_mark": "ff"}, 1.0),
    ]
    _attach(
        feats_tuba,
        0.7,
        contrib=ct_tuba,
        inst={"tuba": 1.0},
        fam={FAMILY_BRASS: 1.0},
        macro={"brass": 1.0},
        pits=[40.0],
        span=5.0,
    )
    feats_tt = dict(feats_tuba)
    _attach(
        feats_tt,
        0.7,
        contrib=ct_tt,
        inst={"trumpet": 0.5, "trombone": 0.5},
        fam={FAMILY_BRASS: 1.0},
        macro={"brass": 1.0},
        pits=[60.0, 55.0],
        span=8.0,
    )
    assert float(feats_tt["projection_divergence_risk"]) >= float(feats_tuba["projection_divergence_risk"]) - 1e-6
