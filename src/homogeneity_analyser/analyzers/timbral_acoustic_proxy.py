"""
Score-derived **timbral-acoustic affinity proxy** (H_TA_acoustic_proxy).

Event-level pairwise kernel over overlap-mass shares: A(t) = sum_ij p_i p_j K(e_i, e_j).
**Not** measured acoustic fusion, FFT, SPL, or perceptually validated blend.

Orthogonal to **H_TI_core** (Herfindahl concentration on canonical instruments).
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.hti_dynamics import dynamic_level_ordinal_01
from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.analyzers.percussion_ontology import PitchStatus, get_percussion_meta
from homogeneity_analyser.analyzers.percussion_pairwise_timbral import is_percussion_family
from homogeneity_analyser.analyzers.symbolic_blend_layers import (
    chromatic_interval_class_d12,
    interval_class_key_for_d12,
)
from homogeneity_analyser.analyzers.technique_state import TechniqueState, technique_state_from_dict
from homogeneity_analyser.analyzers.timbral_affinity import affinity_tags_for_event

_PROFILE_ORDER: dict[str, int] = {
    "strict": 0,
    "conservative": 1,
    "moderate": 2,
    "exploratory": 3,
}

_TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "taxonomy" / "acoustic_timbral_taxonomy.json"
_KERNEL_EPS = 1e-9


@lru_cache(maxsize=1)
def load_acoustic_timbral_taxonomy() -> dict[str, Any]:
    if not _TAXONOMY_PATH.is_file():
        return {}
    try:
        return json.loads(_TAXONOMY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _norm_inst(s: str) -> str:
    return str(s or "").strip().lower()


def _pair_key(a: str, b: str) -> tuple[str, str]:
    x, y = _norm_inst(a), _norm_inst(b)
    return (x, y) if x <= y else (y, x)


def _profile_rank(name: str) -> int:
    return _PROFILE_ORDER.get(str(name).strip().lower(), 1)


def _technique_state_from_event(ev: dict[str, Any]) -> TechniqueState | None:
    raw = ev.get("technique_state")
    if not isinstance(raw, dict):
        return None
    try:
        return technique_state_from_dict(raw)
    except (TypeError, ValueError, KeyError):
        return None


def _effective_source_mechanism(ev: dict[str, Any], tags: dict[str, str], tax: dict[str, Any]) -> str:
    inst = _norm_inst(str(ev.get("instrument") or ""))
    inst_tbl = tax.get("instruments") or {}
    row = inst_tbl.get(inst) if isinstance(inst_tbl, dict) else None
    if isinstance(row, dict) and row.get("source_mechanism"):
        sm = str(row["source_mechanism"])
    else:
        fam = str(ev.get("family") or "")
        fb = tax.get("family_fallback_source_mechanism") or {}
        sm = str(fb.get(fam, "unknown")) if isinstance(fb, dict) else "unknown"
    st = _technique_state_from_event(ev)
    fam = str(ev.get("family") or "")
    if st is not None and fam == "strings":
        p = str(st.primary or "").strip().lower()
        if p == "pizzicato":
            return "plucked_string"
        if p in ("arco", "ordinario", "ordinary"):
            return "bowed_string"
    return sm


def acoustic_tags_for_event(ev: dict[str, Any], tax: dict[str, Any] | None = None) -> dict[str, str]:
    """Merge taxonomy row, family fallback, and technique-aware source mechanism."""
    cfg = tax if tax is not None else load_acoustic_timbral_taxonomy()
    inst = _norm_inst(str(ev.get("instrument") or ""))
    inst_tbl = cfg.get("instruments") or {}
    row = dict(inst_tbl.get(inst, {})) if isinstance(inst_tbl, dict) else {}
    fam = str(ev.get("family") or row.get("instrumental_subfamily") or "unknown")
    lit = affinity_tags_for_event(ev)
    if row.get("source_mechanism"):
        tax_conf = "explicit_instrument_row"
    elif fam in (cfg.get("family_fallback_source_mechanism") or {}):
        tax_conf = "family_fallback_low_confidence"
    else:
        tax_conf = "unknown_instrument_low_confidence"
    tags: dict[str, str] = {
        "canonical_instrument": inst,
        "instrumental_subfamily": fam,
        "macrofamily": str(row.get("macrofamily") or macrofamily_from_instrumental_subfamily(fam)),
        "source_mechanism": _effective_source_mechanism(ev, {}, cfg),
        "exciter_class": str(row.get("exciter_class") or lit.get("excitation_class") or "unknown"),
        "resonator_class": str(row.get("resonator_class") or lit.get("resonator_class") or "unknown"),
        "register_family": str(row.get("register_family") or "unknown"),
        "bore_profile": str(row.get("bore_profile") or ""),
        "attack_class": str(row.get("attack_class") or lit.get("envelope_class") or "unknown"),
        "sustain_class": str(row.get("sustain_class") or "unknown"),
        "taxonomy_confidence": tax_conf,
    }
    return tags


def _source_mechanism_similarity(sm_a: str, sm_b: str, tax: dict[str, Any], profile: str) -> float:
    if sm_a == sm_b and sm_a not in ("", "unknown"):
        return 1.0
    if sm_a == "unknown" or sm_b == "unknown":
        cap = float(tax.get("unknown_source_mechanism_cap", 0.18))
        return float(np.clip(cap, 0.0, 1.0))
    tbl = tax.get("source_mechanism_similarity") or {}
    row = tbl.get(sm_a) if isinstance(tbl, dict) else None
    base = 0.1
    if isinstance(row, dict):
        raw = row.get(sm_b, row.get("unknown", 0.1))
        base = float(raw) if raw is not None else 0.1
    fb_pen = float(tax.get("fallback_source_mechanism_penalty", 0.85))
    scale = float((tax.get("profile_scales") or {}).get(profile, 1.0))
    if _profile_rank(profile) <= _PROFILE_ORDER["strict"]:
        return float(np.clip(base * 0.9 * fb_pen, 0.0, 1.0))
    return float(np.clip(min(1.0, base * scale * fb_pen), 0.0, 1.0))


def _instrument_family_similarity(tags_a: dict[str, str], tags_b: dict[str, str], tax: dict[str, Any]) -> float:
    if tags_a.get("canonical_instrument") == tags_b.get("canonical_instrument") and tags_a.get("canonical_instrument"):
        return 1.0
    if tags_a.get("instrumental_subfamily") == tags_b.get("instrumental_subfamily") and tags_a.get("instrumental_subfamily"):
        bonus = float(tax.get("subfamily_same_mechanism_bonus", 0.12))
        sm_a = tags_a.get("source_mechanism") or ""
        sm_b = tags_b.get("source_mechanism") or ""
        if sm_a == sm_b and sm_a not in ("", "unknown"):
            return float(np.clip(0.88 + bonus, 0.0, 1.0))
        return 0.72
    if tags_a.get("macrofamily") == tags_b.get("macrofamily") and tags_a.get("macrofamily"):
        sm_a = tags_a.get("source_mechanism") or ""
        sm_b = tags_b.get("source_mechanism") or ""
        if sm_a == sm_b and sm_a not in ("", "unknown"):
            return 0.38
        return 0.22
    return 0.12


def _canonical_pair_override(ia: str, ib: str, profile: str, tax: dict[str, Any]) -> float | None:
    pr = _profile_rank(profile)
    for row in tax.get("canonical_pair_overrides") or []:
        if not isinstance(row, dict):
            continue
        pair = row.get("pair")
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        u, v = _norm_inst(str(pair[0])), _norm_inst(str(pair[1]))
        if {u, v} != {_norm_inst(ia), _norm_inst(ib)}:
            continue
        allowed = row.get("profiles")
        if isinstance(allowed, list) and allowed:
            if profile not in [str(x).strip().lower() for x in allowed]:
                continue
        need = _PROFILE_ORDER.get("conservative", 1)
        if pr < need and profile == "strict":
            continue
        try:
            return float(row.get("similarity", 0.0))
        except (TypeError, ValueError):
            return None
    return None


def _representative_midi(ev: dict[str, Any]) -> float | None:
    pitches = ev.get("pitches") or []
    vals: list[float] = []
    for p in pitches:
        try:
            vals.append(float(p))
        except (TypeError, ValueError):
            continue
    if not vals:
        return None
    return float(np.median(np.asarray(vals, dtype=float)))


def _instrument_register_zone(midi: float, inst: str, fam: str) -> str:
    """Coarse instrument-relative register zone (symbolic heuristic)."""
    if fam == "strings":
        if inst == "violin":
            if midi < 55:
                return "low"
            if midi < 72:
                return "middle"
            if midi < 84:
                return "high"
            return "extreme"
        if inst == "viola":
            if midi < 48:
                return "low"
            if midi < 65:
                return "middle"
            return "high"
        if inst == "cello":
            if midi < 40:
                return "low"
            if midi < 60:
                return "middle"
            return "high"
        if inst == "double bass":
            if midi < 40:
                return "low"
            return "middle"
    if midi < 50:
        return "low"
    if midi < 65:
        return "middle"
    if midi < 76:
        return "high"
    return "extreme"


def register_tessitura_similarity(ev_a: dict[str, Any], ev_b: dict[str, Any], tax: dict[str, Any]) -> float | None:
    """
    Symbolic register/tessitura proximity — **not** ``register_compactness`` and **not** measured blend.

    Uses semitone-distance attenuation plus coarse instrument-relative zones. Does **not** treat
    chromatic semitone clusters as inherently more homogeneous than wider spans.
    """
    fam_a = str(ev_a.get("family") or "")
    fam_b = str(ev_b.get("family") or "")
    inst_a = _norm_inst(str(ev_a.get("instrument") or ""))
    inst_b = _norm_inst(str(ev_b.get("instrument") or ""))
    if is_percussion_family(fam_a) or is_percussion_family(fam_b):
        pa = get_percussion_meta(inst_a).pitch_status
        pb = get_percussion_meta(inst_b).pitch_status
        if pa == PitchStatus.UNPITCHED or pb == PitchStatus.UNPITCHED:
            return None
    ma, mb = _representative_midi(ev_a), _representative_midi(ev_b)
    if ma is None or mb is None:
        return None
    cfg = tax.get("register_tessitura") or {}
    d = abs(float(ma) - float(mb))
    scale = float(cfg.get("distance_scale_semitones", 14.0))
    if not math.isfinite(scale) or scale <= 1e-6:
        scale = 14.0
    sim = 1.0 / (1.0 + d / scale)
    za = _instrument_register_zone(ma, inst_a, fam_a)
    zb = _instrument_register_zone(mb, inst_b, fam_b)
    if za == "extreme" or zb == "extreme":
        sim *= float(cfg.get("extreme_register_penalty", 0.75))
    if za == zb and za not in ("", "unknown"):
        sim = min(1.0, sim * float(cfg.get("same_zone_bonus", 1.05)))
    return float(np.clip(sim, 0.0, 1.0))


def interval_class_symbolic_factor(ev_a: dict[str, Any], ev_b: dict[str, Any], tax: dict[str, Any]) -> float | None:
    ma, mb = _representative_midi(ev_a), _representative_midi(ev_b)
    if ma is None or mb is None:
        return None
    d12 = chromatic_interval_class_d12(ma, mb)
    icfg = tax.get("interval_class_symbolic") or {}
    key = interval_class_key_for_d12(d12)
    w = icfg.get(key)
    if not isinstance(w, int | float):
        return None
    return float(np.clip(float(w), 0.0, 1.0))


def _technique_key(ev: dict[str, Any]) -> str | None:
    tuk = str(ev.get("technique_uniformity_key") or "").strip()
    if tuk:
        return tuk
    st = _technique_state_from_event(ev)
    if st is None:
        return None
    return f"{st.instrument}|{st.family}|{st.primary}|{st.mute}|{st.contact_point}"


def technique_compatibility_similarity(ev_a: dict[str, Any], ev_b: dict[str, Any], tax: dict[str, Any]) -> float | None:
    cfg = tax.get("technique_compatibility") or {}
    ka, kb = _technique_key(ev_a), _technique_key(ev_b)
    if not ka or not kb:
        return None
    if ka == kb:
        return float(cfg.get("identical_key", 1.0))
    st_a = _technique_state_from_event(ev_a)
    st_b = _technique_state_from_event(ev_b)
    fam = str(ev_a.get("family") or "")
    fam_b = str(ev_b.get("family") or "")
    if fam not in ("strings", "brass") and fam_b in ("strings", "brass"):
        fam = fam_b
    if fam == "strings" and st_a and st_b:
        pa = str(st_a.primary or "").lower()
        pb = str(st_b.primary or "").lower()
        arco = {"arco", "ordinario", "ordinary"}
        if pa in arco and pb in arco:
            return float(cfg.get("both_ordinary_arco", 0.95))
        if (pa == "pizzicato") != (pb == "pizzicato"):
            return float(cfg.get("pizzicato_vs_arco", 0.38))
        specials = ("sul ponticello", "sul tasto", "col legno", "harmonic", "tremolo")
        if any(s in pa for s in specials) or any(s in pb for s in specials):
            if pa != pb:
                return float(cfg.get("special_effect_mismatch", 0.32))
    if fam == "brass" and st_a and st_b:
        ma, mb = str(st_a.mute or "none").lower(), str(st_b.mute or "none").lower()
        pa, pb = str(st_a.primary or "").lower(), str(st_b.primary or "").lower()
        if pa in ("open", "ordinario", "ordinary") and pb in ("open", "ordinario", "ordinary"):
            if ma == "none" and mb == "none":
                return 0.9
        if pa == "stopped" or pb == "stopped":
            if pa != pb or ma != mb:
                return float(cfg.get("stopped_horn_vs_open", 0.42))
        if ma != "none" and mb != "none":
            if ma == mb:
                return float(cfg.get("same_mute_family", 0.78))
            return float(cfg.get("muted_vs_open_brass", 0.45))
        if (ma == "none") != (mb == "none"):
            return float(cfg.get("muted_vs_open_brass", 0.45))
    return float(cfg.get("special_effect_mismatch", 0.32))


def dynamic_compatibility_similarity(ev_a: dict[str, Any], ev_b: dict[str, Any], tax: dict[str, Any]) -> float | None:
    da = str(ev_a.get("dynamic_mark") or "").strip().lower()
    db = str(ev_b.get("dynamic_mark") or "").strip().lower()
    if not da or not db:
        return None
    oa = dynamic_level_ordinal_01(da)
    ob = dynamic_level_ordinal_01(db)
    if oa is None or ob is None:
        return None
    cfg = tax.get("dynamic_compatibility") or {}
    diff = abs(float(oa) - float(ob))
    base = float(cfg.get("coherence_blend", 0.65)) + (1.0 - diff) * (1.0 - float(cfg.get("coherence_blend", 0.65)))
    if diff > 0.35:
        base *= float(cfg.get("divergence_penalty", 0.55))
    hi = max(float(oa), float(ob))
    if hi > 0.72:
        base *= 1.0 - float(cfg.get("high_dynamic_projection_penalty", 0.12))
    return float(np.clip(base, 0.0, 1.0))


def attack_envelope_similarity(tags_a: dict[str, str], tags_b: dict[str, str]) -> float | None:
    aa = tags_a.get("attack_class") or ""
    ab = tags_b.get("attack_class") or ""
    if not aa or not ab or aa == "unknown" or ab == "unknown":
        return None
    if aa == ab:
        return 1.0
    sustain_pairs = (
        ("bowed_sustain", "reed_sustain"),
        ("air_sustain", "reed_sustain"),
        ("lip_sustain", "reed_sustain"),
    )
    if (aa, ab) in sustain_pairs or (ab, aa) in sustain_pairs:
        return 0.55
    return 0.35


def _serialize_pair_detail(detail: dict[str, Any]) -> dict[str, Any]:
    comps = detail.get("components") or {}
    out_comps: dict[str, Any] = {}
    for k, v in comps.items():
        if v is None:
            out_comps[k] = None
        elif isinstance(v, int | float) and math.isfinite(float(v)):
            out_comps[k] = float(v)
        else:
            out_comps[k] = v
    return {
        "rule": str(detail.get("rule") or ""),
        "components": out_comps,
        "source_mechanism_a": detail.get("source_mechanism_a"),
        "source_mechanism_b": detail.get("source_mechanism_b"),
    }


def _build_timbral_acoustic_affinity_evidence_status(
    *,
    n: int,
    cross_pairs: int,
    comp_out: dict[str, float],
    feats: dict[str, Any] | None,
    low_taxonomy_confidence: bool,
    min_evidence_policy: str,
) -> str:
    """
    Evidence status aligned with ``timbral_acoustic_affinity_components`` and window coverage flags.

    ``comp_out`` keys are authoritative for whether a kernel component contributed to the
    window-level component summary (not whether an individual pair omitted it in a short-circuit).
    """
    parts: list[str] = []
    if n < 2:
        parts.append("single_event_self_similarity_only")
    elif cross_pairs == 0:
        parts.append("insufficient_pairwise")

    feat = feats or {}
    dyn_cov = str(feat.get("dynamic_coverage_status") or "").strip().lower()
    tech_cov = str(feat.get("technique_coverage_status") or "").strip().lower()

    if "technique" in comp_out:
        tv = float(comp_out["technique"])
        if math.isfinite(tv) and tv >= 0.995:
            if tech_cov == "explicit_uniform":
                parts.append("technique_default_only")
            else:
                parts.append("technique_no_special_evidence")
        else:
            parts.append("technique_active")
    elif tech_cov in ("unavailable", "unknown"):
        parts.append("technique_omitted")
    else:
        parts.append("technique_omitted_or_partial")

    if "dynamic" in comp_out:
        if dyn_cov.startswith("explicit") or dyn_cov == "partial":
            parts.append("dynamic_used_explicit_notated")
        else:
            parts.append("dynamic_active")
    else:
        parts.append("dynamic_omitted")

    if low_taxonomy_confidence:
        parts.append("taxonomy_fallback_or_unknown")

    if min_evidence_policy == "strict" and any(
        p in parts for p in ("technique_omitted", "technique_omitted_or_partial", "dynamic_omitted")
    ):
        parts.insert(0, "partial_evidence")

    if not parts:
        return "complete"
    return ";".join(parts)


def _pairwise_export_summary(pair_rows: list[dict[str, Any]]) -> str:
    if not pair_rows:
        return ""
    ranked = sorted(pair_rows, key=lambda r: float(r.get("similarity", 0.0)))
    weak = ranked[:3]
    strong = list(reversed(ranked[-3:]))
    def _pair_label(r: dict[str, Any]) -> str:
        return f"{r.get('event_i_instrument')}-{r.get('event_j_instrument')}:{float(r.get('similarity', 0.0)):.3f}"

    parts = [
        "weakest=" + ",".join(_pair_label(r) for r in weak),
        "strongest=" + ",".join(_pair_label(r) for r in strong),
    ]
    return ";".join(parts)[:400]


def _geometric_kernel(components: dict[str, float | None], weights: dict[str, float]) -> tuple[float, dict[str, float]]:
    used: dict[str, float] = {}
    w_sum = 0.0
    log_acc = 0.0
    for key, w in weights.items():
        if w <= 0.0:
            continue
        val = components.get(key)
        if val is None or not math.isfinite(float(val)):
            continue
        v = max(_KERNEL_EPS, float(val))
        used[key] = v
        log_acc += float(w) * math.log(v)
        w_sum += float(w)
    if w_sum <= 1e-15:
        return float("nan"), used
    k = float(math.exp(log_acc / w_sum))
    return float(np.clip(k, 0.0, 1.0)), used


def pairwise_acoustic_kernel(
    ev_a: dict[str, Any],
    ev_b: dict[str, Any],
    *,
    profile: str,
    kernel_weights: dict[str, float] | None = None,
    include_interval_class: bool = False,
    tax: dict[str, Any] | None = None,
) -> tuple[float, dict[str, Any]]:
    """K(e, f) in [0, 1] with component breakdown."""
    cfg = tax if tax is not None else load_acoustic_timbral_taxonomy()
    prof = str(profile or "conservative").strip().lower()
    ia, ib = str(ev_a.get("instrument") or ""), str(ev_b.get("instrument") or "")
    if _norm_inst(ia) == _norm_inst(ib) and ia.strip():
        tech_id = technique_compatibility_similarity(ev_a, ev_b, cfg)
        if tech_id is not None and float(tech_id) < 0.995:
            return float(np.clip(float(tech_id), 0.0, 1.0)), {
                "rule": "same_canonical_instrument_technique_adjusted",
                "components": {"identity": 1.0, "technique": tech_id},
            }
        comp_meta: dict[str, float | None] = {"identity": 1.0, "technique": float(tech_id) if tech_id is not None else 1.0}
        dyn_id = dynamic_compatibility_similarity(ev_a, ev_b, cfg)
        if dyn_id is not None:
            comp_meta["dynamic"] = float(dyn_id)
        return 1.0, {"rule": "same_canonical_instrument", "components": comp_meta}

    tags_a = acoustic_tags_for_event(ev_a, cfg)
    tags_b = acoustic_tags_for_event(ev_b, cfg)
    ov = _canonical_pair_override(ia, ib, prof, cfg)
    if ov is not None:
        tech_ov = technique_compatibility_similarity(ev_a, ev_b, cfg)
        if tech_ov is not None and float(tech_ov) < 0.98:
            ov = float(ov) * float(tech_ov)
        return float(np.clip(ov, 0.0, 1.0)), {
            "rule": "canonical_pair_override",
            "components": {"override": ov, "technique": tech_ov},
        }

    sm_a = tags_a.get("source_mechanism") or "unknown"
    sm_b = tags_b.get("source_mechanism") or "unknown"
    components: dict[str, float | None] = {
        "source_mechanism": _source_mechanism_similarity(sm_a, sm_b, cfg, prof),
        "instrument_family": _instrument_family_similarity(tags_a, tags_b, cfg),
        "register_tessitura": register_tessitura_similarity(ev_a, ev_b, cfg),
        "technique": technique_compatibility_similarity(ev_a, ev_b, cfg),
        "dynamic": dynamic_compatibility_similarity(ev_a, ev_b, cfg),
        "attack_envelope": attack_envelope_similarity(tags_a, tags_b),
    }
    if include_interval_class:
        components["interval_class"] = interval_class_symbolic_factor(ev_a, ev_b, cfg)

    w_default = dict(cfg.get("default_kernel_weights") or {})
    weights = {**w_default, **(kernel_weights or {})}
    if not include_interval_class:
        weights["interval_class"] = 0.0

    k_val, used = _geometric_kernel(components, weights)
    return k_val, {
        "rule": "pairwise_acoustic_kernel",
        "components": {k: components.get(k) for k in components},
        "components_used": used,
        "source_mechanism_a": sm_a,
        "source_mechanism_b": sm_b,
    }


def compute_timbral_acoustic_affinity(
    contrib: list[tuple[dict[str, Any], float]],
    feats: dict[str, Any] | None,
    *,
    profile: str = "conservative",
    kernel_weights: dict[str, float] | None = None,
    include_interval_class: bool = False,
    collect_pairs: bool = False,
    min_evidence_policy: str = "omit_missing_components",
) -> dict[str, Any]:
    """
    Event-level affinity A(t) = sum_ij p_i p_j K_ij (diagonal K_ii = 1).

    ``contrib`` must be event-level (not chord-tone duplicates).
    """
    nan = float("nan")
    base_status = {
        "acoustic_proxy_not_audio_analysis": True,
        "acoustic_proxy_validation_status": str(
            load_acoustic_timbral_taxonomy().get("validation_status_default", "score_derived_unvalidated")
        ),
    }
    if not contrib:
        return {
            **base_status,
            "timbral_acoustic_affinity": nan,
            "H_TA_acoustic_proxy": nan,
            "timbral_acoustic_affinity_components": {},
            "timbral_acoustic_affinity_profile": str(profile),
            "timbral_acoustic_affinity_evidence_status": "insufficient_events",
            "timbral_acoustic_pairwise_summary": "",
            "_pair_rows": [],
        }

    tot = float(sum(max(0.0, float(ol)) for _, ol in contrib))
    if tot <= 1e-15:
        return {
            **base_status,
            "timbral_acoustic_affinity": nan,
            "H_TA_acoustic_proxy": nan,
            "timbral_acoustic_affinity_components": {},
            "timbral_acoustic_affinity_profile": str(profile),
            "timbral_acoustic_affinity_evidence_status": "insufficient_mass",
            "timbral_acoustic_pairwise_summary": "",
            "_pair_rows": [],
        }

    events = [e for e, _ in contrib]
    p = [max(0.0, float(ol)) / tot for _, ol in contrib]
    n = len(events)
    p_sum = float(sum(p))
    if abs(p_sum - 1.0) > 1e-6 and p_sum > 1e-15:
        p = [float(x) / p_sum for x in p]
    tax = load_acoustic_timbral_taxonomy()
    w_def = dict(tax.get("default_kernel_weights") or {})
    kw = {**w_def, **(kernel_weights or {})}

    acc = 0.0
    pair_rows: list[dict[str, Any]] = []
    component_sums: dict[str, float] = {}
    component_weight_sums: dict[str, float] = {}
    low_taxonomy_confidence = False
    cross_pairs = 0
    pair_memo: dict[tuple[int, int], tuple[float, dict[str, Any]]] = {}

    for i in range(n):
        if acoustic_tags_for_event(events[i], tax).get("taxonomy_confidence") != "explicit_instrument_row":
            low_taxonomy_confidence = True
        for j in range(n):
            wij = p[i] * p[j]
            if i == j:
                k_ij = 1.0
                detail: dict[str, Any] = {"rule": "diagonal"}
            else:
                lo, hi = (i, j) if i < j else (j, i)
                memo_key = (lo, hi)
                if memo_key in pair_memo:
                    k_ij, detail = pair_memo[memo_key]
                else:
                    k_ij, detail = pairwise_acoustic_kernel(
                        events[lo],
                        events[hi],
                        profile=profile,
                        kernel_weights=kw,
                        include_interval_class=include_interval_class,
                        tax=tax,
                    )
                    pair_memo[memo_key] = (float(k_ij), dict(detail))
                cross_pairs += 1
                comps = detail.get("components") or {}
                for ck, cv in comps.items():
                    if cv is not None and math.isfinite(float(cv)):
                        component_sums[ck] = component_sums.get(ck, 0.0) + wij * float(cv)
                        component_weight_sums[ck] = component_weight_sums.get(ck, 0.0) + wij
            acc += wij * float(k_ij)
            if collect_pairs and i < j:
                pair_rows.append(
                    {
                        "event_i_instrument": str(events[i].get("instrument") or ""),
                        "event_j_instrument": str(events[j].get("instrument") or ""),
                        "similarity": float(k_ij),
                        "mass_weight": float(wij),
                        "profile": profile,
                        "pairwise_K": float(k_ij),
                        "evidence_status": "score_derived_symbolic_proxy",
                        "detail": _serialize_pair_detail(detail if isinstance(detail, dict) else {}),
                    }
                )

    affinity = float(np.clip(acc, 0.0, 1.0))
    comp_out: dict[str, float] = {}
    for ck, s in component_sums.items():
        wsum = component_weight_sums.get(ck, 0.0)
        if wsum > 1e-15:
            comp_out[ck] = float(s / wsum)

    ev_status = _build_timbral_acoustic_affinity_evidence_status(
        n=n,
        cross_pairs=cross_pairs,
        comp_out=comp_out,
        feats=feats,
        low_taxonomy_confidence=low_taxonomy_confidence,
        min_evidence_policy=min_evidence_policy,
    )

    sm_keys = sorted({acoustic_tags_for_event(e, tax).get("source_mechanism", "?") for e in events})
    pair_note = _pairwise_export_summary(pair_rows) if pair_rows else ""
    summary = f"n_events={n};p_sum={p_sum:.6f};mechanisms={','.join(sm_keys)};affinity={affinity:.4f}"
    if pair_note:
        summary = f"{summary};{pair_note}"

    out: dict[str, Any] = {
        **base_status,
        "timbral_acoustic_affinity": affinity,
        "H_TA_acoustic_proxy": affinity,
        "timbral_acoustic_affinity_components": comp_out,
        "timbral_acoustic_affinity_profile": str(profile).strip().lower(),
        "timbral_acoustic_affinity_evidence_status": ev_status,
        "timbral_acoustic_pairwise_summary": summary[:500],
        "_pair_rows": pair_rows,
    }
    return out


def compute_H_TA_acoustic_contextual(
    affinity_bundle: dict[str, Any],
    feats: dict[str, Any],
    *,
    register_blend_from_compactness: bool = True,
) -> float:
    """Optional geometric mean with register / technique / dynamic proxies (separate from H_TI_core)."""
    factors: list[float] = []
    ta = affinity_bundle.get("timbral_acoustic_affinity")
    if isinstance(ta, int | float) and math.isfinite(float(ta)):
        factors.append(float(ta))
    if register_blend_from_compactness:
        rp = feats.get("register_compactness")
        if isinstance(rp, int | float) and math.isfinite(float(rp)):
            factors.append(float(rp))
    tu = feats.get("technique_uniformity")
    if isinstance(tu, int | float) and math.isfinite(float(tu)):
        factors.append(float(tu))
    ndc = feats.get("notated_dynamic_coherence")
    if isinstance(ndc, int | float) and math.isfinite(float(ndc)):
        factors.append(float(ndc))
    good = [max(_KERNEL_EPS, x) for x in factors if x > 0]
    if not good:
        return float("nan")
    return float(math.exp(sum(math.log(x) for x in good) / len(good)))


def disabled_acoustic_proxy_bundle() -> dict[str, Any]:
    nan = float("nan")
    return {
        "acoustic_proxy_not_audio_analysis": True,
        "acoustic_proxy_validation_status": "score_derived_unvalidated",
        "timbral_acoustic_affinity": nan,
        "H_TA_acoustic_proxy": nan,
        "H_TA_acoustic_contextual": nan,
        "timbral_acoustic_affinity_components": {},
        "timbral_acoustic_affinity_profile": "",
        "timbral_acoustic_affinity_evidence_status": "disabled",
        "timbral_acoustic_pairwise_summary": "",
        "_pair_rows": [],
    }


# H_TI CSV/JSON column names for optional timbral-acoustic proxy (single source of truth).
HTI_ACOUSTIC_PROXY_SERIES_KEYS: tuple[str, ...] = (
    "H_TA_acoustic_proxy",
    "H_TA_acoustic_contextual",
    "timbral_acoustic_affinity",
    "timbral_acoustic_affinity_components",
    "timbral_acoustic_affinity_profile",
    "timbral_acoustic_affinity_evidence_status",
    "timbral_acoustic_pairwise_summary",
    "acoustic_proxy_not_audio_analysis",
    "acoustic_proxy_validation_status",
)

HTI_ACOUSTIC_PROXY_CSV_JSON_DICT_KEYS: frozenset[str] = frozenset({"timbral_acoustic_affinity_components"})

_HTA_FLOAT_KEYS: frozenset[str] = frozenset(
    {
        "H_TA_acoustic_proxy",
        "H_TA_acoustic_contextual",
        "timbral_acoustic_affinity",
    }
)


def insufficient_window_acoustic_proxy_bundle() -> dict[str, Any]:
    """Proxy bundle for empty-window rows (profile/summary use ``disabled`` sentinel strings)."""
    b = dict(disabled_acoustic_proxy_bundle())
    b["timbral_acoustic_affinity_profile"] = "disabled"
    b["timbral_acoustic_pairwise_summary"] = "disabled"
    return b


def acoustic_proxy_series_value(key: str, acb: dict[str, Any], *, nan_value: float) -> Any:
    """Map one ``HTI_ACOUSTIC_PROXY_SERIES_KEYS`` column from a proxy bundle (matches ``hti.py`` semantics)."""
    av = acb.get(key)
    if key.endswith("_components"):
        return dict(av) if isinstance(av, dict) else {}
    if key == "acoustic_proxy_not_audio_analysis":
        return bool(av)
    if isinstance(av, int | float) and math.isfinite(float(av)):
        return float(av)
    if key in _HTA_FLOAT_KEYS:
        return float(nan_value)
    return str(av or "")


def append_hti_acoustic_proxy_series_row(
    results: dict[str, list[Any]],
    acb: dict[str, Any],
    *,
    nan_value: float,
) -> None:
    """Append one window row for all ``HTI_ACOUSTIC_PROXY_SERIES_KEYS``."""
    for ak in HTI_ACOUSTIC_PROXY_SERIES_KEYS:
        results[ak].append(acoustic_proxy_series_value(ak, acb, nan_value=nan_value))
