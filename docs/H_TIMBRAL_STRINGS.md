# H_timbral: bowed orchestral string refinement (symbolic)

> **Legacy / internal documentation** — **H_TI_core** reuses this symbolic refinement via the shared timbral event pipeline. Not a standalone Gradio product.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

**Notation-only orchestration similarity**, not acoustic timbre. Applies only to the four **bowed orchestral** canonical instruments: ``violin``, ``viola``, ``cello``, ``double bass``. Harp, guitar, mandolin, viola da gamba, and other ``FAMILY_STRINGS`` members **do not** use this pairwise path; they remain on the **legacy** timbral instrument component.

**Implementation:** ``homogeneity_analyser.analyzers.string_pairwise_timbral``.

## Taxonomy

Canonical names must match ``instrument_taxonomy._CANONICAL_INSTRUMENTS``. Only these four activate ``pairwise_string_homogeneity`` / ``blend_string_and_legacy_instrument_component`` inside ``analyzers/timbral.py`` when building the refined instrument factor.

## Blend order (instrument component)

1. **Legacy** set-based instrument factor (unchanged baseline).
2. **String** pairwise blend when ``string_overlap_mass > 0``, using the same ``total_overlap_mass`` denominator as later families.

Later steps (brass, flutes, clarinets, double reeds, saxophones, percussion) blend **on top of** the result of step 2 when their overlap mass is positive. See ``docs/H_TIMBRAL_BRASS.md`` for the next stage.

### Mixed strings + non-strings in one window

Let $f$ be the ratio of **string** overlap mass to **total** overlap mass in the window (clipped to $\left[0,\,1\right]$). The instrument component after the string stage is

$$
C_I \;=\; f\, H_{\text{pair}} + (1-f)\, C_{\text{legacy}},
$$

where $H_{\text{pair}}$ is ``pairwise_string_homogeneity`` over bowed-string events only and $C_{\text{legacy}}$ is the legacy instrument factor. Pure string windows have $f \approx 1$.

## Section similarity (pairwise)

Order of rows/columns in the loaded matrix: **violin**, **viola**, **cello**, **double bass** (``_SECTION_ORDER`` in code).

Symmetric values are taken from ``default_profiles.json`` → ``string_section_similarity_matrix`` (``timbral_numpy_matrix`` at import). Example legacy defaults (high violin–viola affinity; cello–double bass highest cross-size pair in that table):

|  | vn | va | vc | db |
|--|----|----|----|-----|
| **vn** | 1.00 | 0.93 | 0.68 | 0.50 |
| **va** | 0.93 | 1.00 | 0.76 | 0.58 |
| **vc** | 0.68 | 0.76 | 1.00 | 0.90 |
| **db** | 0.50 | 0.58 | 0.90 | 1.00 |

Unknown section pairs fall back to ``string_fallback_section_similarity`` (legacy default **0.35** in packaged ``default_profiles.json``).

## Tessitura / register term (pairwise)

Sounding MIDI ``pitch.ps`` on each string event (same **concert** convention as the rest of the timbral path; see ``docs/H_TIMBRAL_SCORE_REPRESENTATION.md``).

Continuous proximity (no quartile bins on strings):

$$
s_{\text{register}} \;=\; \exp\!\left(-\frac{|p_1 - p_2|}{\tau}\right),
$$

with ``\tau =`` ``string_register_tau_semitones_default`` from ``default_profiles.json`` (legacy packaged default **7.5** semitones).

## Technique similarity

### Legacy path (single label per event)

If events **lack** a ``technique_state`` dict, ``technique`` strings are compared with a fixed symmetric matrix ``string_technique_similarity_matrix`` (order of keys: ``arco``, ``tremolo``, ``sul_pont``, ``sul_tasto``, ``harmonic``, ``muted``, ``pizz``, ``unknown`` — see ``string_technique.py`` constants).

Labels come from ``string_technique_from_note`` / legacy pipelines; ``unknown`` still pairs moderately with ``arco`` in the packaged matrix.

### Multi-state path (preferred when present)

If events carry ``technique_state`` dicts, ``technique_state_similarity`` compares full ``TechniqueState`` objects (bowed-string branch in ``technique_state.py``): excitation, contact, mute, harmonics, pressure, tremolo, etc.

## Pairwise aggregation

For unordered pairs ``i < j`` of bowed-string sounding events in the window, with overlap weights ``w_i =`` ``overlap_ql``:

$$
\text{pair\_sim}_{ij} \;=\; s_{\text{section}}(i,j)\, s_{\text{register}}(i,j)\, s_{\text{technique}}(i,j),
$$

$$
H_{\text{pair}} \;=\; \frac{\sum_{i<j} w_i w_j\, \text{pair\_sim}_{ij}}{\sum_{i<j} w_i w_j}.
$$

If fewer than two qualifying events exist, the pairwise contribution is **1.0** (neutral). The result is clipped to ``[0,1]``.

## Limits

- music21 pitches follow the parsed score (written vs concert depends on encoding and transposition metadata).
- Technique text coverage is heuristic; missing directions are common.
- This layer is **symbolic layout** homogeneity, not a substitute for listening or spectral analysis.
