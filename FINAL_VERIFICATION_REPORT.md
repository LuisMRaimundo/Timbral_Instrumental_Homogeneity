# Final verification report — H_TA_acoustic_proxy audit

**Supplement (2026-06-10):** Docs/CI alignment — **`iav`** runtime dependency documented; CircleCI + GitHub Actions install paths; test count **975 passed** (includes symbolic high-risk and musicological plausibility contract layers). CircleCI **ruff** job temporarily removed.

**Supplement (2026-05-31):** Timbral_Instrumental_Homogeneity branding alignment; **`hti_comparability_class`** export; edge-window plot markers / `exclude_edge_windows`; modular refactor (`hti_comparability.py`, `hti_analyze_series.py`, `timbral_event_build.py`); exporter taxonomy aliases; `__version__` **2.0.0**. No change to **H_TI_core** numerics on golden fixtures.

**Supplement (2026-05-20):** Controlled cleanup — archived root `SANITATION_*.md` → `docs/archive_legacy/`; added **`docs/CLEANUP_REPORT.md`**; refreshed export-path docs (`hti_export_rows` canonical). No `H_TI_core` or public CSV/JSON schema change. Latest full pytest: **884 passed**.

**Supplement (2026-05-19):** Golden `H_TI_core` tests; `hti_*` helper modules; UI split — `ui/hti_ui_params.py`, `legacy_ui_params.py`, `timbral_ui_params.py`, `legacy_multimetric_ui_params.py`, `callback_result_formatting.py` with matching `test_*_ui_params.py` / extended `test_ui_callbacks_smoke.py`. No numerical or CSV/JSON schema change. Coverage gate **`fail_under = 77`**.

**Date:** 2026-05-19 (verification body); counts refreshed 2026-05-20  
**Repository:** `Timbral_Instrumental_Homogeneity` (GitHub: https://github.com/LuisMRaimundo/Timbral_Instrumental_Homogeneity)  
**Code authority:** `src/homogeneity_analyser/` only

---

## 1. Tests run

| Suite | Command | Result |
|-------|---------|--------|
| **Full pytest** | `python -m pytest tests/ -q` | **975 passed**, 3 skipped, 14 warnings (~20 s typical) |
| **Proxy + H_TI guard** | `test_timbral_acoustic_proxy_*.py`, `test_hti_refinement.py`, `test_json_export.py`, `test_documentation_consistency.py` | Included in full run; all passed |
| **New numerical guard** | `test_analyze_hti_core_hti_strict_unchanged_when_acoustic_proxy_toggled` | **Passed** — compares full `analyze_hti` series with `equal_nan=True` |

**Skipped (env-gated, unchanged):** `test_release_mode_technical_manual_narrative_still_clean`, `test_release_gate_no_stale_primary_timbral_tab_phrase`.

---

## 2. Ruff (full repository)

| Command | Result |
|---------|--------|
| `python -m ruff check .` | **All checks passed** |

**Actions taken this pass:**

- `ruff check --fix` on proxy test modules (import sorting).
- **`pyproject.toml` per-file ignores** documented for intentional debt:
  - `packaging/*`: E501, I001 (launcher / Windows packaging)
  - `tools/*`: E501 (emergency restore script)
  - `src/.../timbral_acoustic_proxy.py`: E501, SIM102 (long conditionals in kernel)
  - `src/.../hti.py`: E501, SIM114 (export NaN branch table)
  - `src/.../symbolic_blend_layers.py`: RUF046 (`int(round(...))` idiom)

No behavioural changes from ruff configuration.

---

## 3. Mypy

| Command | Result |
|---------|--------|
| `python -m mypy src/homogeneity_analyser` | **Success: no issues found in 97 source files** |

**Fix applied:** `timbral_acoustic_proxy.py` line 133 — guard `row.get(...)` before `float()` (`arg-type`).

---

## 4. H_TI JSON schema **3.0** — active documentation

| Document | H_TI `3.0` cited | Notes |
|----------|------------------|--------|
| `README.md` | Yes | § JSON exports |
| `QUICK_REFERENCE.md` | Yes | JSON + dynamic_conditioning |
| `TECHNICAL_MANUAL.md` | Yes | §0 checklist, §3 pipeline, §10 JSON |
| `CURRENT_CODE_CHARACTERISTICS_REPORT.md` | Yes | Bundle table |
| `docs/METRIC_CODE_MAP.md` | Yes | H_TI row |
| `docs/H_TA_ACOUSTIC_PROXY.md` | Yes | JSON schema section |

**Code:** `HTI_EXPORT_SCHEMA_VERSION = "3.0"` in `services/json_export.py` (asserted in tests).

**Stale 2.9 in active docs:** none (only **§2.9)** harmonic-pitch section title in `TECHNICAL_MANUAL.md`, and historical **`docs/archive_legacy/*`**).

---

## 5. Combined JSON schema **1.8** — legacy labelling

| Document | Labelled legacy/internal |
|----------|-------------------------|
| `README.md` | “Combined/legacy research JSON”; internal analysers for tests/research |
| `QUICK_REFERENCE.md` | “batch research”; not Gradio product surface |
| `TECHNICAL_MANUAL.md` | “Combined / legacy JSON”; “Library-only” |
| `CURRENT_CODE_CHARACTERISTICS_REPORT.md` | “Legacy / internal”; not main user-facing surface |
| `docs/METRIC_CODE_MAP.md` | “combined legacy bundle **1.8**” |
| `docs/H_TA_ACOUSTIC_PROXY.md` | “combined/legacy bundles remain **1.8**” |

---

## 6. H_TA — not presented as audio measurement

Active docs and UI state clearly that **`H_TA_acoustic_proxy`** is:

- score-derived organology kernel;
- **not** measured audio, **not** FFT/SPL, **not** perceptually validated fusion;
- orthogonal to **`H_TI_core`**.

Representative sources: `README.md` (scope bullets), `QUICK_REFERENCE.md` (§ optional proxy + scope), `TECHNICAL_MANUAL.md` (§10 3.0 acoustic-proxy), `docs/H_TA_ACOUSTIC_PROXY.md`, `gradio_app.py` accordion copy, `json_export.py` semantics strings, module docstring in `timbral_acoustic_proxy.py`.

No active document presents **`H_TA`** as a loudness meter, masking measurement, or waveform analysis product.

---

## 7. Default `include_acoustic_proxy=false`

| Location | Value |
|----------|--------|
| `services/constants.py` → `DEFAULT_HTI_PARAMS` | `"include_acoustic_proxy": False` |
| `ui/callbacks_hti.py` → `run_hti_app` signature (facade: `callbacks.py`) | `include_acoustic_proxy=False` |
| `ui/gradio_app.py` checkbox | `DEFAULT_HTI_PARAMS.get("include_acoustic_proxy", False)` |
| `services/analysis_service.py` | `bool(p.get("include_acoustic_proxy", False))` |
| `docs/H_TA_ACOUSTIC_PROXY.md` parameters table | `false` |

---

## 8. Numerical identity — `H_TI_core`, `H_TI`, `H_TI_strict`

| Check | Result |
|-------|--------|
| Unit: `test_hti_core_unchanged_when_acoustic_proxy_enabled` | `compute_H_TI` independent of proxy flag |
| Integration: `test_analyze_hti_core_hti_strict_unchanged_when_acoustic_proxy_toggled` | Full `analyze_hti` — `H_TI_core`, `H_TI`, `H_TI_strict` **identical** (proxy off vs on); `H_TA_acoustic_proxy` finite only when on |
| Full regression suite | **975 passed** (2026-06-10) — no unexplained numeric failures |

**Conclusion:** No numerical regression in **`H_TI_core`** / **`H_TI`** / **`H_TI_strict`** from enabling the acoustic proxy.

---

## 9. Generated material / archives (sanitation carry-over)

| Path | Status |
|------|--------|
| `build/`, `dist/`, `*.egg-info/`, `site/`, `portable/` install tree | **Absent** on disk |
| `__pycache__/`, `.pytest_cache/` | Regenerated locally by test runs; **gitignored** |
| Stale master doc / audit / narrative | **Archived** under `docs/archive_legacy/` with historical header |
| Broken `project_cleanup_report.md` | **Removed** |

---

## 10. Files changed in this verification pass

| File | Change |
|------|--------|
| `src/homogeneity_analyser/analyzers/timbral_acoustic_proxy.py` | Mypy-safe `float()` on taxonomy lookup |
| `tests/test_timbral_acoustic_proxy_audit.py` | Integration test; import fix; remove unused variable |
| `tests/test_timbral_acoustic_proxy_ranking.py` | Ruff import sort (auto-fix) |
| `pyproject.toml` | Documented ruff per-file ignores |

---

## Summary

| Criterion | Status |
|-----------|--------|
| Full pytest | **975 passed** (2026-06-10 refresh) |
| Ruff full repo | **Clean** (documented per-file ignores) |
| Mypy | **Clean** |
| Schema 3.0 docs | **Consistent** (active set) |
| Schema 1.8 legacy labels | **Consistent** |
| H_TA non-audio messaging | **Consistent** |
| Default proxy off | **Confirmed** |
| H_TI_core numerics | **No regression** |
| Repo hygiene | **Confirmed** from sanitation pass |

## 11. Documentation refresh (follow-up)

Active documentation was updated to reflect:

- H_TI JSON **schema 3.0** and combined JSON **1.8** as legacy/internal
- Separate Gradio accordions for **interval-class / symbolic-blend** vs **H_TA_acoustic_proxy**
- **`timbral_acoustic_affinity_evidence_status`** rules (`dynamic_used_explicit_notated`, `technique_default_only`, …)
- Pointer from README to **`docs/archive_legacy/`** instead of removed active **`SCIENTIFIC_TECHNICAL_AUDIT.md`** path

Files touched: `README.md`, `QUICK_REFERENCE.md`, `TECHNICAL_MANUAL.md`, `CURRENT_CODE_CHARACTERISTICS_REPORT.md`, `docs/H_TA_ACOUSTIC_PROXY.md`, `docs/METRIC_CODE_MAP.md`, `docs/ARCHITECTURE.md`, `docs/index.md`, `src/homogeneity_analyser/ui/components.py`.

### Maintainability (export registry, follow-up)

- **`HTI_SYMBOLIC_BLEND_SERIES_KEYS`** / **`append_hti_symbolic_blend_series_row`** in `symbolic_blend_layers.py` — one place for optional symbolic-blend CSV/JSON columns; `hti.py` unpacks the tuple instead of repeating twelve names.
- **`tests/test_hti_symbolic_blend_exports.py`** — guards CSV/JSON alignment and CSV JSON encoding for dict columns.
- Doc test: every registry key appears in **`QUICK_REFERENCE.md`**.

### Interval-class export labelling (follow-up)

- New guide: **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`** (stable keys vs display labels, **`seconds_sevenths`** semantics, literal vs mod‑12 mass profiles).
- Exports: **`interval_class_profile_display`**, **`literal_interval_semitone_pair_mass`**, **`chromatic_mod12_pair_mass`** (when `include_symbolic_blend_potential`).
- Taxonomy metadata: **`interval_class_semantics_note`** / **`interval_class_display_labels`** in `symbolic_blend_conditioning.json` v1.2.
- UI copy: Gradio symbolic-blend accordion + **`METRICS_EXPLAINER`**.
- Consistency test: `test_docs_interval_class_seconds_sevenths_semantics` in `tests/test_documentation_consistency.py`.

*End of final verification report.*

---

## 12. Module refactor — documentation sync (2026-05-31)

Active docs updated for the **structural split** (no metric or export-schema changes):

- **H_TI:** `hti_window_features.py`, `hti_register_compactness.py`, `hti_analyze_series.py`; `hti.py` = orchestration + re-exports
- **Symbolic pipeline:** `symbolic_event_pipeline.py`, `symbolic_instrument_resolve.py`, `symbolic_pitch_resolve.py`
- **UI:** `callbacks_hti.py`, `callbacks_legacy.py`, `callbacks_inspection.py`; `callbacks.py` = facade
- **New guides:** `docs/HTI_SYMBOLIC_PIPELINE.md`, `docs/PRODUCT_SCOPE.md`

Files touched: `README.md`, `MAINTAINERS.md`, `TECHNICAL_MANUAL.md`, `CURRENT_CODE_CHARACTERISTICS_REPORT.md`, `docs/ARCHITECTURE.md`, `docs/ONBOARDING_H_TI.md`, `docs/METRIC_CODE_MAP.md`, `docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`, `docs/CLEANUP_REPORT.md`, `analyzers/README.md`, `ui/README.md`, `docs/index.md`, `mkdocs.yml`.

Product-path pytest at sync time: **786 passed** (`pytest -m "not legacy"`).
