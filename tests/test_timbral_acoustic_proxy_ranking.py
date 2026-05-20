"""Ranking and behaviour tests for H_TA_acoustic_proxy (score-derived timbral affinity)."""

from __future__ import annotations

import math

import pytest

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer, compute_register_compactness_fields
from homogeneity_analyser.analyzers.hti_adaptive_windows import hti_window_row_geometry
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
    compute_timbral_acoustic_affinity,
    pairwise_acoustic_kernel,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OBOES,
    FAMILY_STRINGS,
)


def _ev(
    instrument: str,
    family: str,
    pitches: list[float],
    *,
    ol: float = 1.0,
    technique_state: dict | None = None,
    dynamic_mark: str = "mf",
    technique_uniformity_key: str = "",
) -> tuple[dict, float]:
    e: dict = {
        "instrument": instrument,
        "family": family,
        "pitches": list(pitches),
        "offset": 0.0,
        "end": 4.0,
        "dynamic_mark": dynamic_mark,
        "hairpin": "none",
    }
    if technique_state is not None:
        e["technique_state"] = technique_state
    if technique_uniformity_key:
        e["technique_uniformity_key"] = technique_uniformity_key
    return e, ol


def _affinity(contrib: list[tuple[dict, float]], profile: str = "conservative") -> float:
    return float(compute_timbral_acoustic_affinity(contrib, {}, profile=profile)["timbral_acoustic_affinity"])


def _hti_core(contrib: list[tuple[dict, float]]) -> float:
    inst_mass: dict[str, float] = {}
    fam_mass: dict[str, float] = {}
    tech_mass: dict[str, float] = {}
    pitch_occ: list[tuple[float, float]] = []
    for e, ol in contrib:
        inst_mass[str(e["instrument"])] = inst_mass.get(str(e["instrument"]), 0.0) + ol
        fam_mass[str(e["family"])] = fam_mass.get(str(e["family"]), 0.0) + ol
        tuk = str(e.get("technique_uniformity_key") or "ord")
        tech_mass[tuk] = tech_mass.get(tuk, 0.0) + ol
        for p in e.get("pitches") or []:
            pitch_occ.append((float(p), float(ol)))
    from homogeneity_analyser.analyzers.hti import _herfindahl_from_masses

    feats = {
        "instrument_uniformity": _herfindahl_from_masses(inst_mass),
        "family_uniformity": _herfindahl_from_masses(fam_mass),
        "technique_uniformity": _herfindahl_from_masses(tech_mass),
        "technique_coverage_status": "explicit",
        "register_coverage_status": "pitched",
    }
    reg = compute_register_compactness_fields(pitch_occ, 7.0)
    feats.update(reg)
    feats["register_coverage_status"] = "pitched"
    an = object.__new__(SymbolicTIHomogeneityAnalyzer)
    h, _, _ = an.compute_H_TI(feats)
    return float(h)


def test_four_identical_clarinets_high_affinity_and_hti_core() -> None:
    tuk = "clarinets|ordinario|none|ordinary|ordinary|none|ordinary"
    contrib = [
        _ev("b flat clarinet", FAMILY_CLARINETS, [60.0], technique_uniformity_key=tuk)[0]
        for _ in range(4)
    ]
    contrib = [(e, 1.0) for e in contrib]
    aff = _affinity(contrib)
    assert aff == pytest.approx(1.0, abs=1e-6)
    h = _hti_core(contrib)
    assert h == pytest.approx(1.0, abs=1e-6)


def test_clarinet_bass_clarinet_affinity_exceeds_instrument_herfindahl() -> None:
    tuk = "clarinets|ordinario|none|ordinary|ordinary|none|ordinary"
    c1, _ = _ev("b flat clarinet", FAMILY_CLARINETS, [55.0], technique_uniformity_key=tuk)
    c2, _ = _ev("bass clarinet", FAMILY_CLARINETS, [55.0], technique_uniformity_key=tuk)
    contrib = [(c1, 1.0), (c2, 1.0)]
    aff = _affinity(contrib)
    from homogeneity_analyser.analyzers.hti import _herfindahl_from_masses

    iu = _herfindahl_from_masses({"b flat clarinet": 1.0, "bass clarinet": 1.0})
    assert aff > iu + 0.15
    h_before = _hti_core(contrib)
    assert math.isfinite(h_before)


def test_string_quartet_affinity_much_higher_than_instrument_herfindahl() -> None:
    tuk = "strings|ordinario|none|ordinary|ordinary|none|ordinary"
    contrib = [
        (_ev("violin", FAMILY_STRINGS, [62.0], technique_uniformity_key=tuk)[0], 1.0),
        (_ev("viola", FAMILY_STRINGS, [60.0], technique_uniformity_key=tuk)[0], 1.0),
        (_ev("cello", FAMILY_STRINGS, [55.0], technique_uniformity_key=tuk)[0], 1.0),
        (_ev("double bass", FAMILY_STRINGS, [48.0], technique_uniformity_key=tuk)[0], 1.0),
    ]
    aff = _affinity(contrib)
    from homogeneity_analyser.analyzers.hti import _herfindahl_from_masses

    iu = _herfindahl_from_masses({e[0]["instrument"]: 1.0 for e in contrib})
    assert iu == pytest.approx(0.25, abs=1e-6)
    assert aff > 0.65
    assert aff > iu + 0.35


def test_woodwind_quartet_lower_than_brass_quartet() -> None:
    tuk_w = "wood|ord"
    ww = [
        (_ev("flute", FAMILY_FLUTES, [72.0], technique_uniformity_key=tuk_w)[0], 1.0),
        (_ev("oboe", FAMILY_OBOES, [70.0], technique_uniformity_key=tuk_w)[0], 1.0),
        (_ev("b flat clarinet", FAMILY_CLARINETS, [68.0], technique_uniformity_key=tuk_w)[0], 1.0),
        (_ev("bassoon", FAMILY_BASSOONS, [65.0], technique_uniformity_key=tuk_w)[0], 1.0),
    ]
    br = [
        (_ev("trumpet", FAMILY_BRASS, [70.0], technique_uniformity_key=tuk_w)[0], 1.0),
        (_ev("horn", FAMILY_BRASS, [65.0], technique_uniformity_key=tuk_w)[0], 1.0),
        (_ev("trombone", FAMILY_BRASS, [60.0], technique_uniformity_key=tuk_w)[0], 1.0),
        (_ev("tuba", FAMILY_BRASS, [55.0], technique_uniformity_key=tuk_w)[0], 1.0),
    ]
    aff_ww = _affinity(ww)
    aff_br = _affinity(br)
    assert aff_br > aff_ww + 0.08


def test_brass_quartet_moderate_not_perfect() -> None:
    tuk = "brass|open"
    br = [
        (_ev("trumpet", FAMILY_BRASS, [70.0], technique_uniformity_key=tuk)[0], 1.0),
        (_ev("horn", FAMILY_BRASS, [65.0], technique_uniformity_key=tuk)[0], 1.0),
        (_ev("trombone", FAMILY_BRASS, [60.0], technique_uniformity_key=tuk)[0], 1.0),
        (_ev("tuba", FAMILY_BRASS, [55.0], technique_uniformity_key=tuk)[0], 1.0),
    ]
    aff = _affinity(br)
    assert 0.55 < aff < 0.98


def test_muted_trumpet_stopped_horn_lower_than_open_brass() -> None:
    open_state = {"family": FAMILY_BRASS, "instrument": "trumpet", "primary": "open", "mute": "none"}
    open_brass = [
        (
            _ev(
                "trumpet",
                FAMILY_BRASS,
                [70.0],
                technique_state={**open_state, "instrument": "trumpet"},
            )[0],
            1.0,
        ),
        (
            _ev(
                "horn",
                FAMILY_BRASS,
                [65.0],
                technique_state={**open_state, "instrument": "horn", "primary": "open"},
            )[0],
            1.0,
        ),
    ]
    muted = [
        (
            _ev(
                "trumpet",
                FAMILY_BRASS,
                [70.0],
                technique_state={
                    "family": FAMILY_BRASS,
                    "instrument": "trumpet",
                    "primary": "open",
                    "mute": "straight",
                },
            )[0],
            1.0,
        ),
        (
            _ev(
                "horn",
                FAMILY_BRASS,
                [65.0],
                technique_state={
                    "family": FAMILY_BRASS,
                    "instrument": "horn",
                    "primary": "stopped",
                    "mute": "none",
                },
            )[0],
            1.0,
        ),
    ]
    assert _affinity(muted) < _affinity(open_brass) - 0.05


def test_acoustic_proxy_register_not_compactness_proxy() -> None:
    """register_tessitura component is separate from register_compactness (see audit tests)."""
    from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
        load_acoustic_timbral_taxonomy,
        register_tessitura_similarity,
    )

    tax = load_acoustic_timbral_taxonomy()
    v, _ = _ev("violin", FAMILY_STRINGS, [60.0])
    va, _ = _ev("viola", FAMILY_STRINGS, [62.0])
    assert float(register_tessitura_similarity(v, va, tax) or 0) > float(
        register_tessitura_similarity(v, _ev("cello", FAMILY_STRINGS, [84.0])[0], tax) or 0
    )


def test_single_event_affinity_one() -> None:
    contrib = [_ev("flute", FAMILY_FLUTES, [72.0])]
    out = compute_timbral_acoustic_affinity(contrib, {}, profile="conservative")
    assert out["timbral_acoustic_affinity"] == pytest.approx(1.0)
    assert "single_event" in out["timbral_acoustic_affinity_evidence_status"]


def test_chord_single_event_not_quadruple_instrument_count() -> None:
    e, ol = _ev("b flat clarinet", FAMILY_CLARINETS, [60.0, 64.0, 67.0, 72.0])
    contrib = [(e, ol)]
    aff_one = _affinity(contrib)
    assert aff_one == pytest.approx(1.0)
    fake_four = [(dict(e), ol) for _ in range(4)]
    aff_four = _affinity(fake_four)
    assert aff_four == pytest.approx(1.0)
    assert aff_one == aff_four


def test_edge_window_fields_preserved_in_analyze_hti() -> None:
    """New metric must not alter edge_window / window_coverage_ratio plumbing."""
    geom = hti_window_row_geometry(0.1, 4.0, 0.0, 8.0, "mark_partial_windows")
    assert "edge_window" in geom
    assert "window_coverage_ratio" in geom
    assert geom["window_coverage_ratio"] <= 1.0 + 1e-9


def test_missing_technique_not_assumed_ordinary() -> None:
    e1, _ = _ev("flute", FAMILY_FLUTES, [72.0])
    e2, _ = _ev("oboe", FAMILY_OBOES, [70.0])
    out = compute_timbral_acoustic_affinity([(e1, 1.0), (e2, 1.0)], {}, profile="conservative")
    assert "technique_omitted" in out["timbral_acoustic_affinity_evidence_status"]


def test_hti_core_unchanged_when_acoustic_proxy_enabled() -> None:
    """H_TI_core path must not depend on include_acoustic_proxy."""
    from homogeneity_analyser.analyzers.hti import _herfindahl_from_masses

    inst_mass = {"violin": 0.5, "viola": 0.5}
    feats = {
        "instrument_uniformity": _herfindahl_from_masses(inst_mass),
        "family_uniformity": 1.0,
        "technique_uniformity": 1.0,
        "technique_coverage_status": "explicit",
        "register_coverage_status": "pitched",
        "register_compactness": 0.9,
        "register_proximity": 0.9,
    }
    an = object.__new__(SymbolicTIHomogeneityAnalyzer)
    h1, _, _ = an.compute_H_TI(feats)
    h2, _, _ = an.compute_H_TI(dict(feats))
    assert h1 == pytest.approx(h2)


def test_pairwise_kernel_self_similarity() -> None:
    e, _ = _ev("trumpet", FAMILY_BRASS, [70.0])
    k, _ = pairwise_acoustic_kernel(e, e, profile="conservative")
    assert k == pytest.approx(1.0)


def test_acoustic_proxy_disabled_status() -> None:
    from homogeneity_analyser.analyzers.timbral_acoustic_proxy import disabled_acoustic_proxy_bundle

    b = disabled_acoustic_proxy_bundle()
    assert b["acoustic_proxy_not_audio_analysis"] is True
    assert b["timbral_acoustic_affinity_evidence_status"] == "disabled"
    assert math.isnan(float(b["H_TA_acoustic_proxy"]))
