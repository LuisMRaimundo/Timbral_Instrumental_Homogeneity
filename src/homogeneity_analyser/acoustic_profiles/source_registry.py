"""Load the acoustic evidence registry (JSON alongside this module)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_JSON_PATH = Path(__file__).with_name("source_registry.json")


def load_source_registry(path: Path | None = None) -> list[dict[str, Any]]:
    """
    Return the list of source records.

    ``private_sources/`` is never read at runtime; only static JSON shipped with the package.
    """
    p = path or REGISTRY_JSON_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("source_registry.json must contain a JSON array at the top level.")
    return [dict(x) for x in raw]
