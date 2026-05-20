# H_timbral: clarinet-family refinement (symbolic)

> **Legacy / internal documentation** — clarinet refinements are part of the **timbral event pipeline** reused by **H_TI_core**.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

**Notation-based orchestration similarity**, not acoustic timbre. Applies when the taxonomy **family** is ``clarinets`` (``FAMILY_CLARINETS``).

## Blend order (instrument component)

1. Legacy set-based factor  
2. String pairwise blend  
3. Brass pairwise blend  
4. Flute-family pairwise blend  
5. **Clarinet-family** pairwise blend  

Each refinement step uses ``clarinet_overlap_mass / total_overlap_mass`` (same ``total_overlap_mass`` as other families: sounding-note overlap in quarter lengths within the window).

## Canonical subtypes (internal)

Part names map to distinct canonical instruments where possible:

- ``a clarinet``, ``b flat clarinet``, ``c clarinet``, ``e flat clarinet``, generic ``clarinet`` (ambiguous soprano), ``alto clarinet``, ``basset horn``, ``basset clarinet``, ``bass clarinet``, ``contrabass clarinet``.

``_normalize`` in ``instrument_taxonomy`` maps hyphens to spaces so ``B-flat Clarinet`` matches ``b flat clarinet`` keys.

## Subtype similarity

Symmetric table ``_SUBTYPE_SIM`` in ``clarinet_pairwise_timbral.py`` encodes e.g.:

- A + B-flat very high vs B-flat + E-flat much lower  
- B-flat + bass lower than A + B-flat  
- Bass + contrabass high vs B-flat + contrabass low  
- E-flat + bass among the weakest pairings  

## Register zones (sounding pitch)

For soprano-family indices (A, B-flat, C, E-flat, generic), **concert** ``pitch.ps`` uses fixed band splits:

- **chalumeau**: below MIDI 66  
- **clarion**: 66–79  
- **altissimo**: 80 and above  

Lower clarinets use three relative zones within each subtype’s practical MIDI span (``_CLAR_TESS_BOUNDS``). Same subtype: zone distance dominates with a small absolute-pitch smoothing term. Cross subtype: normalized height within each instrument’s span plus a secondary absolute term so subtype identity is not erased.

## Technique normalization

``clarinet_technique_from_note`` (``analyzers/clarinet_technique.py``) emits:

``ordinario``, ``light_vibrato``, ``flutter``, ``breathy``, ``slap``, ``multiphonic``, ``unknown``.

Heuristic scan of lyrics and ``TextExpression`` text. Missing markings → ``unknown`` (pairs moderately with ``ordinario`` in ``_TECH_MAT``).

## Pairwise aggregation

For unordered pairs of clarinet-family events:

`w_i w_j × (subtype × register × technique)`

with duration overlap weights, same pattern as flutes/brass.

## Limits

Scores without part-specific transposition names collapse to generic ``clarinet``. This is symbolic homogeneity only; it does not read transposing score spelling.
