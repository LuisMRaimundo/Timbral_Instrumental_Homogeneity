"""
Acoustic **feature vectors** for ``H_fusion_acoustic_heuristic``.

Each canonical instrument (+ optional ``technique_state_id``) maps to a small vector of
literature- or project-tagged scalars. Missing instruments fall back to ``__default__``;
unknown scalar components are ``null`` and contribute to confidence penalties elsewhere.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

FUSION_FEATURE_VECTORS_JSON = Path(__file__).with_name("fusion_acoustic_feature_vectors.json")

FUSION_FEATURE_FIELDS: tuple[str, ...] = (
    "spectral_slope",
    "spectral_centroid_class",
    "attack_time_class",
    "harmonicity",
    "noise_ratio",
    "directionality_variance",
    "dynamic_spectral_sensitivity",
)


class AcousticFeatureVector(TypedDict, total=False):
    """Per-instrument (+ technique) acoustic proxy features in coarse normalized space."""

    spectral_slope: float | None
    spectral_centroid_class: float | None
    attack_time_class: float | None
    harmonicity: float | None
    noise_ratio: float | None
    directionality_variance: float | None
    dynamic_spectral_sensitivity: float | None


_DOC: dict[str, Any] | None = None
_EXACT: dict[tuple[str, str], dict[str, Any]] = {}
_INST_DEFAULT: dict[str, dict[str, Any]] = {}
_FALLBACK: dict[str, Any] | None = None


def _blank_vector() -> dict[str, float | None]:
    return {k: None for k in FUSION_FEATURE_FIELDS}


def _ensure_loaded() -> None:
    global _DOC, _EXACT, _INST_DEFAULT, _FALLBACK
    if _DOC is not None:
        return
    raw = json.loads(FUSION_FEATURE_VECTORS_JSON.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "entries" not in raw:
        raise ValueError("fusion_acoustic_feature_vectors.json must contain entries.")
    _DOC = raw
    _EXACT = {}
    _INST_DEFAULT = {}
    _FALLBACK = None
    for row in raw["entries"]:
        inst = str(row.get("instrument") or "").strip()
        tech_raw = row.get("technique_state_id")
        tech = "" if tech_raw is None else str(tech_raw).strip()
        payload = {
            "vector": dict(row.get("vector") or {}),
            "field_sources": dict(row.get("field_sources") or {}),
        }
        if inst == "__default__":
            _FALLBACK = payload
            continue
        if tech:
            _EXACT[(inst, tech)] = payload
        else:
            _INST_DEFAULT[inst] = payload
    if _FALLBACK is None:
        raise ValueError("fusion_acoustic_feature_vectors.json requires a __default__ instrument row.")


def get_fusion_feature_document() -> dict[str, Any]:
    """Return the full fusion feature JSON document (metadata + entries)."""
    _ensure_loaded()
    assert _DOC is not None
    return _DOC


def resolve_acoustic_feature_row(
    instrument: str,
    technique_state_id: str | None,
) -> dict[str, Any]:
    """
    Resolve feature vector + per-field ``source_key`` strings for one instrument/technique.

    Returns a dict with:
      - ``vector``: :class:`AcousticFeatureVector`-shaped mapping (floats or ``None``)
      - ``field_sources``: field name -> source_key or ``\"unknown\"``
      - ``match_rule``: which lookup tier matched
      - ``missing_features``: fields that are null after merge
    """
    _ensure_loaded()
    assert _FALLBACK is not None
    inst = str(instrument or "").strip() or "__default__"
    tech = (technique_state_id or "").strip()

    chosen: dict[str, Any] | None = None
    match_rule = "default_only"
    if tech and (inst, tech) in _EXACT:
        chosen = _EXACT[(inst, tech)]
        match_rule = "exact_instrument_technique"
    elif inst in _INST_DEFAULT:
        chosen = _INST_DEFAULT[inst]
        match_rule = "instrument_default_technique"
    else:
        chosen = _FALLBACK
        match_rule = "global_default"

    vec_raw = dict(chosen.get("vector") or {})
    src_raw = dict(chosen.get("field_sources") or {})
    out_vec: dict[str, float | None] = _blank_vector()
    out_src: dict[str, str] = {}
    for k in FUSION_FEATURE_FIELDS:
        v = vec_raw.get(k)
        if v is None:
            out_vec[k] = None
            out_src[k] = "unknown"
            continue
        try:
            out_vec[k] = float(v)
        except (TypeError, ValueError):
            out_vec[k] = None
            out_src[k] = "unknown"
            continue
        sk = src_raw.get(k)
        out_src[k] = str(sk).strip() if isinstance(sk, str) and sk.strip() else "project_specific"

    missing = [k for k, v in out_vec.items() if v is None]
    return {
        "vector": out_vec,
        "field_sources": out_src,
        "match_rule": match_rule,
        "missing_features": missing,
        "instrument_query": inst,
        "technique_state_id_query": tech,
    }
