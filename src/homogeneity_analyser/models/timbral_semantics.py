"""
Explicit semantic naming for timbral analysis (H_timbral).

``H_timbral`` combines symbolic orchestration signals with notation-derived heuristics.
This module defines **model mode** labels for diagnostics and JSON export; only ``legacy``
is implemented today — other modes are reserved for future work without changing defaults.
"""

from __future__ import annotations

from typing import Any, Literal, cast

TimbralModelMode = Literal["legacy", "symbolic", "acoustic_heuristic"]

TIMBRAL_MODEL_SEMANTICS_VERSION = "1.0"

_MODEL_DESCRIPTIONS: dict[TimbralModelMode, str] = {
    "legacy": (
        "Legacy symbolic timbral-instrumental homogeneity: MusicXML/MIDI part names mapped to a "
        "taxonomy, register span, technique-state concentration, overlap-weighted family pairwise "
        "refinements, and bounded cross-family boosts. Uses fixed numeric matrices inspired by "
        "orchestration literature; it is **not** measured acoustic timbre or audio analysis."
    ),
    "symbolic": (
        "Symbolic timbral homogeneity: same register/instrument/pairwise scaffolding as legacy, but "
        "the **technique multiplier** uses **technique-only** concentration (instrument-stripped "
        "``technique_state_id`` tails) so clarinet vs bass clarinet both *ordinario* are not "
        "double-penalized on the technique axis for differing canonical instrument names."
    ),
    "acoustic_heuristic": (
        "Timbral mode aligned with the separate ``H_fusion_acoustic_heuristic`` philosophy: same "
        "**technique-only** concentration rule as ``symbolic`` for the technique multiplier; still "
        "notation-only (no measured audio)."
    ),
}


def assert_active_timbral_model_mode(value: Any) -> TimbralModelMode:
    """
    Return ``legacy`` for ``None``/empty/``\"legacy\"``.

    ``symbolic`` and ``acoustic_heuristic`` are supported for **technique-axis concentration**
    splitting; other strings raise ``ValueError``.
    """
    if value is None or value == "":
        return "legacy"
    if value in ("legacy", "symbolic", "acoustic_heuristic"):
        return cast(TimbralModelMode, value)
    raise ValueError(f"Invalid timbral_model_mode: {value!r}. Use 'legacy', 'symbolic', or 'acoustic_heuristic'.")


def timbral_model_metadata_for_diagnostics(mode: str) -> dict[str, Any]:
    """Fields merged into each ``H_timbral_diagnostics`` row (JSON-friendly)."""
    m = assert_active_timbral_model_mode(mode)
    return {
        "timbral_model_mode": m,
        "model_description": _MODEL_DESCRIPTIONS[m],
        "model_version": TIMBRAL_MODEL_SEMANTICS_VERSION,
        "not_audio_analysis": True,
    }
