"""
Verified, bibliography-scoped **cross-family** timbral affinities for ``H_timbral``.

This is an additive layer on top of existing family-specific pairwise models. It does **not**
replace them and does **not** define a general cross-instrument similarity matrix.

Pairs that are already modeled inside another module contribute **zero** here (e.g. oboe
family vs bassoon family affinity lives in ``double_reed_pairwise_timbral``).

**Conditional relations** do not model audio transients; they use conservative
tessitura / MIDI pitch-space overlap proxies only (see project docs).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from homogeneity_analyser.acoustic_profiles.model_config import timbral_float
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OBOES,
    FAMILY_SAXOPHONES,
)

# Cap on the **additive** boost applied to the instrument component after family blends.
_MAX_ADDITIVE_CROSS_BOOST = timbral_float("cross_timbral_max_additive_boost")

# Base strengths (scaled by pair overlap weight); kept conservative vs within-family models.
_ST_TENOR_SAX_CLARINET = timbral_float("cross_timbral_strength_tenor_sax_clarinet")
_ST_ALTO_SAX_HORN = timbral_float("cross_timbral_strength_alto_sax_horn")
_ST_TRUMPET_OBOE = timbral_float("cross_timbral_strength_trumpet_oboe")
_ST_BASS_CLAR_BASSOON = timbral_float("cross_timbral_strength_bass_clarinet_bassoon")
_ST_HORN_BASSOON = timbral_float("cross_timbral_strength_horn_bassoon")
_ST_HIGH_CLAR_FLUTE = timbral_float("cross_timbral_strength_high_clarinet_flute")
_ST_NATURAL_HORN_TRUMPET = timbral_float("cross_timbral_strength_natural_horn_trumpet")

# Soprano-line clarinets allowed for narrow cross-family rules (excludes bass, alto, basset, etc.).
_SOPRANO_CLARINET_FOR_CROSS: frozenset[str] = frozenset({"clarinet", "b flat clarinet", "a clarinet", "c clarinet"})

_CT_TSAX_LO = timbral_float("cross_timbral_tenor_sax_ps_low")
_CT_TSAX_HI = timbral_float("cross_timbral_tenor_sax_ps_high")
_CT_SCL_LO = timbral_float("cross_timbral_soprano_clarinet_ps_low")
_CT_SCL_HI = timbral_float("cross_timbral_soprano_clarinet_ps_high")
_CT_TSAX_CLAR_ABS = timbral_float("cross_timbral_tenor_sax_clarinet_abs_ps_max")
_CT_ASAX_LO = timbral_float("cross_timbral_alto_sax_ps_low")
_CT_ASAX_HI = timbral_float("cross_timbral_alto_sax_ps_high")
_CT_HORN_LO = timbral_float("cross_timbral_horn_ps_low")
_CT_HORN_HI = timbral_float("cross_timbral_horn_ps_high")
_CT_ASAX_HORN_ABS = timbral_float("cross_timbral_alto_sax_horn_abs_ps_max")
_CT_TRP_LO = timbral_float("cross_timbral_trumpet_ps_low")
_CT_TRP_HI = timbral_float("cross_timbral_trumpet_ps_high")
_CT_OBOE_LO = timbral_float("cross_timbral_oboe_ps_low")
_CT_OBOE_HI = timbral_float("cross_timbral_oboe_ps_high")
_CT_TRP_OBOE_ABS = timbral_float("cross_timbral_trumpet_oboe_abs_ps_max")
_CT_NH_LO = timbral_float("cross_timbral_natural_horn_ps_low")
_CT_NH_HI = timbral_float("cross_timbral_natural_horn_ps_high")
_CT_TRP_PAIR_LO = timbral_float("cross_timbral_trumpet_pair_ps_low")
_CT_TRP_PAIR_HI = timbral_float("cross_timbral_trumpet_pair_ps_high")
_CT_NH_TRP_ABS = timbral_float("cross_timbral_natural_horn_trumpet_abs_ps_max")
_CT_HICLAR_MIN = timbral_float("cross_timbral_high_clarinet_ps_min")
_CT_FLUTE_MIN = timbral_float("cross_timbral_flute_ps_min")
_CT_HICL_FL_ABS = timbral_float("cross_timbral_high_clar_flute_abs_ps_max")


@dataclass(frozen=True)
class VerifiedCrossTimbralRelation:
    """Audit metadata for one authorized relation (not all rows imply a runtime boost here)."""

    source_relation_key: str
    instruments_or_clusters_involved: str
    relation_strength: str
    evidence_status: str  # directly_attested | bibliographically_derived
    condition_type: str  # unconditional | conditional
    documentation_note: str


VERIFIED_CROSS_TIMBRAL_REGISTRY: tuple[VerifiedCrossTimbralRelation, ...] = (
    VerifiedCrossTimbralRelation(
        source_relation_key="double_reed_oboe_bassoon_macro_cluster",
        instruments_or_clusters_involved="oboes family ↔ bassoons family (distinct families)",
        relation_strength="primary model in double_reed_pairwise_timbral (not duplicated here)",
        evidence_status="directly_attested",
        condition_type="unconditional",
        documentation_note=(
            "Cross-family double-reed affinity is implemented in ``double_reed_pairwise_timbral``; "
            "this registry entry documents the attested relation. The cross-relations scorer "
            "skips oboe↔bassoon pairs to avoid double counting."
        ),
    ),
    VerifiedCrossTimbralRelation(
        source_relation_key="tenor_saxophone_clarinet",
        instruments_or_clusters_involved="tenor saxophone ↔ soprano-line clarinets (not all saxophones)",
        relation_strength=f"bounded additive (base {_ST_TENOR_SAX_CLARINET:.3f} × overlap weight)",
        evidence_status="directly_attested",
        condition_type="conditional",
        documentation_note=(
            "Canonical ``tenor saxophone`` plus only ``clarinet``, ``b flat clarinet``, ``a clarinet``, "
            "``c clarinet``; tessitura overlap in concert MIDI ps. No general saxophone↔clarinet rule."
        ),
    ),
    VerifiedCrossTimbralRelation(
        source_relation_key="alto_saxophone_french_horn",
        instruments_or_clusters_involved="alto saxophone ↔ horn (French horn maps to canonical ``horn``)",
        relation_strength=f"bounded additive (base {_ST_ALTO_SAX_HORN:.3f} × overlap weight)",
        evidence_status="directly_attested",
        condition_type="conditional",
        documentation_note=(
            "Narrow subtype match: ``alto saxophone`` + ``horn`` only, with tessitura overlap. "
            "Does not extend to other saxophones or brass by default."
        ),
    ),
    VerifiedCrossTimbralRelation(
        source_relation_key="trumpet_oboe",
        instruments_or_clusters_involved="trumpet ↔ oboe (canonical ``oboe`` only)",
        relation_strength=f"bounded additive (base {_ST_TRUMPET_OBOE:.3f} × overlap weight)",
        evidence_status="directly_attested",
        condition_type="conditional",
        documentation_note=(
            "Conservative tessitura gate; weaker than close within-family refinements. "
            "No general brass↔double-reed rule."
        ),
    ),
    VerifiedCrossTimbralRelation(
        source_relation_key="natural_horn_cor_de_chasse_trumpet_bass_trumpet",
        instruments_or_clusters_involved=(
            "canonical ``natural horn`` (incl. cor de chasse label) ↔ trumpet / bass trumpet"
        ),
        relation_strength=f"bounded additive (base {_ST_NATURAL_HORN_TRUMPET:.3f} × overlap weight)",
        evidence_status="directly_attested",
        condition_type="conditional",
        documentation_note=(
            "Canonical **natural horn** only (score labels natural horn / cor de chasse / hunting horn); "
            "paired with ``trumpet`` or ``bass trumpet``. ``french horn`` / ``horn`` (valve horn) excluded. "
            "Does **not** broaden general horn↔trumpet similarity in the brass pairwise layer."
        ),
    ),
    VerifiedCrossTimbralRelation(
        source_relation_key="bass_clarinet_bassoon",
        instruments_or_clusters_involved="bass clarinet ↔ bassoon",
        relation_strength=f"bounded additive (base {_ST_BASS_CLAR_BASSOON:.3f} × overlap weight)",
        evidence_status="bibliographically_derived",
        condition_type="unconditional",
        documentation_note="Low/dark reed pairing only; not extended to all clarinets↔bassoons.",
    ),
    VerifiedCrossTimbralRelation(
        source_relation_key="horn_bassoon",
        instruments_or_clusters_involved="horn ↔ bassoon",
        relation_strength=f"bounded additive (base {_ST_HORN_BASSOON:.3f} × overlap weight)",
        evidence_status="bibliographically_derived",
        condition_type="unconditional",
        documentation_note="Moderate affinity; not a general brass↔bassoon rule.",
    ),
    VerifiedCrossTimbralRelation(
        source_relation_key="high_register_clarinet_flute",
        instruments_or_clusters_involved="clarinet family ↔ flute family (high clarinet register only)",
        relation_strength=f"bounded additive (base {_ST_HIGH_CLAR_FLUTE:.3f} × overlap weight)",
        evidence_status="bibliographically_derived",
        condition_type="conditional",
        documentation_note=(
            "Clarinet side restricted to soprano-line canonicals "
            "``clarinet`` / ``b flat clarinet`` / ``a clarinet`` / ``c clarinet`` only "
            "(not bass, e-flat, basset, etc.). "
            "Concert MIDI high band + flute tessitura gate; weaker than clarinet-family internal models."
        ),
    ),
)


def _pair_overlap_weight(wa: float, wb: float, total_mass: float) -> float:
    if total_mass <= 0.0:
        return 0.0
    wa = max(float(wa), 0.0)
    wb = max(float(wb), 0.0)
    geom = math.sqrt(wa * wb)
    return float(min(1.0, geom / total_mass))


def _double_reed_oboe_bassoon_pair(fa: str, fb: str) -> bool:
    return (fa == FAMILY_OBOES and fb == FAMILY_BASSOONS) or (fa == FAMILY_BASSOONS and fb == FAMILY_OBOES)


def _tenor_sax_clarinet_strength(
    inst_a: str,
    fam_a: str,
    ps_a: float,
    inst_b: str,
    fam_b: str,
    ps_b: float,
) -> float:
    if fam_a == FAMILY_SAXOPHONES and inst_a == "tenor saxophone" and fam_b == FAMILY_CLARINETS:
        ps_sax, ps_cl = ps_a, ps_b
        inst_cl = inst_b
    elif fam_b == FAMILY_SAXOPHONES and inst_b == "tenor saxophone" and fam_a == FAMILY_CLARINETS:
        ps_sax, ps_cl = ps_b, ps_a
        inst_cl = inst_a
    else:
        return 0.0
    if inst_cl not in _SOPRANO_CLARINET_FOR_CROSS:
        return 0.0
    # Tessitura overlap: both in a mid “speaking” band (conservative spectral overlap proxy).
    if not (_CT_TSAX_LO <= ps_sax <= _CT_TSAX_HI and _CT_SCL_LO <= ps_cl <= _CT_SCL_HI):
        return 0.0
    if abs(ps_sax - ps_cl) > _CT_TSAX_CLAR_ABS:
        return 0.0
    return _ST_TENOR_SAX_CLARINET


def _alto_sax_horn_strength(
    inst_a: str,
    fam_a: str,
    ps_a: float,
    inst_b: str,
    fam_b: str,
    ps_b: float,
) -> float:
    if fam_a == FAMILY_SAXOPHONES and inst_a == "alto saxophone" and fam_b == FAMILY_BRASS and inst_b == "horn":
        ps_s, ps_h = ps_a, ps_b
    elif fam_b == FAMILY_SAXOPHONES and inst_b == "alto saxophone" and fam_a == FAMILY_BRASS and inst_a == "horn":
        ps_s, ps_h = ps_b, ps_a
    else:
        return 0.0
    if not (_CT_ASAX_LO <= ps_s <= _CT_ASAX_HI and _CT_HORN_LO <= ps_h <= _CT_HORN_HI):
        return 0.0
    if abs(ps_s - ps_h) > _CT_ASAX_HORN_ABS:
        return 0.0
    return _ST_ALTO_SAX_HORN


def _trumpet_oboe_strength(
    inst_a: str,
    fam_a: str,
    ps_a: float,
    inst_b: str,
    fam_b: str,
    ps_b: float,
) -> float:
    if fam_a == FAMILY_BRASS and inst_a == "trumpet" and fam_b == FAMILY_OBOES and inst_b == "oboe":
        ps_t, ps_o = ps_a, ps_b
    elif fam_b == FAMILY_BRASS and inst_b == "trumpet" and fam_a == FAMILY_OBOES and inst_a == "oboe":
        ps_t, ps_o = ps_b, ps_a
    else:
        return 0.0
    if not (_CT_TRP_LO <= ps_t <= _CT_TRP_HI and _CT_OBOE_LO <= ps_o <= _CT_OBOE_HI):
        return 0.0
    if abs(ps_t - ps_o) > _CT_TRP_OBOE_ABS:
        return 0.0
    return _ST_TRUMPET_OBOE


def _bass_clarinet_bassoon_strength(
    inst_a: str,
    fam_a: str,
    inst_b: str,
    fam_b: str,
) -> float:
    if fam_a == FAMILY_CLARINETS and inst_a == "bass clarinet" and fam_b == FAMILY_BASSOONS and inst_b == "bassoon":
        return _ST_BASS_CLAR_BASSOON
    if fam_b == FAMILY_CLARINETS and inst_b == "bass clarinet" and fam_a == FAMILY_BASSOONS and inst_a == "bassoon":
        return _ST_BASS_CLAR_BASSOON
    return 0.0


def _natural_horn_trumpet_strength(
    inst_a: str,
    fam_a: str,
    ps_a: float,
    inst_b: str,
    fam_b: str,
    ps_b: float,
) -> float:
    if fam_a != FAMILY_BRASS or fam_b != FAMILY_BRASS:
        return 0.0
    nh = "natural horn"
    tr_ok = frozenset({"trumpet", "bass trumpet"})
    if inst_a == nh and inst_b in tr_ok:
        ps_n, ps_t = ps_a, ps_b
    elif inst_b == nh and inst_a in tr_ok:
        ps_n, ps_t = ps_b, ps_a
    else:
        return 0.0
    if not (_CT_NH_LO <= ps_n <= _CT_NH_HI and _CT_TRP_PAIR_LO <= ps_t <= _CT_TRP_PAIR_HI):
        return 0.0
    if abs(ps_n - ps_t) > _CT_NH_TRP_ABS:
        return 0.0
    return _ST_NATURAL_HORN_TRUMPET


def _horn_bassoon_strength(
    inst_a: str,
    fam_a: str,
    inst_b: str,
    fam_b: str,
) -> float:
    if fam_a == FAMILY_BRASS and inst_a == "horn" and fam_b == FAMILY_BASSOONS and inst_b == "bassoon":
        return _ST_HORN_BASSOON
    if fam_b == FAMILY_BRASS and inst_b == "horn" and fam_a == FAMILY_BASSOONS and inst_a == "bassoon":
        return _ST_HORN_BASSOON
    return 0.0


def _high_clarinet_flute_strength(
    inst_a: str,
    fam_a: str,
    ps_a: float,
    inst_b: str,
    fam_b: str,
    ps_b: float,
) -> float:
    if fam_a == FAMILY_CLARINETS and fam_b == FAMILY_FLUTES:
        inst_c, ps_c, ps_f = inst_a, ps_a, ps_b
    elif fam_b == FAMILY_CLARINETS and fam_a == FAMILY_FLUTES:
        inst_c, ps_c, ps_f = inst_b, ps_b, ps_a
    else:
        return 0.0
    if inst_c not in _SOPRANO_CLARINET_FOR_CROSS:
        return 0.0
    # High clarinet register (concert MIDI); flute in upper-middle so the boost is not global.
    if ps_c < _CT_HICLAR_MIN:
        return 0.0
    if ps_f < _CT_FLUTE_MIN:
        return 0.0
    if abs(ps_c - ps_f) > _CT_HICL_FL_ABS:
        return 0.0
    return _ST_HIGH_CLAR_FLUTE


def _pair_authorized_strength(
    inst_a: str,
    fam_a: str,
    ps_a: float,
    inst_b: str,
    fam_b: str,
    ps_b: float,
) -> float:
    """Max base strength among authorized cross-family rules for one unordered instrument pair."""
    if fam_a == fam_b:
        # Same family: normally no cross boost; narrow exception for historical natural horn + trumpet.
        if fam_a == FAMILY_BRASS:
            nh = _natural_horn_trumpet_strength(inst_a, fam_a, ps_a, inst_b, fam_b, ps_b)
            if nh > 0.0:
                return nh
        return 0.0
    if _double_reed_oboe_bassoon_pair(fam_a, fam_b):
        return 0.0
    candidates = (
        _tenor_sax_clarinet_strength(inst_a, fam_a, ps_a, inst_b, fam_b, ps_b),
        _alto_sax_horn_strength(inst_a, fam_a, ps_a, inst_b, fam_b, ps_b),
        _trumpet_oboe_strength(inst_a, fam_a, ps_a, inst_b, fam_b, ps_b),
        _bass_clarinet_bassoon_strength(inst_a, fam_a, inst_b, fam_b),
        _horn_bassoon_strength(inst_a, fam_a, inst_b, fam_b),
        _high_clarinet_flute_strength(inst_a, fam_a, ps_a, inst_b, fam_b, ps_b),
    )
    return float(max(candidates))


def verified_cross_timbral_boost(
    timbral_note_slices: list[dict[str, Any]] | None,
    total_overlap_mass: float,
) -> float:
    """
    Return a small non-negative additive boost for the timbral instrument component.

    ``timbral_note_slices`` items: ``instrument``, ``family``, ``pitch`` (MIDI ps), ``overlap_ql``.
    """
    if not timbral_note_slices:
        return 0.0
    tm = float(total_overlap_mass)
    if tm <= 0.0:
        return 0.0
    slices = timbral_note_slices
    n = len(slices)
    acc = 0.0
    for i in range(n):
        ai = slices[i]
        ia = str(ai.get("instrument", ""))
        fa = str(ai.get("family", ""))
        wa = float(ai.get("overlap_ql", 0.0) or 0.0)
        ps_a = float(ai.get("pitch", 0.0) or 0.0)
        if wa <= 0.0:
            continue
        for j in range(i + 1, n):
            aj = slices[j]
            ib = str(aj.get("instrument", ""))
            fb = str(aj.get("family", ""))
            wb = float(aj.get("overlap_ql", 0.0) or 0.0)
            ps_b = float(aj.get("pitch", 0.0) or 0.0)
            if wb <= 0.0:
                continue
            base = _pair_authorized_strength(ia, fa, ps_a, ib, fb, ps_b)
            if base <= 0.0:
                continue
            acc += base * _pair_overlap_weight(wa, wb, tm)
    return float(min(_MAX_ADDITIVE_CROSS_BOOST, acc))
