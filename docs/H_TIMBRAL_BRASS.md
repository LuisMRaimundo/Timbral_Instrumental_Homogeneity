# H_timbral: brass refinement (symbolic)

> **Legacy / internal documentation** — **H_TI_core** reuses this symbolic refinement via the shared timbral event pipeline. Not a standalone Gradio product.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

**Notation-only orchestration similarity**, not acoustic timbre. Applies to parts whose taxonomy **family** is ``brass``. The global register-span term in H_timbral is unchanged; only the **instrument component** is refined when brass overlap mass is positive.

## Taxonomy

``bass trombone`` is a **canonical instrument distinct from** ``trombone`` (scores labelled “Bass Trombone” map to ``bass trombone``). Other tenor/alto/soprano trombones remain ``trombone``.

## Blend order

1. Legacy set-based instrument factor (unchanged).
2. **String** pairwise blend (if string mass > 0), using ``total_overlap_mass``.
3. **Brass** pairwise blend on the result of step 2 (if brass mass > 0), using the same denominator.

Mixed families: mass ratio ``f = brass_overlap_mass / total_overlap_mass`` pulls toward the brass pairwise score conservatively.

## Section similarity (pairwise)

Five buckets: **trumpet-like** (trumpet, cornet, flugelhorn, mellophone, bugle, cornett), **horn-like** (horn, Wagner tuba, alphorn), **trombone**, **bass trombone**, **tuba-like** (tuba, euphonium, cimbasso, sousaphone, serpent, ophicleide, …). A fixed symmetric table encodes orchestral distance (e.g. trombone–bass trombone closer than trumpet–trombone). Rare brass canonicals default to the **trombone** bucket for similarity.

## Tessitura / register term (pairwise)

Per bucket, sounding MIDI ``pitch.ps`` is mapped to **quartile zones** within instrument-specific bounds, then:

- **Same bucket:** zone distance (adjacent zones stay fairly high) plus a small same-bucket pitch decay.
- **Different buckets:** alignment of **normalized height** within each bucket’s range, plus absolute pitch proximity (secondary).

This keeps **trumpet high + trumpet mid** closer than **trumpet high + trombone high** when section similarity is lower.

## Technique / mute normalization

``brass_technique_from_note`` (``analyzers/brass_technique.py``) returns labels such as ``open``, ``straight_mute``, ``cup_mute``, ``harmon_mute``, ``bucket_mute``, ``stopped`` (horn-style `Stopped` articulation on brass), ``flutter``, ``muted_generic``, ``unknown``. Keywords scan lyrics and ``TextExpression`` text (e.g. “con sord.”, “Harmon”, “flutter”). Coverage is heuristic; missing markup yields ``unknown``, which still pairs moderately with ``open`` in the technique matrix.

## Pairwise aggregation

Same weighting pattern as strings: for unordered pairs of brass sounding events,
`w_i w_j × (section × register × technique)`, normalized over active pairs.

## Limits

music21 pitches follow the parsed score (concert vs written depends on encoding). Mute text is often absent; do not treat symbolic H_timbral as performance truth.
