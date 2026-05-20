"""README / QUICK_REFERENCE / TECHNICAL_MANUAL alignment with H_TI primary product."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from homogeneity_analyser.acoustic_profiles.source_validation import PAGE_REQUIRED_SENTINEL
from homogeneity_analyser.analyzers.symbolic_blend_layers import HTI_SYMBOLIC_BLEND_SERIES_KEYS
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import HTI_ACOUSTIC_PROXY_SERIES_KEYS
from homogeneity_analyser.services.json_export import HTI_EXPORT_SCHEMA_VERSION, JSON_EXPORT_SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
QUICK_REFERENCE = REPO_ROOT / "QUICK_REFERENCE.md"
TECH_MANUAL = REPO_ROOT / "TECHNICAL_MANUAL.md"

HTI_PRIMARY_ANCHOR = "H_TI(t)"
HTI_JSON_SCHEMA = HTI_EXPORT_SCHEMA_VERSION


def _read(p: Path) -> str:
    assert p.is_file(), f"missing {p}"
    return p.read_text(encoding="utf-8")


def _section_hti_core(md: str) -> str:
    """Narrative through notated dynamic conditioning; formal H_TI + dynamics."""
    start = md.find("## 4) H_TI_core formal definition")
    assert start != -1, "TECHNICAL_MANUAL missing ## 4) H_TI_core formal definition"
    end = md.find("\n## 7) Family-sensitive interpretation rules", start)
    assert end != -1, "TECHNICAL_MANUAL missing ## 7) Family-sensitive after H_TI / dynamics sections"
    return md[start:end]


def test_hti_primary_mentioned_in_readme_quick_ref_and_manual() -> None:
    for path in (README, QUICK_REFERENCE, TECH_MANUAL):
        text = _read(path)
        assert HTI_PRIMARY_ANCHOR in text, f"{path.name} should mention H_TI(t)"
        assert "symbolic" in text.lower(), f"{path.name} should state symbolic scope"


def test_quick_reference_hti_schema_and_internal_schema_note() -> None:
    qr = _read(QUICK_REFERENCE)
    assert HTI_JSON_SCHEMA in qr
    assert "not_audio_analysis" in qr
    assert "1.8" in qr
    assert "H_TI_core" in qr
    assert "H_cluster" not in qr
    assert "Timbral homogeneity H_timbral(t)" not in qr


def test_quick_reference_heuristic_not_measured_audio() -> None:
    qr = _read(QUICK_REFERENCE)
    assert "not measured audio" in qr.lower() or "not measured" in qr.lower()
    assert "waveform" in qr.lower()


def test_technical_manual_hti_intro_covers_dynamic_and_taxonomy() -> None:
    chunk = _section_hti_core(_read(TECH_MANUAL))
    for token in (
        "macrofamily",
        "instrumental subfamily",
        "technique_coverage_status",
        "ordinary_default_uniform",
        "notated_dynamic_coherence",
        "soft_blend_potential",
        "projection_divergence_risk",
        "masked_tonal_mass_risk",
    ):
        assert token in chunk.lower() or token.replace("_", " ") in chunk.lower(), f"§0 H_TI should mention {token!r}"


def test_release_facing_docs_exclude_page_placeholder_sentinel() -> None:
    """README and QUICK_REFERENCE are release-facing summaries; §19 mirrors raw JSON separately."""
    for path in (README, QUICK_REFERENCE):
        body = _read(path)
        assert PAGE_REQUIRED_SENTINEL not in body, f"{path.name} must not embed {PAGE_REQUIRED_SENTINEL!r}"


def test_release_mode_technical_manual_narrative_still_clean() -> None:
    if os.environ.get("HOMOGENEITY_ANALYSER_RELEASE_DOCUMENTATION") != "1":
        pytest.skip("Set HOMOGENEITY_ANALYSER_RELEASE_DOCUMENTATION=1 to scan TECHNICAL_MANUAL narrative")
    md = _read(TECH_MANUAL)
    bib = md.find("## 19) Bibliography")
    assert bib != -1
    narrative = md[:bib]
    narrative = re.sub(r"`[^`]*`", " ", narrative)
    assert PAGE_REQUIRED_SENTINEL not in narrative


def test_readme_technical_manual_agree_on_schema_1_6() -> None:
    assert "1.8" in _read(README)
    assert "1.8" in _read(TECH_MANUAL)


def test_docs_schema_matches_json_export_constant() -> None:
    """Release docs and ``json_export.JSON_EXPORT_SCHEMA_VERSION`` must stay aligned."""
    ver = JSON_EXPORT_SCHEMA_VERSION
    assert ver == "1.8"
    for path in (README, QUICK_REFERENCE, TECH_MANUAL):
        body = _read(path)
        assert ver in body, f"{path.name} must cite export schema {ver} (same as JSON_EXPORT_SCHEMA_VERSION)"


def test_technical_manual_json_export_model_version_note() -> None:
    md = _read(TECH_MANUAL)
    assert "**Two different `model_version` fields:**" in md
    assert "timbral_semantic_model" in md
    assert "JSON_EXPORT_MODEL_VERSION" in md


def test_readme_quick_ref_no_combined_workflow_recommended() -> None:
    bad = re.compile(r"combined\s+workflow\s+recommended", re.IGNORECASE)
    for path in (README, QUICK_REFERENCE):
        assert bad.search(_read(path)) is None, f"{path.name} must not recommend the old combined workflow"


def test_docs_symbolic_blend_export_fields_match_code_registry() -> None:
    """Release docs name the same optional symbolic columns as ``HTI_SYMBOLIC_BLEND_SERIES_KEYS``."""
    for k in HTI_SYMBOLIC_BLEND_SERIES_KEYS:
        assert k in _read(QUICK_REFERENCE), f"QUICK_REFERENCE missing export key {k!r}"


def test_docs_acoustic_proxy_export_fields_match_code_registry() -> None:
    """Release docs name the same optional acoustic-proxy columns as ``HTI_ACOUSTIC_PROXY_SERIES_KEYS``."""
    for k in HTI_ACOUSTIC_PROXY_SERIES_KEYS:
        assert k in _read(QUICK_REFERENCE), f"QUICK_REFERENCE missing export key {k!r}"


def test_docs_interval_class_seconds_sevenths_semantics() -> None:
    """Release docs must not imply literal sevenths when only the seconds_sevenths bucket is meant."""
    for path in (README, QUICK_REFERENCE, TECH_MANUAL):
        body = _read(path)
        assert "seconds_sevenths" in body, f"{path.name} should document seconds_sevenths key"
        assert "literal_interval_semitone_pair_mass" in body, (
            f"{path.name} should document literal_interval_semitone_pair_mass"
        )
    assert "SYMBOLIC_INTERVAL_CLASS_LAYER.md" in _read(REPO_ROOT / "docs" / "index.md")


def test_gradio_source_hti_primary_no_legacy_timbral_tab() -> None:
    ga = REPO_ROOT / "src" / "homogeneity_analyser" / "ui" / "gradio_app.py"
    text = ga.read_text(encoding="utf-8")
    assert "run_hti_app" in text
    assert "H_TI_core" in text
    assert "notated dynamic conditioning" in text.lower()
    assert 'TabItem("Legacy H_timbral (diagnostic)")' not in text
    assert "Timbral homogeneity H_timbral(t)" not in text


def test_readme_quick_ref_manual_hti_messaging() -> None:
    """Primary docs centre H_TI; legacy fusion language is framed as non-measured / non-validated."""
    for path in (README, QUICK_REFERENCE, TECH_MANUAL):
        body = _read(path)
        assert HTI_PRIMARY_ANCHOR in body
        assert "not measured audio" in body.lower() or "not measured" in body.lower()
        assert "acoustically validated fusion" in body.lower() or "not acoustically validated fusion" in body.lower()


def test_release_gate_no_stale_primary_timbral_tab_phrase() -> None:
    """Fails in release mode if the old Gradio tab title reappears in user-facing docs."""
    if os.environ.get("HOMOGENEITY_ANALYSER_RELEASE_GATE") != "1":
        pytest.skip("Set HOMOGENEITY_ANALYSER_RELEASE_GATE=1 for release messaging checks")
    bad = re.compile(r"Timbral homogeneity H_timbral\(t\)", re.IGNORECASE)
    for path in (README, QUICK_REFERENCE, TECH_MANUAL):
        assert bad.search(_read(path)) is None, f"{path.name} must not revive the old primary timbral tab title"
    for path in (README, QUICK_REFERENCE, TECH_MANUAL):
        assert "confidence" in _read(path).lower(), f"{path.name} should mention fusion confidence / confidence fields"
