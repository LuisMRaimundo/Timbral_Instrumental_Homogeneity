"""
Writable export paths for Gradio CSV/PNG outputs with TTL cleanup.

Set HOMOGENEITY_CACHE_DIR to override the directory (e.g. a dedicated disk).
"""

from __future__ import annotations

import contextlib
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

_DEFAULT_SUBDIR = "homogeneity_analyser_exports"


def export_directory() -> Path:
    """Directory for CSV/PNG exports; created if missing."""
    env = os.environ.get("HOMOGENEITY_CACHE_DIR", "").strip()
    p = Path(env) if env else Path(tempfile.gettempdir()) / _DEFAULT_SUBDIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def gradio_allowed_paths() -> list[str]:
    """
    Directories Gradio may read/write for File/Download outputs.

    Required when ``HOMOGENEITY_CACHE_DIR`` points outside cwd and system temp
    (e.g. ``%LOCALAPPDATA%\\Orchomogeneity\\exports`` from ``run.bat``).
    """
    seen: set[str] = set()
    out: list[str] = []
    for raw in (
        export_directory(),
        Path.cwd(),
        Path(tempfile.gettempdir()),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Orchomogeneity" / "exports",
        Path(os.environ.get("LOCALAPPDATA", "")) / "HomogeneityAnalyser" / "exports",
    ):
        s = str(raw)
        if not s or s in seen:
            continue
        try:
            resolved = str(Path(s).resolve())
        except OSError:
            resolved = s
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(resolved)
    return out


def gradio_launch_kwargs(**overrides: Any) -> dict[str, Any]:
    """Common ``Blocks.launch()`` options (``allowed_paths``, ``show_error``)."""
    kw: dict[str, Any] = {
        "allowed_paths": gradio_allowed_paths(),
        "show_error": True,
    }
    kw.update(overrides)
    return kw


def new_export_path(prefix: str, suffix: str) -> str:
    """
    Return a unique path under `export_directory()`. Calls cleanup first.
    prefix/suffix should look like 'homogeneity_' and '.csv'.
    """
    cleanup_stale_exports()
    name = f"{prefix}{uuid.uuid4().hex[:16]}{suffix}"
    return str(export_directory() / name)


def cleanup_stale_exports(max_age_seconds: float = 86400.0, max_files: int = 400) -> None:
    """
    Remove files older than max_age_seconds, then trim to max_files by age (oldest first).
    """
    d = export_directory()
    now = time.time()
    try:
        files = [f for f in d.iterdir() if f.is_file()]
    except OSError:
        return
    for f in files:
        try:
            if now - f.stat().st_mtime > max_age_seconds:
                f.unlink()
        except OSError:
            pass
    try:
        files = sorted(
            (f for f in d.iterdir() if f.is_file()),
            key=lambda f: f.stat().st_mtime,
        )
    except OSError:
        return
    while len(files) > max_files:
        with contextlib.suppress(OSError):
            files[0].unlink()
        files = files[1:]
