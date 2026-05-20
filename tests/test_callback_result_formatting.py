"""Tests for ``ui/callback_result_formatting.py``."""

from __future__ import annotations

from pathlib import Path

from homogeneity_analyser.ui.callback_result_formatting import (
    dataframe_cell,
    rows_to_dataframe,
    write_temp_csv,
)


def test_dataframe_cell_serializes_dict() -> None:
    assert dataframe_cell({"a": 1}) == '{"a": 1}'


def test_dataframe_cell_nan_float_becomes_none() -> None:
    assert dataframe_cell(float("nan")) is None


def test_rows_to_dataframe_empty_headers() -> None:
    df = rows_to_dataframe([], ("col_a", "col_b"))
    assert list(df.columns) == ["col_a", "col_b"]
    assert len(df) == 0


def test_write_temp_csv_creates_file(tmp_path) -> None:
    path = write_temp_csv("audit.csv", "a,b\n1,2\n")
    assert path.endswith("audit.csv")
    assert "a,b" in Path(path).read_text(encoding="utf-8")
