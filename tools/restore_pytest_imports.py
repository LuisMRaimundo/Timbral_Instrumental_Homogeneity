"""Re-add ``import pytest`` to test modules that use pytest but lost the import."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tests"


def insert_pytest_import(lines: list[str]) -> list[str]:
    i = 0
    if lines and lines[0].startswith('"""'):
        for j, line in enumerate(lines[1:], 1):
            if line.strip().endswith('"""'):
                i = j + 1
                break
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i < len(lines) and "from __future__" in lines[i]:
        i += 1
        while i < len(lines) and lines[i].strip() == "":
            i += 1
    out = lines[:i] + ["import pytest", ""] + lines[i:]
    return out


for path in sorted(ROOT.glob("test_*.py")):
    text = path.read_text(encoding="utf-8")
    if not re.search(r"\bpytest\.", text) or "import pytest" in text:
        continue
    lines = text.splitlines()
    path.write_text("\n".join(insert_pytest_import(lines)) + "\n", encoding="utf-8")
    print("restored", path.name)
