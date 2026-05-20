"""Repair test modules corrupted by misplaced ``import pytest`` lines."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tests"


def repair(text: str) -> str:
    lines = text.splitlines()
    # drop misplaced import pytest (not in first 25 lines)
    cleaned: list[str] = []
    for i, line in enumerate(lines):
        if line.strip() == "import pytest" and i >= 25:
            continue
        cleaned.append(line)
    text = "\n".join(cleaned) + "\n"
    # if file starts with import pytest before docstring, reorder
    if text.lstrip().startswith("import pytest"):
        lines = text.splitlines()
        pytest_lines: list[str] = []
        rest: list[str] = []
        for line in lines:
            if line.strip() == "import pytest" and not rest:
                pytest_lines.append(line)
            elif line.strip() == "" and not rest and pytest_lines:
                continue
            else:
                rest.append(line)
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
        if "import pytest" not in "\n".join(rest[: j + 5]):
            rest = rest[:j] + ["import pytest", ""] + rest[j:]
        text = "\n".join(rest) + "\n"
    # ensure pytest import if pytest. used
    if re.search(r"\bpytest\.", text) and "import pytest" not in text:
        lines = text.splitlines()
        j = 0
        if lines and lines[0].startswith('"""'):
            for k, line in enumerate(lines[1:], 1):
                if line.strip().endswith('"""'):
                    j = k + 1
                    break
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines) and "from __future__" in lines[j]:
            j += 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
        lines = lines[:j] + ["import pytest", ""] + lines[j:]
        text = "\n".join(lines) + "\n"
    return text


for path in sorted(ROOT.glob("test_*.py")):
    raw = path.read_text(encoding="utf-8")
    fixed = repair(raw)
    if fixed != raw:
        path.write_text(fixed, encoding="utf-8")
        print("repaired", path.name)
