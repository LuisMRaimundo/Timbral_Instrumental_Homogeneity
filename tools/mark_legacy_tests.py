"""Add module-level pytest.mark.legacy to designated test modules."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tests"
MARKER_BLOCK = 'pytestmark = pytest.mark.legacy\n'
FILES = [
    "test_analysis_service.py",
    "test_cluster_metric.py",
    "test_fusion_acoustic_heuristic.py",
    "test_notated_fusion_potential.py",
    "test_notated_fusion_dynamic.py",
    "test_timbral_fusion_corpus_validation.py",
    "test_legacy_package.py",
    "test_legacy_ui_params.py",
    "test_legacy_multimetric_ui_params.py",
    "test_timbral_ui_params.py",
    "test_timbral_decomposition.py",
    "test_parse_ui_float.py",
]


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "pytestmark = pytest.mark.legacy" in text:
        return
    if "import pytest" not in text:
        # after module docstring / future imports
        lines = text.splitlines(keepends=True)
        insert_at = 0
        if lines and lines[0].startswith('"""'):
            for i, line in enumerate(lines[1:], 1):
                if line.strip().endswith('"""'):
                    insert_at = i + 1
                    break
        if insert_at < len(lines) and "from __future__" in lines[insert_at]:
            insert_at += 1
            if insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
        lines.insert(insert_at, "import pytest\n\n")
        lines.insert(insert_at + 2, MARKER_BLOCK)
        text = "".join(lines)
    else:
        if "pytestmark" not in text:
            text = text.replace("import pytest\n", f"import pytest\n\n{MARKER_BLOCK}", 1)
    path.write_text(text, encoding="utf-8")
    print("patched", path.name)


for name in FILES:
    p = ROOT / name
    if p.is_file():
        patch(p)
