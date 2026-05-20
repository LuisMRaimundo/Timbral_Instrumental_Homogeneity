# Metric → code map (concise)

| Metric / object | Primary implementation |
|-----------------|------------------------|
| **H(t)** weighted geometric mean of m1, m2, m3 | `homogeneity_analyser.analyzers.common.combine_weighted_geometric` |
| **m1** intra-window (entropy-based) | `HomogeneityAnalyzer.compute_metric_intra` in `analyzers/homogeneity.py` |
| **m2** inter-window Wasserstein stability | `HomogeneityAnalyzer.compute_metric_inter` (scipy `wasserstein_distance`) |
| **m3** multi-scale density / sustained branch | `HomogeneityAnalyzer.compute_metric_scale` (constants `M3_*` in same module) |
| **H_timbral** part-name / taxonomy | `TimbralHomogeneityAnalyzer` in `analyzers/timbral.py` + `taxonomy/instrument_taxonomy.py` |
| **H_timbral** concert sounding pitch for tessitura | `analyzers/timbral_sounding_pitch.py` — see `docs/H_TIMBRAL_SCORE_REPRESENTATION.md` |
| **H_timbral** measure-level text for techniques | `analyzers/notation_context.py` — see `docs/H_TIMBRAL_SCORE_REPRESENTATION.md` |
| **H_timbral** bowed string refinement | `analyzers/string_pairwise_timbral.py` + `analyzers/string_technique.py` — see `docs/H_TIMBRAL_STRINGS.md` |
| **H_timbral** brass refinement | `analyzers/brass_pairwise_timbral.py` + `analyzers/brass_technique.py` — see `docs/H_TIMBRAL_BRASS.md` |
| **H_timbral** flute-family refinement | `analyzers/flute_pairwise_timbral.py` + `analyzers/flute_technique.py` — see `docs/H_TIMBRAL_FLUTES.md` |
| **H_timbral** clarinet-family refinement | `analyzers/clarinet_pairwise_timbral.py` + `analyzers/clarinet_technique.py` — see `docs/H_TIMBRAL_CLARINETS.md` |
| **H_timbral** double-reed refinement | `analyzers/double_reed_pairwise_timbral.py` + `analyzers/double_reed_technique.py` — see `docs/H_TIMBRAL_DOUBLE_REEDS.md` |
| **H_timbral** saxophone-family refinement | `analyzers/saxophone_pairwise_timbral.py` + `analyzers/saxophone_technique.py` — see `docs/H_TIMBRAL_SAXOPHONES.md` |
| **H_timbral** percussion subsystem | `analyzers/percussion_pairwise_timbral.py` + `analyzers/percussion_technique.py` + `analyzers/percussion_ontology.py` — see `docs/H_TIMBRAL_PERCUSSION.md` |
| **H_timbral** unpitched percussion register proxy | `unpitched_percussion_register_proxy` in `analyzers/percussion_pairwise_timbral.py` — see `docs/H_TIMBRAL_SCORE_REPRESENTATION.md` |
| **H_timbral** verified cross-family layer (restricted bibliography list) | `analyzers/timbre_cross_relations.py` + note field `timbral_note_slices` in `analyzers/timbral.py` — see `docs/H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md` |
| **U(t)** register uniformity | `RegisterUniformityAnalyzer` in `analyzers/register.py` |
| Full-score **H(t)** pipeline | `run_homogeneity_analysis` in `services/analysis_service.py` |
| **JSON export** (parameters + series + summaries + metadata) | `services/json_export.py` — used by Gradio “Download full results (JSON)” |
| Combined CSV **H + H_timbral** | `build_combined_csv` in `services/result_assembly.py` |
| Typed series wrappers | `homogeneity_analyser.models.results` (`HomogeneitySeriesResult`, etc.) |
| MXL / file safety before music21 | `homogeneity_analyser.io.score_validation` → used by `io/score_loader.parse_score` |

---

## H_TI — symbolic timbral–instrumental homogeneity (primary product)

| Field / concept | Primary implementation | Reading contract |
|-------------------|------------------------|------------------|
| **H_TI_core** | `SymbolicTIHomogeneityAnalyzer.compute_H_TI` in `analyzers/hti.py` | **Score-based symbolic** timbral–instrumental homogeneity; **not** measured acoustic or perceptual fusion. |
| **register_compactness** | `compute_register_compactness_fields` in `hti.py` | **Pitch-space proximity / dispersion** (span + pairwise **semitone-distance** factors). **Does not** encode mod‑12 interval-class “consonance”. |
| **register_span_factor** | Same value as **`register_span_proximity`** in exports | Explicit alias: **span-based** registral compactness **component**. |
| **register_pair_distance_factor** | Same value as **`pairwise_interval_proximity`** in exports | Explicit alias: **pairwise semitone-distance** compactness **component**. |
| **interval_class_blend_factor** | `compute_interval_class_blend_factor` / `compute_pairwise_interval_blend_factor` in `analyzers/symbolic_blend_layers.py` | **Symbolic interval-class favourability** (optional); orthogonal to **register_compactness** and **H_TI_core**. |
| **interval_class_profile** | `compute_interval_class_blend_factor` in `symbolic_blend_layers.py` | Mass distribution over **stable** interval-class keys (`seconds_sevenths`, …). Keys name **mod‑12 equivalence buckets**, not literal interval content in the score. |
| **interval_class_profile_display** | Same function | Same masses as **`interval_class_profile`**, keyed by **`interval_class_display_labels`** (human-readable). |
| **literal_interval_semitone_pair_mass** | Same function | Overlap mass by **absolute** semitone distance before mod‑12 grouping (string keys: `"1"`, `"2"`, …). |
| **chromatic_mod12_pair_mass** | Same function | Overlap mass by chromatic distance mod 12 (`"0"`…`"11"`). |
| **interval_class_evidence_status** | From `taxonomy/symbolic_blend_conditioning.json` (default **`symbolic_convention`**) | **Provenance** for the mapping — **not** a claim of psychoacoustic validation unless separately page-verified. |
| **symbolic_blend_potential** | `compute_symbolic_blend_bundle_for_window` in `symbolic_blend_layers.py` | **Optional score-based symbolic blend-tendency diagnostic** when **`include_symbolic_blend_potential`**; **not** SPL-based blend. |
| Interval / attack profile data | `taxonomy/symbolic_blend_conditioning.json` | Configurable **symbolic** weights — conventions, not acoustic measurements. |
| **H_TI-only JSON `schema_version`** | **`"3.0"`** — `HTI_EXPORT_SCHEMA_VERSION` in `services/json_export.py` | Adds optional **`H_TA_acoustic_proxy`** / **`timbral_acoustic_affinity`**; **`H_TI_core`** unchanged. Distinct from combined legacy bundle **`1.8`**. |
| **Legacy multimetric analysers** | `homogeneity_analyser/legacy/` (shims: `analyzers/homogeneity.py`, `cluster.py`, …) | **H(t)**, **H_cluster**, **H_orchestration_symbolic**, **H_notated_fusion_potential**, **H_fusion_acoustic_heuristic**, **U(t)** — `services/analysis_service.py`, tests only for product UI. |
| **H_TA_acoustic_proxy** | `analyzers/timbral_acoustic_proxy.py` (`HTI_ACOUSTIC_PROXY_SERIES_KEYS`, `append_hti_acoustic_proxy_series_row`) | Score-derived event-pair kernel; default off (`include_acoustic_proxy`). Not literature **`timbral_affinity_*`** relief. Evidence: **`timbral_acoustic_affinity_evidence_status`** aligned with **`timbral_acoustic_affinity_components`** — see **`docs/H_TA_ACOUSTIC_PROXY.md`**. |
| **Optional interval-class / symbolic blend** | `analyzers/symbolic_blend_layers.py` (`HTI_SYMBOLIC_BLEND_SERIES_KEYS`, `append_hti_symbolic_blend_series_row`) | `include_symbolic_blend_potential`; orthogonal to **H_TI_core** and **H_TA**; separate Gradio accordion. Narrative: **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`**. |
