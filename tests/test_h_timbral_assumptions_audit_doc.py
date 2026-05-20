"""Non-invasive check that the H_timbral assumptions audit doc is present and substantive."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = REPO_ROOT / "docs" / "model_audit" / "H_TIMBRAL_ASSUMPTIONS_AUDIT.md"


def test_h_timbral_assumptions_audit_file_exists_and_covers_pipeline():
    text = AUDIT_PATH.read_text(encoding="utf-8")
    assert "analyzers/timbral.py" in text
    assert "_REGISTER_GLOBAL_DAMPEN_FOR_PAIRWISE_COVERAGE" in text
    assert "0.18 + 0.82" in text
    assert "Undocumented-in-manual" in text or "undocumented" in text.lower()
    assert len(text) > 4000
