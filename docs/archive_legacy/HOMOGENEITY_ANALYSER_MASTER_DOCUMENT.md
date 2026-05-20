This document is historical and is not the current specification.

# Homogeneity Analyser — Master Technical Reference

**Document role:** Single consolidated reference for the **Homogeneity_analyser** repository. It reorganises material from `README.md`, `QUICK_REFERENCE.md`, `TECHNICAL_MANUAL.md`, and other `docs/` sources **without** concatenating them verbatim. Where sources disagreed, **current `src/homogeneity_analyser/` code** prevails.

**Non-goals (unchanged product boundary):** The software does **not** analyse audio waveforms, perform **FFT** on recordings, estimate **SPL**, or provide **measured acoustic or perceptual fusion**. **H_TI_core** is **notation-derived** only.

**Authoritative mathematics and pseudocode:** Root `TECHNICAL_MANUAL.md` **§2** (Mathematical specification) and **Appendix C** (pseudocode). This master document summarises and points there for proofs-level detail.

---

## 1. Executive overview

The package loads **MusicXML / MXL / MIDI** via music21, builds a shared **timbral event list** (`analyzers/timbral.py`), and computes **H_TI_core(t)** in sliding windows: overlap-mass Herfindahl-style concentration on **canonical instruments**, **instrumental subfamilies** (taxonomy `family`), optional **technique_uniformity** from **`technique_uniformity_key`**, and **register compactness** (**pitch-space proximity / dispersion** from **sounding MIDI** span + pairwise **semitone-distance** factors — **not** mod‑12 interval-class consonance). Optional **literature-conditioned symbolic blend** diagnostics (**`interval_class_blend_factor`**, **`symbolic_blend_potential`**, etc., when enabled) are **orthogonal** to **H_TI_core** and are **not** measured acoustic or perceptual fusion. **Written dynamics** feed a **separate interpretive layer** (`hti_dynamics.py`, `hti_dynamic_conditioning.py`) that **does not rescale** **H_TI_core**.

The **Gradio** entry point (`python -m homogeneity_analyser`) exposes **H_TI** analysis plus optional **symbolic inspection** tables (diagnostic, not a metric).

---

## 2. Methodological scope

| In scope | Out of scope |
|----------|----------------|
| Symbolic overlap mass on notation timeline | Microphones, rooms, listening tests |
| Ordinal dynamic ladder (`pppp` … `ffff`) | SPL, dB, waveform loudness |
| Literature-governed **symbolic** affinity (optional) | Measured timbral similarity vectors |
| Conservative harmonic pitch audit | Acoustic partial tracking |
| Register span + pairwise **semitone-distance** proximity on MIDI | Perceptual “fusion proof” or validated consonance judgment |

---

## 3. H_TI model (headline)

- **H_TI_core** — **score-based symbolic** timbral–instrumental homogeneity (**not** a measured fusion metric).
- **H_TI(t) = H_TI_strict(t) = H_TI_core(t)** in exports when a window has active events (`analyzers/hti.py`).
- **H_TI_subfamily_relieved** blends instrument uniformity toward subfamily uniformity (`same_subfamily_relief_factor`); still distinct from affinity relief.
- **Macrofamily uniformity** is computed and exported but **excluded** from the default four-component geometric mean unless you fork the analyser.

Default weights (renormalised if components omitted): **instrument 0.40**, **subfamily (`family`) 0.25**, **technique 0.15**, **register 0.20**.

---

## 4. Mathematical definitions (summary table)

| Quantity | Formula / rule (implemented) | Module |
|----------|------------------------------|--------|
| Overlap mass $m_e$ | $\max(0,\min(z,t+w/2)-\max(o,t-w/2))$ in ql | `hti.py` |
| Herfindahl $U$ | $\sum p^2$ on normalised masses | `hti._herfindahl_from_masses` |
| Register span proximity | $1/(1+\mathrm{span}/\mathrm{ref})$ | `compute_register_compactness_fields` |
| **register_span_factor** | Same numeric as register span proximity | Explicit export alias (span component). |
| Pairwise proximity | Weighted mean of $1/(1+d_{ij}/\mathrm{ref})$, weights $m_i m_j$ | same (**absolute** semitone distance — **not** interval-class). |
| **register_pair_distance_factor** | Same numeric as pairwise proximity | Explicit export alias (pairwise distance component). |
| Register compactness | $\sqrt{\max(\varepsilon,R_\mathrm{span})\max(\varepsilon,R_\mathrm{pair})}$ | **Pitch-space** compactness only; orthogonal to optional **interval_class_blend_factor**. |
| **interval_class_blend_factor** | Mod‑12 class weights × optional wide-span attenuation | `symbolic_blend_layers.compute_interval_class_blend_factor`; optional export; **symbolic convention** unless bibliographically verified. |
| **symbolic_blend_potential** | Optional **score-based symbolic blend-tendency diagnostic** | `symbolic_blend_layers.compute_symbolic_blend_bundle_for_window`; only when **`include_symbolic_blend_potential`**; **not** SPL-based blend. |
| **H_TI_core** | Weighted geometric mean on active components | `compute_H_TI` — **notation-derived homogeneity**, not a fusion meter. |
| Dynamic coherence | $\sum q_d^2$ over **known** dynamic mass | `hti_dynamics.py` |
| Affinity uniformity | $\sum_{e,e'} p_e p_{e'} S_{e,e'}$ over **events** | `timbral_affinity.py` |

Full symbolic specification: **`TECHNICAL_MANUAL.md` §2**.

---

## 5. Data pipeline

1. **Validation** — `io/score_validation.py` (size, extension).
2. **Parse** — music21 stream.
3. **Taxonomy** — `taxonomy/instrument_taxonomy.py` → `canonical_instrument`, instrumental `family`, macrofamily mapping (`hti_taxonomy.py`).
4. **Pitch** — `timbral_sounding_pitch.py` + `pitch_interpretation.py` + optional `harmonic_pitch.py`.
5. **Technique state** — `notation_context.py`, `technique_state.py`.
6. **Windowing** — user step/size or `hti_adaptive_windows.resolve_hti_windowing` + `build_hti_window_centers`.
7. **H_TI** — `SymbolicTIHomogeneityAnalyzer.analyze_hti`.
8. **Exports** — `json_export.build_hti_export`, `HTI_CSV_COLUMNS`, `ui/callbacks.py`.

**Code map:** `docs/METRIC_CODE_MAP.md`, `docs/ARCHITECTURE.md`.

---

## 6. Pitch interpretation

Four **`pitch_interpretation_mode`** values are implemented (`pitch_interpretation.py`): `musicxml_sounding`, `xml_pitch_as_real`, `ignore_octave_transpositions_only`, `xml_pitch_as_real_with_octave_transposers`. **`effective_written_midi`** uses letter–octave base + **`effective_alter`** (explicit `alter` or inferred from recognised accidental text). **`effective_sounding_midi`** follows the mode rules; in general **`effective_sounding_midi = effective_written_midi + total_transpose_applied`** for the ordinary (non-harmonic-override) path.

Transpose audit splits **`chromatic_transpose_detected`** / **`octave_transpose_detected`** vs **`…_applied`**.

---

## 7. Harmonics

Default **`harmonic_pitch_policy`** is **`conservative`**. Artificial harmonic inference uses **`ARTIFICIAL_STRING_HARMONIC_INTERVALS`** with **±0.25** semitone tolerance and **`harmonic_sounding_midi = harmonic_base_midi + sounding_interval_above_base`** in **written MIDI space**, then transposed to sounding frame. **`explicit`** and **`inferred_common_artificial`** may overwrite `effective_sounding_midi`; **`unresolved`** does **not**.

Reference chart limitations: `docs/STRING_HARMONIC_INTERVAL_REFERENCE.md`.

---

## 8. Microtonality

`compute_effective_alter` documents how fractional alter and accidental text combine; unknown text yields **`microtonal_accidental_status: unknown`** without inventing new quarter-tone values beyond the explicit mapping tables.

---

## 9. Technique-state model

- **`technique_state_id`:** full fingerprint including instrument context.
- **`technique_uniformity_key`:** instrument-free bucket for **Herfindahl technique term** and **`technique_state_distribution`** in H_TI windows.

Coverage statuses (`unavailable`, `ambiguous`, `ordinary_default_uniform`, `explicit_uniform`, `explicit_mixed`): see **`TECHNICAL_MANUAL.md` §2.3** and §5 (technique-state table).

---

## 10. Register compactness vs interval-class layer

**Register compactness** (**`register_compactness`**) is **pitch-space proximity / dispersion** only: the geometric mean of **span-based** and **pairwise semitone-distance** factors (`compute_register_compactness_fields` in `hti.py`). Exports also emit **`register_span_factor`** and **`register_pair_distance_factor`** as explicit aliases of **`register_span_proximity`** and **`pairwise_interval_proximity`**. It **does not** implement “intervallic fusion” or psychoacoustic consonance inside **H_TI_core**.

**Interval-class symbolic favourability** (**`interval_class_blend_factor`**, **`interval_class_profile`**, **`interval_class_evidence_status`**) lives in **`symbolic_blend_layers.py`** with weights in **`taxonomy/symbolic_blend_conditioning.json`**. It is **orthogonal** to register compactness: e.g. **C4–D4** can be **register-compact** but only **moderately** favourable in the interval-class table; **C4–C5** is often **less** compact in register space but **high** in octave-class favourability; **C4–G4** is **fifth-favourable**; **C4–F♯4** is **tritone-unfavourable** under the default **symbolic convention** (default evidence status **`symbolic_convention`** — not empirical validation).

**`symbolic_blend_potential`** is an **optional interpretive diagnostic** (normalized geometric mean of available positive factors including **H_TI_core** when enabled via **`include_symbolic_blend_potential`**). It is **score-based symbolic blend potential**, **not** measured acoustic fusion and **not** psychoacoustic proof.

Unpitched-only windows omit the register factor from the **H_TI_core** geometric mean. **`register_proximity`** duplicates **`register_compactness`** for legacy CSV consumers.

---

## 11. Dynamic conditioning

Ordinal ladder in `NOTATED_DYNAMIC_SYMBOLIC_ORDINAL` + secondary aliases. **`dynamic_divergence_detected`:** ≥2 known classes each with ≥**12%** of total overlap mass. Interpretive scalars (**`soft_blend_potential`**, **`projection_divergence_risk`**, etc.) are defined in `apply_notated_dynamic_conditioning` — see **§2.7** of `TECHNICAL_MANUAL.md` for formulas. They **do not** modify **H_TI_core**.

---

## 12. Timbral-affinity layer

Optional; **`timbral_affinity_relief_factor` = 0** by default. **`H_TI_affinity_literature_relieved`** substitutes a blend of raw instrument uniformity and **`timbral_affinity_uniformity`**. Profiles **`strict` / `conservative` / `moderate` / `exploratory`** gate rule tiers. **`H_TI_affinity_dynamic_conditioned`** is a further **interpretive** scalar. Governance: `docs/TIMBRAL_AFFINITY_LITERATURE_AUDIT.md`, `taxonomy/timbral_affinity_registry.json`.

---

## 13. Adaptive windowing

Modes: **`manual`**, **`auto_by_excerpt_duration`**, **`auto_by_target_windows`**. Clamps and **`edge_policy`** (`include_partial_windows`, `drop_partial_windows`, `mark_partial_windows`) — **`TECHNICAL_MANUAL.md` §2.10** and **§3.1**. Adaptive logic **does not** change the **H_TI_core** formula.

---

## 14. Dominant-category tie handling

`dominant_with_ties` exposes **`dominant_primary`** (compat), **`dominant_all`**, **`tie`**, **`max_share`**, **`margin_to_second`** (default tolerance **1e-9**). Prefer plural + `*_tie` fields for analysis.

---

## 15. Symbolic inspection

`services/score_audit.build_symbolic_inspection_tables` — three tables: inventory, per-pitch event audit, vertical sonorities. Column orders `SCORE_AUDIT_*_COLUMNS`. Diagnostic only.

---

## 16. CSV and JSON exports

| Artifact | Schema / version | Key constants |
|----------|------------------|---------------|
| H_TI JSON | **`schema_version` `"2.9"`** | `HTI_EXPORT_SCHEMA_VERSION` |
| Combined / legacy JSON | **`schema_version` `"1.8"`** | `JSON_EXPORT_SCHEMA_VERSION` |
| Package version | **1.0.0** (current `__init__.py`) | `homogeneity_analyser.__version__` |
| Export wrapper | **`model_version` `"1.0"`** | `JSON_EXPORT_MODEL_VERSION` |

Per-window keys align with `HTI_CSV_COLUMNS` / `HTI_EXPORT_TIME_SERIES_KEYS` in `hti.py`, including **2.9** fields: **`register_span_factor`**, **`register_pair_distance_factor`**, and (when optional symbolic blend is enabled) **`interval_class_blend_factor`**, **`interval_class_profile`**, **`interval_class_evidence_status`**, **`symbolic_blend_potential`**, **`symbolic_blend_components`**, **`attack_compatibility_factor`**, **`attack_class_distribution`** (see source tuples for the full list).

---

## 17. Architecture and code map

See **`docs/ARCHITECTURE.md`** (source of truth under `src/homogeneity_analyser/`, generated `build/` / `dist/` hygiene) and **`docs/METRIC_CODE_MAP.md`**.

---

## 18. UI / Gradio workflow

`ui/gradio_app.py`, `ui/components.py`, `ui/callbacks.py` — upload or path, pitch mode, harmonic policy, H_TI parameters, optional affinity controls, optional **literature-conditioned symbolic blend** diagnostics (**`include_symbolic_blend_potential`** — adds **interval-class** / attack / **`symbolic_blend_potential`** columns only; **not** acoustic fusion), run analysis, download CSV/JSON/plots. Symbolic inspection runs on upload / mode change (`run_loaded_xml_inspection`).

---

## 19. Validation and testing

CI (when present): **ruff**, **mypy**, **pytest** per `pyproject.toml`. Last documented counts in **`docs/SCIENTIFIC_TECHNICAL_AUDIT.md`** (re-run after substantive edits; counts may lag).

---

## 20. Scientific / technical audit summary

**Verdict (condensed from `docs/SCIENTIFIC_TECHNICAL_AUDIT.md`):** Useful **symbolic** orchestration tool with strong regression tests for declared scope; **not** validated perceptual or acoustic measurement software. **Doctoral use** requires explicit framing as notation-derived and avoids implying empirical blend validation.

---

## 21. Limitations

Exporter-dependent semantics; MIDI metadata poverty; heuristic dynamic labels; literature pagination in `source_registry.json` may still be **pending verification** before page-grounded citation — see **`TECHNICAL_MANUAL.md` §19** and `docs/bibliography/ACOUSTIC_SOURCE_REGISTRY.md`.

---

## 22. Bibliography / literature governance

Canonical JSON: `src/homogeneity_analyser/acoustic_profiles/source_registry.json`. Developer/audit overview: `docs/bibliography/ACOUSTIC_SOURCE_REGISTRY.md`. Public governance and registry-key index: **`TECHNICAL_MANUAL.md` §19**.

---

## 23. Legacy / internal modules

**Not** the current Gradio product: `homogeneity.py`, `cluster.py`, `orchestration_symbolic.py`, `notated_fusion_potential.py`, `fusion_acoustic_heuristic.py`, `register.py` (see **`TECHNICAL_MANUAL.md` Appendix A**). **`confidence_score`** on legacy fusion branches is **internal coverage**, not empirical validation.

**Documentation legacy:** `docs/H_TIMBRAL_*.md` (family-specific timbral design notes), `docs/archive_legacy/*`, `docs/model_audit/H_TIMBRAL_ASSUMPTIONS_AUDIT.md` — internal design history; do not read as current product marketing. Each of those **H_TIMBRAL** Markdown files opens with **“Terminology (H_TIMBRAL vs H_TI 2.9)”**: words like “blend” there mean **symbolic timbral-design / affinity** inside that module, not the **H_TI 2.9** export fields **`interval_class_blend_factor`** / **`symbolic_blend_potential`**.

---

## 24. Windows packaging / distribution

If PyInstaller or wheel build instructions exist in-repo, follow maintainer scripts in `scripts/` and `pyproject.toml`. **Do not** ship or edit **`build/lib/`** trees as authoritative sources.

---

## 25. Appendices (this document)

### Appendix A — Formulas

See **`TECHNICAL_MANUAL.md` §2** (primary) and **§4** (short recap).

### Appendix B — Algorithms / pseudocode

See **`TECHNICAL_MANUAL.md` Appendix C**.

### Appendix C — Field glossary

| Field group | Reference |
|-------------|-----------|
| H_TI time series | `HTI_CSV_COLUMNS`, `HTI_EXPORT_TIME_SERIES_KEYS` in `analyzers/hti.py` |
| Symbolic inspection | `SCORE_AUDIT_*_COLUMNS` in `services/score_audit.py` |
| Harmonic audit | `SCORE_AUDIT_HARMONIC_PITCH_COLUMNS` |

### Appendix D — Schema / version map

| Name | Value / location |
|------|------------------|
| H_TI JSON `schema_version` | `"2.9"` — `json_export.HTI_EXPORT_SCHEMA_VERSION` |
| Combined JSON `schema_version` | `"1.8"` — `json_export.JSON_EXPORT_SCHEMA_VERSION` |
| `JSON_EXPORT_MODEL_VERSION` | `"1.0"` |
| `TIMBRAL_MODEL_SEMANTICS_VERSION` | `"1.0"` — `models/timbral_semantics.py` |
| `TECHNIQUE_MODEL_VERSION` | `hti.TECHNIQUE_MODEL_VERSION` |

---

## Family-specific symbolic notes (legacy docs index)

| Topic | Document |
|-------|----------|
| Strings | `docs/H_TIMBRAL_STRINGS.md` |
| Brass | `docs/H_TIMBRAL_BRASS.md` |
| Clarinets | `docs/H_TIMBRAL_CLARINETS.md` |
| Flutes | `docs/H_TIMBRAL_FLUTES.md` |
| Double reeds | `docs/H_TIMBRAL_DOUBLE_REEDS.md` |
| Saxophones | `docs/H_TIMBRAL_SAXOPHONES.md` |
| Percussion | `docs/H_TIMBRAL_PERCUSSION.md` |
| Score representation | `docs/H_TIMBRAL_SCORE_REPRESENTATION.md` |
| Cross-relations | `docs/H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md` |
| Narrative companion | `docs/TECHNICAL_MANUAL_NARRATIVE_HTI_2026.md` |

These files inform **interpretation** and legacy timbral context; **H_TI_core** formulas remain in `hti.py`.

---

*End of master document.*
