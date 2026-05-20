# Current code characteristics report

**Document:** `CURRENT_CODE_CHARACTERISTICS_REPORT.md`  
**Project:** `homogeneity-analyser` (package `homogeneity_analyser`)  
**Audience:** Developers and auditors who want a **single inventory** of how the repository behaves **today**, aligned with the **H_TI-first** product.

**Canonical user docs:** `README.md`, `QUICK_REFERENCE.md`, `TECHNICAL_MANUAL.md` (not duplicated here).

---

## 1. Executive summary

1. **Primary product:** **Symbolic timbral–instrumental homogeneity** — **H_TI_core(t)** on a quarter-note time axis, from **MusicXML / MXL / MIDI** only. Headline series **H_TI(t)** is numerically identical to **H_TI_core(t)** in exports.
2. **Interpretive layer:** **Notated dynamic conditioning** (ordinal written dynamics, coherence, family-aware scalars, **`dynamic_interpretation_label`**). It does **not** rescale **H_TI_core**; it qualifies reading. **`not_audio_analysis: true`** on H_TI JSON.
3. **Register term:** **register_compactness** = geometric mean of **register_span_proximity** (outer span) and overlap-weighted **pairwise_interval_proximity** (pairwise **semitone-distance** vs reference — **not** mod‑12 interval-class consonance). Exports also emit **`register_span_factor`** and **`register_pair_distance_factor`** as explicit aliases of those two components. The column **`register_proximity`** duplicates **register_compactness** for backward compatibility. Percussion-family **unpitched** instruments skip pitched register mass (aligned with **`timbral.py`**). Optional **`interval_class_blend_factor`** / **`symbolic_blend_potential`** (when enabled) are **orthogonal** symbolic layers — see **`symbolic_blend_layers.py`** and **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`** (**`seconds_sevenths`** = mod‑12 bucket, not literal sevenths).
4. **Optional H_TA_acoustic_proxy:** Score-derived **timbral-acoustic affinity** (event-level pairwise kernel). **Orthogonal** to **H_TI_core**; default **off** (`include_acoustic_proxy`). **Not** measured audio; **not** the literature-governed **`timbral_affinity_*`** relief layer. See **`docs/H_TA_ACOUSTIC_PROXY.md`**.
5. **Gradio UI:** **H_TI** run + **symbolic inspection** (upload-driven); separate accordions for **interval-class / symbolic-blend-potential** (`include_symbolic_blend_potential`) and **H_TA acoustic proxy** (`include_acoustic_proxy`, default off).
6. **Legacy / internal:** Multimetric implementations under **`src/homogeneity_analyser/legacy/`** (compatibility shims in **`analyzers/`**). **Combined** JSON (**`schema_version` `1.8`**) for **tests** and **batch/research** — **not** the Gradio product. Coverage CI gate (**`fail_under` 77**) applies to the **product path** (legacy omitted; measured total ~**79%**). **`tests/test_hti_core_golden_outputs.py`** locks **`H_TI_core`** numerics. UI: **`callbacks.py`** is the Gradio boundary; parameter/result adapters live in **`ui/hti_ui_params.py`** and legacy/timbral/combined **`ui/*_ui_params.py`** (no analytical change). Repository hygiene log: **`docs/CLEANUP_REPORT.md`**. See **`legacy/README.md`**, **`docs/METRIC_CODE_MAP.md`**, **`docs/archive_legacy/`**.

---

## 2. H_TI_core — structure (where it lives)

| Concern | Location |
|--------|----------|
| Window features, register compactness | `src/homogeneity_analyser/analyzers/hti.py` (`SymbolicTIHomogeneityAnalyzer`, `compute_register_compactness_fields`). CSV/JSON column lists: **`hti_export_rows.py`** (`HTI_CSV_COLUMNS`, `HTI_EXPORT_TIME_SERIES_KEYS`, `hti_csv_row_dict`; re-exported from `hti.py` for compatibility). Optional export registries: **`HTI_SYMBOLIC_BLEND_SERIES_KEYS`** / `append_hti_symbolic_blend_series_row` in `symbolic_blend_layers.py`; **`HTI_ACOUSTIC_PROXY_SERIES_KEYS`** / `append_hti_acoustic_proxy_series_row` in `timbral_acoustic_proxy.py`. See **`MAINTAINERS.md`**. |
| Event list / sounding pitches / taxonomy | `analyzers/timbral.py` (base class reused by H_TI) |
| Written dynamics aggregation | `analyzers/hti_dynamics.py` |
| Dynamic conditioning + labels | `analyzers/hti_dynamic_conditioning.py` |
| Macrofamily diagnostic | `analyzers/hti_taxonomy.py` |
| H_TI run + summary text | `services/analysis_service.py` (`run_symbolic_ti_homogeneity_analysis`) |
| Optional timbral-acoustic affinity proxy | `analyzers/timbral_acoustic_proxy.py`, `taxonomy/acoustic_timbral_taxonomy.json` |
| H_TI params + validation | `services/param_validation.py`, `services/constants.py` (`DEFAULT_HTI_PARAMS`) |

**H_TI_core** is a weighted geometric mean of (when active): **instrument_uniformity**, **family_uniformity** (instrumental subfamily), **technique_uniformity**, **register_proximity** (= **register_compactness**). Weights renormalise when technique or register is omitted.

---

## 3. Exports — schema versions (do not conflate)

| Bundle | `schema_version` | Notes |
|--------|------------------|--------|
| **H_TI-only JSON** | **`3.0`** (`HTI_EXPORT_SCHEMA_VERSION` in `services/json_export.py`) | `build_hti_export`; **`H_TI_core`** unchanged; optional **`H_TA_acoustic_proxy`** columns (NaN + `evidence_status: disabled` when proxy off); **`timbral_acoustic_affinity_evidence_status`** aligned with **components** when proxy on; nested **`dynamic_conditioning`**; optional symbolic blend / timbral-affinity / acoustic-proxy fields when enabled. |
| **Combined / legacy library JSON** | **`1.8`** (`JSON_EXPORT_SCHEMA_VERSION`) | Used when building combined or older metric exports in code/tests — **not** the Gradio headline product. |

---

## 4. Gradio application (current)

| Item | Detail |
|------|--------|
| Entry | `homogeneity-analyser` → `homogeneity_analyser.ui.gradio_app:main`; `python -m homogeneity_analyser` |
| Layout | `ui/gradio_app.py` — **H_TI_core** plot; timbral-affinity relief controls; accordion **Optional symbolic interval-class / blend-potential diagnostics**; accordion **Acoustic-aligned symbolic timbral-affinity proxy**; accordion **Symbolic inspection** |
| Run path | `ui/callbacks.py` — **`run_hti_app`** → `run_symbolic_ti_homogeneity_analysis` → CSV/JSON/plot paths |
| Copy | `ui/components.py` — `METRICS_EXPLAINER`, intro markdown |

---

## 5. Register / interval fields (H_TI time series)

Per window (when pitched evidence exists): **`register_span_semitones`**, **`register_span_proximity`**, **`register_span_factor`** (same numeric as span proximity), **`pairwise_interval_proximity`**, **`register_pair_distance_factor`** (same numeric as pairwise proximity), **`pairwise_interval_coverage_status`** (`sufficient_pairs` / `insufficient_pairs` / `unpitched_only`), **`register_compactness`**, **`register_proximity`** (alias), **`register_coverage_status`**. When **`include_symbolic_blend_potential`**: **`interval_class_blend_factor`**, **`pairwise_interval_blend_factor`** (legacy alias), **`interval_class_profile`** (stable keys; **`seconds_sevenths`** = mod‑12 {1,2,10,11} bucket, not literal sevenths), **`interval_class_profile_display`**, **`literal_interval_semitone_pair_mass`**, **`chromatic_mod12_pair_mass`**, **`interval_class_evidence_status`**, **`symbolic_blend_potential`**, etc. CSV column order is defined by **`HTI_CSV_COLUMNS`** in `hti.py`.

---

## 6. Legacy / internal modules (non–user-primary)

Still in the package for infrastructure and regression coverage (non-exhaustive):

| Area | Examples |
|------|-----------|
| Texture / legacy timbral / cluster / orchestration / fusion / register U | `homogeneity.py`, `timbral.py`, `cluster.py`, `orchestration_symbolic.py`, `notated_fusion_potential.py`, `fusion_acoustic_heuristic.py`, `register.py` |
| Combined pipeline | `analysis_service.run_both_and_combine`, `result_assembly.py`, combined builders in `json_export.py` |
| Acoustic profile / registry | `acoustic_profiles/*` — literature-linked **heuristic** paths; not a claim of measured fusion in **H_TI_core** |

**Archived narrative** describing the old multi-tab + `schema_version` 1.5 report: **`docs/archive_legacy/report_legacy_multimetric.md`**.

---

## 7. Repository layout (high level)

| Path | Role |
|------|------|
| `src/homogeneity_analyser/` | Production code |
| `tests/` | Pytest (includes H_TI, dynamics, register compactness, JSON, Gradio wiring, taxonomy, timbral regression) |
| `docs/` | Architecture, metric map, timbral notes, **`docs/archive_legacy/`** |
| `validation/` | Optional validation runner + fixtures |
| `pyproject.toml` | Dependencies, scripts, pytest / coverage / ruff / mypy |

---

## 8. Security & file ingestion (unchanged)

`io/score_validation.py`: size limits, allowed extensions, MXL ZIP safety (member caps, traversal rejection). See **`TECHNICAL_MANUAL.md`** for policy detail.

---

## 9. Testing & quality gates (typical)

- **pytest** — broad coverage of analyzers, H_TI, exports, UI validation, documentation consistency (env-gated checks optional).
- **ruff / mypy** — configured in `pyproject.toml`; CI/local health may still have debt outside this report’s scope.

---

## 10. Documentation map (pointers only)

| Document | Role |
|----------|------|
| `README.md` | Install, scope, **H_TI_core**, dynamic conditioning, **schema 3.0** (H_TI JSON), optional **H_TA_acoustic_proxy** |
| `QUICK_REFERENCE.md` | One-page operator guide |
| `TECHNICAL_MANUAL.md` | Full methodology + §19 bibliography + Appendix D (symbolic vocabularies) |
| `docs/ARCHITECTURE.md` | System map |
| `docs/METRIC_CODE_MAP.md` | Code paths for **H_TI** + legacy/internal |
| `docs/H_TA_ACOUSTIC_PROXY.md` | Acoustic proxy formula, evidence tags, UI separation |
| `docs/archive_legacy/` | Superseded or historical docs, including **`report_legacy_multimetric.md`** |
| `FINAL_VERIFICATION_REPORT.md` | Latest pytest / ruff / mypy / doc-alignment verification |

---

*End of report.*
