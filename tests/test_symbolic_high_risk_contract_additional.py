"""
Focused validation layer for highest scientific-risk symbolic modules.

Covers gaps in:
- ``technique_state`` and family technique parsers;
- ``timbral_sounding_pitch`` transposition contracts;
- ``io/score_validation`` MXL/path safety;
- ``notation_context`` chronological vs legacy measure text;
- H_TI sliding-window edge geometry and export flags.

Tests only. No production code changes.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from music21 import articulations, chord, dynamics, expressions, instrument, note, stream

from homogeneity_analyser.analyzers.brass_technique import (
    BRASS_HARMON,
    BRASS_STOPPED,
    brass_technique_from_note,
)
from homogeneity_analyser.analyzers.clarinet_technique import (
    CLARINET_BREATHY,
    CLARINET_MULTIPHONIC,
    clarinet_technique_from_note,
)
from homogeneity_analyser.analyzers.hti import HTI_CSV_COLUMNS, SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.hti_adaptive_windows import (
    HTI_EDGE_DROP,
    HTI_EDGE_INCLUDE,
    HTI_EDGE_MARK,
    build_hti_window_centers,
    hti_window_row_geometry,
    resolve_hti_windowing,
)
from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.analyzers.saxophone_technique import (
    SAX_GROWL,
    SAX_SUBTONE,
    saxophone_technique_from_note,
)
from homogeneity_analyser.analyzers.technique_state import (
    TechniqueState,
    TechniqueStateContext,
    compute_technique_uniformity_key,
    merge_note_technique_state,
    normalize_technique_text,
    parse_standard_dynamic_mark,
    technique_state_id,
)
from homogeneity_analyser.analyzers.timbral_sounding_pitch import sounding_pitch_ps_list
from homogeneity_analyser.io.score_validation import (
    MAX_SCORE_FILE_BYTES,
    MAX_ZIP_SINGLE_UNCOMPRESSED_BYTES,
    ScoreValidationError,
    validate_score_path,
    validate_zip_archive,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_SAXOPHONES,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"


# ---------------------------------------------------------------------------
# io/score_validation
# ---------------------------------------------------------------------------


def test_validate_score_path_rejects_empty_and_non_string() -> None:
    with pytest.raises(ScoreValidationError, match="No file path"):
        validate_score_path("")
    with pytest.raises(ScoreValidationError, match="No file path"):
        validate_score_path(None)  # type: ignore[arg-type]


def test_validate_score_path_rejects_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.xml"
    p.write_bytes(b"")
    with pytest.raises(ScoreValidationError, match="empty"):
        validate_score_path(str(p))


def test_validate_score_path_accepts_minimal_musicxml(tmp_path: Path) -> None:
    p = tmp_path / "ok.xml"
    p.write_text('<?xml version="1.0"?><score-partwise/>', encoding="utf-8")
    validate_score_path(str(p))


def test_validate_score_path_rejects_oversized_file(tmp_path: Path) -> None:
    p = tmp_path / "big.xml"
    p.write_bytes(b"x")
    with patch.object(Path, "stat") as mock_stat:
        mock_stat.return_value = Mock(st_size=MAX_SCORE_FILE_BYTES + 1, st_mode=0o100644)
        with pytest.raises(ScoreValidationError, match="too large"):
            validate_score_path(str(p))


def test_validate_zip_rejects_bad_zip(tmp_path: Path) -> None:
    bad = tmp_path / "bad.mxl"
    bad.write_bytes(b"not-a-zip")
    with pytest.raises(ScoreValidationError, match="Invalid or corrupted ZIP"):
        validate_zip_archive(str(bad))


def test_validate_zip_rejects_oversized_member(tmp_path: Path) -> None:
    mxl = tmp_path / "huge.mxl"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "score.xml",
            b"x" * (MAX_ZIP_SINGLE_UNCOMPRESSED_BYTES + 1),
            compress_type=zipfile.ZIP_STORED,
        )
    mxl.write_bytes(buf.getvalue())
    with pytest.raises(ScoreValidationError, match="uncompressed size"):
        validate_zip_archive(str(mxl))


def test_validate_mxl_rejects_absolute_member_path(tmp_path: Path) -> None:
    mxl = tmp_path / "abs.mxl"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("/etc/passwd.xml", b"<score/>")
    mxl.write_bytes(buf.getvalue())
    with pytest.raises(ScoreValidationError, match="Unsafe path"):
        validate_score_path(str(mxl))


# ---------------------------------------------------------------------------
# notation_context — prior / none / legacy semantics
# ---------------------------------------------------------------------------


def _measure_with_directions() -> tuple[stream.Measure, note.Note, note.Note]:
    m = stream.Measure()
    m.insert(0.0, expressions.TextExpression("early arco"))
    m.insert(1.0, note.Note("C4", quarterLength=1.0))
    m.insert(2.0, expressions.TextExpression("late pizz"))
    m.insert(3.0, note.Note("D4", quarterLength=1.0))
    return m, m.notes[0], m.notes[1]


def test_notation_context_prior_excludes_later_measure_directions() -> None:
    _, early, late = _measure_with_directions()
    assert "early arco" in notation_text_context_for_note(early, measure_text="prior")
    assert "pizz" not in notation_text_context_for_note(early, measure_text="prior")
    assert "pizz" in notation_text_context_for_note(late, measure_text="prior")


def test_notation_context_none_is_note_local_only() -> None:
    m = stream.Measure()
    m.insert(0.0, expressions.TextExpression("measure sul pont"))
    n = note.Note("E4")
    n.expressions.append(expressions.TextExpression("local trem"))
    m.insert(1.0, n)
    blob = notation_text_context_for_note(n, measure_text="none")
    assert "local trem" in blob
    assert "sul pont" not in blob


def test_notation_context_legacy_includes_all_measure_directions() -> None:
    _, early, late = _measure_with_directions()
    legacy_early = notation_text_context_for_note(early, measure_text="legacy")
    assert "early arco" in legacy_early
    assert "pizz" in legacy_early
    assert legacy_early == notation_text_context_for_note(late, measure_text="legacy")


def test_notation_context_prior_includes_dynamics_before_note() -> None:
    m = stream.Measure()
    m.insert(0.0, dynamics.Dynamic("pp"))
    m.insert(1.0, note.Note("F4"))
    n = m.notes[0]
    assert "pp" in notation_text_context_for_note(n, measure_text="prior")


# ---------------------------------------------------------------------------
# timbral_sounding_pitch — transposition contracts
# ---------------------------------------------------------------------------


def test_sounding_pitch_transposes_chord_for_bb_clarinet() -> None:
    p = stream.Part()
    p.insert(0, instrument.Clarinet())
    c = chord.Chord(["C4", "E4", "G4"])
    p.append(c)
    written = [float(x.ps) for x in c.pitches]
    ps = sounding_pitch_ps_list(c, p)
    assert len(ps) == 3
    assert all(s < w for s, w in zip(ps, written, strict=True))


def test_sounding_pitch_falls_back_to_part_transposition_for_generic_note_instrument() -> None:
    p = stream.Part()
    ins = instrument.Trumpet()
    p.insert(0, ins)
    n = note.Note("C4")
    p.append(n)
    ps = sounding_pitch_ps_list(n, p)
    expected = float(n.pitch.transpose(ins.transposition).ps)
    assert ps == [pytest.approx(expected)]


def test_sounding_pitch_returns_empty_for_unpitched() -> None:
    from music21.note import Unpitched

    p = stream.Part()
    u = Unpitched()
    p.append(u)
    assert sounding_pitch_ps_list(u, p) == []


# ---------------------------------------------------------------------------
# technique_state helpers and family technique parsers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("  Pizz.  ", "pizz"),
        ("Sul ponticello", "sul ponticello"),
        ("con sordino", "con sordino"),
        ("café", "cafe"),
    ],
)
def test_normalize_technique_text_strips_accents_and_punctuation(raw: str, expected: str) -> None:
    assert normalize_technique_text(raw) == expected


@pytest.mark.parametrize(
    "blob, token",
    [
        ("mf", "mf"),
        ("  pp  ", "pp"),
        ("not-a-dynamic", None),
    ],
)
def test_parse_standard_dynamic_mark(blob: str, token: str | None) -> None:
    assert parse_standard_dynamic_mark(blob) == token


def test_technique_state_id_and_uniformity_key_stable() -> None:
    st = TechniqueState(family=FAMILY_BRASS, instrument="horn", primary="stopped")
    tid = technique_state_id("horn", FAMILY_BRASS, st)
    assert tid == "horn|stopped"
    key = compute_technique_uniformity_key("horn", FAMILY_BRASS, st)
    assert key
    assert "horn" not in key.lower() or "stopped" in key


def test_merge_note_technique_state_applies_brass_stopped_articulation() -> None:
    p = stream.Part()
    p.insert(0, instrument.Horn())
    n = note.Note("G4")
    n.articulations = [articulations.Stopped()]
    ctx = TechniqueStateContext(instrument="horn", family=FAMILY_BRASS)
    st = merge_note_technique_state(ctx, n, instrument="horn", family=FAMILY_BRASS)
    assert st.primary == "stopped"


def test_brass_technique_from_note_detects_harmon_and_stopped() -> None:
    n_harmon = note.Note("C5")
    n_harmon.expressions = [expressions.TextExpression("wah-wah mute")]
    assert brass_technique_from_note(n_harmon, family=FAMILY_BRASS) == BRASS_HARMON

    n_stop = note.Note("D5")
    n_stop.articulations = [articulations.Stopped()]
    assert brass_technique_from_note(n_stop, family=FAMILY_BRASS) == BRASS_STOPPED


def test_clarinet_technique_from_note_detects_multiphonic_and_breathy() -> None:
    n_multi = note.Note("E4")
    n_multi.expressions = [expressions.TextExpression("multiphonic")]
    assert clarinet_technique_from_note(n_multi, family=FAMILY_CLARINETS) == CLARINET_MULTIPHONIC

    n_breath = note.Note("F4")
    n_breath.expressions = [expressions.TextExpression("breathy tone")]
    assert clarinet_technique_from_note(n_breath, family=FAMILY_CLARINETS) == CLARINET_BREATHY


def test_saxophone_technique_from_note_detects_growl_and_subtone() -> None:
    n_growl = note.Note("A3")
    n_growl.expressions = [expressions.TextExpression("growl")]
    assert saxophone_technique_from_note(n_growl, family=FAMILY_SAXOPHONES) == SAX_GROWL

    n_sub = note.Note("B3")
    n_sub.expressions = [expressions.TextExpression("subtone")]
    assert saxophone_technique_from_note(n_sub, family=FAMILY_SAXOPHONES) == SAX_SUBTONE


# ---------------------------------------------------------------------------
# H_TI sliding-window edge geometry and export flags
# ---------------------------------------------------------------------------


def test_hti_edge_include_never_flags_edge_window() -> None:
    for center in (0.0, 3.0, 9.0):
        g = hti_window_row_geometry(center, 6.0, 0.0, 10.0, HTI_EDGE_INCLUDE)
        assert g["edge_window"] is False
        assert 0.0 < g["window_coverage_ratio"] <= 1.0


def test_hti_edge_mark_flags_partial_centers_only() -> None:
    start_edge = hti_window_row_geometry(0.0, 6.0, 0.0, 10.0, HTI_EDGE_MARK)
    mid = hti_window_row_geometry(5.0, 6.0, 0.0, 10.0, HTI_EDGE_MARK)
    assert start_edge["edge_window"] is True
    assert start_edge["window_coverage_ratio"] == pytest.approx(0.5)
    assert mid["edge_window"] is False
    assert mid["window_coverage_ratio"] == pytest.approx(1.0)


def test_build_hti_window_centers_drop_trims_partial_tail() -> None:
    inc = build_hti_window_centers(10.0, 1.0, 6.0, HTI_EDGE_INCLUDE)
    drp = build_hti_window_centers(10.0, 1.0, 6.0, HTI_EDGE_DROP)
    assert len(drp) < len(inc)
    assert drp[-1] + 3.0 <= 10.0 + 1e-9


def test_resolve_hti_windowing_non_positive_step_yields_empty_centers() -> None:
    p = {"window_mode": "manual", "time_step": 0.0, "window_size": 4.0, "edge_policy": HTI_EDGE_MARK}
    r = resolve_hti_windowing(p, excerpt_duration_quarter_length=8.0)
    assert build_hti_window_centers(8.0, r["time_step_effective"], r["window_size_effective"], HTI_EDGE_MARK) == []


def test_hti_analyze_series_exports_edge_fields_for_all_policies() -> None:
    path = FIXTURE_DIR / "golden_two_violins_unison_c5.musicxml"
    if not path.is_file():
        pytest.skip("fixture missing")
    from music21 import converter

    sc = converter.parse(str(path))
    for policy in (HTI_EDGE_INCLUDE, HTI_EDGE_DROP, HTI_EDGE_MARK):
        an = SymbolicTIHomogeneityAnalyzer(music21_score=sc, time_step=1.0)
        r = an.analyze_hti(4.0, edge_policy=policy)
        assert len(r["edge_window"]) == len(r["H_TI"])
        assert len(r["window_coverage_ratio"]) == len(r["H_TI"])
        for col in ("window_start", "window_end", "edge_window", "window_coverage_ratio"):
            assert col in HTI_CSV_COLUMNS
