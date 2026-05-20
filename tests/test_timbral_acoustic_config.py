"""Timbral default_profiles.json wiring, registry linkage, and numeric regression guards."""

from __future__ import annotations

import pytest
from music21 import instrument as m21inst
from music21 import meter, note, stream

from homogeneity_analyser.acoustic_profiles.model_config import (
    all_timbral_acoustic_semantic_names,
    get_timbral_acoustic_profile_document,
    timbral_acoustic_diagnostics_bundle,
    timbral_float,
)
from homogeneity_analyser.acoustic_profiles.source_registry import load_source_registry
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer


def _pair_score(can1: str, can2: str, cls1, cls2) -> float:
    sc = stream.Score()
    for _c, ins in ((can1, cls1), (can2, cls2)):
        p = stream.Part()
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, ins())
        p.insert(0, note.Note("C4", quarterLength=4.0))
        sc.append(p)
    an = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    f = an.extract_timbral_features(2.0, 4.0)
    return float(an.compute_H_timbral(f))


def test_default_profile_document_version() -> None:
    doc = get_timbral_acoustic_profile_document()
    assert doc["profile_name"] == "legacy_default"
    assert doc["config_model_version"] == "1.0.0"
    assert len(doc["constants"]) >= 130


def test_all_profile_constants_have_required_metadata() -> None:
    doc = get_timbral_acoustic_profile_document()
    required = (
        "semantic_name",
        "value",
        "description",
        "affects",
        "model_role",
        "source_key",
        "page_reference",
        "rationale",
        "confidence",
        "evidence_status",
    )
    for c in doc["constants"]:
        for k in required:
            assert k in c, c["semantic_name"]
        assert str(c["page_reference"]).strip()


def test_non_project_source_keys_exist_in_registry() -> None:
    reg_keys = {e["source_key"] for e in load_source_registry()}
    for c in get_timbral_acoustic_profile_document()["constants"]:
        sk = c.get("source_key")
        if sk and sk != "project_specific":
            assert sk in reg_keys, c["semantic_name"]


def test_diagnostics_bundle_keys() -> None:
    b = timbral_acoustic_diagnostics_bundle()
    assert b["config_profile_name"] == "legacy_default"
    assert set(b) >= {
        "config_profile_name",
        "config_model_version",
        "constants_used",
        "source_keys_used",
        "provisional_constants_used",
    }


def test_semantic_names_indexable() -> None:
    names = all_timbral_acoustic_semantic_names()
    assert "timbral_technique_component_offset" in names
    timbral_float("timbral_technique_component_offset")


@pytest.mark.parametrize(
    ("c1", "c2", "i1", "i2", "expected"),
    [
        ("violin", "violin", m21inst.Violin, m21inst.Violin, 0.958),
        ("horn", "horn", m21inst.Horn, m21inst.Horn, 0.958),
        ("b flat clarinet", "b flat clarinet", m21inst.Clarinet, m21inst.Clarinet, 0.8605),
    ],
)
def test_h_timbral_pairwise_families_unchanged(c1: str, c2: str, i1, i2, expected: float) -> None:
    assert _pair_score(c1, c2, i1, i2) == pytest.approx(expected, abs=1e-9)


def test_decomposition_includes_acoustic_config_fields() -> None:
    sc = stream.Score()
    for _ in range(2):
        p = stream.Part()
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, m21inst.Violin())
        p.insert(0, note.Note("C4", quarterLength=4.0))
        sc.append(p)
    an = TimbralHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
    f = an.extract_timbral_features(2.0, 4.0)
    _, d = an.compute_H_timbral_decomposition(f)
    assert d["config_profile_name"] == "legacy_default"
    cu = d["constants_used"]
    assert "string_section_similarity_matrix" in cu
    assert "brass_section_similarity_matrix" not in cu
    assert "clarinet_subtype_similarity_matrix" not in cu
    assert len(cu) < 80
