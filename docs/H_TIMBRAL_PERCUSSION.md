# H_timbral: percussion subsystem (symbolic, second generation)

> **Legacy / internal documentation** — percussion handling is part of the **timbral event pipeline** reused by **H_TI_core**.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

**Notation-based orchestration similarity**, not acoustic timbre estimation or audio analysis.

## Why a separate subsystem

Flat ``FAMILY_PERCUSSION`` + global pitch span cannot represent membranophones vs bar vs metal pitched vs plates vs small metals, or pitched vs unpitched behavior. The percussion path replaces **only** the within-window contribution blended by ``percussion_overlap_mass / total_overlap_mass``; the global ``register_component`` from pitch span is unchanged for the whole sonority.

## Ontology (`percussion_ontology.py`)

Each canonical taxonomy instrument maps to ``PercussionMeta``:

- **macro_class**: tuned membranophone (timpani), untuned membranophone, wooden-bar idiophone, metallic pitched idiophone, plate/shell metal, small high metal, misc small, generic.
- **material**, **pitch_status** (pitched / quasi_pitched / unpitched).
- **resonance** and **noise** ordinals (coarse proxies).
- **size_bin** (1–5) for unpitched **size / spectral-center** pairing instead of melodic tessitura.
- **tessitura_lo/hi** (MIDI, concert) where pitched or quasi with a practical range.

Generic ``percussion`` / unknown names → **GENERIC** meta with low confidence.

## Pairwise score (`percussion_pairwise_timbral.py`)

For each unordered pair of percussion events:

`instrument_similarity × pitch_status_similarity × technique_similarity × register_size_similarity × (weighted resonance) × (weighted noise)`

- **instrument_similarity**: explicit pair overrides (sorted keys) for critical orchestral cases, else same-macro default, else cross-macro matrix.
- **Pitched / quasi**: tessitura zones inside ``tessitura_lo/hi``.
- **Unpitched–unpitched**: ``size_bin`` + weak MIDI distance (not treated as scale steps).
- **Mixed pitched/unpitched**: conservative blended factor (~0.62 floor + decay).

## Technique (`percussion_technique.py`)

Heuristic labels include mallet hardness, sticks/brushes, snare on/off, damped/open, roll, bowed, vibraphone pedal hints, cymbal suspended/crash, rim. Missing text → ``unknown``.

## Limits

music21 exposes limited performance directions; many scores have no mallet or damping text. This remains **symbolic** homogeneity for scoring layout, not DAW-quality performance analysis.
