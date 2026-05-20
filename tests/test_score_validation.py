from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from homogeneity_analyser.io.score_validation import ScoreValidationError, validate_score_path


def test_validate_rejects_nonexistent(tmp_path: Path) -> None:
    p = tmp_path / "missing.xml"
    with pytest.raises(ScoreValidationError, match="not found"):
        validate_score_path(str(p))


def test_validate_rejects_bad_extension(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_bytes(b"hello")
    with pytest.raises(ScoreValidationError, match="Unsupported extension"):
        validate_score_path(str(p))


def test_validate_mxl_rejects_zip_slip(tmp_path: Path) -> None:
    mxl = tmp_path / "bad.mxl"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../../evil.xml", b"<score/>")
    mxl.write_bytes(buf.getvalue())
    with pytest.raises(ScoreValidationError, match="Unsafe path"):
        validate_score_path(str(mxl))


def test_validate_mxl_rejects_too_many_members(tmp_path: Path) -> None:
    mxl = tmp_path / "many.mxl"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(300):
            zf.writestr(f"f{i}.xml", b"<a/>")
    mxl.write_bytes(buf.getvalue())
    with pytest.raises(ScoreValidationError, match="too many entries"):
        validate_score_path(str(mxl))
