"""Gradio callback: symbolic inspection tables (no H_TI run)."""

from __future__ import annotations

import logging
from pathlib import Path

import gradio as gr

from homogeneity_analyser.io.score_loader import parse_score
from homogeneity_analyser.io.score_validation import ScoreValidationError, validate_score_path
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS
from homogeneity_analyser.services.score_audit import (
    SCORE_AUDIT_EVENT_COLUMNS,
    SCORE_AUDIT_INVENTORY_COLUMNS,
    SCORE_AUDIT_VERTICAL_COLUMNS,
    audit_rows_to_csv_string,
    build_symbolic_inspection_tables,
)
from homogeneity_analyser.ui.callback_result_formatting import (
    rows_to_dataframe as rows_to_dataframe,
    write_temp_csv as write_temp_csv,
)
from homogeneity_analyser.ui.validation import gradio_upload_to_path

_LOG = logging.getLogger(__name__)

def run_loaded_xml_inspection(file_obj, pitch_interpretation_mode=None, harmonic_pitch_policy=None):
    """
    Refresh symbolic score audit tables when the shared upload changes.

    Does not run H / U / H_timbral; failures are surfaced in the notice only.
    """
    idle_notice = (
        "Upload a score file above to populate **Symbolic inspection**. "
        "MusicXML / MXL is recommended for instrument names, directions, and articulations."
    )
    empty_inv_df = rows_to_dataframe([], SCORE_AUDIT_INVENTORY_COLUMNS)
    empty_ev_df = rows_to_dataframe([], SCORE_AUDIT_EVENT_COLUMNS)
    empty_ver_df = rows_to_dataframe([], SCORE_AUDIT_VERTICAL_COLUMNS)
    # Order: notice (Markdown), inv table, inv.csv, ev table, ev.csv, ver table, ver.csv
    empty = (idle_notice, empty_inv_df, None, empty_ev_df, None, empty_ver_df, None)
    if file_obj is None:
        return empty

    upload_path = gradio_upload_to_path(file_obj)
    if upload_path is None or not upload_path.is_file():
        return (
            "⚠️ **Inspection skipped:** uploaded file path is missing or not found.",
            empty_inv_df,
            None,
            empty_ev_df,
            None,
            empty_ver_df,
            None,
        )

    score_path = str(upload_path)
    ext = upload_path.suffix.lower()
    if ext not in {".xml", ".musicxml", ".mxl", ".mid", ".midi"}:
        return (
            "⚠️ **Inspection skipped:** unsupported file type for this UI.",
            empty_inv_df,
            None,
            empty_ev_df,
            None,
            empty_ver_df,
            None,
        )

    try:
        validate_score_path(score_path)
    except ScoreValidationError as exc:
        return (
            f"⚠️ **Inspection skipped:** {exc}",
            empty_inv_df,
            None,
            empty_ev_df,
            None,
            empty_ver_df,
            None,
        )

    try:
        score = parse_score(score_path)
        pim = str(
            pitch_interpretation_mode or DEFAULT_HTI_PARAMS.get("pitch_interpretation_mode") or "musicxml_sounding"
        )
        hpol = (
            str(harmonic_pitch_policy or DEFAULT_HTI_PARAMS.get("harmonic_pitch_policy") or "conservative")
            .strip()
            .lower()
        )
        inv, events, vert = build_symbolic_inspection_tables(
            score, pitch_interpretation_mode=pim.strip(), harmonic_pitch_policy=hpol
        )
        inv_csv_text = audit_rows_to_csv_string(inv, fieldnames=SCORE_AUDIT_INVENTORY_COLUMNS)
        ev_csv_text = audit_rows_to_csv_string(events, fieldnames=SCORE_AUDIT_EVENT_COLUMNS)
        ver_csv_text = audit_rows_to_csv_string(vert, fieldnames=SCORE_AUDIT_VERTICAL_COLUMNS)
        inv_path = write_temp_csv("instrument_inventory.csv", inv_csv_text)
        ev_path = write_temp_csv("event_audit.csv", ev_csv_text)
        ver_path = write_temp_csv("vertical_sonorities.csv", ver_csv_text)
        label = Path(score_path).name
        notice = (
            f"**Symbolic inspection updated** — **{label}**: {len(inv)} part(s), "
            f"{len(events)} pitch-level event row(s), {len(vert)} vertical sonorit(y/ies). CSV downloads below."
        )
        inventory_df = rows_to_dataframe(inv, SCORE_AUDIT_INVENTORY_COLUMNS)
        event_df = rows_to_dataframe(events, SCORE_AUDIT_EVENT_COLUMNS)
        vertical_df = rows_to_dataframe(vert, SCORE_AUDIT_VERTICAL_COLUMNS)
        return (notice, inventory_df, inv_path, event_df, ev_path, vertical_df, ver_path)
    except Exception as exc:  # pragma: no cover - defensive UI path
        _LOG.exception("Loaded XML inspection failed")
        return (
            f"⚠️ **Inspection failed** (other tabs are unaffected): `{type(exc).__name__}: {exc}`",
            empty_inv_df,
            None,
            empty_ev_df,
            None,
            empty_ver_df,
            None,
        )
