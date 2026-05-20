# Legacy report — pre-H_TI refactor. Not current documentation.

This file preserves the former root **`report.md`** snapshot describing the **multi-tab Gradio** product, **`schema_version` 1.5** combined exports, and **H(t) / H_timbral / cluster / orchestration / fusion / register U** as co-primary user workflows. The **current** product is **H_TI_core(t)** with **notated dynamic conditioning**; see **`CURRENT_CODE_CHARACTERISTICS_REPORT.md`** at the repository root and **`README.md`** / **`TECHNICAL_MANUAL.md`**.

---

# Homogeneity Analyser — Full code characteristics report

**Document:** `report.md`  
**Project:** `homogeneity-analyser` (package `homogeneity_analyser`)  
**Version (package):** `1.0.0` (`pyproject.toml`, `homogeneity_analyser.__init__.__version__`)  
**Scope:** Symbolic-score analysis only (MusicXML / MIDI). No user audio waveforms, no FFT on recordings.

This report inventories **architecture**, **metrics**, **data paths**, **UI**, **exports**, **profiles & bibliography plumbing**, **quality gates**, and **documentation** as implemented in the repository.

---

## 1. Executive summary

The codebase is a **Python 3.10+** application that:

1. Loads scores via **music21** after **structural file validation** (size, extension, ZIP/MXL safety).
2. Computes several **time-indexed metrics** on a shared quarter-note grid: **H(t)** (distribution homogeneity), **H_timbral(t)** (legacy symbolic timbral/orchestration-register homogeneity), **H_cluster(t)** (vertical pitch compactness), **H_orchestration_symbolic(t)** (Herfindahl-style symbolic orchestration), **H_fusion_acoustic_heuristic(t)** (literature-linked heuristic fusion proxy), and **U(t)** (register uniformity).
3. Exposes workflows through a **Gradio** web UI and a **service layer** suitable for headless use.
4. Serializes results to **CSV**, **PNG/HTML plots** (matplotlib / plotly), and **JSON** with **`schema_version` `1.5`**, including `model_version`, `metric_kind`, `not_audio_analysis`, nested combined payloads, and fusion **`source_keys`** where applicable.

Design themes: **modular analyzers**, **explicit export schema evolution**, **taxonomy-driven instrument resolution**, **technique state** with chronological directions vs. note-local merge, and **broad automated tests** (pytest + optional coverage / ruff / mypy per `pyproject.toml`).

---

## 2. Project identity & distribution

| Item | Value |
|------|-------|
| PyPI-style name | `homogeneity-analyser` |
| Install layout | `src` layout; `setuptools.packages.find` → `where = ["src"]` |
| Console entry | `homogeneity-analyser` → `homogeneity_analyser.ui.gradio_app:main` |
| Module run | `python -m homogeneity_analyser` (`__main__.py`) |
| Core dependencies | `numpy`, `pandas`, `scipy`, `music21`, `matplotlib`, `plotly` (6.x), `kaleido` (1.x), `gradio` (4+) |
| Dev optional extras | `pytest`, `pytest-cov`, `ruff`, `mypy` |
| Packaged non-Python data | `homogeneity_analyser.acoustic_profiles`: `*.json`, `*.yaml` |

---

## 3. Repository layout (top level)

| Area | Role |
|------|------|
| `src/homogeneity_analyser/` | All production Python (~67 modules under the package). |
| `tests/` | Pytest suite (~45 `test_*.py` files); integration, metric, UI, doc consistency, corpus MusicXML. |
| `docs/` | Architecture, metric map, timbral family notes, model audit, symbolic names. |
| `validation/` | Extra validation runner + `cases/` (MusicXML fixtures, CSV-driven fusion checks). |
| `README.md`, `QUICK_REFERENCE.md`, `TECHNICAL_MANUAL.md` | User-facing documentation (tutorial, formulas, UI §3.x). |
| `pyproject.toml` | Build, deps, scripts, **pytest**, **coverage** (`fail_under = 60`), **ruff**, **mypy** (with overrides for music21/gradio/plotly and homogeneity mypy workaround). |
| `requirements.txt` | Typically editable dev install (`-e ".[dev]"`). |

**Note:** A `build/` tree (e.g. legacy `setuptools` copy) may exist in some checkouts; **authoritative code** is under `src/`. Releases should not ship stale `build/lib` trees.

---

## 4. Package structure (`homogeneity_analyser`)

### 4.1 `analyzers/` (29 modules)

**Core metrics**

| Module | Responsibility |
|--------|----------------|
| `homogeneity.py` | **H(t)**, m1/m2/m3; overlap-weighted windows; Wasserstein inter-window; chord pitch-mass split; **written/display MIDI** for H (documented vs timbral sounding path). |
| `common.py` | Shared numerics: overlap ql, weighted geometric combine, homogeneity weight normalization, pitch space helpers. |
| `parsing_bridge.py` | Score parsing entry used by analyzers (delegates to I/O). |
| `register.py` | **U(t)** register uniformity within user bounds. |
| `timbral.py` | **H_timbral**: event building, family pairwise kernels, diagnostics hooks, concentration splits integration. |
| `timbral_sounding_pitch.py` | **Sounding** pitch lists for timbral events (transposition-aware). |
| `notation_context.py` | `notation_text_context_for_note` (`none` / `prior` / `legacy`) for text context. |
| `technique_state.py` | Persistent **TechniqueStateContext** per part; wind/string/brass/percussion direction parsers; `merge_note_technique_state`; `iter_timbral_elements` ordering (directions before notes at same offset). |
| `cluster.py` | **H_cluster** from vertical **sounding** MIDI pitch sets. |
| `orchestration_symbolic.py` | **H_orchestration_symbolic** — Herfindahl-style concentration on instrument / family / `technique_state_id`. |
| `fusion_acoustic_heuristic.py` | **H_fusion_acoustic_heuristic** — profile + roughness proxy; diagnostics with `sources_used` / confidence-style fields. |
| `timbral_concentration_splits.py` | Optional decomposition of concentration (e.g. instrument vs technique channels) for analysis/diagnostics. |

**Family-specific timbral layers**

Pairwise + technique helpers: `string_*`, `brass_*`, `flute_*`, `clarinet_*`, `double_reed_*`, `saxophone_*`, `percussion_*`, `timbre_cross_relations.py` (verified cross-family add-ons), `percussion_ontology.py`.

### 4.2 `services/` (8 modules)

| Module | Responsibility |
|--------|----------------|
| `analysis_service.py` | Orchestrates **run_homogeneity_analysis**, **run_timbral_analysis**, **run_cluster_analysis**, **run_orchestration_symbolic_analysis**, **run_fusion_acoustic_heuristic_analysis**, **run_register_uniformity_analysis**, **run_both_and_combine**; timbral diagnostics CSV helpers. |
| `result_assembly.py` | Combined CSV assembly, alignment of series onto shared time bases, fusion/native confidence bridging. |
| `json_export.py` | **JSON_EXPORT_SCHEMA_VERSION = "1.5"**, **JSON_EXPORT_MODEL_VERSION**; builders per `kind`; combined nested exports; `_fusion_source_keys_union`. |
| `param_validation.py` | Validates analysis parameter dicts against expected keys/ranges. |
| `score_audit.py` | Row models / columns for **Loaded XML inspection** (inventory, events, vertical sonorities). |
| `window_pipeline.py` | Time-grid interpolation utilities shared by combined exports. |
| `constants.py` | Shared service constants. |

### 4.3 `io/`

| Module | Responsibility |
|--------|----------------|
| `score_loader.py` | Load path → music21 score (uses validation). |
| `score_validation.py` | **ScoreValidationError**; max file size; allowed extensions; **MXL ZIP** member limits, path traversal guard, uncompressed size caps. |

### 4.4 `taxonomy/`

| Module | Responsibility |
|--------|----------------|
| `instrument_taxonomy.py` | Canonical instrument names, **families**, aliases, collision log API; large vocabulary for orchestral / band / early-music naming. |

### 4.5 `models/`

| Module | Responsibility |
|--------|----------------|
| `results.py` | Typed / dataclass-style result wrappers for series summaries. |
| `timbral_semantics.py` | Timbral model metadata for diagnostics / exports. |

### 4.6 `acoustic_profiles/`

| Asset / module | Responsibility |
|----------------|----------------|
| `source_registry.json` / `.yaml` | Bibliography and evidence metadata keys for acoustic/fusion governance. |
| `source_registry.py` / `source_validation.py` | Load registry; validate keys, pages, release-mode rules. |
| `default_profiles.json` / `.yaml` | Default acoustic/heuristic profile configuration. |
| `fusion_acoustic_feature_vectors.json` | Packaged feature vectors for fusion heuristic. |
| `model_config.py` | Timbral/fusion model configuration builders; window diagnostics bundles. |
| `timbral_diag_constants.py` | Window-scoped diagnostic constant naming for audits. |
| `features.py`, `similarity.py`, `spectral_proxy.py` | Feature construction and similarity helpers for fusion / spectral proxies. |

### 4.7 `plotting/`

| Module | Responsibility |
|--------|----------------|
| `time_series.py`, `summaries.py`, `common.py` | Matplotlib time series; Plotly interactive variants; gauge / homogeneity / timbral / cluster / orchestration figure builders (used by UI callbacks). |

### 4.8 `ui/`

| Module | Responsibility |
|--------|----------------|
| `gradio_app.py` | **Gradio** layout: shared upload, tabs (Homogeneity, Timbral, Register, Combined, Loaded XML inspection). |
| `callbacks.py` | Run handlers: validation, **`parse_ui_float`** / **`coerce_float`** (strict on invalid non-empty), progress, exports, combined outputs, **Loaded XML inspection** (DataFrames + temp CSVs). |
| `validation.py` | **`validate_uploaded_score`**, **`gradio_upload_to_path`** (multiple Gradio payload shapes), **`parse_ui_float`**, **`coerce_float`**. |
| `components.py` | Static copy / labels shared by the app. |

### 4.9 `utils/`

| Module | Responsibility |
|--------|----------------|
| `output_paths.py` | Temp export paths, cleanup of stale exports (`HOMOGENEITY_CACHE_DIR` pattern documented in manual). |

---

## 5. Metric catalogue (behavioural)

| Metric | Range / type | Primary inputs | Notes |
|---------|----------------|----------------|-------|
| **H(t)** | [0,1] typical | Written/display pitch, durations, densities; user weights on m1–m3 | Weighted geometric mean of **m1**, **m2**, **m3** after normalization. |
| **m1** | [0,1] | Intra-window pitch & duration entropy-style signals | Chord mass split across tones. |
| **m2** | [0,1] | Inter-window Wasserstein on pitch / duration features | Stability vs previous window. |
| **m3** | [0,1] | Multi-scale density branch | Sustained-texture heuristics (`M3_*` constants in `homogeneity.py`). |
| **H_timbral** | [0,1] typical | Instrument + family taxonomy, **sounding** pitch span, technique state, pairwise per family | Legacy scalar; **not** measured acoustic timbre. |
| **H_cluster** | [0,1] typical | Vertical **sounding** MIDI pitch classes per slice | Instrument-independent. |
| **H_orchestration_symbolic** | [0,1] typical | Instrument, family, `technique_state_id` Herfindahl-style | Distinct from H_timbral kernels. |
| **H_fusion_acoustic_heuristic** | [0,1] typical | Profile vectors + symbolic roughness proxy | **not_audio_analysis**; confidence fields in exports. |
| **U(t)** | [0,1] typical | Pitches within user register strip | Evenness of register distribution. |

**Asymmetry (documented in code):** **H(t)** uses **written/display** MIDI `ps`; **H_timbral** tessitura path uses **sounding** pitch. Cross-metric pitch comparability across transposing staves is not automatically unified.

---

## 6. Data flow (end-to-end)

1. **Upload / path** → `validate_uploaded_score` / `gradio_upload_to_path` → filesystem path.
2. **Pre-parse** → `score_validation.validate_score_path` (size, extension, ZIP safety).
3. **Parse** → `parse_score` / `score_loader` → `music21.stream.Score`.
4. **Analyze** → per-tab service in `analysis_service` invoking the appropriate **Analyzer** classes.
5. **Combine (optional)** → `run_both_and_combine` + `result_assembly` for aligned series and combined CSV/JSON.
6. **Present** → Gradio plots + summaries + file downloads; JSON via `json_export.write_json_export` + `build_*_export` functions.

---

## 7. JSON export characteristics (`schema_version` 1.5)

- **Every** export document includes: `schema_version`, `model_version`, `metric_kind` (mirrors `kind`), `not_audio_analysis: true`.
- **Kinds** include (non-exhaustive): homogeneity, timbral, register, cluster, orchestration_symbolic, fusion_acoustic_heuristic, combined bundles with nested sub-documents.
- **Combined** exports: aligned `combined_series`, optional **`dominant_timbral_state`**, nested cluster/orchestration/fusion payloads, **`combined_csv`** text field, diagnostics CSV text where built, root **`source_keys`** when fusion is embedded (sorted union of per-window `sources_used`).

See `TECHNICAL_MANUAL.md` §1c.13 and `docs/METRIC_CODE_MAP.md` for field-level mapping.

---

## 8. UI characteristics (Gradio)

- **Single shared upload** feeding all tabs; `file_shared.change` refreshes Loaded XML inspection.
- **Numeric parsing:** comma or dot decimals; ambiguous mixed separators rejected; empty optional fields → defaults; **invalid non-empty** → error (H_timbral: friendly stub return; Homogeneity / Combined / orchestration: **`gr.Error`**).
- **Outputs per tab:** matplotlib and/or plotly figures, text summaries, CSV paths, plot file paths, JSON paths; timbral optional **diagnostics table** + diagnostics CSV; combined tab multiple plots + combined CSV + diagnostics + nested JSON.
- **Loaded XML inspection:** pandas **DataFrames** with fixed column schemas from `score_audit.py`; temp CSVs via callbacks; JSON-stringified cells for nested structures in tables.

---

## 9. Security & robustness (file ingestion)

From `io/score_validation.py` (representative policy):

- Maximum on-disk score size (**50 MiB** before decompress).
- Allowed extensions: `.xml`, `.musicxml`, `.mxl`, `.mid`, `.midi`.
- ZIP (`MXL`): member count cap, per-member and total uncompressed size caps, **path traversal** rejection on member names.

---

## 10. Testing & quality gates

| Mechanism | Configuration / intent |
|-----------|-------------------------|
| **pytest** | `tests/`; verbose short tracebacks in `addopts`. |
| **Coverage** | Branch coverage; `fail_under = 60` total; omits `*/tests/*`. |
| **Ruff** | Lint + format; `src`, `tests`, `validation`; excludes `build`, `dist`. |
| **mypy** | Strict optional; third-party stubs ignored per overrides; `homogeneity.py` has targeted `ignore_errors` workaround. |
| **Documentation tests** | `test_documentation_consistency.py` (Gradio combined tab title, schema 1.5 mentions, tutorial tokens, release-facing sentinel rules). |
| **Validation harness** | `python validation/run_validation.py` (see `validation/cases/README.md`). |

Test modules cover: all major analyzers, JSON export, fusion corpus CSV, cluster/orchestration/fusion, timbral families, taxonomy, score validation, UI validation & audit CSV, Gradio wiring, plotting, score audit rows, bibliography mirror checks, parameter validation, overlap semantics, MusicXML corpora.

---

## 11. Documentation map (human-readable)

| Document | Audience | Content |
|----------|----------|---------|
| `README.md` | Quick start | Install, scope, tabs overview, schema 1.5 pointer. |
| `QUICK_REFERENCE.md` | One-page | Inputs, outputs, presets, troubleshooting. |
| `TECHNICAL_MANUAL.md` | Full | Tutorial §3, formulas §1, UI §3.0, instruments §9.5, bibliography §18. |
| `docs/ARCHITECTURE.md` | Developers | Module map, CI, coverage notes. |
| `docs/METRIC_CODE_MAP.md` | Developers | Metric → file map. |
| `docs/H_TIMBRAL_SCORE_REPRESENTATION.md` | Method | Sounding pitch, notation context, percussion register, persistence rules. |
| `docs/H_TIMBRAL_*.md` | Method | Per-family timbral assumptions. |
| `docs/model_audit/*` | Audit | Model revision summary, assumptions audits. |
| `docs/QUICK_REFERENCE_SYMBOLIC_NAMES.md` | Reference | Canonical IDs and parsers. |

---

## 12. Known limitations (inherent to design)

- **Symbolic only:** no audio analysis; fusion is **heuristic** and bibliography-governed at metadata level, not a substitute for measurements.
- **H vs H_timbral pitch basis** mismatch on transposed staves unless scores are pre-normalized (see `homogeneity.py` module docstring vs `H_TIMBRAL_SCORE_REPRESENTATION.md`).
- **Heuristic text parsing:** free-text directions vary by publisher; unknown states are common.
- **Homogeneity pitch bins** span global score range by default → cross-score comparability of raw m1 needs care (discussed in project audits / manual).

---

## 13. Summary statistics (approximate)

| Measure | Approximate value |
|---------|-------------------|
| Production Python modules under `src/homogeneity_analyser/` | **~67** |
| Analyzer modules alone | **29** |
| Pytest files under `tests/` | **~45** |
| Automated tests (last full run in development) | **565+** executed, **2** optional skips (env-gated doc scans) |

---

## 14. Change control recommendation

- Treat **`src/`** + **`pyproject.toml`** + **`tests/`** as the release boundary.
- Regenerate distributable ZIP/tar with **`git archive`** or a script that excludes `build/`, `dist/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.coverage`, `*.egg-info/`, and local private material (`private_sources/`, local PDFs if policy requires).

---

*End of report.*
