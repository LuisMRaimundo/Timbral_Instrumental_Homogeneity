"""
Local dev launcher for the Gradio H_TI app (run with Python; not the PyInstaller entry).

Usage (from repository root):

  Command Prompt:
      set PYTHONPATH=src
      python packaging/windows/launcher.py

  PowerShell:
      $env:PYTHONPATH = "src"
      python packaging/windows/launcher.py

  If you nest this inside ``powershell -Command "..."`` from another host, escape ``$`` (e.g. `` `$env:PYTHONPATH``)
  or use ``cmd /c "set PYTHONPATH=src && python packaging\\windows\\launcher.py"`` so ``$env:`` is not stripped.

  (Or install the package with ``pip install -e .`` so ``homogeneity_analyser`` is on path; PYTHONPATH is then optional.)

Binds only to 127.0.0.1, picks the first free port from 7860 upward, opens the browser (``inbrowser=True``).
"""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path


def _ensure_src_on_path() -> Path:
    """Repository root (parent of ``packaging/``)."""
    here = Path(__file__).resolve().parent
    repo = here.parent.parent
    src = repo / "src"
    sp = str(src)
    if sp not in sys.path:
        sys.path.insert(0, sp)
    return repo


def pick_free_port(host: str = "127.0.0.1", start: int = 7860, max_tries: int = 64) -> int:
    """Return the first port in ``[start, start+max_tries)`` that accepts a TCP bind on ``host``."""
    for port in range(start, start + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except OSError:
                continue
        return port
    raise RuntimeError(f"No free TCP port on {host!r} in range {start}..{start + max_tries - 1}")


def main() -> None:
    _ensure_src_on_path()
    host = "127.0.0.1"
    port = pick_free_port(host=host, start=7860)
    os.environ.setdefault("HOMOGENEITY_CACHE_DIR", str(Path(os.environ.get("LOCALAPPDATA", "")) / "HomogeneityAnalyser" / "exports"))
    Path(os.environ["HOMOGENEITY_CACHE_DIR"]).mkdir(parents=True, exist_ok=True)

    from homogeneity_analyser.utils.output_paths import cleanup_stale_exports, gradio_launch_kwargs
    from homogeneity_analyser.ui.gradio_app import build_demo

    cleanup_stale_exports()
    url = f"http://{host}:{port}/"
    print(f"Homogeneity Analyser: binding {url} (browser will open if supported)")
    build_demo().launch(
        **gradio_launch_kwargs(
            server_name=host,
            server_port=port,
            inbrowser=True,
        )
    )


if __name__ == "__main__":
    main()
