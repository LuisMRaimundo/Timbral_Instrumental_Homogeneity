"""
Notation-derived dynamic diagnostics for H_TI (ordinal marks and hairpins — not SPL).

Written dynamics are **symbolic** evidence on a fixed ordinal ladder; they are **not** SPL,
perceptual loudness, or measured acoustic intensity.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from homogeneity_analyser.analyzers.dominant_distribution import dominant_with_ties
from homogeneity_analyser.analyzers.technique_state import parse_standard_dynamic_mark

# Primary ladder (spec): symbolic ordinal in [0, 1], **not** SPL.
NOTATED_DYNAMIC_SYMBOLIC_ORDINAL: dict[str, float] = {
    "pppp": 0.00,
    "ppp": 0.08,
    "pp": 0.16,
    "p": 0.30,
    "mp": 0.43,
    "mf": 0.55,
    "f": 0.72,
    "ff": 0.88,
    "fff": 0.96,
    "ffff": 1.00,
}

# Secondary MusicXML / music21 tokens mapped conservatively onto the same ladder.
_SECONDARY_ORDINAL: dict[str, float] = {
    "mpp": 0.16,
    "mfp": 0.55,
    "nf": 0.55,
    "fp": 0.43,
    "sf": 0.72,
    "sfp": 0.55,
    "sfz": 0.72,
    "sffz": 0.88,
    "fz": 0.72,
    "rf": 0.72,
    "sp": 0.55,
    "sfzp": 0.55,
    "n": 0.55,
}


def symbolic_dynamic_intensity(token: str | None) -> float | None:
    """Return fixed symbolic intensity in ``[0, 1]`` or ``None`` if not a recognised mark."""
    if token is None:
        return None
    t = str(token).strip().lower()
    if t in NOTATED_DYNAMIC_SYMBOLIC_ORDINAL:
        return float(NOTATED_DYNAMIC_SYMBOLIC_ORDINAL[t])
    if t in _SECONDARY_ORDINAL:
        return float(_SECONDARY_ORDINAL[t])
    return None


def dynamic_level_ordinal_01(token: str | None) -> float | None:
    """Alias for tests / callers: symbolic ordinal for a single token."""
    return symbolic_dynamic_intensity(token)


def notated_dynamic_scale_export() -> dict[str, Any]:
    """JSON-friendly ladder: primary ordinals plus secondary token map."""
    return {
        "primary": dict(NOTATED_DYNAMIC_SYMBOLIC_ORDINAL),
        "secondary_aliases": dict(_SECONDARY_ORDINAL),
    }


def aggregate_notated_dynamics_for_window(
    active_events: list[dict[str, Any]],
    overlap_fn: Any,
    t_start: float,
    t_end: float,
) -> dict[str, Any]:
    """
    Overlap-weighted distribution of written ``dynamic_mark`` tokens plus hairpin flags.

    ``dynamic_intensity_ordinal`` is overlap-mass-weighted mean of symbolic ordinals.
    ``notated_dynamic_coherence`` = Σ p_d² over **notated** dynamic classes (unknown excluded).
    """
    level_mass: dict[str, float] = defaultdict(float)
    unknown_mass = 0.0
    total = 0.0
    ord_weighted = 0.0
    ord_mass = 0.0
    cresc = False
    dim = False

    for e in active_events:
        ol = float(overlap_fn(e, t_start, t_end))
        if ol <= 0.0:
            continue
        total += ol
        hp = str(e.get("hairpin") or "none")
        if hp == "crescendo":
            cresc = True
        if hp == "diminuendo":
            dim = True
        dm_raw = e.get("dynamic_mark")
        tok = parse_standard_dynamic_mark(str(dm_raw) if dm_raw is not None else "")
        if tok and symbolic_dynamic_intensity(tok) is not None:
            level_mass[tok] += ol
            o = symbolic_dynamic_intensity(tok)
            if o is not None:
                ord_weighted += float(o) * ol
                ord_mass += ol
        else:
            unknown_mass += ol

    if total <= 1e-15:
        return {
            "notated_dynamic_level_distribution": {},
            "notated_dynamic_coherence": float("nan"),
            "dominant_dynamic": None,
            "dominant_dynamics": [],
            "dominant_dynamic_tie": False,
            "dominant_dynamic_share": float("nan"),
            "dominant_dynamic_margin": float("nan"),
            "dynamic_intensity_ordinal": float("nan"),
            "dynamic_softness": float("nan"),
            "dynamic_coverage_status": "unavailable",
            "crescendo_active": False,
            "diminuendo_active": False,
            "dynamic_divergence_detected": False,
        }

    dist = {k: float(v) / total for k, v in level_mass.items()}
    if unknown_mass > 1e-12:
        dist["__unknown__"] = float(unknown_mass) / total

    known_tot = float(sum(level_mass.values()))
    coherence = float("nan")
    if known_tot > 1e-15:
        coherence = 0.0
        for v in level_mass.values():
            p = float(v) / known_tot
            coherence += p * p

    dist_for_dom = {k: float(v) for k, v in dist.items() if not str(k).startswith("__")}
    d_dyn = dominant_with_ties(dist_for_dom if dist_for_dom else dist)
    dom = str(d_dyn["dominant_primary"]) if d_dyn.get("dominant_primary") is not None else None

    dyn_int = float(ord_weighted / ord_mass) if ord_mass > 1e-15 else float("nan")
    dyn_soft = float(1.0 - dyn_int) if math.isfinite(dyn_int) else float("nan")

    # Two+ dynamic classes each carrying a non-trivial share of **total** overlap mass.
    divergence = False
    if len(level_mass) >= 2:
        masses_sorted = sorted((float(v) for v in level_mass.values()), reverse=True)
        nontrivial = sum(1 for m in masses_sorted if m / total >= 0.12)
        divergence = nontrivial >= 2

    known_frac = known_tot / total if total > 1e-15 else 0.0
    if known_tot <= 1e-15:
        cov = "unavailable"
    elif known_frac >= 0.72:
        cov = "explicit"
    elif known_frac >= 0.08:
        cov = "partial"
    else:
        cov = "unavailable"

    d_share = d_dyn["max_share"]
    d_margin = d_dyn["margin_to_second"]
    return {
        "notated_dynamic_level_distribution": dict(dist),
        "notated_dynamic_coherence": float(coherence) if math.isfinite(coherence) else float("nan"),
        "dominant_dynamic": dom,
        "dominant_dynamics": list(d_dyn["dominant_all"]),
        "dominant_dynamic_tie": bool(d_dyn["tie"]),
        "dominant_dynamic_share": float(d_share)
        if d_share is not None and math.isfinite(float(d_share))
        else float("nan"),
        "dominant_dynamic_margin": (
            float(d_margin) if d_margin is not None and math.isfinite(float(d_margin)) else float("nan")
        ),
        "dynamic_intensity_ordinal": float(dyn_int) if math.isfinite(dyn_int) else float("nan"),
        "dynamic_softness": float(dyn_soft) if math.isfinite(dyn_soft) else float("nan"),
        "dynamic_coverage_status": cov,
        "crescendo_active": bool(cresc),
        "diminuendo_active": bool(dim),
        "dynamic_divergence_detected": bool(divergence),
    }
