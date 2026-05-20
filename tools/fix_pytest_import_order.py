"""Move ``import pytest`` after module docstring and ``from __future__``."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tests"


def fix(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "import pytest":
        return text
    # collect pytest line(s) at top
    i = 0
    while i < len(lines) and lines[i].strip() in ("import pytest", ""):
        i += 1
    rest = lines[i:]
    # find insert point in rest
    j = 0
    if rest and rest[0].startswith('"""'):
        for k, line in enumerate(rest[1:], 1):
            if line.strip().endswith('"""'):
                j = k + 1
                break
    while j < len(rest) and rest[j].strip() == "":
        j += 1
    if j < len(rest) and "from __future__" in rest[j]:
        j += 1
        while j < len(rest) and rest[j].strip() == "":
            j += 1
    if j < len(rest) and rest[j].strip() == "import pytest":
        return "\n".join(rest) + "\n"
    new = rest[:j] + ["import pytest", ""] + rest[j:]
    return "\n".join(new) + "\n"


for path in ROOT.glob("test_*.py"):
    raw = path.read_text(encoding="utf-8")
    fixed = fix(raw)
    if fixed != raw:
        path.write_text(fixed, encoding="utf-8")
        print("fixed", path.name)
