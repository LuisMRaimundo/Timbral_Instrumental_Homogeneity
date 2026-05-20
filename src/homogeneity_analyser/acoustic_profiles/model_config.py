"""Versioned, source-linked defaults for timbral acoustic-inspired numeric knobs."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_PROFILES_JSON_PATH = Path(__file__).with_name("default_profiles.json")

_PROFILE_DOC: dict[str, Any] | None = None
_INDEX: dict[str, dict[str, Any]] | None = None


def _ensure_loaded() -> None:
    global _PROFILE_DOC, _INDEX
    if _PROFILE_DOC is not None:
        return
    raw = json.loads(DEFAULT_PROFILES_JSON_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "constants" not in raw:
        raise ValueError("default_profiles.json must contain a constants array.")
    _PROFILE_DOC = raw
    _INDEX = {}
    for entry in raw["constants"]:
        name = entry.get("semantic_name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Each constant needs semantic_name.")
        if name in _INDEX:
            raise ValueError(f"Duplicate semantic_name: {name}")
        _INDEX[name] = entry


def get_timbral_acoustic_profile_document() -> dict[str, Any]:
    """Return the full profile document (metadata + constants list)."""
    _ensure_loaded()
    assert _PROFILE_DOC is not None
    return _PROFILE_DOC


def get_timbral_acoustic_value(semantic_name: str) -> Any:
    """Return the raw JSON value for a constant."""
    _ensure_loaded()
    assert _INDEX is not None
    if semantic_name not in _INDEX:
        raise KeyError(f"Unknown timbral acoustic constant: {semantic_name}")
    return _INDEX[semantic_name]["value"]


def timbral_float(semantic_name: str) -> float:
    return float(get_timbral_acoustic_value(semantic_name))


def timbral_int(semantic_name: str) -> int:
    return int(get_timbral_acoustic_value(semantic_name))


def timbral_numpy_matrix(semantic_name: str) -> np.ndarray:
    return np.asarray(get_timbral_acoustic_value(semantic_name), dtype=float)


def timbral_float_tuple(semantic_name: str, *, length: int | None = None) -> tuple[float, ...]:
    v = get_timbral_acoustic_value(semantic_name)
    if not isinstance(v, list):
        raise TypeError(f"{semantic_name} must be a JSON list.")
    out = tuple(float(x) for x in v)
    if length is not None and len(out) != length:
        raise ValueError(f"{semantic_name} expected length {length}, got {len(out)}")
    return out


def timbral_bounds_list(semantic_name: str) -> list[tuple[float, float]]:
    raw = get_timbral_acoustic_value(semantic_name)
    if not isinstance(raw, list):
        raise TypeError(f"{semantic_name} must be a list of [lo, hi] pairs.")
    return [(float(a), float(b)) for a, b in raw]


def timbral_acoustic_diagnostics_bundle() -> dict[str, Any]:
    """
    Metadata about the **full** active timbral numeric profile (all semantic knobs).

    For per-window ``H_timbral_diagnostics`` tied to an actual computation path, use
    :func:`build_timbral_window_diagnostics_bundle` instead.
    """
    _ensure_loaded()
    assert _INDEX is not None
    assert _PROFILE_DOC is not None
    all_names = sorted(_INDEX.keys())
    provisional: list[str] = []
    source_keys: set[str] = set()
    for name, entry in _INDEX.items():
        sk = entry.get("source_key")
        if isinstance(sk, str) and sk.strip() and sk != "project_specific":
            source_keys.add(sk)
        if sk == "project_specific" or entry.get("evidence_status") in ("provisional", "needs_validation"):
            provisional.append(name)
    return {
        "config_profile_name": str(_PROFILE_DOC.get("profile_name", "")),
        "config_model_version": str(_PROFILE_DOC.get("config_model_version", "")),
        "constants_used": all_names,
        "source_keys_used": sorted(source_keys),
        "provisional_constants_used": sorted(provisional),
    }


def build_timbral_window_diagnostics_bundle(semantic_names: Iterable[str]) -> dict[str, Any]:
    """
    Per-window diagnostics slice: only ``semantic_names`` that exist in the profile index.

    ``source_keys_used`` is the union of non-``project_specific`` keys on those rows.
    ``provisional_constants_used`` is the subset whose ``source_key`` is ``project_specific`` or whose
    ``evidence_status`` is ``provisional`` / ``needs_validation``.
    """
    _ensure_loaded()
    assert _INDEX is not None
    assert _PROFILE_DOC is not None
    names_sorted = sorted({str(n) for n in semantic_names if isinstance(n, str) and n.strip()})
    provisional: list[str] = []
    source_keys: set[str] = set()
    for name in names_sorted:
        entry = _INDEX.get(name)
        if entry is None:
            continue
        sk = entry.get("source_key")
        if isinstance(sk, str) and sk.strip() and sk != "project_specific":
            source_keys.add(sk.strip())
        if sk == "project_specific" or entry.get("evidence_status") in ("provisional", "needs_validation"):
            provisional.append(name)
    return {
        "config_profile_name": str(_PROFILE_DOC.get("profile_name", "")),
        "config_model_version": str(_PROFILE_DOC.get("config_model_version", "")),
        "constants_used": names_sorted,
        "source_keys_used": sorted(source_keys),
        "provisional_constants_used": sorted(provisional),
    }


def all_timbral_acoustic_semantic_names() -> frozenset[str]:
    _ensure_loaded()
    assert _INDEX is not None
    return frozenset(_INDEX.keys())
