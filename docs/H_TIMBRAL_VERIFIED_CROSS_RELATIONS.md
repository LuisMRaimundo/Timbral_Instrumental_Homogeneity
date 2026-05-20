# Verified cross-instrument timbral relations (`H_timbral`)

> **Legacy / internal documentation** — cross-family boosts live in the **timbral event pipeline** reused by **H_TI_core**; not a standalone user-facing tab.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

This document describes a **restricted, auditable layer** of cross-family affinities applied **after** the existing family-specific pairwise refinements in `TimbralHomogeneityAnalyzer.compute_H_timbral`. It is **not** a full inter-instrument timbral map and **not** a matrix of heuristic orchestration lore.

Implementation: `homogeneity_analyser.analyzers.timbre_cross_relations` (registry + `verified_cross_timbral_boost`). Integration: `homogeneity_analyser.analyzers.timbral` (additive clip on the instrument component). Per-window note slices: `timbral_note_slices` on the timbral feature dict (canonical instrument, taxonomy family, MIDI `pitch`, `overlap_ql`).

**Pitch on slices:** ``pitch`` is **concert (sounding) MIDI**, consistent with ``timbral_sounding_pitch`` (see ``docs/H_TIMBRAL_SCORE_REPRESENTATION.md``).

## Methodological status tags

| Tag | Meaning |
|-----|---------|
| `directly_attested` | Explicitly listed in the project’s reviewed bibliography scope for this layer. |
| `bibliographically_derived` | Derived in a conservative way from that same bibliography; still narrow and explicit. |
| `conditional` | Strength is reduced to **zero** unless register / tessitura proxies encoded below are satisfied. |
| `unconditional` | Small constant relation strength subject only to overlap weighting and a global cap. |

**Limits of the current signal:** there is **no** audio analysis, **no** transient envelope model, and **no** separate “attack” channel. “Conditional” rules therefore use **register / tessitura overlap** (MIDI pitch space and simple proximity gates) as the only robust proxies available in this pipeline. Where a condition cannot be represented faithfully, the code applies **no** boost rather than inventing a hidden cue.

## Relation list (authorized only)

### A — Double-reed macro-cluster (oboe family ↔ bassoon family)

| Field | Value |
|-------|--------|
| Evidence | `directly_attested` |
| Condition | `unconditional` (within the double-reed subsystem) |
| Runtime in this layer | **No additive boost** — cross-family oboe↔bassoon affinity is implemented in `double_reed_pairwise_timbral.py` to avoid double counting. This document + `VERIFIED_CROSS_TIMBRAL_REGISTRY` record the attested relation. |
| Comparative consequence | Oboe+bassoon scoring vs oboe+flute / oboe+clarinet remains guaranteed by the double-reed pair model and tests. |

### B — Tenor saxophone ↔ clarinet (narrow)

| Field | Value |
|-------|--------|
| Evidence | `directly_attested` |
| Condition | `conditional` — canonical `tenor saxophone` only; clarinet side **excludes** bass / contrabass / alto clarinet; tessitura overlap gates on MIDI ps. |
| Not implemented | Any general “saxophones ↔ woodwinds” or “all saxophones ↔ all clarinets” rule. |

### C — Alto saxophone ↔ French horn (narrow)

| Field | Value |
|-------|--------|
| Evidence | `directly_attested` |
| Condition | `conditional` — canonical `alto saxophone` + canonical `horn` (score label “French horn” maps to `horn`) with tessitura overlap. |
| Not implemented | Alto saxophone ↔ trumpet or other brass except where other subsystems already apply. |

### D — Trumpet ↔ oboe (narrow)

| Field | Value |
|-------|--------|
| Evidence | `directly_attested` |
| Condition | `conditional` — canonical `trumpet` + canonical `oboe` only (not cor anglais / musette, etc.); tessitura gates. |
| Strength policy | Remains a **small** additive bump; weaker than close same-family / same-section refinements. |

### E — Natural / cor de chasse horn ↔ trumpet / bass trumpet

| Field | Value |
|-------|--------|
| Evidence | `directly_attested` (bibliography) |
| Implementation | **Implemented** for canonical ``natural horn`` (score labels ``natural horn``, ``cor de chasse``, ``hunting horn``) with ``trumpet`` or ``bass trumpet`` only. **Excluded:** canonical ``horn`` (French / valve horn) so general horn↔trumpet similarity is not widened. (Same ``brass`` family: handled as the sole same-family exception in ``_pair_authorized_strength``.) |
| Condition | `conditional` — tessitura overlap in concert MIDI ps (no transient model). |

### F — Bass clarinet ↔ bassoon

| Field | Value |
|-------|--------|
| Evidence | `bibliographically_derived` |
| Condition | `unconditional` (still overlap-weighted and globally capped). |
| Not implemented | General clarinet ↔ bassoon shortcut. |

### G — Horn ↔ bassoon

| Field | Value |
|-------|--------|
| Evidence | `bibliographically_derived` |
| Condition | `unconditional` (overlap-weighted, capped). |
| Not implemented | General brass ↔ bassoon shortcut. |

### H — High-register clarinet ↔ flute

| Field | Value |
|-------|--------|
| Evidence | `bibliographically_derived` |
| Clarinet-side scope | **Only** canonical ``clarinet``, ``b flat clarinet``, ``a clarinet``, ``c clarinet``. Excludes bass / contrabass / alto / e-flat / basset family members. |
| Condition | `conditional` — clarinet-side concert MIDI ps in a **high** band; flute side gated to upper-middle register; pitch proximity cap. |
| Strength policy | Deliberately **weaker** than the dedicated clarinet-family pairwise path when clarinets dominate a window. |

### I — Oboe ↔ bassoon vs oboe ↔ flute / oboe ↔ clarinet

| Field | Value |
|-------|--------|
| Evidence | Emerges from **A** (`double_reed_pairwise_timbral`); comparative ordering is regression-tested. |
| This layer | Does not add a second oboe↔bassoon bump. |

## Global cap

All implemented boosts from `verified_cross_timbral_boost` are summed then **clipped** by a small maximum before being added to the post-blend instrument component, so the cross layer stays modulatory.
