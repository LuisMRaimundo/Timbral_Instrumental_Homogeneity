# Maintainer guide — Orchomogeneity Analyser

Practical map for developers changing exports, weights, UI copy, or documentation. This project favours **small, test-backed edits** over large refactors.

## Product contract

- **`H_TI_core`** is the primary **score-based symbolic** timbral–instrumental homogeneity metric (Herfindahl-style concentration + register compactness + technique). **`H_TI`** in exports matches **`H_TI_core`** numerically.
- **Optional symbolic-blend** columns (`include_symbolic_blend_potential`) and **optional acoustic-proxy** columns (`include_acoustic_proxy`) are **diagnostics / proxies**. They do **not** replace **`H_TI_core`** and are **not** measured audio or perceptual validation.
- **Legacy multimetric** code lives under **`src/homogeneity_analyser/legacy/`** (H(t), H_cluster, fusion heuristics, U(t), …). **`homogeneity_analyser.analyzers.<name>`** paths are **compatibility shims** only. Combined JSON uses **`schema_version` `1.8`**; user-facing H_TI JSON uses **`3.0`**.

## Where to change what

| Area | Primary locations |
|------|-------------------|
| **Core H_TI / organological homogeneity** | **Orchestration:** `analyzers/hti.py` — **implementation:** `hti_window_features.py`, `hti_register_compactness.py`, `hti_active_weights.py`, `hti_technique_coverage.py`, `hti_concentration.py`, `hti_analyze_series.py`, `hti_comparability.py`, `hti_export_rows.py` — map in `analyzers/README.md` and **`docs/HTI_SYMBOLIC_PIPELINE.md`** |
| **Symbolic score → events (shared H_TI + H_timbral)** | `symbolic_event_pipeline.py`, `symbolic_instrument_resolve.py`, `symbolic_pitch_resolve.py`, `timbral_event_build.py`, `pitch_interpretation.py`, `technique_state.py`, `taxonomy/instrument_taxonomy.py` |
| **Gradio UI (tested helpers)** | `ui/callbacks.py` (facade); **`callbacks_hti.py`**, **`callbacks_legacy.py`**, **`callbacks_inspection.py`**, **`callback_helpers.py`**; `hti_ui_params.py`, `legacy_ui_params.py`, `timbral_ui_params.py`, `legacy_multimetric_ui_params.py`, `callback_result_formatting.py` — `ui/README.md` |
| **Legacy multimetric (internal)** | `legacy/` only — **`LEGACY.md`**; `analyzers/*.py` shims are re-exports; import via `homogeneity_analyser.legacy` |
| **Run orchestration & defaults** | **H_TI:** `services/analysis_service_hti.py` — **legacy metrics:** `services/analysis_service_legacy.py` — facade `analysis_service.py`; `constants.py`, `param_validation.py` |
| **Symbolic-blend optional layer** | `analyzers/symbolic_blend_layers.py`, `taxonomy/symbolic_blend_conditioning.json` |
| **Acoustic-proxy optional layer** | `analyzers/timbral_acoustic_proxy.py`, `taxonomy/acoustic_timbral_taxonomy.json` |
| **Literature timbral affinity relief** | `analyzers/timbral_affinity.py`, `acoustic_profiles/` registry |
| **Heuristic weights & taxonomy tables** | `taxonomy/*.json`, profile sections inside `symbolic_blend_conditioning.json` and `acoustic_timbral_taxonomy.json` |
| **CSV / JSON export column registries** | Symbolic/acoustic registries in `symbolic_blend_layers.py` / `timbral_acoustic_proxy.py`; column order in `hti_export_rows.py` (`HTI_CSV_COLUMNS`, `HTI_EXPORT_TIME_SERIES_KEYS`); bundle build in `services/json_export.py` |
| **CSV dict JSON encoding** | `hti_csv_row_dict()` in `hti_export_rows.py` — use `HTI_*_CSV_JSON_DICT_KEYS` frozensets |
| **Gradio UI & labels** | `ui/gradio_app.py`, static copy in `ui/components.py` (`METRICS_EXPLAINER`) |
| **User documentation** | `README.md`, `QUICK_REFERENCE.md`, `TECHNICAL_MANUAL.md`, `docs/*.md` (see `docs/index.md`, `mkdocs.yml`) |

## Export fields — do not duplicate names

When adding or renaming a **per-window export column**:

1. Add the stable key to the correct registry tuple (`HTI_SYMBOLIC_BLEND_SERIES_KEYS` or `HTI_ACOUSTIC_PROXY_SERIES_KEYS`). If the CSV stores a JSON-encoded dict, add it to the matching `*_CSV_JSON_DICT_KEYS` frozenset.
2. Wire **`hti_analyze_series.py`** (`HTI_ANALYZE_SERIES_KEYS`) and **`hti_export_rows.py`** (`HTI_CSV_COLUMNS`, `HTI_EXPORT_TIME_SERIES_KEYS`) — do not paste the same string list in four places. `hti.py` re-exports tuples for backward-compatible imports only.
3. Extend **`append_hti_*_series_row`** (or `acoustic_proxy_series_value` semantics) for enabled/disabled/empty-window behaviour.
4. Update **`hti_csv_row_dict`** if the column is dict-shaped in CSV.
5. Add or extend tests in `tests/test_hti_symbolic_blend_exports.py` and/or `tests/test_hti_acoustic_proxy_exports.py`.
6. Update **`QUICK_REFERENCE.md`** (and `docs/METRIC_CODE_MAP.md` when the field is a named metric). Run `tests/test_documentation_consistency.py`.

## Tests to run after export / weight / label changes

```bash
python -m pytest tests/test_hti_symbolic_blend_exports.py tests/test_hti_acoustic_proxy_exports.py tests/test_legacy_package.py tests/test_coverage_policy.py tests/test_documentation_consistency.py tests/test_json_export.py tests/test_timbral_acoustic_proxy_audit.py -q
python -m pytest tests/ --cov=homogeneity_analyser --cov-report=term-missing -q
python -m ruff check src tests
python -m mypy src/homogeneity_analyser
```

**Coverage policy:** `pyproject.toml` enforces **`fail_under = 77`** on the **product path** (`legacy/*` omitted; UI facade + **`callbacks_hti.py`** included — see `tests/test_coverage_policy.py`). Pure UI adapters (`hti_ui_params.py`, `legacy_*_ui_params.py`, `callback_result_formatting.py`) carry focused tests. Measured product-path coverage is ~78–79%. Prefer **localized tests** over inflating the global threshold.

**Cleanup log:** `docs/CLEANUP_REPORT.md` — archived point-in-time reports under `docs/archive_legacy/`.

**Onboarding:** `docs/ONBOARDING_H_TI.md`, **`docs/PRODUCT_SCOPE.md`**, **`docs/HTI_SYMBOLIC_PIPELINE.md`** — symbolic pipeline vs legacy metrics.

**Tests (day-to-day):** `python -m pytest tests/ -m "not legacy" -q` — full suite without marker runs everything.

## What to avoid

- **Changing `H_TI_core` weights or formulas** without explicit approval and numeric regression tests (`test_hti_core_golden_outputs.py`, `test_hti_refinement.py`, `test_analyze_hti_core_hti_strict_unchanged_when_*`).
- **Renaming public export columns** without updating registries, docs, and consistency tests in the same change.
- **Adding logic to `hti.py` or `timbral.py` facades** when a dedicated module exists (see **`docs/HTI_SYMBOLIC_PIPELINE.md`**) — extend the focused module instead.

## Optional layers (quick reference)

| Parameter | Registry / helper module |
|-----------|-------------------------|
| `include_symbolic_blend_potential` | `symbolic_blend_layers.py` — `docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md` |
| `include_acoustic_proxy` | `timbral_acoustic_proxy.py` — `docs/H_TA_ACOUSTIC_PROXY.md` |
| `acoustic_proxy_include_interval_class` | API only (`constants.py`); same stable interval-class keys as symbolic layer |
