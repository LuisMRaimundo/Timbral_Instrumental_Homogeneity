"""Loaded XML inspection CSV download plumbing."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from homogeneity_analyser.services.score_audit import (
    SCORE_AUDIT_EVENT_COLUMNS,
    SCORE_AUDIT_INVENTORY_COLUMNS,
    SCORE_AUDIT_VERTICAL_COLUMNS,
    audit_rows_to_csv_string,
)
from homogeneity_analyser.ui.callbacks import _rows_to_dataframe, _write_temp_csv, run_loaded_xml_inspection

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_XML = REPO_ROOT / "validation" / "fixtures_musicxml" / "step_density.xml"


def test_write_temp_csv_creates_file_with_expected_header():
    text = "h1,h2\n1,2\n"
    p_str = _write_temp_csv("instrument_inventory.csv", text)
    p = Path(p_str)
    assert p.is_file()
    assert p.name == "instrument_inventory.csv"
    first = p.read_text(encoding="utf-8").splitlines()[0]
    assert first == "h1,h2"


def test_audit_csv_texts_round_trip_through_write_temp_csv():
    """Same fieldnames as the Loaded XML inspection callback; paths exist and headers match."""
    inv_row = {k: ("x" if k == "part_id" else "") for k in SCORE_AUDIT_INVENTORY_COLUMNS}
    ev_row = {k: "" for k in SCORE_AUDIT_EVENT_COLUMNS}
    ev_row.update(
        {
            "measure": 1,
            "offset_quarterLength": 0.0,
            "duration_quarterLength": 1.0,
            "sounding_midi": 60,
            "written_midi": 60,
            "chord_tone_index": 0,
            "is_chord_tone": False,
            "is_unpitched": False,
            "crescendo_active": False,
            "diminuendo_active": False,
        }
    )
    ver_row = {k: "" for k in SCORE_AUDIT_VERTICAL_COLUMNS}
    ver_row.update(
        {
            "measure": 1,
            "offset_quarterLength": 0.0,
            "number_of_active_events": 1,
            "vertical_pitch_cardinality": 1,
            "register_span_semitones": 0.0,
            "duplicate_pitch_count": 0,
            "n_unique_sounding_midis": 1,
            "technique_coverage_status": "ordinary_default_uniform",
        }
    )

    inv_csv = audit_rows_to_csv_string([inv_row], fieldnames=SCORE_AUDIT_INVENTORY_COLUMNS)
    ev_csv = audit_rows_to_csv_string([ev_row], fieldnames=SCORE_AUDIT_EVENT_COLUMNS)
    ver_csv = audit_rows_to_csv_string([ver_row], fieldnames=SCORE_AUDIT_VERTICAL_COLUMNS)

    p_inv = Path(_write_temp_csv("instrument_inventory.csv", inv_csv))
    p_ev = Path(_write_temp_csv("event_audit.csv", ev_csv))
    p_ver = Path(_write_temp_csv("vertical_sonorities.csv", ver_csv))

    for path, expected_first_line in (
        (p_inv, ",".join(SCORE_AUDIT_INVENTORY_COLUMNS)),
        (p_ev, ",".join(SCORE_AUDIT_EVENT_COLUMNS)),
        (p_ver, ",".join(SCORE_AUDIT_VERTICAL_COLUMNS)),
    ):
        assert path.is_file()
        assert path.read_text(encoding="utf-8").splitlines()[0] == expected_first_line


def _assert_no_dict_cells(df: pd.DataFrame) -> None:
    for _col, series in df.items():
        for v in series:
            if pd.isna(v):
                continue
            assert not isinstance(v, dict), f"unexpected dict in column {_col!r}"


def test_rows_to_dataframe_empty_has_headers():
    df = _rows_to_dataframe([], SCORE_AUDIT_INVENTORY_COLUMNS)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == list(SCORE_AUDIT_INVENTORY_COLUMNS)
    assert len(df) == 0


def test_run_loaded_xml_inspection_returns_dataframes_and_csv_paths():
    if not FIXTURE_XML.is_file():
        pytest.skip("Fixture not found")
    out = run_loaded_xml_inspection(str(FIXTURE_XML))
    assert len(out) == 7
    notice, inv_df, inv_p, ev_df, ev_p, ver_df, ver_p = out
    assert isinstance(notice, str)
    for df in (inv_df, ev_df, ver_df):
        assert isinstance(df, pd.DataFrame)
        _assert_no_dict_cells(df)
    assert list(inv_df.columns) == list(SCORE_AUDIT_INVENTORY_COLUMNS)
    assert list(ev_df.columns) == list(SCORE_AUDIT_EVENT_COLUMNS)
    assert list(ver_df.columns) == list(SCORE_AUDIT_VERTICAL_COLUMNS)
    assert {"part_id", "part_name", "canonical_instrument"} <= set(inv_df.columns)
    assert {"offset_quarterLength", "part_name", "sounding_pitch", "sounding_midi"} <= set(ev_df.columns)
    assert {
        "offset_quarterLength",
        "number_of_active_events",
        "midi_set",
        "register_span_semitones",
        "register_compactness",
    } <= set(ver_df.columns)
    for path in (inv_p, ev_p, ver_p):
        assert isinstance(path, str)
        assert Path(path).is_file()
        assert Path(path).read_text(encoding="utf-8").strip()


def test_run_loaded_xml_inspection_accepts_gradio_style_dict():
    if not FIXTURE_XML.is_file():
        pytest.skip("Fixture not found")
    out = run_loaded_xml_inspection({"path": str(FIXTURE_XML)})
    assert len(out) == 7
    inv_csv = out[2]
    assert isinstance(inv_csv, str)
    text = Path(inv_csv).read_text(encoding="utf-8")
    assert text.splitlines()[0] == ",".join(SCORE_AUDIT_INVENTORY_COLUMNS)
