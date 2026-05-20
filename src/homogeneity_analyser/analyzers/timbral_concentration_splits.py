"""
Overlap-weighted **concentration splits** for timbral / orchestration diagnostics.

Separates **instrument** mass, **family** mass, **full ``technique_state_id``** mass (legacy-style),
and **technique-only** mass (instrument-agnostic playing state) so symbolic modes can apply
technique penalties only when playing technique genuinely differs — e.g. clarinet vs bass
clarinet both *ordinario* should not be split on the technique axis merely because canonical
instrument names differ in the composite id.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def herfindahl_concentration(masses: dict[str, float]) -> float:
    """``sum_i (m_i / sum m)^2`` for nonnegative masses; empty or zero total → ``0.5``."""
    tot = sum(max(0.0, float(v)) for v in masses.values())
    if tot <= 1e-15:
        return 0.5
    h = 0.0
    for m in masses.values():
        p = max(0.0, float(m)) / tot
        h += p * p
    return float(min(1.0, max(0.0, h)))


def technique_only_distribution_key(technique_state_id: str, canonical_instrument: str) -> str:
    """
    Map ``(technique_state_id, instrument)`` to a **technique-only** bucket.

    Rules (v1):
    - ``technique_state_id`` is normally ``instrument|…`` (see ``technique_state_id()``). When the
      first ``|`` segment matches ``canonical_instrument`` (case-insensitive), the remainder is
      the technique-only key (e.g. ``violin|arco|sul_pont`` → ``arco|sul_pont``, ``horn|stopped``
      → ``stopped``).
    - A **single** segment equal to the instrument name means no encoded technique variation →
      ``__ordinary__``.
    - A **single** segment that is **not** the instrument name is treated as a shorthand
      technique label (tests and compact ids), e.g. ``stopped`` under instrument ``Horn``.
    - Empty id → ``__ordinary__``.
    """
    tid = (technique_state_id or "").strip()
    inst = (canonical_instrument or "").strip()
    if not tid:
        return "__ordinary__"
    parts = [p.strip() for p in tid.split("|") if p.strip()]
    if not parts:
        return "__ordinary__"
    if len(parts) == 1:
        if parts[0].lower() == inst.lower():
            return "__ordinary__"
        return parts[0]
    if parts[0].lower() == inst.lower():
        tail = "|".join(parts[1:])
        return tail if tail else "__ordinary__"
    # Defensive: unexpected shape — keep full id so we do not silently merge distinct states.
    return tid


def concentration_bundle_from_timbral_slices(slices: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Build overlap mass distributions and Herfindahl concentrations from ``timbral_note_slices``.

    Returns JSON-friendly floats and normalized distribution dicts (stable sort).
    """
    inst_m: dict[str, float] = defaultdict(float)
    fam_m: dict[str, float] = defaultdict(float)
    full_tech_m: dict[str, float] = defaultdict(float)
    tech_only_m: dict[str, float] = defaultdict(float)

    for s in slices:
        if not isinstance(s, dict):
            continue
        ol = float(s.get("overlap_ql", 0.0) or 0.0)
        if ol <= 0.0:
            continue
        inst = str(s.get("instrument") or "")
        fam = str(s.get("family") or "")
        inst_m[inst] += ol
        fam_m[fam] += ol
        tid = str(s.get("technique_state_id") or "")
        full_key = tid if tid else "__none__"
        full_tech_m[full_key] += ol
        to_key = technique_only_distribution_key(tid, inst)
        tech_only_m[to_key] += ol

    def _norm_dist(m: dict[str, float], tot: float) -> dict[str, float]:
        if tot <= 1e-15:
            return {}
        return {k: float(v) / tot for k, v in sorted(m.items(), key=lambda kv: (-kv[1], kv[0]))}

    tot_i = sum(inst_m.values())
    tot_f = sum(fam_m.values())
    tot_ft = sum(full_tech_m.values())
    tot_to = sum(tech_only_m.values())

    hi = herfindahl_concentration(dict(inst_m))
    hf = herfindahl_concentration(dict(fam_m))
    h_full = herfindahl_concentration(dict(full_tech_m))
    h_only = herfindahl_concentration(dict(tech_only_m))

    return {
        "instrument_distribution": _norm_dist(dict(inst_m), tot_i),
        "family_distribution": _norm_dist(dict(fam_m), tot_f),
        "technique_state_distribution_full": _norm_dist(dict(full_tech_m), tot_ft),
        "technique_only_distribution": _norm_dist(dict(tech_only_m), tot_to),
        "instrument_distribution_concentration": float(hi),
        "family_distribution_concentration": float(hf),
        "full_state_concentration": float(h_full),
        "technique_only_concentration": float(h_only),
    }
