"""Unit tests for ``homogeneity_analyser.services.score_audit``."""

from __future__ import annotations

from pathlib import Path

import pytest
from music21 import articulations, chord, meter, note, stream

from homogeneity_analyser.io.score_loader import parse_score
from homogeneity_analyser.services.score_audit import (
    SCORE_AUDIT_EVENT_COLUMNS,
    SCORE_AUDIT_INVENTORY_COLUMNS,
    audit_rows_to_csv_string,
    build_symbolic_inspection_tables,
    build_vertical_sonority_audit,
    extract_instrument_inventory,
    extract_score_event_audit,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"


def _four_parts_one_note_each() -> stream.Score:
    sc = stream.Score()
    for i in range(4):
        p = stream.Part(id=f"P{i + 1}")
        p.partName = f"Part{i + 1}"
        p.insert(0, meter.TimeSignature("4/4"))
        p.insert(0, note.Note("C4", quarterLength=1.0))
        sc.insert(0, p)
    return sc


def test_build_symbolic_inspection_tables_returns_three_tables():
    sc = _four_parts_one_note_each()
    inv, ev, vert = build_symbolic_inspection_tables(sc)
    assert len(inv) == 4
    assert len(ev) == 4
    assert len(vert) == 1
    assert set(inv[0].keys()) == set(SCORE_AUDIT_INVENTORY_COLUMNS)
    assert set(ev[0].keys()) == set(SCORE_AUDIT_EVENT_COLUMNS)


def test_four_parts_four_event_rows():
    sc = _four_parts_one_note_each()
    rows = extract_score_event_audit(sc)
    assert len(rows) == 4


def test_vertical_cluster_b3_to_d4():
    events = [
        {
            "offset_quarterLength": 0.0,
            "sounding_midi": 59,
            "sounding_pitch": "B3",
            "written_pitch": "B3",
            "written_midi": 59,
            "part_name": "A",
            "raw_part_name": "",
            "section_label": "",
            "desk_group": "",
            "part_label_original": "",
            "canonical_instrument": "Violin",
            "instrumental_subfamily": "strings",
            "technique_state_id": "violin|arco",
            "technique_uniformity_key": "ordinary_default",
            "explicit_technique": "none",
            "explicit_technique_detected": False,
            "is_unpitched": False,
            "measure": 1,
            "active_dynamic": "unknown",
            "articulation_marks": "",
            "other_effects": "none",
            "parser_warning": "",
        },
        {
            "offset_quarterLength": 0.0,
            "sounding_midi": 60,
            "sounding_pitch": "C4",
            "written_pitch": "C4",
            "written_midi": 60,
            "part_name": "B",
            "raw_part_name": "",
            "section_label": "",
            "desk_group": "",
            "part_label_original": "",
            "canonical_instrument": "Violin",
            "instrumental_subfamily": "strings",
            "technique_state_id": "violin|arco",
            "technique_uniformity_key": "ordinary_default",
            "explicit_technique": "none",
            "explicit_technique_detected": False,
            "is_unpitched": False,
            "measure": 1,
            "active_dynamic": "unknown",
            "articulation_marks": "",
            "other_effects": "none",
            "parser_warning": "",
        },
        {
            "offset_quarterLength": 0.0,
            "sounding_midi": 61,
            "sounding_pitch": "C#4",
            "written_pitch": "C#4",
            "written_midi": 61,
            "part_name": "C",
            "raw_part_name": "",
            "section_label": "",
            "desk_group": "",
            "part_label_original": "",
            "canonical_instrument": "Violin",
            "instrumental_subfamily": "strings",
            "technique_state_id": "violin|arco",
            "technique_uniformity_key": "ordinary_default",
            "explicit_technique": "none",
            "explicit_technique_detected": False,
            "is_unpitched": False,
            "measure": 1,
            "active_dynamic": "unknown",
            "articulation_marks": "",
            "other_effects": "none",
            "parser_warning": "",
        },
        {
            "offset_quarterLength": 0.0,
            "sounding_midi": 62,
            "sounding_pitch": "D4",
            "written_pitch": "D4",
            "written_midi": 62,
            "part_name": "D",
            "raw_part_name": "",
            "section_label": "",
            "desk_group": "",
            "part_label_original": "",
            "canonical_instrument": "Violin",
            "instrumental_subfamily": "strings",
            "technique_state_id": "violin|arco",
            "technique_uniformity_key": "ordinary_default",
            "explicit_technique": "none",
            "explicit_technique_detected": False,
            "is_unpitched": False,
            "measure": 1,
            "active_dynamic": "unknown",
            "articulation_marks": "",
            "other_effects": "none",
            "parser_warning": "",
        },
    ]
    vert = build_vertical_sonority_audit(events)
    assert len(vert) == 1
    row = vert[0]
    assert row["number_of_active_events"] == 4
    assert row["vertical_pitch_cardinality"] == 4
    assert row["midi_set"] == "59, 60, 61, 62"
    assert row["register_span_semitones"] == pytest.approx(3.0)
    assert row["active_technique_states"] == "ordinary_default"
    assert row["technique_coverage_status"] == "ordinary_default_uniform"


def test_chord_expanded_to_one_row_per_pitch():
    p = stream.Part(id="P1")
    p.partName = "Violin"
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, chord.Chord(["C4", "E4", "G4"], quarterLength=2.0))
    sc = stream.Score()
    sc.insert(0, p)
    rows = extract_score_event_audit(sc)
    assert len(rows) == 3
    midis = sorted(int(r["sounding_midi"]) for r in rows)
    assert midis == [60, 64, 67]
    assert sum(1 for r in rows if r["is_chord_tone"]) == 3


def test_missing_instrument_names_do_not_crash():
    p = stream.Part()
    p.partName = ""
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, note.Note("D4", quarterLength=1.0))
    sc = stream.Score()
    sc.insert(0, p)
    inv = extract_instrument_inventory(sc)
    ev = extract_score_event_audit(sc)
    assert len(inv) == 1
    assert isinstance(inv[0]["raw_instrument_name"], str)
    assert len(ev) == 1


def test_articulation_appears_in_raw_columns():
    p = stream.Part(id="P1")
    p.partName = "Violin"
    p.insert(0, meter.TimeSignature("4/4"))
    n = note.Note("G4", quarterLength=1.0)
    n.articulations = [articulations.Staccato()]
    p.insert(0, n)
    sc = stream.Score()
    sc.insert(0, p)
    rows = extract_score_event_audit(sc)
    assert len(rows) == 1
    assert "Staccato" in rows[0]["articulation_marks"]
    assert "Staccato" in rows[0]["technical_marks"]


@pytest.mark.parametrize(
    "fixture, needle_raw, needle_interpreted",
    [
        ("corpus_horn_techniques.musicxml", "gestopft", "stopped"),
        ("corpus_strings_techniques.musicxml", "sul pont", "sul_pont"),
    ],
)
def test_technique_raw_and_interpreted(fixture: str, needle_raw: str, needle_interpreted: str):
    path = FIXTURE_DIR / fixture
    if not path.is_file():
        pytest.skip(f"Missing fixture {path}")
    sc = parse_score(str(path))
    rows = extract_score_event_audit(sc)
    hits = [r for r in rows if needle_raw.lower() in (r.get("direction_text") or "").lower()]
    assert hits, f"expected direction text {needle_raw!r} in audit rows"
    assert any(needle_interpreted in (r.get("technique_state_id") or "") for r in hits), (
        f"expected {needle_interpreted!r} in technique_state_id for rows with {needle_raw!r}"
    )


def test_csv_header_only_when_empty():
    s = audit_rows_to_csv_string([], fieldnames=SCORE_AUDIT_EVENT_COLUMNS)
    lines = s.strip().splitlines()
    assert len(lines) == 1
    assert lines[0].split(",")[0] == "measure"


def test_unpitched_percussion_no_sounding_midi():
    p = stream.Part(id="P1")
    p.partName = "Snare Drum"
    p.insert(0, meter.TimeSignature("4/4"))
    u = note.Unpitched()
    u.displayStep = "F"
    u.displayOctave = 4
    u.duration.quarterLength = 1.0
    p.insert(0, u)
    sc = stream.Score()
    sc.insert(0, p)
    rows = extract_score_event_audit(sc)
    assert len(rows) == 1
    assert rows[0]["is_unpitched"] is True
    assert rows[0]["sounding_midi"] == "unknown"
    assert rows[0]["sounding_pitch"] == "unknown"


def test_unknown_instrument_mapping_warning():
    p = stream.Part(id="P1")
    p.partName = "TotallyUnknownInstrumentXYZ123"
    p.insert(0, meter.TimeSignature("4/4"))
    p.insert(0, note.Note("C4", quarterLength=1.0))
    sc = stream.Score()
    sc.insert(0, p)
    inv, _, _ = build_symbolic_inspection_tables(sc)
    assert inv[0]["unresolved_or_ambiguous_mapping"] == "taxonomy_other_bucket"
