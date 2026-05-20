# H_timbral: flute-family refinement (symbolic)

> **Legacy / internal documentation** — flute refinements are part of the **timbral event pipeline** reused by **H_TI_core**.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

**Notation-only orchestration similarity**, not acoustic timbre. Applies when the taxonomy **family** is ``flutes`` (constant ``FAMILY_FLUTES`` in code).

## Blend order (instrument component)

1. Legacy set-based factor.  
2. **String** pairwise blend (mass-weighted).  
3. **Brass** pairwise blend.  
4. **Flute-family** pairwise blend.

Each step uses the same ``total_overlap_mass`` denominator (sounding-pitch overlap in quarter lengths within the analysis window).

## Subtype similarity

Orchestral core canonicals: **flute**, **alto flute**, **bass flute**, **piccolo**. Other flute-family instruments (fife, pan flute, shakuhachi, etc.) share an **other** bucket so they still participate without overstating proximity to piccolo.

Explicit symmetric table in ``flute_pairwise_timbral._SUBTYPE_SIM`` encodes:

- flute + alto flute **>** flute + bass flute **>** flute + piccolo  
- alto + bass **>** alto + piccolo  
- bass + piccolo remains among the **lowest** intra-family pairs  

## Tessitura

Per subtype, sounding ``pitch.ps`` is mapped to **quartile zones** within instrument-specific MIDI bounds, then combined like the brass model: strong agreement within the same subtype; across subtypes, **normalized height** within each subtype’s range plus a secondary absolute-pitch term so **flute high + flute mid** stays closer than **flute high + bass flute high** when subtype similarity is lower.

## Technique normalization

``flute_technique_from_note`` (``analyzers/flute_technique.py``) emits labels such as ``ordinario``, ``vibrato``, ``breathy``, ``flutter``, ``harmonic``, ``whistle``, ``air_keys``, ``unknown``. Keywords scan lyrics and ``TextExpression`` text; ``articulations.Harmonic`` maps to ``harmonic``. Coverage is heuristic.

## Pairwise aggregation

Same pattern as strings/brass: for unordered pairs of flute-family events,
`w_i w_j × (subtype × technique × tessitura)` with duration overlap weights.

## Limits

music21 pitches follow the parsed score. Missing directions → ``unknown``, which still pairs moderately with ``ordinario`` in the technique matrix.
