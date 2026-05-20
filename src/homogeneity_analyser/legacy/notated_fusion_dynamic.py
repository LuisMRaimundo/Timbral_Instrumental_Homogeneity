"""
Dynamic **coherence** for ``H_notated_fusion_potential_dynamic`` (notation-symbolic only).

Penalises **divergence** of dynamic level / hairpin process / salient accents across simultaneous
active events in a window — **not** absolute level (``mf`` is not less coherent than ``pp`` when all
share ``mf``), and **not** SPL.

``H_notated_fusion_potential_dynamic = H_base * dynamic_coherence ** weight_dynamic``.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np


def _herfindahl_from_masses(masses: dict[str, float]) -> float:
    """Concentration ``sum p_i^2`` on positive masses (0..1). Empty → 1.0."""
    tot = float(sum(max(0.0, float(v)) for v in masses.values()))
    if tot <= 1e-18:
        return 1.0
    s = 0.0
    for v in masses.values():
        p = max(0.0, float(v)) / tot
        s += p * p
    return float(np.clip(s, 0.0, 1.0))


def compute_dynamic_coherence_bundle(
    active_events: list[dict[str, Any]],
    t_start: float,
    t_end: float,
    *,
    h_base: float,
    weight_dynamic: float,
) -> dict[str, Any]:
    """
    Build diagnostics and ``H_notated_fusion_potential_dynamic`` from overlap-weighted score events.

    When there is no notated dynamic / hairpin / salient-accent signal in the window,
    ``dynamic_coverage_status`` is ``no_dynamic_evidence``, ``dynamic_coherence`` is ``1.0``, and the
    dynamic-adjusted scalar equals ``h_base``.
    """
    w_dyn = float(np.clip(float(weight_dynamic), 0.0, 1.0))
    hb = float(h_base)
    if not math.isfinite(hb):
        hb = 0.5
    hb = float(np.clip(hb, 0.0, 1.0))

    rows: list[tuple[float, str, str, bool]] = []
    for e in active_events:
        if not isinstance(e, dict):
            continue
        ol = max(0.0, min(float(e["end"]), t_end) - max(float(e["offset"]), t_start))
        if ol <= 1e-18:
            continue
        dm = str(e.get("dynamic_mark") or "").strip()
        hp = str(e.get("hairpin") or "none").strip().lower()
        if hp not in ("none", "crescendo", "diminuendo"):
            hp = "none"
        sal = bool(e.get("salient_articulation"))
        rows.append((float(ol), dm, hp, sal))

    total_mass = float(sum(r[0] for r in rows))
    if total_mass <= 1e-18:
        return neutral_dynamic_bundle(hb, w_dyn, reason="no_events")

    any_mark = any(r[1] for r in rows)
    any_hp = any(r[2] != "none" for r in rows)
    any_sal = any(r[3] for r in rows)
    has_signal = bool(any_mark or any_hp or any_sal)

    level_dist: dict[str, float] = defaultdict(float)
    hp_dist: dict[str, float] = defaultdict(float)
    accent_plain = 0.0
    accent_sal = 0.0
    for ol, dm, hp, sal in rows:
        hp_dist[hp] += ol
        if sal:
            accent_sal += ol
        else:
            accent_plain += ol
        if dm:
            level_dist[dm] += ol
        elif any_mark:
            # Others have explicit marks; missing mark on this event is a divergent bucket.
            level_dist["__absent__"] += ol

    if not has_signal:
        return neutral_dynamic_bundle(hb, w_dyn, reason="no_dynamic_evidence")

    # Level: only when at least one explicit mark exists; otherwise no level divergence axis.
    level_c = _herfindahl_from_masses(dict(level_dist)) if any_mark and level_dist else 1.0

    hairpin_c = _herfindahl_from_masses(dict(hp_dist))

    if accent_sal <= 1e-18 or accent_plain <= 1e-18:
        accent_c = 1.0
    else:
        accent_c = _herfindahl_from_masses({"plain": accent_plain, "salient": accent_sal})

    dyn_c = float(min(level_c, hairpin_c, accent_c))
    dyn_c = float(np.clip(dyn_c, 0.0, 1.0))
    h_dyn = float(np.clip(hb * (dyn_c**w_dyn), 0.0, 1.0))

    tot_hp = sum(hp_dist.values())
    cresc_active = bool((hp_dist.get("crescendo", 0.0) / tot_hp) > 1e-12) if tot_hp > 1e-18 else False
    dim_active = bool((hp_dist.get("diminuendo", 0.0) / tot_hp) > 1e-12) if tot_hp > 1e-18 else False
    div_detected = bool(dyn_c < 1.0 - 1e-9)

    def _norm(d: dict[str, float]) -> dict[str, float]:
        s = float(sum(d.values()))
        if s <= 1e-18:
            return {}
        return {k: float(v) / s for k, v in sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))}

    cov = "ok"
    ev_stat = "symbolic_dynamic_coherence_proxy"

    return {
        "dynamic_coherence": dyn_c,
        "dynamic_level_distribution": _norm(dict(level_dist)) if any_mark else {},
        "dynamic_process_distribution": _norm(dict(hp_dist)),
        "crescendo_active": cresc_active,
        "diminuendo_active": dim_active,
        "dynamic_divergence_detected": div_detected,
        "dynamic_coverage_status": cov,
        "dynamic_evidence_status": ev_stat,
        "H_notated_fusion_potential_dynamic": h_dyn,
        "weight_dynamic": w_dyn,
        "dynamic_level_coherence": level_c,
        "dynamic_hairpin_coherence": hairpin_c,
        "dynamic_accent_coherence": accent_c,
    }


def neutral_dynamic_bundle(h_base: float, weight_dynamic: float, *, reason: str) -> dict[str, Any]:
    """Neutral diagnostics (coherence 1.0) for empty windows or absent symbolic dynamic evidence."""
    return {
        "dynamic_coherence": 1.0,
        "dynamic_level_distribution": {},
        "dynamic_process_distribution": {},
        "crescendo_active": False,
        "diminuendo_active": False,
        "dynamic_divergence_detected": False,
        "dynamic_coverage_status": reason,
        "dynamic_evidence_status": "no_dynamic_evidence",
        "H_notated_fusion_potential_dynamic": float(np.clip(h_base, 0.0, 1.0)),
        "weight_dynamic": float(np.clip(weight_dynamic, 0.0, 1.0)),
        "dynamic_level_coherence": 1.0,
        "dynamic_hairpin_coherence": 1.0,
        "dynamic_accent_coherence": 1.0,
    }
