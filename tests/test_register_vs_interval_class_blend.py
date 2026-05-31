"""Register compactness vs interval-class symbolic blend factor (orthogonal layers)."""

from __future__ import annotations

import math

from homogeneity_analyser.analyzers.hti import compute_register_compactness_fields
from homogeneity_analyser.analyzers.hti_analyze_series import hti_pitch_occurrences_for_symbolic_layers
from homogeneity_analyser.analyzers.symbolic_blend_layers import (
    compute_interval_class_blend_factor,
    load_symbolic_blend_conditioning_profile,
)

REF = 7.0


def test_c4_d4_high_register_compactness_lower_interval_class_than_c4_c5() -> None:
    """C4–D4: smaller registral span than C4–C5; interval class seconds vs octave/unison class."""
    cd = compute_register_compactness_fields([(60.0, 1.0), (62.0, 1.0)], REF)
    cc = compute_register_compactness_fields([(60.0, 1.0), (72.0, 1.0)], REF)
    assert float(cd["register_compactness"]) > float(cc["register_compactness"])
    cfg = load_symbolic_blend_conditioning_profile()
    ic_cd = compute_interval_class_blend_factor([60.0, 62.0], None, cfg=cfg)["interval_class_blend_factor"]
    ic_cc = compute_interval_class_blend_factor([60.0, 72.0], None, cfg=cfg)["interval_class_blend_factor"]
    assert math.isfinite(ic_cd) and math.isfinite(ic_cc)
    assert ic_cc > ic_cd + 1e-6


def test_c4_g4_high_interval_class_fifth() -> None:
    cfg = load_symbolic_blend_conditioning_profile()
    ic = compute_interval_class_blend_factor([60.0, 67.0], None, cfg=cfg)["interval_class_blend_factor"]
    assert ic > 0.85


def test_c4_f_sharp4_low_interval_class_tritone() -> None:
    cfg = load_symbolic_blend_conditioning_profile()
    ic = compute_interval_class_blend_factor([60.0, 66.0], None, cfg=cfg)["interval_class_blend_factor"]
    assert ic < 0.4


def test_single_pitch_interval_class_nan_no_crash() -> None:
    cfg = load_symbolic_blend_conditioning_profile()
    out = compute_interval_class_blend_factor([60.0], None, cfg=cfg)
    assert math.isnan(float(out["interval_class_blend_factor"]))
    assert out["pairwise_interval_class_coverage_status"] == "insufficient_pairs"


def test_octave_doubles_attenuation_reduces_factor_vs_simple_octave() -> None:
    """C4–C5 (12 st) vs C4–C6 (24 st): same mod-12 class; wider span lowers score via attenuation."""
    cfg = load_symbolic_blend_conditioning_profile()
    ic12 = compute_interval_class_blend_factor([60.0, 72.0], None, cfg=cfg)["interval_class_blend_factor"]
    ic24 = compute_interval_class_blend_factor([60.0, 84.0], None, cfg=cfg)["interval_class_blend_factor"]
    assert ic12 > ic24 + 1e-6


def test_unpitched_percussion_empty_pitch_list_no_crash() -> None:
    ev = {
        "instrument": "bass drum",
        "family": "percussion",
        "pitches": [],
        "technique_uniformity_key": "ordinary_default_uniform",
    }
    po = hti_pitch_occurrences_for_symbolic_layers([(ev, 1.0)])
    assert po == []
    out = compute_interval_class_blend_factor([p for p, _ in po], None)
    assert math.isnan(float(out["interval_class_blend_factor"]))


def test_register_aliases_match_legacy_keys() -> None:
    b = compute_register_compactness_fields([(60.0, 1.0), (64.0, 1.0)], REF)
    assert b["register_span_factor"] == b["register_span_proximity"]
    assert b["register_pair_distance_factor"] == b["pairwise_interval_proximity"]
