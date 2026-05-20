"""Pre-parse validation for score files (size, extension, MXL zip safety)."""

from __future__ import annotations

import zipfile
from pathlib import Path

# 50 MiB on-disk file (before decompress)
MAX_SCORE_FILE_BYTES = 50 * 1024 * 1024
# Zip member limits (MXL is a zip container)
MAX_ZIP_MEMBERS = 256
MAX_ZIP_SINGLE_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES = 400 * 1024 * 1024

VALID_SCORE_EXTENSIONS = frozenset({".xml", ".musicxml", ".mxl", ".mid", ".midi"})


class ScoreValidationError(ValueError):
    """Raised when a score path fails structural or safety checks before music21 parsing."""


def _unsafe_zip_member_name(name: str) -> bool:
    n = name.replace("\\", "/")
    if n.startswith("/") or ".." in n.split("/"):
        return True
    return bool(Path(n).is_absolute())


def validate_zip_archive(path: str) -> None:
    """
    Reject suspicious MXL/MusicXML zip containers (path traversal, huge members).
    Does not decompress full payload — uses ZipInfo metadata only.
    """
    try:
        zf = zipfile.ZipFile(path, "r")
    except zipfile.BadZipFile as e:
        raise ScoreValidationError(f"Invalid or corrupted ZIP (MXL): {e}") from e
    try:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_MEMBERS:
            raise ScoreValidationError(
                f"ZIP contains too many entries ({len(infos)}); maximum allowed is {MAX_ZIP_MEMBERS}."
            )
        total_uncompressed = 0
        for zi in infos:
            if _unsafe_zip_member_name(zi.filename):
                raise ScoreValidationError(f"Unsafe path inside ZIP: {zi.filename!r}")
            usize = int(zi.file_size)
            if usize > MAX_ZIP_SINGLE_UNCOMPRESSED_BYTES:
                raise ScoreValidationError(
                    f"ZIP member {zi.filename!r} declares uncompressed size {usize} bytes; "
                    f"limit is {MAX_ZIP_SINGLE_UNCOMPRESSED_BYTES}."
                )
            total_uncompressed += usize
            if total_uncompressed > MAX_ZIP_TOTAL_UNCOMPRESSED_BYTES:
                raise ScoreValidationError(
                    "ZIP declares excessive total uncompressed size; file may be malicious or corrupt."
                )
    finally:
        zf.close()


def validate_score_path(path: str) -> None:
    """
    Validate path exists, extension allowed, file size, and MXL zip structure.
    Call before music21.converter.parse.
    """
    if not path or not isinstance(path, str):
        raise ScoreValidationError("No file path provided.")
    p = Path(path)
    if not p.is_file():
        raise ScoreValidationError(f"Score file not found: {path}")
    ext = p.suffix.lower()
    if ext not in VALID_SCORE_EXTENSIONS:
        raise ScoreValidationError(
            f"Unsupported extension {ext!r}. Use MusicXML (.xml, .musicxml, .mxl) or MIDI (.mid, .midi)."
        )
    size = p.stat().st_size
    if size > MAX_SCORE_FILE_BYTES:
        raise ScoreValidationError(
            f"File too large ({size} bytes). Maximum allowed is {MAX_SCORE_FILE_BYTES} bytes (~50 MiB)."
        )
    if size == 0:
        raise ScoreValidationError("File is empty.")
    if ext == ".mxl":
        validate_zip_archive(path)
