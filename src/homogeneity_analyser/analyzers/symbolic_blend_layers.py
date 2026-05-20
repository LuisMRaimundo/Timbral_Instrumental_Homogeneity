"""
Optional **literature-conditioned symbolic blend** diagnostics (notation-derived).

This is a **score-based symbolic model**. It does **not** measure acoustic fusion, spectral
similarity, SPL, masking, or perceptual fusion.

These layers are **not** ``H_TI_core``, **not** measured audio, and **not** validated perceptual fusion.
They combine interval-class weights (orthogonal to registral span / ``register_compactness``),
attack-class compatibility, optional timbral-affinity diagnostics, and ordinal dynamic conditioning
**only** when the caller enables the bundle.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.timbral_affinity import affinity_tags_for_event

_JSON_PATH = Path(__file__).resolve().parent.parent / "taxonomy" / "symbolic_blend_conditioning.json"

_BLEND_GEOM_EPS = 1e-12

# Stable JSON / config keys (backward compatible). Display text is separate — see below.
INTERVAL_CLASS_KEYS: tuple[str, ...] = (
    "unison_octave",
    "fifth_twelfth",
    "fourth_class",
    "thirds_sixths",
    "tritone",
    "seconds_sevenths",
)

INTERVAL_CLASS_DISPLAY_LABELS: dict[str, str] = {
    "unison_octave": "unison / octave equivalence class",
    "fifth_twelfth": "fifth / twelfth equivalence class",
    "fourth_class": "fourth equivalence class",
    "thirds_sixths": "third-class / sixth-class equivalence group",
    "tritone": "tritone equivalence class",
    "seconds_sevenths": "second-class / seventh-class equivalence group",
}


@lru_cache(maxsize=1)
def load_symbolic_blend_conditioning_profile() -> dict[str, Any]:
    if not _JSON_PATH.is_file():
        return {}
    try:
        return json.loads(_JSON_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _interval_blend_table_for_profile(cfg: dict[str, Any], profile: str) -> dict[str, Any]:
    """Resolve per-profile interval-class weights; fall back to legacy ``interval_class_blend``."""
    profs = cfg.get("interval_class_blend_profiles")
    if isinstance(profs, dict):
        sub = profs.get(str(profile).strip().lower())
        if isinstance(sub, dict) and sub:
            return sub
    ib = cfg.get("interval_class_blend") or {}
    return ib if isinstance(ib, dict) else {}


def chromatic_interval_class_d12(midi_a: float, midi_b: float) -> int:
    """Octave-reduced chromatic distance in semitones (0..11), not inversion-collapsed Forte ic."""
    d = abs(float(midi_a) - float(midi_b))
    return int(round(d)) % 12


def interval_class_key_for_d12(d12: int) -> str:
    """Map chromatic mod‑12 distance (0..11) to a stable symbolic interval-class bucket key."""
    d = int(d12) % 12
    if d == 0:
        return "unison_octave"
    if d == 7:
        return "fifth_twelfth"
    if d == 5:
        return "fourth_class"
    if d in (3, 4, 8, 9):
        return "thirds_sixths"
    if d == 6:
        return "tritone"
    return "seconds_sevenths"


def interval_class_display_label(class_key: str, cfg: dict[str, Any] | None = None) -> str:
    """Human-readable label for a stable ``interval_class_profile`` key (exports / UI)."""
    c = cfg if isinstance(cfg, dict) else load_symbolic_blend_conditioning_profile()
    labels = c.get("interval_class_display_labels")
    table = labels if isinstance(labels, dict) else INTERVAL_CLASS_DISPLAY_LABELS
    key = str(class_key or "").strip()
    lab = table.get(key)
    if isinstance(lab, str) and lab.strip():
        return lab.strip()
    return INTERVAL_CLASS_DISPLAY_LABELS.get(key, key or "unknown_interval_class")


def interval_class_profile_to_display_profile(
    prof: dict[str, float],
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Same overlap masses as ``interval_class_profile``, keyed by display labels."""
    c = cfg if isinstance(cfg, dict) else load_symbolic_blend_conditioning_profile()
    return {
        interval_class_display_label(k, c): float(v)
        for k, v in sorted(prof.items())
        if isinstance(v, int | float) and math.isfinite(float(v))
    }


def interval_class_blend_weight(
    d12: int, cfg: dict[str, Any], *, profile: str = "conservative"
) -> tuple[str, float]:
    """Map ``d12`` (0..11) to a named class key and blend weight from the active profile table."""
    ib = _interval_blend_table_for_profile(cfg, profile)
    key = interval_class_key_for_d12(d12)
    w = ib.get(key)
    if not isinstance(w, int | float) or not math.isfinite(float(w)):
        w = 0.5
    return key, float(np.clip(float(w), 0.0, 1.0))


def _distance_attenuation(interval_semitones: float, cfg: dict[str, Any]) -> float:
    """
    Optional penalty for wide registral separation **without** erasing interval-class identity.

    ``1 / (1 + max(0, |Δpitch| - free_span) / distance_scale)`` — no penalty up to ``free_span``.
    """
    sec = cfg.get("interval_blend_distance_attenuation") or {}
    if not isinstance(sec, dict) or not bool(sec.get("enabled", True)):
        return 1.0
    scale = float(sec.get("distance_scale_semitones", 24.0))
    if not math.isfinite(scale) or scale <= 1e-12:
        scale = 24.0
    free = float(sec.get("free_span_before_penalty_semitones", 12.0))
    if not math.isfinite(free):
        free = 12.0
    excess = max(0.0, float(interval_semitones) - free)
    return float(1.0 / (1.0 + excess / scale))


def _interval_class_evidence_status_default(cfg: dict[str, Any]) -> str:
    v = cfg.get("interval_class_evidence_status_default")
    if isinstance(v, str) and v.strip():
        return v.strip()
    return "symbolic_convention"


def _normalized_geometric_mean(factors: list[float], *, eps: float = _BLEND_GEOM_EPS) -> float:
    good = [
        float(x)
        for x in factors
        if isinstance(x, int | float) and math.isfinite(float(x)) and float(x) > 0.0
    ]
    if not good:
        return float("nan")
    clipped = [max(x, eps) for x in good]
    return float(math.exp(sum(math.log(x) for x in clipped) / len(clipped)))


def compute_interval_class_blend_factor(
    active_pitches: Sequence[float],
    weights: Sequence[float] | None = None,
    profile: str = "conservative",
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Weighted mean of **symbolic** interval-class favourability × optional distance attenuation.

    This is a **score-based symbolic model**. It does **not** measure acoustic fusion, spectral
    similarity, SPL, masking, or perceptual fusion.

    ``active_pitches`` are sounding MIDI numbers; ``weights`` must match length when provided.
    Pairwise scores use ``interval_class_value * distance_attenuation`` so registral width can
    weaken a relation **without** collapsing the interval-class label (orthogonal to
    ``register_compactness`` in ``H_TI_core``).
    """
    c = cfg if isinstance(cfg, dict) else load_symbolic_blend_conditioning_profile()
    prof = str(profile or "conservative").strip().lower()
    evidence = _interval_class_evidence_status_default(c)

    pitches = [float(p) for p in active_pitches]
    n = len(pitches)
    if n < 2:
        return {
            "interval_class_blend_factor": float("nan"),
            "interval_class_profile": {},
            "interval_class_profile_display": {},
            "literal_interval_semitone_pair_mass": {},
            "chromatic_mod12_pair_mass": {},
            "pairwise_interval_class_coverage_status": "insufficient_pairs",
            "interval_class_evidence_status": evidence,
        }
    if weights is None:
        wts = [1.0] * n
    else:
        wts = [float(w) for w in weights]
        if len(wts) != n:
            raise ValueError("weights must have the same length as active_pitches.")
    num = 0.0
    den = 0.0
    dist: dict[str, float] = {}
    literal_mass: dict[str, float] = {}
    mod12_mass: dict[str, float] = {}
    for i in range(n):
        wi = max(0.0, wts[i])
        for j in range(i + 1, n):
            wj = max(0.0, wts[j])
            interval_semitones = abs(pitches[i] - pitches[j])
            literal_key = str(int(round(interval_semitones)))
            d12 = int(round(interval_semitones)) % 12
            mod12_key = str(d12)
            cls, v_class = interval_class_blend_weight(d12, c, profile=prof)
            da = _distance_attenuation(interval_semitones, c)
            rel_score = float(np.clip(float(v_class) * float(da), 0.0, 1.0))
            wij = wi * wj
            num += wij * rel_score
            den += wij
            dist[cls] = dist.get(cls, 0.0) + wij
            literal_mass[literal_key] = literal_mass.get(literal_key, 0.0) + wij
            mod12_mass[mod12_key] = mod12_mass.get(mod12_key, 0.0) + wij
    totw = sum(dist.values()) or 1.0
    prof_out = {k: float(v) / totw for k, v in sorted(dist.items())}
    lit_tot = sum(literal_mass.values()) or 1.0
    literal_out = {k: float(v) / lit_tot for k, v in sorted(literal_mass.items(), key=lambda x: int(x[0]))}
    m12_tot = sum(mod12_mass.values()) or 1.0
    mod12_out = {k: float(v) / m12_tot for k, v in sorted(mod12_mass.items(), key=lambda x: int(x[0]))}
    fac = float(num / den) if den > 1e-15 else float("nan")
    fac_out = float(np.clip(fac, 0.0, 1.0)) if math.isfinite(fac) else float("nan")
    return {
        "interval_class_blend_factor": fac_out,
        "interval_class_profile": prof_out,
        "interval_class_profile_display": interval_class_profile_to_display_profile(prof_out, cfg=c),
        "literal_interval_semitone_pair_mass": literal_out,
        "chromatic_mod12_pair_mass": mod12_out,
        "pairwise_interval_class_coverage_status": "sufficient_pairs",
        "interval_class_evidence_status": evidence,
    }


def compute_pairwise_interval_blend_factor(
    pitch_occurrences: list[tuple[float, float]],
    *,
    cfg: dict[str, Any] | None = None,
    profile: str = "conservative",
) -> dict[str, Any]:
    """
    Overlap-weighted **interval-class** blend diagnostics (orthogonal to ``register_compactness``).

    This is a **score-based symbolic model**. It does **not** measure acoustic fusion, spectral
    similarity, SPL, masking, or perceptual fusion.

    Does not replace ``pairwise_interval_proximity`` inside ``H_TI_core``.
    """
    c = cfg if isinstance(cfg, dict) else load_symbolic_blend_conditioning_profile()
    if len(pitch_occurrences) < 2:
        ev = _interval_class_evidence_status_default(c)
        nan = float("nan")
        return {
            "pairwise_interval_blend_factor": nan,
            "interval_class_blend_factor": nan,
            "symbolic_blend_interval_profile": {},
            "interval_class_profile": {},
            "interval_class_profile_display": {},
            "literal_interval_semitone_pair_mass": {},
            "chromatic_mod12_pair_mass": {},
            "pairwise_interval_class_coverage_status": "insufficient_pairs",
            "interval_class_evidence_status": ev,
        }
    pitches = [float(pitch_occurrences[i][0]) for i in range(len(pitch_occurrences))]
    wts = [float(pitch_occurrences[i][1]) for i in range(len(pitch_occurrences))]
    inner = compute_interval_class_blend_factor(pitches, wts, profile=profile, cfg=c)
    fac = float(inner["interval_class_blend_factor"])
    prof = dict(inner.get("interval_class_profile") or {})
    st = str(inner.get("pairwise_interval_class_coverage_status") or "")
    ev = str(inner.get("interval_class_evidence_status") or "")
    return {
        "pairwise_interval_blend_factor": fac,
        "interval_class_blend_factor": fac,
        "symbolic_blend_interval_profile": prof,
        "interval_class_profile": prof,
        "interval_class_profile_display": dict(inner.get("interval_class_profile_display") or {}),
        "literal_interval_semitone_pair_mass": dict(inner.get("literal_interval_semitone_pair_mass") or {}),
        "chromatic_mod12_pair_mass": dict(inner.get("chromatic_mod12_pair_mass") or {}),
        "pairwise_interval_class_coverage_status": st,
        "interval_class_evidence_status": ev,
    }


def _norm_inst(s: str) -> str:
    return str(s or "").strip().lower()


def _attack_class_for_event(ev: dict[str, Any], tags: dict[str, str], cfg: dict[str, Any]) -> str:
    inst = _norm_inst(str(ev.get("instrument") or ""))
    fam = str(ev.get("family") or "")
    env = str(tags.get("envelope_class") or "")
    exc = str(tags.get("excitation_class") or "")
    bright = {_norm_inst(x) for x in (cfg.get("brass_bright_tendency_instruments") or [])}
    mellow = {_norm_inst(x) for x in (cfg.get("brass_mellow_tendency_instruments") or [])}
    if fam == "brass" and inst in bright:
        return "brass_bright"
    if fam == "brass" and inst in mellow:
        return "brass_mellow"
    if exc == "plucked_string" or env == "plucked_decay":
        return "plucked"
    if env in ("membrane_decay", "wooden_struck_decay", "dry_struck_decay", "metallic_resonant_decay"):
        return "impulsive"
    if exc == "bowed_string" or env in (
        "sustained_bowed",
        "reiterated_sustain",
        "bright_bowed_noise_edge",
        "soft_bowed_sustain",
        "harmonic_light_sustain",
    ):
        return "bowed_sustained"
    if exc in ("single_reed", "double_reed") or env in ("sustained_reed", "noisy_air_reiteration"):
        return "reed_sustained"
    if exc == "air_jet" or env == "sustained_air":
        return "sustained"
    if exc == "lip_reed" or env == "sustained_brass":
        return "brass_bright"
    if env == "stopped_brass":
        return "brass_mellow"
    return "sustained"


def _attack_compat_score(a: str, b: str, table: dict[str, Any]) -> float:
    if a == b:
        return 1.0
    keys = [
        f"{a}_{b}",
        f"{b}_{a}",
    ]
    for k in keys:
        if k in table:
            return float(np.clip(float(table[k]), 0.0, 1.0))
    d = float(table.get("default", 0.65))
    return float(np.clip(d, 0.0, 1.0))


def compute_attack_compatibility_factor(
    contrib: list[tuple[dict[str, Any], float]],
    *,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Conservative overlap-weighted attack / onset class compatibility (symbolic).

    This is a **score-based symbolic model**. It does **not** measure acoustic fusion, spectral
    similarity, SPL, masking, or perceptual fusion.
    """
    c = cfg if isinstance(cfg, dict) else load_symbolic_blend_conditioning_profile()
    ac = c.get("attack_compatibility") or {}
    if not isinstance(ac, dict):
        ac = {}
    if not contrib:
        return {
            "attack_compatibility_factor": float("nan"),
            "attack_class_distribution": {},
        }
    tot = float(sum(max(0.0, float(ol)) for _, ol in contrib))
    if tot <= 1e-15:
        return {
            "attack_compatibility_factor": float("nan"),
            "attack_class_distribution": {},
        }
    classes: list[str] = []
    masses: list[float] = []
    for ev, ol in contrib:
        tags = affinity_tags_for_event(ev)
        cls = _attack_class_for_event(ev, tags, c)
        classes.append(cls)
        masses.append(max(0.0, float(ol)))
    dist: dict[str, float] = {}
    for cls, m in zip(classes, masses, strict=True):
        dist[cls] = dist.get(cls, 0.0) + m
    for k in list(dist.keys()):
        dist[k] = float(dist[k]) / tot
    n = len(classes)
    acc = 0.0
    wsum = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            wij = masses[i] * masses[j]
            s = _attack_compat_score(classes[i], classes[j], ac)
            acc += wij * s
            wsum += wij
    fac = float(acc / wsum) if wsum > 1e-15 else float("nan")
    return {
        "attack_compatibility_factor": float(np.clip(fac, 0.0, 1.0)) if math.isfinite(fac) else float("nan"),
        "attack_class_distribution": dist,
    }


def clarinet_register_zone_from_soundings(pitches: list[float], cfg: dict[str, Any]) -> str:
    thr = cfg.get("clarinet_register_thresholds_sound_midi") or {}
    if not isinstance(thr, dict) or not pitches:
        return "n/a"
    try:
        mx = max(float(p) for p in pitches)
    except (TypeError, ValueError):
        return "n/a"
    chmx = float(thr.get("chalumeau_max_below", 60.0))
    clmx = float(thr.get("clarion_max_below", 77.0))
    if mx < chmx:
        return "chalumeau"
    if mx < clmx:
        return "clarion"
    return "altissimo"


def clarinet_register_zone_penalty(ev_a: dict[str, Any], ev_b: dict[str, Any], cfg: dict[str, Any]) -> float:
    """1.0 when zones align or not applicable; lower when both clarinets in different zones."""
    if str(ev_a.get("family") or "") != "clarinets" or str(ev_b.get("family") or "") != "clarinets":
        return 1.0
    pa = [float(x) for x in (ev_a.get("pitches") or [])]
    pb = [float(x) for x in (ev_b.get("pitches") or [])]
    za = clarinet_register_zone_from_soundings(pa, cfg)
    zb = clarinet_register_zone_from_soundings(pb, cfg)
    if za == "n/a" or zb == "n/a":
        return 1.0
    if za == zb:
        return 1.0
    # Adjacent zones retain partial symbolic proximity; cross chalumeau/altissimo is weakest.
    order = ("chalumeau", "clarion", "altissimo")
    ia, ib = order.index(za), order.index(zb)
    gap = abs(ia - ib)
    if gap >= 2:
        return 0.55
    return 0.78


def compute_literature_symbolic_dynamic_conditioning_scalar(feats: dict[str, Any], cfg: dict[str, Any]) -> float:
    """
    Ordinal dynamics-only scalar in [0,1] for optional blend bundle (never SPL / loudness).

    This is a **score-based symbolic model**. It does **not** measure acoustic fusion, spectral
    similarity, SPL, masking, or perceptual fusion.
    """
    lit = cfg.get("literature_symbolic_dynamic_conditioning") or {}
    if not isinstance(lit, dict):
        lit = {}
    wc = float(lit.get("coherence_weight", 0.35))
    ws = float(lit.get("softness_weight", 0.25))
    wr = float(lit.get("projection_risk_guard", 0.40))
    coh = float(feats.get("notated_dynamic_coherence") or 0.0)
    if not math.isfinite(coh):
        coh = 0.0
    soft = float(feats.get("dynamic_softness") or 0.5)
    if not math.isfinite(soft):
        soft = 0.5
    prisk = float(feats.get("family_specific_projection_weight") or 0.0)
    if not math.isfinite(prisk):
        prisk = 0.0
    v = wc * float(np.clip(coh, 0.0, 1.0))
    v += ws * float(np.clip(soft, 0.0, 1.0))
    v += wr * float(np.clip(1.0 - prisk, 0.0, 1.0))
    return float(np.clip(v / max(wc + ws + wr, 1e-12), 0.0, 1.0))


def compute_symbolic_blend_bundle_for_window(
    feats: dict[str, Any],
    contrib: list[tuple[dict[str, Any], float]],
    pitch_occurrences: list[tuple[float, float]],
    *,
    h_ti_core: float,
    timbral_affinity_uniformity: float | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Optional **symbolic blend potential**: normalized geometric mean of available positive factors.

    Combines **H_TI_core** × interval-class blend × (optional) attack compatibility × (optional)
    dynamic conditioning, omitting factors that are non-finite. Clarinet register-zone penalty
    applies as a final multiplicative guard on the literature-conditioned proxy.

    This is a **score-based symbolic model**. It does **not** measure acoustic fusion, spectral
    similarity, SPL, masking, or perceptual fusion.

    ``not_audio_analysis`` and ``literature_conditioned_symbolic_proxy`` are echoed for JSON consumers.
    """
    c = cfg if isinstance(cfg, dict) else load_symbolic_blend_conditioning_profile()
    iv = compute_pairwise_interval_blend_factor(pitch_occurrences, cfg=c)
    atk = compute_attack_compatibility_factor(contrib, cfg=c)
    dyn_sym = compute_literature_symbolic_dynamic_conditioning_scalar(feats, c)

    h = float(h_ti_core)
    ivf = float(iv["interval_class_blend_factor"])
    acf = float(atk["attack_compatibility_factor"])

    factors: list[float] = []
    if math.isfinite(h) and h > 0.0:
        factors.append(float(np.clip(h, 0.0, 1.0)))
    if math.isfinite(ivf) and ivf > 0.0:
        factors.append(float(np.clip(ivf, 0.0, 1.0)))
    if math.isfinite(acf) and acf > 0.0:
        factors.append(float(np.clip(acf, 0.0, 1.0)))

    dcs = str(feats.get("dynamic_coverage_status") or "").strip().lower()
    if dcs not in ("unavailable", "none", "") and math.isfinite(dyn_sym) and dyn_sym > 0.0:
        factors.append(float(np.clip(dyn_sym, 0.0, 1.0)))

    blend_potential = _normalized_geometric_mean(factors)

    clarinet_pen = 1.0
    if len(contrib) >= 2:
        evs = [e for e, _ in contrib]
        for i in range(len(evs)):
            for j in range(i + 1, len(evs)):
                clarinet_pen = min(clarinet_pen, clarinet_register_zone_penalty(evs[i], evs[j], c))
    if math.isfinite(blend_potential):
        blend_potential = float(np.clip(blend_potential * clarinet_pen, 0.0, 1.0))
    else:
        blend_potential = float("nan")

    tau = float(timbral_affinity_uniformity) if timbral_affinity_uniformity is not None else float("nan")

    return {
        "not_audio_analysis": True,
        "literature_conditioned_symbolic_proxy": True,
        "symbolic_blend_potential": blend_potential,
        "symbolic_blend_components": {
            "H_TI_core": float(h) if math.isfinite(h) else float("nan"),
            "interval_class_blend_factor": float(ivf) if math.isfinite(ivf) else float("nan"),
            "attack_compatibility_factor": float(acf) if math.isfinite(acf) else float("nan"),
            "literature_symbolic_dynamic_conditioning": float(dyn_sym) if math.isfinite(dyn_sym) else float("nan"),
            "clarinet_register_zone_symbolic_penalty": clarinet_pen,
            "literature_informed_symbolic_affinity_uniformity": float(tau) if math.isfinite(tau) else float("nan"),
            "blend_model": "normalized_geometric_mean_of_available_positive_factors",
        },
        "symbolic_blend_interval_profile": iv.get("symbolic_blend_interval_profile"),
        "interval_class_profile": iv.get("interval_class_profile"),
        "interval_class_profile_display": iv.get("interval_class_profile_display"),
        "literal_interval_semitone_pair_mass": iv.get("literal_interval_semitone_pair_mass"),
        "chromatic_mod12_pair_mass": iv.get("chromatic_mod12_pair_mass"),
        "interval_class_evidence_status": iv.get("interval_class_evidence_status"),
        "attack_class_distribution": atk.get("attack_class_distribution"),
        "symbolic_blend_profile_version": str(c.get("profile_version") or ""),
    }


# H_TI CSV/JSON column names for optional symbolic interval-class / blend-potential (single source of truth).
HTI_SYMBOLIC_BLEND_SERIES_KEYS: tuple[str, ...] = (
    "pairwise_interval_blend_factor",
    "interval_class_blend_factor",
    "symbolic_blend_interval_profile",
    "interval_class_profile",
    "interval_class_profile_display",
    "literal_interval_semitone_pair_mass",
    "chromatic_mod12_pair_mass",
    "interval_class_evidence_status",
    "attack_compatibility_factor",
    "attack_class_distribution",
    "symbolic_blend_potential",
    "symbolic_blend_components",
)

HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS: frozenset[str] = frozenset(
    (
        "symbolic_blend_interval_profile",
        "interval_class_profile",
        "interval_class_profile_display",
        "literal_interval_semitone_pair_mass",
        "chromatic_mod12_pair_mass",
        "attack_class_distribution",
        "symbolic_blend_components",
    )
)

_IVB_PROFILE_KEYS: tuple[str, ...] = tuple(
    k
    for k in HTI_SYMBOLIC_BLEND_SERIES_KEYS
    if k.endswith("_profile") or k.endswith("_mass")
)


def append_hti_symbolic_blend_series_row(
    results: dict[str, list[Any]],
    *,
    enabled: bool,
    ivb: dict[str, Any] | None,
    atk: dict[str, Any] | None,
    sympk: dict[str, Any] | None,
    nan_value: float,
) -> None:
    """Append one window row for all ``HTI_SYMBOLIC_BLEND_SERIES_KEYS`` (enabled or disabled)."""
    if enabled and ivb is not None and atk is not None and sympk is not None:
        pibf = float(ivb["pairwise_interval_blend_factor"])
        results["pairwise_interval_blend_factor"].append(pibf)
        results["interval_class_blend_factor"].append(float(ivb.get("interval_class_blend_factor", pibf)))
        for k in _IVB_PROFILE_KEYS:
            results[k].append(dict(ivb.get(k) or {}))
        results["interval_class_evidence_status"].append(str(ivb.get("interval_class_evidence_status") or ""))
        results["attack_compatibility_factor"].append(float(atk["attack_compatibility_factor"]))
        results["attack_class_distribution"].append(dict(atk.get("attack_class_distribution") or {}))
        results["symbolic_blend_potential"].append(float(sympk["symbolic_blend_potential"]))
        results["symbolic_blend_components"].append(dict(sympk.get("symbolic_blend_components") or {}))
        return
    for k in (
        "pairwise_interval_blend_factor",
        "interval_class_blend_factor",
        "attack_compatibility_factor",
        "symbolic_blend_potential",
    ):
        results[k].append(float(nan_value))
    for k in HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS:
        results[k].append({})
    results["interval_class_evidence_status"].append("")
