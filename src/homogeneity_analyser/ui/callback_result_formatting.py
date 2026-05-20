"""Shared audit-table / CSV helpers for UI callbacks (no Gradio)."""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd


def dataframe_cell(v: Any) -> Any:
    """Normalize audit cell values so Gradio Dataframes never receive raw dict/list objects."""
    if v is None:
        return None
    if isinstance(v, bool | int | float | str):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return v
    if isinstance(v, dict | list):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def rows_to_dataframe(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> pd.DataFrame:
    """Build a pandas DataFrame with stable columns (empty input still yields headers only)."""
    cols = list(columns)
    if not rows:
        return pd.DataFrame([], columns=cols)
    return pd.DataFrame([{c: dataframe_cell(r.get(c, "")) for c in cols} for r in rows], columns=cols)


def write_temp_csv(filename: str, csv_text: str) -> str:
    """Write CSV text to a new temp file; return path string for ``gr.File``."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="homogeneity_audit_"))
    out_path = tmp_dir / filename
    out_path.write_text(csv_text, encoding="utf-8", newline="")
    return str(out_path)
