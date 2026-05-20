"""Audit tests: formula, separation, taxonomy, and export stability for H_TA_acoustic_proxy."""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from homogeneity_analyser.analyzers.hti import (
    HTI_EXPORT_TIME_SERIES_KEYS,
    SymbolicTIHomogeneityAnalyzer,
    compute_register_compactness_fields,
)
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
    acoustic_tags_for_event,
    compute_timbral_acoustic_affinity,
    pairwise_acoustic_kernel,
)
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
    disabled_acoustic_proxy_bundle as proxy_disabled,
)
from homogeneity_analyser.services.json_export import HTI_EXPORT_SCHEMA_VERSION
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_KEYBOARD,
    FAMILY_OBOES,
    FAMILY_OTHER,
    FAMILY_PERCUSSION,
    FAMILY_SAXOPHONES,
    FAMILY_STRINGS,
)
from tests.test_timbral_acoustic_proxy_ranking import _affinity, _ev, _hti_core


def test_mass_shares_sum_to_one() -> None:
    contrib = [(_ev("flute", FAMILY_FLUTES, [72.0])[0], 2.0), (_ev("oboe", FAMILY_OBOES, [70.0])[0], 1.0)]
    out = compute_timbral_acoustic_affinity(contrib, {}, profile="conservative")
    assert "p_sum=" in out["timbral_acoustic_pairwise_summary"]
    assert float(out["timbral_acoustic_affinity"]) <= 1.0 + 1e-9


def test_pairwise_kernel_symmetric() -> None:
    a, _ = _ev("trumpet", FAMILY_BRASS, [70.0])
    b, _ = _ev("horn", FAMILY_BRASS, [65.0])
    k_ab, _ = pairwise_acoustic_kernel(a, b, profile="conservative")
    k_ba, _ = pairwise_acoustic_kernel(b, a, profile="conservative")
    assert k_ab == pytest.approx(k_ba, abs=1e-9)
    assert 0.0 <= k_ab <= 1.0


def test_acoustic_proxy_does_not_equate_chromatic_compactness_with_blend() -> None:
    """register_compactness may favour C4–D4; register_tessitura must not blindly copy that."""
    from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
        load_acoustic_timbral_taxonomy,
        register_tessitura_similarity,
    )

    tax = load_acoustic_timbral_taxonomy()
    v60, _ = _ev("violin", FAMILY_STRINGS, [60.0])
    va62, _ = _ev("viola", FAMILY_STRINGS, [62.0])
    vc84, _ = _ev("cello", FAMILY_STRINGS, [84.0])
    reg_near = register_tessitura_similarity(v60, va62, tax)
    reg_wide = register_tessitura_similarity(v60, vc84, tax)
    assert reg_near is not None and reg_wide is not None
    assert float(reg_near) > float(reg_wide)
    rc_semi = compute_register_compactness_fields([(60.0, 1.0), (62.0, 1.0)], 7.0)["register_compactness"]
    rc_wide = compute_register_compactness_fields([(60.0, 1.0), (84.0, 1.0)], 7.0)["register_compactness"]
    assert float(rc_semi) > float(rc_wide)


def test_flute_piccolo_high_but_not_identical_extreme_register() -> None:
    fl, _ = _ev("flute", FAMILY_FLUTES, [72.0])
    pic, _ = _ev("piccolo", FAMILY_FLUTES, [88.0])
    aff = _affinity([(fl, 1.0), (pic, 1.0)])
    assert 0.55 < aff < 0.98
    k_ident, _ = pairwise_acoustic_kernel(fl, fl, profile="conservative")
    assert k_ident == pytest.approx(1.0)


def test_oboe_cor_anglais_high_moderate() -> None:
    o, _ = _ev("oboe", FAMILY_OBOES, [70.0])
    ca, _ = _ev("cor anglais", FAMILY_OBOES, [65.0])
    assert _affinity([(o, 1.0), (ca, 1.0)]) > 0.7


def test_oboe_bassoon_moderate_not_identical() -> None:
    o, _ = _ev("oboe", FAMILY_OBOES, [70.0])
    bn, _ = _ev("bassoon", FAMILY_BASSOONS, [65.0])
    aff = _affinity([(o, 1.0), (bn, 1.0)])
    assert 0.45 < aff < 0.92


def test_clarinet_sax_below_clarinet_bass_clarinet() -> None:
    tuk = "cl|ord"
    bc, _ = _ev("b flat clarinet", FAMILY_CLARINETS, [60.0], technique_uniformity_key=tuk)
    bcl, _ = _ev("bass clarinet", FAMILY_CLARINETS, [55.0], technique_uniformity_key=tuk)
    sx, _ = _ev("soprano saxophone", FAMILY_SAXOPHONES, [60.0], technique_uniformity_key=tuk)
    aff_bc = _affinity([(bc, 1.0), (bcl, 1.0)])
    aff_cs = _affinity([(bc, 1.0), (sx, 1.0)])
    assert aff_bc > aff_cs + 0.03


def test_horn_trumpet_below_identical_trumpets() -> None:
    open_st = {"family": FAMILY_BRASS, "primary": "open", "mute": "none"}
    t1, _ = _ev("trumpet", FAMILY_BRASS, [70.0], technique_state={**open_st, "instrument": "trumpet"})
    t2, _ = _ev("trumpet", FAMILY_BRASS, [70.0], technique_state={**open_st, "instrument": "trumpet"})
    h, _ = _ev("horn", FAMILY_BRASS, [65.0], technique_state={**open_st, "instrument": "horn"})
    assert _affinity([(t1, 1.0), (t2, 1.0)]) == pytest.approx(1.0)
    assert _affinity([(t1, 1.0), (h, 1.0)]) < 0.95


def test_horn_stopped_lower_than_horn_open() -> None:
    open_st = {"family": FAMILY_BRASS, "instrument": "horn", "primary": "open", "mute": "none"}
    stop_st = {"family": FAMILY_BRASS, "instrument": "horn", "primary": "stopped", "mute": "none"}
    ho, _ = _ev("horn", FAMILY_BRASS, [65.0], technique_state=open_st)
    hs, _ = _ev("horn", FAMILY_BRASS, [65.0], technique_state=stop_st)
    k_open, _ = pairwise_acoustic_kernel(ho, ho, profile="conservative")
    k_mix, _ = pairwise_acoustic_kernel(ho, hs, profile="conservative")
    assert k_open == pytest.approx(1.0)
    assert k_mix < 0.75


def test_violin_arco_pizzicato_lower_than_arco_arco() -> None:
    arco = {"family": FAMILY_STRINGS, "instrument": "violin", "primary": "ordinario", "mute": "none"}
    pizz = {"family": FAMILY_STRINGS, "instrument": "violin", "primary": "pizzicato", "mute": "none"}
    v1, _ = _ev("violin", FAMILY_STRINGS, [62.0], technique_state=arco)
    v2, _ = _ev("violin", FAMILY_STRINGS, [62.0], technique_state=arco)
    vp, _ = _ev("violin", FAMILY_STRINGS, [62.0], technique_state=pizz)
    assert _affinity([(v1, 1.0), (vp, 1.0)]) < _affinity([(v1, 1.0), (v2, 1.0)]) - 0.2


def test_harp_pizzicato_strings_partial_not_identity() -> None:
    pizz = {"family": FAMILY_STRINGS, "instrument": "violin", "primary": "pizzicato", "mute": "none"}
    v, _ = _ev("violin", FAMILY_STRINGS, [62.0], technique_state=pizz)
    h, _ = _ev("harp", FAMILY_STRINGS, [62.0])
    aff = _affinity([(v, 1.0), (h, 1.0)])
    assert 0.25 < aff < 0.75


def test_piano_harp_not_strongly_homogeneous() -> None:
    p, _ = _ev("piano", FAMILY_KEYBOARD, [60.0])
    h, _ = _ev("harp", FAMILY_STRINGS, [60.0])
    assert _affinity([(p, 1.0), (h, 1.0)]) < 0.65
    k_ph, _ = pairwise_acoustic_kernel(p, h, profile="conservative")
    assert k_ph < 0.5


def test_unknown_instrument_low_confidence_tags() -> None:
    u, _ = _ev("mystery_instrument_xyz", FAMILY_OTHER, [60.0])
    tags = acoustic_tags_for_event(u)
    assert tags["source_mechanism"] == "unknown"
    assert "unknown" in tags["taxonomy_confidence"] or "fallback" in tags["taxonomy_confidence"]
    out = compute_timbral_acoustic_affinity([(u, 1.0), (_ev("flute", FAMILY_FLUTES, [60.0])[0], 1.0)], {})
    assert "taxonomy_fallback_or_unknown" in out["timbral_acoustic_affinity_evidence_status"]


def test_unpitched_percussion_register_omitted() -> None:
    sd, _ = _ev("snare drum", FAMILY_PERCUSSION, [])
    tb, _ = _ev("timpani", FAMILY_PERCUSSION, [48.0])
    out = compute_timbral_acoustic_affinity([(sd, 1.0), (tb, 1.0)], {}, profile="conservative")
    assert math.isfinite(float(out["timbral_acoustic_affinity"]))


def test_analyze_hti_core_hti_strict_unchanged_when_acoustic_proxy_toggled() -> None:
    """Full analyze_hti: H_TI_core, H_TI, H_TI_strict must not depend on include_acoustic_proxy."""
    from music21 import instrument, note, stream

    sc = stream.Score()
    for inst_cls in (instrument.Violin, instrument.Viola):
        p = stream.Part()
        p.insert(0, inst_cls())
        m = stream.Measure()
        m.insert(0, note.Note("G4", quarterLength=4.0))
        p.append(m)
        sc.append(p)
    off = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0, include_acoustic_proxy=False)
    on = SymbolicTIHomogeneityAnalyzer(
        music21_score=sc,
        time_step=1.0,
        include_acoustic_proxy=True,
        acoustic_proxy_profile="conservative",
    )
    r_off = off.analyze_hti(4.0)
    r_on = on.analyze_hti(4.0)
    assert len(r_off["t"]) == len(r_on["t"]) >= 1
    for key in ("H_TI_core", "H_TI", "H_TI_strict"):
        np.testing.assert_allclose(r_off[key], r_on[key], rtol=0.0, atol=0.0, equal_nan=True)
    assert any(math.isfinite(float(x)) for x in r_on["H_TA_acoustic_proxy"])
    assert all(math.isnan(float(x)) for x in r_off["H_TA_acoustic_proxy"])


def _assert_evidence_consistent_with_components(
    out: dict,
    *,
    feats: dict | None = None,
) -> None:
    """Components dict and evidence_status must agree; optional window coverage flags."""
    comps = out.get("timbral_acoustic_affinity_components") or {}
    ev = str(out.get("timbral_acoustic_affinity_evidence_status") or "")
    feat = feats or {}
    dyn_cov = str(feat.get("dynamic_coverage_status") or "").lower()
    tech_cov = str(feat.get("technique_coverage_status") or "").lower()

    if "dynamic" in comps:
        assert "dynamic_omitted" not in ev
        if dyn_cov.startswith("explicit") or dyn_cov == "partial":
            assert "dynamic_used_explicit_notated" in ev
        else:
            assert "dynamic_active" in ev
    else:
        assert "dynamic_omitted" in ev

    if "technique" in comps:
        assert "technique_omitted" not in ev
        tv = float(comps["technique"])
        if math.isfinite(tv) and tv >= 0.995:
            assert "technique_default_only" in ev or "technique_no_special_evidence" in ev
        else:
            assert "technique_active" in ev
    else:
        assert "technique_omitted" in ev or "technique_omitted_or_partial" in ev

    if tech_cov == "explicit_uniform" and "technique" in comps and float(comps["technique"]) >= 0.995:
        assert "technique_default_only" in ev


def test_evidence_dynamic_explicit_when_component_present() -> None:
    e1, _ = _ev("flute", FAMILY_FLUTES, [72.0], dynamic_mark="mf")
    e2, _ = _ev("oboe", FAMILY_OBOES, [70.0], dynamic_mark="mf")
    feats = {"dynamic_coverage_status": "explicit", "technique_coverage_status": "explicit_mixed"}
    out = compute_timbral_acoustic_affinity([(e1, 1.0), (e2, 1.0)], feats, profile="conservative")
    assert "dynamic" in out["timbral_acoustic_affinity_components"]
    _assert_evidence_consistent_with_components(out, feats=feats)


def test_evidence_dynamic_not_omitted_when_same_instrument_shortcircuit() -> None:
    arco = {"family": FAMILY_STRINGS, "instrument": "violin", "primary": "ordinario", "mute": "none"}
    v1, _ = _ev("violin", FAMILY_STRINGS, [62.0], technique_state=arco, dynamic_mark="mf")
    v2, _ = _ev("violin", FAMILY_STRINGS, [64.0], technique_state=arco, dynamic_mark="mf")
    feats = {"dynamic_coverage_status": "explicit", "technique_coverage_status": "explicit_uniform"}
    out = compute_timbral_acoustic_affinity([(v1, 1.0), (v2, 1.0)], feats, profile="conservative")
    assert "dynamic" in out["timbral_acoustic_affinity_components"]
    _assert_evidence_consistent_with_components(out, feats=feats)


def test_evidence_technique_default_only_for_uniform_ordinary() -> None:
    arco = {"family": FAMILY_STRINGS, "instrument": "violin", "primary": "ordinario", "mute": "none"}
    v1, _ = _ev("violin", FAMILY_STRINGS, [62.0], technique_state=arco, dynamic_mark="mf")
    v2, _ = _ev("violin", FAMILY_STRINGS, [64.0], technique_state=arco, dynamic_mark="mf")
    feats = {"technique_coverage_status": "explicit_uniform", "dynamic_coverage_status": "explicit"}
    out = compute_timbral_acoustic_affinity([(v1, 1.0), (v2, 1.0)], feats)
    assert out["timbral_acoustic_affinity_components"]["technique"] == pytest.approx(1.0)
    assert "technique_default_only" in out["timbral_acoustic_affinity_evidence_status"]
    _assert_evidence_consistent_with_components(out, feats=feats)


def test_evidence_technique_active_when_mixed_techniques() -> None:
    arco = {"family": FAMILY_STRINGS, "instrument": "violin", "primary": "ordinario", "mute": "none"}
    pizz = {"family": FAMILY_STRINGS, "instrument": "violin", "primary": "pizzicato", "mute": "none"}
    v1, _ = _ev("violin", FAMILY_STRINGS, [62.0], technique_state=arco)
    vp, _ = _ev("violin", FAMILY_STRINGS, [62.0], technique_state=pizz)
    feats = {"technique_coverage_status": "explicit_mixed", "dynamic_coverage_status": "explicit"}
    out = compute_timbral_acoustic_affinity([(v1, 1.0), (vp, 1.0)], feats)
    assert "technique" in out["timbral_acoustic_affinity_components"]
    assert float(out["timbral_acoustic_affinity_components"]["technique"]) < 0.995
    assert "technique_active" in out["timbral_acoustic_affinity_evidence_status"]
    _assert_evidence_consistent_with_components(out, feats=feats)


def test_evidence_dynamic_omitted_when_no_marks() -> None:
    e1, _ = _ev("flute", FAMILY_FLUTES, [72.0], dynamic_mark="")
    e2, _ = _ev("oboe", FAMILY_OBOES, [70.0], dynamic_mark="")
    feats = {"dynamic_coverage_status": "unavailable", "technique_coverage_status": "explicit_mixed"}
    out = compute_timbral_acoustic_affinity([(e1, 1.0), (e2, 1.0)], feats)
    assert "dynamic" not in out["timbral_acoustic_affinity_components"]
    assert "dynamic_omitted" in out["timbral_acoustic_affinity_evidence_status"]


def test_hti_core_identical_with_proxy_disabled_fields() -> None:
    contrib = [
        (_ev("violin", FAMILY_STRINGS, [62.0])[0], 1.0),
        (_ev("viola", FAMILY_STRINGS, [60.0])[0], 1.0),
    ]
    h = _hti_core(contrib)
    assert math.isfinite(h)
    dis = proxy_disabled()
    assert dis["acoustic_proxy_not_audio_analysis"] is True
    assert dis["acoustic_proxy_validation_status"] == "score_derived_unvalidated"


def test_hti_export_schema_and_acoustic_keys() -> None:
    from homogeneity_analyser.analyzers.timbral_acoustic_proxy import HTI_ACOUSTIC_PROXY_SERIES_KEYS

    assert HTI_EXPORT_SCHEMA_VERSION == "3.0"
    for k in HTI_ACOUSTIC_PROXY_SERIES_KEYS:
        assert k in HTI_EXPORT_TIME_SERIES_KEYS


def test_pairwise_export_json_serialisable() -> None:
    fl, _ = _ev("flute", FAMILY_FLUTES, [72.0])
    ob, _ = _ev("oboe", FAMILY_OBOES, [70.0])
    out = compute_timbral_acoustic_affinity(
        [(fl, 1.0), (ob, 1.0)], {}, profile="conservative", collect_pairs=True
    )
    rows = out.pop("_pair_rows", [])
    assert rows
    json.dumps(rows, default=str)


def test_qualitative_probe_rankings_synthetic() -> None:
    """Sanity ordering only — not perceptual validation."""
    tuk_c = "cl|ord"
    clar_choir = _affinity(
        [(_ev("b flat clarinet", FAMILY_CLARINETS, [60.0], technique_uniformity_key=tuk_c)[0], 1.0)] * 4
    )
    brass = _affinity(
        [
            (_ev("trumpet", FAMILY_BRASS, [70.0])[0], 1.0),
            (_ev("horn", FAMILY_BRASS, [65.0])[0], 1.0),
            (_ev("trombone", FAMILY_BRASS, [60.0])[0], 1.0),
            (_ev("tuba", FAMILY_BRASS, [55.0])[0], 1.0),
        ]
    )
    ww = _affinity(
        [
            (_ev("flute", FAMILY_FLUTES, [72.0])[0], 1.0),
            (_ev("oboe", FAMILY_OBOES, [70.0])[0], 1.0),
            (_ev("b flat clarinet", FAMILY_CLARINETS, [68.0])[0], 1.0),
            (_ev("bassoon", FAMILY_BASSOONS, [65.0])[0], 1.0),
        ]
    )
    strings = _affinity(
        [
            (_ev("violin", FAMILY_STRINGS, [62.0])[0], 1.0),
            (_ev("viola", FAMILY_STRINGS, [60.0])[0], 1.0),
            (_ev("cello", FAMILY_STRINGS, [55.0])[0], 1.0),
            (_ev("double bass", FAMILY_STRINGS, [48.0])[0], 1.0),
        ]
    )
    tutti = _affinity(
        [
            (_ev("flute", FAMILY_FLUTES, [80.0])[0], 1.0),
            (_ev("tuba", FAMILY_BRASS, [40.0])[0], 1.0),
            (_ev("violin", FAMILY_STRINGS, [76.0])[0], 1.0),
            (_ev("piano", FAMILY_KEYBOARD, [60.0])[0], 1.0),
        ]
    )
    assert clar_choir > tutti
    assert brass > ww
    assert strings > ww
    assert clar_choir >= brass - 0.05
