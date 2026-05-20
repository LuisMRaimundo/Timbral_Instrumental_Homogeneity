"""Gradio upload validation and numeric coercion."""

from __future__ import annotations

import math
import numbers
from pathlib import Path
from typing import Any

import gradio as gr

from homogeneity_analyser.io.score_validation import ScoreValidationError, validate_score_path

VALID_SCORE_EXTENSIONS_UI = frozenset({".xml", ".musicxml", ".mxl", ".mid", ".midi"})

_UNSET: Any = object()


def _is_empty_ui_number(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _parse_ui_float_string(s: str, *, field_name: str) -> float:
    """
    Parse a non-empty stripped string to float.

    Accepts ``.`` or ``,`` as the single decimal separator. Rejects ambiguous
    mixed thousands/decimal patterns (both ``.`` and ``,`` present, or multiple of one kind).
    """
    if "," in s and "." in s:
        raise ValueError(
            f"{field_name}: ambiguous number {s!r} (contains both ',' and '.'). "
            "Use only one decimal separator, e.g. 0.25 or 0,25."
        )
    if s.count(",") > 1:
        raise ValueError(f"{field_name}: invalid number {s!r} (multiple commas).")
    if s.count(".") > 1:
        raise ValueError(f"{field_name}: invalid number {s!r} (multiple decimal points).")
    if "," in s:
        s = s.replace(",", ".", 1)
    try:
        out = float(s)
    except ValueError as e:
        raise ValueError(f"{field_name}: could not parse {s!r} as a number.") from e
    if not math.isfinite(out):
        raise ValueError(f"{field_name}: value must be finite (got {s!r}).")
    return out


def parse_ui_float(value: Any, default: Any = _UNSET, *, field_name: str = "value") -> float | None:
    """
    Parse Gradio numeric inputs for European ``0,25`` or US ``0.25`` decimal styles.

    - ``int`` / ``float`` (not ``bool``): returned as ``float`` if finite.
    - ``str``: stripped; empty → ``default`` when ``default`` is not ``_UNSET``, else ``None`` if
      ``default is None``, else ``ValueError``.
    - If ``default`` is ``_UNSET`` (omitted): empty or invalid input raises ``ValueError`` with
      ``field_name``.
    - If ``default`` is set (including ``None``): empty input returns that default; invalid input
      still raises ``ValueError``.
    """
    if isinstance(value, bool):
        raise ValueError(f"{field_name}: boolean is not a valid number.")
    if isinstance(value, numbers.Real):
        f = float(value)
        if not math.isfinite(f):
            raise ValueError(f"{field_name}: value must be finite.")
        return f
    if _is_empty_ui_number(value):
        if default is _UNSET:
            raise ValueError(f"{field_name}: value is required.")
        if default is None:
            return None
        return float(default)
    if not isinstance(value, str):
        value = str(value)
    s = value.strip()
    return _parse_ui_float_string(s, field_name=field_name)


def coerce_float(x: Any, default: float, *, field_name: str = "numeric input") -> float:
    """
    Parse a UI float with a default for empty input.

    Empty/None → ``default``. Invalid non-empty input raises ``ValueError`` (no silent fallback).
    """
    parsed = parse_ui_float(x, default=default, field_name=field_name)
    if parsed is None:
        return float(default)
    return float(parsed)


def gradio_upload_to_path(file_obj: Any) -> Path | None:
    """
    Normalize a Gradio ``File`` / upload value to a filesystem path.

    Handles ``None``, ``str``, ``pathlib.Path``, dict payloads (``path`` / ``name``),
    objects with ``.path`` or ``.name``, and a single-element list/tuple of any of the above.
    """
    if file_obj is None:
        return None
    if isinstance(file_obj, list | tuple):
        if len(file_obj) == 0:
            return None
        if len(file_obj) == 1:
            return gradio_upload_to_path(file_obj[0])
        return None
    if isinstance(file_obj, Path):
        return file_obj
    if isinstance(file_obj, str):
        s = file_obj.strip()
        return Path(s) if s else None
    if isinstance(file_obj, dict):
        for key in ("path", "name"):
            v = file_obj.get(key)
            if v is not None and str(v).strip():
                return Path(str(v).strip())
        return None
    path_attr = getattr(file_obj, "path", None)
    if path_attr is not None and str(path_attr).strip():
        return Path(str(path_attr).strip())
    name_attr = getattr(file_obj, "name", None)
    if name_attr is not None and str(name_attr).strip():
        return Path(str(name_attr).strip())
    return None


def validate_uploaded_score(file_obj: Any) -> str:
    """Return path to uploaded score or raise gr.Error."""
    path = gradio_upload_to_path(file_obj)
    if path is None:
        raise gr.Error("Upload a MusicXML (.xml/.musicxml/.mxl) or MIDI (.mid/.midi) file.")
    score_path = str(path)
    if not path.is_file():
        raise gr.Error("Uploaded file path not found.")
    ext = path.suffix.lower()
    if ext not in VALID_SCORE_EXTENSIONS_UI:
        raise gr.Error("Unsupported file type. Use MusicXML or MIDI.")
    try:
        validate_score_path(score_path)
    except ScoreValidationError as e:
        raise gr.Error(str(e)) from e
    return score_path
