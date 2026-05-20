# H_timbral: saxophone-family refinement (symbolic)

> **Legacy / internal documentation** — saxophone refinements are part of the **timbral event pipeline** reused by **H_TI_core**.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

**Notation-based orchestration similarity**, not acoustic timbre estimation. Applies when the taxonomy **family** is ``saxophones``.

## Blend order

After string, brass, flute, clarinet, and double-reed refinements, saxophone overlap mass blends toward ``pairwise_saxophone_homogeneity`` using the same mass-weighted rule as other families.

## Canonical subtypes

From ``instrument_taxonomy``: ``sopranino saxophone``, ``soprano saxophone``, ``alto saxophone``, ``tenor saxophone``, ``baritone saxophone``, ``bass saxophone``, and generic ``saxophone`` / ``sax`` → canonical ``saxophone`` mapped to an internal **generic** bucket (index 6) with moderate similarity to all typed saxes.

## Subtype similarity

Symmetric matrix ``_SUBTYPE_SIM`` in ``saxophone_pairwise_timbral.py`` encodes proximity along the size line (sopranino → bass): neighbors high, soprano–bass low, baritone–bass very high, alto–tenor higher than alto–baritone, etc.

## Tessitura

Sounding ``pitch.ps``. Per subtype, practical MIDI bounds define **four** relative zones (low / lower-middle / upper-middle / high). Same subtype: zone-distance decay plus a small absolute-pitch term. Cross subtype: normalized height within each instrument’s span plus a secondary absolute term so **alto middle + alto high** stays closer than **alto middle + baritone middle** when subtype similarity is lower.

## Technique normalization

``saxophone_technique_from_note`` → ``ordinario``, ``subtone``, ``growl``, ``flutter``, ``slap``, ``breathy``, ``overtone_special``, ``unknown``. Heuristic text scan; see module docstring.

## Pairwise aggregation

`w_i w_j × (subtype × tessitura × technique)` with duration overlap weights.

## Limits

Part names must resolve in the taxonomy; missing markings → ``unknown``.
