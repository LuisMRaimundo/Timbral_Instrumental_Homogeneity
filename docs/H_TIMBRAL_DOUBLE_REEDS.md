# H_timbral: double-reed refinement (symbolic)

> **Legacy / internal documentation** — double-reed refinements are part of the **timbral event pipeline** reused by **H_TI_core**.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

**Notation-based orchestration similarity**, not acoustic timbre estimation.

## Taxonomy vs macro-cluster

The taxonomy still uses two separate families: ``FAMILY_OBOES`` and ``FAMILY_BASSOONS`` (e.g. same-family bonus unchanged). The timbral **pairwise** layer adds a **double-reed macro-cluster**: a single similarity matrix over canonical oboe-side and bassoon-side instruments so oboe + bassoon is graded **between** pure same-family pairs and unrelated woodwinds.

## Blend order (instrument component)

After string, brass, flute, and clarinet refinements, **double-reed** overlap mass blends toward ``pairwise_double_reed_homogeneity`` using the same mass-weighted rule as other refinements.

## Instrument similarity table

Canonical names from ``instrument_taxonomy`` map to bucket indices (oboe, cor anglais, oboe d’amore, oboe da caccia, bass oboe, other oboe-family, bassoon, contrabassoon, other bassoon-family). The symmetric matrix in ``double_reed_pairwise_timbral._SUBTYPE_SIM`` encodes:

- high oboe-family internal affinity (e.g. oboe + cor anglais);  
- high bassoon + contrabassoon;  
- moderate **cross-family** oboe-side ↔ bassoon-side (double-reed affinity);  
- oboe + contrabassoon weaker than oboe + bassoon.

## Register

Sounding ``pitch.ps``. Three relative zones per instrument bucket within practical MIDI spans; same subtype prefers same zone, with distance decay and a small absolute-pitch term.

## Technique (secondary)

``double_reed_technique_from_note`` → ``ordinario``, ``flutter``, ``multiphonic``, ``breathy``, ``unknown``. Light keyword scan of lyrics/expressions.

## Cross-cluster diagnostic score

``double_reed_pair_score`` supports tests comparing double-reed pairs to flute/clarinet stubs (low instrument factor × pitch distance × technique).

## Limits

Part names must hit the taxonomy; ethnic doubles are bucketed coarsely. No acoustic analysis.
