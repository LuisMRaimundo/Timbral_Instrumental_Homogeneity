"""
PyInstaller entrypoint for the frozen Windows build.

Sets a user-writable export/cache directory and sensible Gradio bind defaults
before importing the application (no changes to core analysis code).
"""

from __future__ import annotations

import os
import socket
import sys


def _pick_free_port(host: str, start: int, max_tries: int = 64) -> int:
    """First TCP port in ``[start, start+max_tries)`` that accepts a bind on ``host``."""
    for port in range(start, start + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except OSError:
                continue
        return port
    raise RuntimeError(f"No free TCP port on {host!r} in range {start}..{start + max_tries - 1}")


def _resolve_listen_port(host: str, preferred: int) -> int:
    """Use ``preferred`` when free; otherwise the next free port from ``preferred`` upward."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, preferred))
            return preferred
        except OSError:
            return _pick_free_port(host, preferred + 1)


def _configure_runtime() -> None:
    if not getattr(sys, "frozen", False):
        return
    # PyInstaller one-file extracts to sys._MEIPASS; one-dir uses executable folder.
    base = os.environ.get("LOCALAPPDATA", "").strip() or os.path.expanduser("~")
    cache = os.path.join(base, "HomogeneityAnalyser", "exports")
    os.makedirs(cache, exist_ok=True)
    os.environ.setdefault("HOMOGENEITY_CACHE_DIR", cache)
    # Local-only server; avoids binding 0.0.0.0 without user intent.
    os.environ.setdefault("GRADIO_SERVER_NAME", "127.0.0.1")
    # Default listen port (may be replaced in main() if busy).
    os.environ.setdefault("GRADIO_SERVER_PORT", "7860")


def main() -> None:
    _configure_runtime()
    from homogeneity_analyser.ui.gradio_app import build_demo
    from homogeneity_analyser.utils.output_paths import cleanup_stale_exports, gradio_launch_kwargs

    cleanup_stale_exports()
    host = (os.environ.get("GRADIO_SERVER_NAME") or "127.0.0.1").strip() or "127.0.0.1"
    preferred = int((os.environ.get("GRADIO_SERVER_PORT") or "7860").strip() or "7860")
    port = _resolve_listen_port(host, preferred)
    os.environ["GRADIO_SERVER_PORT"] = str(port)
    print(f"Homogeneity Analyser (frozen): http://{host}:{port}/ (browser will open if supported)")
    # Same Blocks entry as dev: ``python -m homogeneity_analyser`` → ``build_demo()`` (H_TI + Symbolic inspection).
    build_demo().launch(
        **gradio_launch_kwargs(
            server_name=host,
            server_port=port,
            inbrowser=True,
        )
    )


if __name__ == "__main__":
    main()
