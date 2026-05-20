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

_DEFAULT_SUBDIR = "homogeneity_analyser_exports"


def export_directory() -> Path:
    """Directory for CSV/PNG exports; created if missing."""
    env = os.environ.get("HOMOGENEITY_CACHE_DIR", "").strip()
    p = Path(env) if env else Path(tempfile.gettempdir()) / _DEFAULT_SUBDIR
    p.mkdir(parents=True, exist_ok=True)
    return p


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
