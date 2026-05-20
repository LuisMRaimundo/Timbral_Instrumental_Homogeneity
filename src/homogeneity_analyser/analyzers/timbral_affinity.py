"""
Literature-governed **symbolic** timbral affinity for optional H_TI relief.

Score-derived only: canonical instrument, taxonomy family, technique_state, and a data-driven
rule registry. **Not** measured acoustic similarity, spectral fusion, or perceptual listening tests.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.analyzers.technique_state import (
    FAMILY_STRINGS,
    TechniqueState,
    harmonic_dim,
    technique_state_from_dict,
)

PROFILE_ORDER: dict[str, int] = {
    "strict": 0,
    "conservative": 1,
    "moderate": 2,
    "exploratory": 3,
}

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "taxonomy" / "timbral_affinity_registry.json"
_SYMBOLIC_BLEND_JSON = Path(__file__).resolve().parent.parent / "taxonomy" / "symbolic_blend_conditioning.json"


@lru_cache(maxsize=1)
def _load_flute_variant_similarity_rows() -> tuple[dict[str, Any], ...]:
    if not _SYMBOLIC_BLEND_JSON.is_file():
        return ()
    try:
        data = json.loads(_SYMBOLIC_BLEND_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    block = (data.get("flute_variant_pair_similarity") or {}).get("conservative") or []
    if not isinstance(block, list):
        return ()
    return tuple(r for r in block if isinstance(r, dict))


def _flute_variant_similarity(ia: str, ib: str) -> float | None:
    a, b = _norm_inst(ia), _norm_inst(ib)
    if a == b:
        return None
    for row in _load_flute_variant_similarity_rows():
        pair = row.get("pair")
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        u, v = _norm_inst(str(pair[0])), _norm_inst(str(pair[1]))
        if {u, v} == {a, b}:
            try:
                return float(row.get("similarity", 0.0))
            except (TypeError, ValueError):
                return None
    return None


def _evidence_profile_floor_for_release(release_status: str) -> int:
    rs = str(release_status or "source_key_only").strip().lower()
    if rs == "page_verified":
        return PROFILE_ORDER["conservative"]
    if rs == "needs_page_verification":
        return PROFILE_ORDER["exploratory"]
    return PROFILE_ORDER["moderate"]


def _rule_eligible_for_profile(rule: dict[str, Any], profile: str) -> bool:
    """True when both the declared ``profile_minimum`` and bibliography ``release_status`` allow firing."""
    pr = _profile_rank(profile)
    need_pub = _profile_rank(str(rule.get("profile_minimum") or "conservative"))
    need_ev = _evidence_profile_floor_for_release(str(rule.get("release_status") or ""))
    return pr >= max(need_pub, need_ev)


def _pair_has_blocked_unverified_registry_match(ev_a: dict[str, Any], ev_b: dict[str, Any], profile: str) -> bool:
    ia, ib = str(ev_a.get("instrument") or ""), str(ev_b.get("instrument") or "")
    tags_a = affinity_tags_for_event(ev_a)
    tags_b = affinity_tags_for_event(ev_b)
    for rule in _load_pair_rules():
        if _rule_eligible_for_profile(rule, profile):
            continue
        rs = str(rule.get("release_status") or "").strip().lower()
        if rs not in ("source_key_only", "needs_page_verification", "unverified"):
            continue
        if rule.get("instruments") and _instruments_match_rule(rule, ia, ib):
            return True
        if rule.get("requires_tags") and _tags_requirement_met(rule, tags_a, tags_b, ev_a, ev_b):
            return True
    return False


def _string_harmonic_vs_bowed_mismatch(ev_a: dict[str, Any], ev_b: dict[str, Any]) -> bool:
    if str(ev_a.get("family") or "") != FAMILY_STRINGS or str(ev_b.get("family") or "") != FAMILY_STRINGS:
        return False
    if _norm_inst(str(ev_a.get("instrument") or "")) != _norm_inst(str(ev_b.get("instrument") or "")):
        return False
    st_a = _technique_state_from_event(ev_a)
    st_b = _technique_state_from_event(ev_b)
    if st_a is None or st_b is None:
        return False
    ha = harmonic_dim(st_a) != "none"
    hb = harmonic_dim(st_b) != "none"
    return ha != hb


def _same_organological_family(tags_a: dict[str, str], tags_b: dict[str, str]) -> bool:
    oa = str(tags_a.get("organological_family") or "")
    ob = str(tags_b.get("organological_family") or "")
    return bool(oa and ob and oa == ob and oa != "unknown")


@lru_cache(maxsize=1)
def _load_pair_rules() -> tuple[dict[str, Any], ...]:
    if not _REGISTRY_PATH.is_file():
        return ()
    try:
        data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    rules = data.get("pair_rules") or []
    return tuple(r for r in rules if isinstance(r, dict))


def _profile_rank(name: str) -> int:
    return PROFILE_ORDER.get(str(name).strip().lower(), 1)


def _norm_inst(s: str) -> str:
    return str(s or "").strip().lower()


def _pair_key(a: str, b: str) -> tuple[str, str]:
    x, y = _norm_inst(a), _norm_inst(b)
    return (x, y) if x <= y else (y, x)


# Canonical instrument -> organology / material tags (taxonomy-level; not measured spectra).
_BASE_INSTRUMENT_TAGS: dict[str, dict[str, str]] = {
    "flute": {
        "excitation_class": "air_jet",
        "envelope_class": "sustained_air",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "flute_family",
    },
    "piccolo": {
        "excitation_class": "air_jet",
        "envelope_class": "sustained_air",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "flute_family",
    },
    "alto flute": {
        "excitation_class": "air_jet",
        "envelope_class": "sustained_air",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "flute_family",
    },
    "bass flute": {
        "excitation_class": "air_jet",
        "envelope_class": "sustained_air",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "flute_family",
    },
    "oboe": {
        "excitation_class": "double_reed",
        "envelope_class": "sustained_reed",
        "resonator_class": "air_column",
        "material_class": "wood",
        "organological_family": "double_reed_conical",
    },
    "cor anglais": {
        "excitation_class": "double_reed",
        "envelope_class": "sustained_reed",
        "resonator_class": "air_column",
        "material_class": "wood",
        "organological_family": "double_reed_conical",
    },
    "bassoon": {
        "excitation_class": "double_reed",
        "envelope_class": "sustained_reed",
        "resonator_class": "air_column",
        "material_class": "wood",
        "organological_family": "double_reed_bassoon",
    },
    "contrabassoon": {
        "excitation_class": "double_reed",
        "envelope_class": "sustained_reed",
        "resonator_class": "air_column",
        "material_class": "wood",
        "organological_family": "double_reed_bassoon",
    },
    "clarinet": {
        "excitation_class": "single_reed",
        "envelope_class": "sustained_reed",
        "resonator_class": "air_column",
        "material_class": "wood",
        "organological_family": "single_reed_cylindrical",
    },
    "bass clarinet": {
        "excitation_class": "single_reed",
        "envelope_class": "sustained_reed",
        "resonator_class": "air_column",
        "material_class": "wood",
        "organological_family": "single_reed_cylindrical",
    },
    "saxophone": {
        "excitation_class": "single_reed",
        "envelope_class": "sustained_reed",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "single_reed_conical",
    },
    "trumpet": {
        "excitation_class": "lip_reed",
        "envelope_class": "sustained_brass",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "brass_cylindrical",
    },
    "cornet": {
        "excitation_class": "lip_reed",
        "envelope_class": "sustained_brass",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "brass_conical",
    },
    "flugelhorn": {
        "excitation_class": "lip_reed",
        "envelope_class": "sustained_brass",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "brass_conical",
    },
    "horn": {
        "excitation_class": "lip_reed",
        "envelope_class": "sustained_brass",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "brass_horn",
    },
    "trombone": {
        "excitation_class": "lip_reed",
        "envelope_class": "sustained_brass",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "brass_slide",
    },
    "bass trombone": {
        "excitation_class": "lip_reed",
        "envelope_class": "sustained_brass",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "brass_slide",
    },
    "euphonium": {
        "excitation_class": "lip_reed",
        "envelope_class": "sustained_brass",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "brass_conical",
    },
    "tuba": {
        "excitation_class": "lip_reed",
        "envelope_class": "sustained_brass",
        "resonator_class": "air_column",
        "material_class": "metal",
        "organological_family": "brass_conical",
    },
    "violin": {
        "excitation_class": "bowed_string",
        "envelope_class": "sustained_bowed",
        "resonator_class": "string_body",
        "material_class": "string",
        "organological_family": "bowed_strings",
    },
    "viola": {
        "excitation_class": "bowed_string",
        "envelope_class": "sustained_bowed",
        "resonator_class": "string_body",
        "material_class": "string",
        "organological_family": "bowed_strings",
    },
    "cello": {
        "excitation_class": "bowed_string",
        "envelope_class": "sustained_bowed",
        "resonator_class": "string_body",
        "material_class": "string",
        "organological_family": "bowed_strings",
    },
    "double bass": {
        "excitation_class": "bowed_string",
        "envelope_class": "sustained_bowed",
        "resonator_class": "string_body",
        "material_class": "string",
        "organological_family": "bowed_strings",
    },
    "harp": {
        "excitation_class": "plucked_string",
        "envelope_class": "plucked_decay",
        "resonator_class": "string_body",
        "material_class": "string",
        "organological_family": "harp",
    },
    "celesta": {
        "excitation_class": "struck_idiophone",
        "envelope_class": "metallic_resonant_decay",
        "resonator_class": "resonant_plate_bar",
        "material_class": "metal",
        "organological_family": "keyboard_struck_metal",
    },
    "glockenspiel": {
        "excitation_class": "struck_idiophone",
        "envelope_class": "metallic_resonant_decay",
        "resonator_class": "resonant_plate_bar",
        "material_class": "metal",
        "organological_family": "pitched_metal_bars",
    },
    "wood block": {
        "excitation_class": "struck_idiophone",
        "envelope_class": "wooden_struck_decay",
        "resonator_class": "idiophone_body",
        "material_class": "wood",
        "organological_family": "unpitched_wood",
    },
    "snare drum": {
        "excitation_class": "struck_membrane",
        "envelope_class": "membrane_decay",
        "resonator_class": "membrane_body",
        "material_class": "mixed",
        "organological_family": "membrane_drums",
    },
    "bass drum": {
        "excitation_class": "struck_membrane",
        "envelope_class": "membrane_decay",
        "resonator_class": "membrane_body",
        "material_class": "mixed",
        "organological_family": "membrane_drums",
    },
    "cymbal": {
        "excitation_class": "struck_idiophone",
        "envelope_class": "metallic_resonant_decay",
        "resonator_class": "idiophone_body",
        "material_class": "metal",
        "organological_family": "metallic_plates",
    },
    "tam-tam": {
        "excitation_class": "struck_idiophone",
        "envelope_class": "metallic_resonant_decay",
        "resonator_class": "idiophone_body",
        "material_class": "metal",
        "organological_family": "metallic_plates",
    },
}


def _unknown_tags() -> dict[str, str]:
    return {
        "excitation_class": "unknown",
        "envelope_class": "unknown",
        "resonator_class": "unknown",
        "material_class": "unknown",
        "organological_family": "unknown",
    }


def _technique_state_from_event(ev: dict[str, Any]) -> TechniqueState | None:
    raw = ev.get("technique_state")
    if not isinstance(raw, dict):
        return None
    try:
        return technique_state_from_dict(raw)
    except (TypeError, ValueError, KeyError):
        return None


def _apply_technique_tag_overrides(ev: dict[str, Any], tags: dict[str, str]) -> dict[str, str]:
    """Override envelope / excitation from explicit ``technique_state`` only (no XML inference)."""
    out = dict(tags)
    st = _technique_state_from_event(ev)
    if st is None:
        return out
    fam = str(ev.get("family") or "")
    primary = str(st.primary or "").strip().lower()
    if fam == "strings":
        if primary == "pizzicato":
            out["excitation_class"] = "plucked_string"
            out["envelope_class"] = "plucked_decay"
        elif primary in ("arco", "ordinario", "ordinary"):
            out["excitation_class"] = "bowed_string"
            out["envelope_class"] = "sustained_bowed"
        elif "col legno" in primary or primary == "col legno battuto":
            out["excitation_class"] = "struck_woodlike"
            out["envelope_class"] = "dry_struck_decay"
        elif primary == "tremolo":
            out["envelope_class"] = "reiterated_sustain"
        elif primary == "sul ponticello":
            out["envelope_class"] = "bright_bowed_noise_edge"
        elif primary == "sul tasto":
            out["envelope_class"] = "soft_bowed_sustain"
        elif "harmonic" in primary:
            out["envelope_class"] = "harmonic_light_sustain"
    if fam == "brass" and primary == "stopped":
        out["envelope_class"] = "stopped_brass"
    if fam in ("flutes", "clarinets", "oboes", "bassoons") and "flutter" in primary:
        out["envelope_class"] = "noisy_air_reiteration"
    return out


def affinity_tags_for_event(ev: dict[str, Any]) -> dict[str, str]:
    inst = _norm_inst(str(ev.get("instrument") or ""))
    base = dict(_BASE_INSTRUMENT_TAGS.get(inst, _unknown_tags()))
    base["canonical_instrument"] = inst
    base["instrumental_subfamily"] = str(ev.get("family") or "")
    base["macrofamily"] = macrofamily_from_instrumental_subfamily(base["instrumental_subfamily"])
    return _apply_technique_tag_overrides(ev, base)


def _event_gesture_tags(ev: dict[str, Any], tags: dict[str, str]) -> frozenset[str]:
    s: set[str] = set()
    st = _technique_state_from_event(ev)
    fam = str(ev.get("family") or "")
    if fam == "strings" and st is not None:
        p = str(st.primary or "").strip().lower()
        if p == "pizzicato":
            s.add("gesture_plucked_string")
        if "col legno" in p or p == "col legno battuto":
            s.add("gesture_col_legno_battuto")
        if p == "sul ponticello":
            s.add("gesture_sul_ponticello")
    inst = tags.get("canonical_instrument", "")
    if inst == "harp":
        s.add("harp_family")
    if inst == "wood block":
        s.add("woodblock_family")
    if (
        tags.get("macrofamily") == "percussion"
        and tags.get("material_class") == "metal"
        and "glock" not in inst
        and inst in ("cymbal", "tam-tam", "suspended cymbal")
    ):
        s.add("metallic_unpitched_family")
    return frozenset(s)


def _instruments_match_rule(rule: dict[str, Any], a: str, b: str) -> bool:
    insts = rule.get("instruments")
    if not isinstance(insts, list) or len(insts) != 2:
        return False
    u, v = _norm_inst(str(insts[0])), _norm_inst(str(insts[1]))
    return {_norm_inst(a), _norm_inst(b)} == {u, v}


def _tags_requirement_met(
    rule: dict[str, Any], tags_a: dict[str, str], tags_b: dict[str, str], ev_a: dict, ev_b: dict
) -> bool:
    req = rule.get("requires_tags")
    if not isinstance(req, list) or not req:
        return False
    ga = _event_gesture_tags(ev_a, tags_a)
    gb = _event_gesture_tags(ev_b, tags_b)
    union = ga | gb
    return all(t in union for t in req)


def pairwise_similarity(
    ev_a: dict[str, Any],
    ev_b: dict[str, Any],
    *,
    profile: str,
) -> tuple[float, str, list[str]]:
    """
    Return (S_ij, rule_id_or_bucket, source_keys) for ordered pair (a,b); symmetric caller may duplicate.
    """
    ia, ib = str(ev_a.get("instrument") or ""), str(ev_b.get("instrument") or "")
    if _norm_inst(ia) == _norm_inst(ib) and ia.strip():
        if _string_harmonic_vs_bowed_mismatch(ev_a, ev_b):
            return 0.38, "tier1_string_harmonic_vs_bowed_symbolic_separation", []
        return 1.0, "tier1_same_canonical_instrument", []

    pr = str(profile).strip().lower()
    if pr == "strict":
        return 0.0, "strict_no_cross_instrument", []

    tags_a = affinity_tags_for_event(ev_a)
    tags_b = affinity_tags_for_event(ev_b)
    if tags_a.get("excitation_class") == "unknown" or tags_b.get("excitation_class") == "unknown":
        return 0.1, "unknown_instrument_low", []

    # Explicit registry pair_rules (bibliography governance: unverified rows require moderate+ / exploratory).
    for rule in _load_pair_rules():
        if not _rule_eligible_for_profile(rule, pr):
            continue
        rid = str(rule.get("rule_id") or "registry_rule")
        if rule.get("instruments"):
            if _instruments_match_rule(rule, ia, ib):
                return float(rule.get("similarity", 0.0)), rid, list(rule.get("source_keys") or [])
        elif rule.get("requires_tags") and _tags_requirement_met(rule, tags_a, tags_b, ev_a, ev_b):
            return float(rule.get("similarity", 0.0)), rid, list(rule.get("source_keys") or [])

    fam_a = tags_a.get("instrumental_subfamily") or str(ev_a.get("family") or "")
    fam_b = tags_b.get("instrumental_subfamily") or str(ev_b.get("family") or "")
    if fam_a and fam_a == fam_b and _profile_rank(pr) >= 1 and _same_organological_family(tags_a, tags_b):
        org = str(tags_a.get("organological_family") or "")
        if org == "flute_family" and _norm_inst(ia) != _norm_inst(ib):
            fv = _flute_variant_similarity(ia, ib)
            if fv is not None:
                return float(fv), "tier2_flute_family_variant_symbolic_table", ["symbolic_blend_conditioning.json"]
        return 0.88, "tier2_same_instrumental_subfamily_default", ["taxonomy_organology_internal"]

    exc_a = tags_a.get("excitation_class") or ""
    exc_b = tags_b.get("excitation_class") or ""
    if exc_a == exc_b and exc_a not in ("unknown", "") and fam_a != fam_b and _profile_rank(pr) >= 2:
        if exc_a == "lip_reed":
            return (
                0.52,
                "tier3_same_excitation_lip_reed_default",
                ["campbell_gilbert_myers_2021_science_of_brass_instruments"],
            )
        if exc_a == "double_reed":
            return (
                0.42,
                "tier3_same_excitation_double_reed_cross_subfamily_symbolic",
                ["fletcher_rossing_1998_physics_of_musical_instruments"],
            )
        if exc_a == "single_reed":
            if _profile_rank(pr) >= 2:
                return (
                    0.55,
                    "tier3_same_excitation_single_reed_default",
                    ["benade_1976_fundamentals_musical_acoustics"],
                )
            return 0.0, "tier3_single_reed_requires_moderate_profile", []
        if exc_a == "air_jet":
            return (
                0.62,
                "tier3_same_excitation_air_jet_default",
                ["fletcher_rossing_1998_physics_of_musical_instruments"],
            )

    env_a = tags_a.get("envelope_class") or ""
    env_b = tags_b.get("envelope_class") or ""
    if env_a and env_a == env_b and env_a.startswith("plucked") and _profile_rank(pr) >= 2:
        return 0.52, "tier4_same_plucked_envelope_default", ["rossing_2010_science_of_string_instruments"]

    mf_a = tags_a.get("macrofamily") or macrofamily_from_instrumental_subfamily(fam_a)
    mf_b = tags_b.get("macrofamily") or macrofamily_from_instrumental_subfamily(fam_b)
    if mf_a != mf_b:
        v = 0.08 if _profile_rank(pr) <= 1 else 0.12
        return v, "tier_default_cross_macrofamily", []

    v = 0.12 if _profile_rank(pr) <= 1 else 0.18
    return v, "tier_default_same_macro_cross_subfamily", []


def _pair_evidence_status_label(rule_id: str, source_keys: list[str]) -> str:
    sks = ";".join(source_keys)
    if "taxonomy_organology_internal" in sks:
        return "taxonomy_internal"
    if "symbolic_blend_conditioning.json" in sks:
        return "configured_symbolic_table"
    if source_keys:
        return "literature_key_symbolic_when_profile_allows"
    return "implicit_default"


def _registry_provenance_for_pair(ev_a: dict[str, Any], ev_b: dict[str, Any], profile: str) -> dict[str, Any]:
    ia, ib = str(ev_a.get("instrument") or ""), str(ev_b.get("instrument") or "")
    tags_a = affinity_tags_for_event(ev_a)
    tags_b = affinity_tags_for_event(ev_b)
    for rule in _load_pair_rules():
        rid = str(rule.get("rule_id") or "")
        match = False
        inst_ok = bool(rule.get("instruments") and _instruments_match_rule(rule, ia, ib))
        tag_ok = bool(
            rule.get("requires_tags") and _tags_requirement_met(rule, tags_a, tags_b, ev_a, ev_b)
        )
        if inst_ok or tag_ok:
            match = True
        if not match:
            continue
        pm = str(rule.get("profile_minimum") or "conservative")
        rs = str(rule.get("release_status") or "source_key_only")
        eligible = _rule_eligible_for_profile(rule, profile)
        return {
            "registry_rule_id": rid,
            "evidence_status": rs,
            "profile_minimum": pm,
            "why_fired": rid if eligible else "",
            "why_blocked": (
                ""
                if eligible
                else "release_status_requires_moderate_or_exploratory_for_source_key_only_or_unverified"
            ),
        }
    return {
        "registry_rule_id": "",
        "evidence_status": "n/a",
        "profile_minimum": "",
        "why_fired": "",
        "why_blocked": "",
    }


def compute_timbral_affinity_uniformity(
    contrib: list[tuple[dict[str, Any], float]],
    *,
    profile: str,
    collect_pairs: bool = False,
) -> dict[str, Any]:
    """
    Generalised Herfindahl: sum_i sum_j p_i p_j S_ij with p_i overlap share among **events**.
    """
    if not contrib:
        return {
            "timbral_affinity_uniformity": float("nan"),
            "timbral_affinity_rule_summary": "",
            "timbral_affinity_literature_sources": "",
            "timbral_affinity_evidence_status": "insufficient",
            "literature_affinity_unverified_rule_blocked": False,
            "_pair_rows": [],
        }
    tot = float(sum(max(0.0, float(ol)) for _, ol in contrib))
    if tot <= 1e-15:
        return {
            "timbral_affinity_uniformity": float("nan"),
            "timbral_affinity_rule_summary": "",
            "timbral_affinity_literature_sources": "",
            "timbral_affinity_evidence_status": "insufficient",
            "literature_affinity_unverified_rule_blocked": False,
            "_pair_rows": [],
        }
    p = [max(0.0, float(ol)) / tot for _, ol in contrib]
    events = [e for e, _ in contrib]
    n = len(events)
    acc = 0.0
    rules_hit: list[str] = []
    sources: set[str] = set()
    pair_rows: list[dict[str, Any]] = []
    prof_l = str(profile)
    blocked_any = any(
        _pair_has_blocked_unverified_registry_match(events[i], events[j], prof_l)
        for i in range(n)
        for j in range(i + 1, n)
    )
    for i in range(n):
        for j in range(n):
            wij = p[i] * p[j]
            if i == j:
                s_ij = 1.0
                rid = "diagonal_identity"
                sk: list[str] = []
            else:
                s_ij, rid, sk = pairwise_similarity(events[i], events[j], profile=profile)
                for x in sk:
                    sources.add(str(x))
            acc += wij * float(s_ij)
            if collect_pairs and i < j:
                tuk_i = str(events[i].get("technique_uniformity_key") or "")
                tuk_j = str(events[j].get("technique_uniformity_key") or "")
                prov = _registry_provenance_for_pair(events[i], events[j], prof_l)
                wb = ""
                if _pair_has_blocked_unverified_registry_match(events[i], events[j], prof_l):
                    wb = "matching_registry_row_exists_but_evidence_profile_blocks_firing"
                pair_rows.append(
                    {
                        "event_i_instrument": str(events[i].get("instrument") or ""),
                        "event_j_instrument": str(events[j].get("instrument") or ""),
                        "event_i_technique_key": tuk_i,
                        "event_j_technique_key": tuk_j,
                        "similarity": float(s_ij),
                        "rule_id": rid,
                        "rule_tier": _rule_tier_from_id(rid),
                        "profile": profile,
                        "confidence": "moderate" if "default" not in rid else "weak",
                        "source_keys": ";".join(sk),
                        "explanation": "pairwise_symbolic_timbral_affinity",
                        "evidence_status": _pair_evidence_status_label(rid, sk),
                        "registry_rule_id": prov.get("registry_rule_id"),
                        "registry_evidence_status": prov.get("evidence_status"),
                        "profile_minimum": prov.get("profile_minimum"),
                        "why_fired": prov.get("why_fired") or rid,
                        "why_blocked": wb or str(prov.get("why_blocked") or ""),
                    }
                )
            if i < j and rid not in ("diagonal_identity",):
                rules_hit.append(rid)

    ev_status = "moderate"
    if profile == "exploratory":
        ev_status = "exploratory_mixed"
    elif any("exploratory" in r or "unknown" in r for r in rules_hit):
        ev_status = "weak"
    summary = ";".join(sorted(set(rules_hit))[:12]) if rules_hit else "no_cross_pairs"
    lit = ";".join(sorted(sources)) if sources else ""
    return {
        "timbral_affinity_uniformity": float(np.clip(acc, 0.0, 1.0)),
        "timbral_affinity_rule_summary": summary[:500],
        "timbral_affinity_literature_sources": lit[:800],
        "timbral_affinity_evidence_status": ev_status,
        "literature_affinity_unverified_rule_blocked": bool(blocked_any),
        "_pair_rows": pair_rows,
    }


def _rule_tier_from_id(rid: str) -> int:
    if "tier1" in rid or "same_canonical" in rid:
        return 1
    if rid.startswith("tier2") or "subfamily" in rid:
        return 2
    if "tier3" in rid or "cross" in rid:
        return 3
    if "tier4" in rid or "gesture" in rid:
        return 4
    if "tier5" in rid or "exploratory" in rid:
        return 5
    return 2


def _affinity_dynamic_bundle(feats: dict[str, Any], h_lit: float, *, enabled: bool) -> dict[str, Any]:
    """Interpretive diagnostics only; does not alter H_TI_core."""
    nan = float("nan")
    if not enabled:
        return {
            "timbral_affinity_dynamic_factor": nan,
            "timbral_affinity_dynamic_status": "disabled",
            "affinity_dynamic_interpretation_label": "affinity_dynamic_layer_disabled",
            "H_TI_affinity_dynamic_conditioned": nan,
        }
    cov = str(feats.get("dynamic_coverage_status") or "")
    if cov == "unavailable":
        return {
            "timbral_affinity_dynamic_factor": nan,
            "timbral_affinity_dynamic_status": "insufficient",
            "affinity_dynamic_interpretation_label": "insufficient_dynamic_evidence_for_affinity_qualifier",
            "H_TI_affinity_dynamic_conditioned": float(h_lit) if math.isfinite(float(h_lit)) else nan,
        }
    ds_raw = feats.get("dynamic_softness")
    ds = float(ds_raw) if isinstance(ds_raw, int | float) and math.isfinite(float(ds_raw)) else 0.5
    di_raw = feats.get("dynamic_intensity_ordinal")
    di = float(di_raw) if isinstance(di_raw, int | float) and math.isfinite(float(di_raw)) else 0.5
    lbl = str(feats.get("dynamic_interpretation_label") or "")
    factor = 0.62 + 0.38 * float(np.clip(ds, 0.0, 1.0))
    if "cross_family_masked" in lbl or "brass_projection_divergence" in lbl:
        factor *= max(0.55, 1.0 - 0.35 * float(np.clip(di, 0.0, 1.0)))
    elif "transparent_blend" in lbl and di < 0.55:
        factor = min(1.0, factor * 1.05)
    factor = float(np.clip(factor, 0.35, 1.0))
    h_lc = float(h_lit) * factor if math.isfinite(float(h_lit)) else nan
    aff_lbl = "affinity_dynamic_soft_context" if ds > 0.55 and di < 0.45 else "affinity_dynamic_neutral"
    if di > 0.72 and "cross_family" in lbl:
        aff_lbl = "affinity_dynamic_high_intensity_cross_family_guard"
    return {
        "timbral_affinity_dynamic_factor": factor,
        "timbral_affinity_dynamic_status": "active",
        "affinity_dynamic_interpretation_label": aff_lbl,
        "H_TI_affinity_dynamic_conditioned": h_lc,
    }


def compute_timbral_affinity_bundle_for_window(
    contrib: list[tuple[dict[str, Any], float]],
    feats: dict[str, Any],
    *,
    profile: str,
    relief_factor: float,
    instrument_uniformity: float,
    compute_h_ti: Callable[..., tuple[float, dict[str, Any], dict[str, float]]],
    feats_for_h_ti: dict[str, Any],
    w_instr: float,
    w_fam: float,
    w_tech: float,
    w_reg: float,
    collect_pairs: bool,
) -> dict[str, Any]:
    r = float(np.clip(float(relief_factor), 0.0, 1.0))
    prof = str(profile or "conservative").strip().lower()
    if prof not in PROFILE_ORDER:
        prof = "conservative"

    aff_u = compute_timbral_affinity_uniformity(contrib, profile=prof, collect_pairs=collect_pairs)
    tau = float(aff_u["timbral_affinity_uniformity"])
    iu = float(instrument_uniformity)
    if not math.isfinite(tau):
        iaeff = float("nan")
        h_lit = float("nan")
    else:
        iaeff = (1.0 - r) * iu + r * tau
        h_lit, _, _ = compute_h_ti(
            feats_for_h_ti,
            w_instr=w_instr,
            w_fam=w_fam,
            w_tech=w_tech,
            w_reg=w_reg,
            instrument_uniformity_component=float(iaeff),
        )

    out = {
        **aff_u,
        "instrument_affinity_effective_uniformity": float(iaeff) if math.isfinite(iaeff) else float("nan"),
        "H_TI_affinity_literature_relieved": float(h_lit) if math.isfinite(float(h_lit)) else float("nan"),
        "timbral_affinity_profile": prof,
        "timbral_affinity_relief_factor": r,
    }
    return out


def finalize_timbral_affinity_dynamic(
    aff: dict[str, Any],
    feats_post_attach: dict[str, Any],
    *,
    dynamic_affinity_enabled: bool,
) -> dict[str, Any]:
    """Populate dynamic-qualifier fields after ``attach_dynamic_conditioning_for_window``."""
    h_raw = aff.get("H_TI_affinity_literature_relieved")
    h_lit = float(h_raw) if isinstance(h_raw, int | float) and math.isfinite(float(h_raw)) else float("nan")
    dyn = _affinity_dynamic_bundle(feats_post_attach, h_lit, enabled=bool(dynamic_affinity_enabled))
    out = dict(aff)
    out.update(dyn)
    return out
