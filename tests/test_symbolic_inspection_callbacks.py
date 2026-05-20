"""Gradio symbolic inspection callback (upload-driven audit)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from homogeneity_analyser.services.score_audit import SCORE_AUDIT_EVENT_COLUMNS, SCORE_AUDIT_INVENTORY_COLUMNS
from homogeneity_analyser.ui.callbacks import run_loaded_xml_inspection

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"


def test_inspection_no_upload_returns_header_only_frames():
    notice, inv_df, inv_csv, ev_df, ev_csv, ver_df, ver_csv = run_loaded_xml_inspection(None)
    assert isinstance(inv_df, pd.DataFrame)
    assert list(inv_df.columns) == list(SCORE_AUDIT_INVENTORY_COLUMNS)
    assert inv_df.shape[0] == 0
    assert list(ev_df.columns) == list(SCORE_AUDIT_EVENT_COLUMNS)
    assert ev_df.shape[0] == 0
    assert inv_csv is None and ev_csv is None and ver_csv is None
    assert "Upload" in notice or "Symbolic" in notice


def test_inspection_fixture_writes_three_csv_paths():
    path = FIXTURE_DIR / "corpus_strings_techniques.musicxml"
    if not path.is_file():
        pytest.skip(f"Missing fixture {path}")
    notice, inv_df, inv_csv, ev_df, ev_csv, ver_df, ver_csv = run_loaded_xml_inspection({"path": str(path)})
    assert "Symbolic inspection updated" in notice
    assert inv_df.shape[0] >= 1
    assert ev_df.shape[0] >= 1
    assert ver_df.shape[0] >= 1
    for p in (inv_csv, ev_csv, ver_csv):
        assert p is not None
        assert Path(p).is_file()
        assert Path(p).stat().st_size > 0
    assert Path(ver_csv).name == "vertical_sonorities.csv"
