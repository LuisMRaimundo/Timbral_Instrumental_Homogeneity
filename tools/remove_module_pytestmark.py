"""Remove module-level pytestmark blocks added by mark_legacy_tests.py."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tests"

for path in ROOT.glob("test_*.py"):
    text = path.read_text(encoding="utf-8")
    new = re.sub(r"\nimport pytest\n\npytestmark = pytest\.mark\.legacy\n\n", "\n", text, count=1)
    new = re.sub(r"^import pytest\n\n\"\"\"", '"""', new, count=1, flags=re.M)
    new = re.sub(r"^pytestmark = pytest\.mark\.legacy\n\n", "", new, flags=re.M)
    if new != text:
        path.write_text(new, encoding="utf-8")
        print("cleaned", path.name)
