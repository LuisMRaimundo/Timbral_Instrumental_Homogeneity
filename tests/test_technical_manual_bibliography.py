"""Documentation consistency: TECHNICAL_MANUAL, README, source registry, and model_config."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from homogeneity_analyser.acoustic_profiles.model_config import DEFAULT_PROFILES_JSON_PATH
from homogeneity_analyser.acoustic_profiles.source_registry import load_source_registry
from homogeneity_analyser.acoustic_profiles.source_validation import PAGE_REQUIRED_SENTINEL

REPO_ROOT = Path(__file__).resolve().parents[1]
TECH_MANUAL = REPO_ROOT / "TECHNICAL_MANUAL.md"
README = REPO_ROOT / "README.md"


def _read_manual() -> str:
    assert TECH_MANUAL.is_file(), "TECHNICAL_MANUAL.md must exist at repository root"
    return TECH_MANUAL.read_text(encoding="utf-8")


def _narrative_before_bibliography(manual: str) -> str:
    marker = "## 19) Bibliography"
    i = manual.find(marker)
    return manual if i == -1 else manual[:i]


def _strip_inline_backticks(text: str) -> str:
    return re.sub(r"`[^`]*`", " ", text)


def test_technical_manual_exists() -> None:
    assert TECH_MANUAL.stat().st_size > 0


def test_manual_has_architecture_and_evidence_sections() -> None:
    md = _read_manual()
    assert "## 3) Data pipeline" in md
    assert "## 10) JSON output" in md
    assert "## 12) Bibliographic rationale" in md
    assert "source_registry.json" in md
    assert "## 19) Bibliography" in md


def test_registry_source_keys_documented_in_manual_bibliography() -> None:
    md = _read_manual()
    bib = md.split("## 19) Bibliography", 1)[1]
    for entry in load_source_registry():
        sk = entry["source_key"]
        assert f"### `{sk}`" in bib, f"Bibliography missing subsection for source_key {sk!r}"


def test_model_config_source_keys_appear_in_manual_or_registry_doc() -> None:
    """Non-project `source_key` values in default_profiles must map to documented literature."""
    manual = _read_manual()
    doc = json.loads(DEFAULT_PROFILES_JSON_PATH.read_text(encoding="utf-8"))
    keys: set[str] = set()
    for row in doc.get("constants", []):
        sk = row.get("source_key")
        if isinstance(sk, str) and sk.strip() and sk != "project_specific":
            keys.add(sk.strip())
    for sk in sorted(keys):
        assert sk in manual, (
            f"source_key {sk!r} from default_profiles.json must appear in TECHNICAL_MANUAL.md "
            "(bibliography or narrative)."
        )


def test_default_profiles_constants_have_provenance_fields() -> None:
    doc = json.loads(DEFAULT_PROFILES_JSON_PATH.read_text(encoding="utf-8"))
    for row in doc.get("constants", []):
        name = row.get("semantic_name")
        assert isinstance(name, str) and name
        sk = row.get("source_key")
        assert isinstance(sk, str) and sk.strip(), f"{name}: source_key required"
        rat = row.get("rationale")
        assert isinstance(rat, str) and rat.strip(), f"{name}: rationale required"


def test_no_long_quoted_blocks_in_manual() -> None:
    """Heuristic: no single narrative line should exceed 160 words (guards pasted block quotations)."""
    md = _narrative_before_bibliography(_read_manual())
    for line in md.splitlines():
        n = len(line.split())
        assert n <= 160, f"Suspiciously long line ({n} words); check for pasted quotations: {line[:120]}…"


def test_release_mode_forbids_page_placeholder_outside_bibliography() -> None:
    """When HOMOGENEITY_ANALYSER_RELEASE_DOCUMENTATION=1, narrative must not contain the sentinel."""
    if os.environ.get("HOMOGENEITY_ANALYSER_RELEASE_DOCUMENTATION") != "1":
        pytest.skip("Set HOMOGENEITY_ANALYSER_RELEASE_DOCUMENTATION=1 to enforce release doc scan")
    md = _read_manual()
    narrative = _strip_inline_backticks(_narrative_before_bibliography(md))
    assert PAGE_REQUIRED_SENTINEL not in narrative


def test_readme_and_manual_share_metric_vocabulary() -> None:
    manual = _read_manual()
    readme = README.read_text(encoding="utf-8")
    hti_anchor = "H_TI(t)"
    assert hti_anchor in manual
    assert hti_anchor in readme
    for token in (
        "H_cluster",
        "H_orchestration_symbolic",
        "H_fusion_acoustic_heuristic",
        "symbolic notation",
        "MusicXML",
    ):
        assert token in manual
        assert token in readme


def test_manual_registry_path_matches_packaged_file() -> None:
    manual = _read_manual()
    rel = "src/homogeneity_analyser/acoustic_profiles/source_registry.json"
    assert rel in manual
    assert (REPO_ROOT / rel.replace("/", os.sep)).is_file()
