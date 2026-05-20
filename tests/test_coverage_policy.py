"""Coverage policy: product-path threshold (legacy excluded; UI params in product path)."""

from __future__ import annotations

import re
from pathlib import Path


def test_pyproject_coverage_fail_under_product_path() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r"fail_under\s*=\s*(\d+)", text)
    assert m is not None
    assert int(m.group(1)) >= 77
    omit_block = text.split("[tool.coverage.run]", 1)[1].split("[tool.coverage.report]", 1)[0]
    assert "homogeneity_analyser/legacy/*" in omit_block
    assert "homogeneity_analyser/ui/callbacks.py" not in omit_block
