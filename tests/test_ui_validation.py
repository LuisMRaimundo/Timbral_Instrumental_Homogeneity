from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import gradio as gr
import pytest

from homogeneity_analyser.ui.validation import coerce_float, gradio_upload_to_path, validate_uploaded_score


@pytest.mark.parametrize(
    ("raw", "default", "expected"),
    [
        (None, 1.25, 1.25),
        ("", 2.0, 2.0),
        ("3.5", 0.0, 3.5),
        ("3,5", 0.0, 3.5),
    ],
)
def test_coerce_float(raw, default, expected):
    assert coerce_float(raw, default) == expected


def test_coerce_float_invalid_non_empty_raises():
    with pytest.raises(ValueError, match="numeric input"):
        coerce_float("not-a-number", 7.0)


def test_validate_uploaded_score_none_raises():
    with pytest.raises(gr.Error, match="Upload a MusicXML"):
        validate_uploaded_score(None)


def test_validate_uploaded_score_missing_path_raises(tmp_path: Path):
    missing = tmp_path / "gone.xml"
    fake = SimpleNamespace(name=str(missing))
    with pytest.raises(gr.Error, match="not found"):
        validate_uploaded_score(fake)


def test_validate_uploaded_score_bad_extension(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_text("hello", encoding="utf-8")
    fake = SimpleNamespace(name=str(p))
    with pytest.raises(gr.Error, match="Unsupported file type"):
        validate_uploaded_score(fake)


def test_validate_uploaded_score_accepts_valid_xml(tmp_path: Path):
    p = tmp_path / "score.xml"
    p.write_bytes(b"<?xml version='1.0'?><score-partwise/>")
    fake = SimpleNamespace(name=str(p))
    assert validate_uploaded_score(fake) == str(p)


def test_validate_uploaded_score_accepts_str_and_path(tmp_path: Path):
    p = tmp_path / "a.xml"
    p.write_bytes(b"<?xml version='1.0'?><score-partwise/>")
    assert validate_uploaded_score(str(p)) == str(p)
    assert validate_uploaded_score(p) == str(p)


def test_validate_uploaded_score_accepts_dict_with_path(tmp_path: Path):
    p = tmp_path / "b.xml"
    p.write_bytes(b"<?xml version='1.0'?><score-partwise/>")
    assert validate_uploaded_score({"path": str(p)}) == str(p)


def test_validate_uploaded_score_accepts_dict_with_name(tmp_path: Path):
    p = tmp_path / "c.xml"
    p.write_bytes(b"<?xml version='1.0'?><score-partwise/>")
    assert validate_uploaded_score({"name": str(p)}) == str(p)


def test_validate_uploaded_score_accepts_object_with_path(tmp_path: Path):
    p = tmp_path / "d.xml"
    p.write_bytes(b"<?xml version='1.0'?><score-partwise/>")
    assert validate_uploaded_score(SimpleNamespace(path=str(p))) == str(p)


def test_gradio_upload_to_path_unwraps_single_file_list(tmp_path: Path):
    p = tmp_path / "e.xml"
    p.write_bytes(b"<?xml version='1.0'?><score-partwise/>")
    assert gradio_upload_to_path([str(p)]) == p
    assert gradio_upload_to_path([{"path": str(p)}]) == p
