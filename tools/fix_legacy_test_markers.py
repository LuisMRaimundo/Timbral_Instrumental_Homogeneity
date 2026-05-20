"""Fix pytestmark placement: after module docstring and __future__, before other imports."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tests"
MARKER = "pytestmark = pytest.mark.legacy\n"
FILES = list(ROOT.glob("test_*.py"))


def fix(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "pytestmark = pytest.mark.legacy" not in text:
        return False
    # strip broken marker blocks and misplaced import pytest
    text = re.sub(r"^import pytest\n\n", "", text, count=1, flags=re.M)
    text = re.sub(r"^pytestmark = pytest\.mark\.legacy\n\n?", "", text, flags=re.M)
    lines = text.splitlines(keepends=True)
    # find end of header (docstring + optional __future__)
    i = 0
    if lines and lines[0].startswith('"""'):
        while i < len(lines):
            if lines[i].strip().endswith('"""') and i > 0:
                i += 1
                break
            i += 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i < len(lines) and "from __future__" in lines[i]:
        i += 1
        while i < len(lines) and lines[i].strip() == "":
            i += 1
    block = "import pytest\n\n" + MARKER
    if lines[i : i + 2] == ["import pytest\n", "\n"]:
        i += 2
    new_lines = lines[:i] + [block] + lines[i:]
    path.write_text("".join(new_lines), encoding="utf-8")
    print("fixed", path.name)
    return True


for p in FILES:
    if "pytestmark" in p.read_text(encoding="utf-8"):
        fix(p)
