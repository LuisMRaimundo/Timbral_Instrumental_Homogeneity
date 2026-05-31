# Repository cleanup report

**Date:** 2026-05-20  
**Repository:** Homogeneity_analyser (`homogeneity_analyser`)  
**Scope:** Documentation hygiene, transient artifacts, archival of point-in-time reports. **No** analytical, numeric, or public export-schema changes.

---

## 1. Files deleted (local / generated)

| Path | Reason |
|------|--------|
| `src/homogeneity_analyser.egg-info/` | Setuptools generated metadata (gitignored) |
| `docs/Instrumental articulation catalogue.mhtml` | Stale browser export; canonical `.md` retained |
| `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `site/`, `.coverage` | Tool/build caches (if present) |
| `**/__pycache__/` under `src`, `tests`, `validation`, `scripts`, `tools` | Bytecode caches |

No source modules, shims, legacy analyzers, or test fixtures removed.

---

## 2. Files archived / moved

| From | To |
|------|-----|
| `SANITATION_INVENTORY.md` | `docs/archive_legacy/SANITATION_INVENTORY_2026-05-19.md` |
| `SANITATION_REPORT.md` | `docs/archive_legacy/SANITATION_REPORT_2026-05-19.md` |

`docs/archive_legacy/README.md` updated with pointers. Historical headers added to archived sanitation docs.

---

## 3. Documents updated

| File | Change |
|------|--------|
| `MAINTAINERS.md` | Coverage policy: `callbacks.py` in product path; pointer to this report |
| `TECHNICAL_MANUAL.md` | Canonical CSV columns → `hti_export_rows.py`; `callbacks.py` = file wiring |
| `docs/ARCHITECTURE.md` | UI helper modules listed; coverage note refreshed |
| `CURRENT_CODE_CHARACTERISTICS_REPORT.md` | `hti_export_rows` canonical; ~79% coverage; cleanup log pointer |
| `FINAL_VERIFICATION_REPORT.md` | Pytest **884**, mypy **97** files; 2026-05-20 supplement |
| `docs/index.md` | Link to this report |
| `src/homogeneity_analyser/analyzers/README.md` | Note re-export from `hti.py` |
| `docs/archive_legacy/README.md` | Sanitation archive entries |

---

## 4. Scripts removed or archived

**None.** Active scripts unchanged:

- `scripts/build_acoustic_source_registry_json.py`
- `scripts/build_default_timbral_profile_json.py`
- `scripts/make_release_zip.ps1`
- `tools/emergency_restore_markdown.py` (+ `_appendix_d_extract.md`)

---

## 5. Functions / imports / code lines removed

**None** in `src/` or `tests/`. Ruff F401/F841 was already clean before this pass.

---

## 6. Compatibility preserved

- `homogeneity_analyser.legacy/*` and `analyzers/*.py` shims unchanged
- `hti.py` re-exports from `hti_export_rows.py` unchanged
- `callbacks._timbral_config_from_optional` alias unchanged
- Tests importing `HTI_CSV_COLUMNS` from `analyzers.hti` unchanged

---

## 7. Tests

**No tests removed or weakened.** Existing golden, registry, shim, and UI helper tests retained.

---

## 8. Verification (post-cleanup)

| Tool | Command | Result |
|------|---------|--------|
| pytest | `python -m pytest tests/ -q` | **884 passed**, 3 skipped |
| coverage | `python -m pytest tests/ --cov=homogeneity_analyser -q` | **78.87%** total; gate **77** met |
| ruff | `python -m ruff check src tests` | All checks passed |
| mypy | `python -m mypy src/homogeneity_analyser` | Success — 97 source files |
| compileall | `python -m compileall -q src/homogeneity_analyser` | OK |
| mkdocs | `mkdocs build -q` | OK |

---

## 9. Numerical and schema confirmation

- **`H_TI_core` / `H_TI` / `H_TI_strict`:** not intentionally changed
- **H_TI JSON `schema_version`:** remains **3.0**
- **Combined legacy JSON:** remains **1.8**
- **Public CSV column sets:** unchanged (`HTI_CSV_COLUMNS` in `hti_export_rows.py`)

---

## 10. Phase A/B (2026-05-20) — onboarding and service split

| Change | Detail |
|--------|--------|
| **Phase A** | `docs/ONBOARDING_H_TI.md`; `timbral.py` docstring (pipeline vs H_timbral metric); `LEGACY.md`, `README.md`, `MAINTAINERS.md`, `docs/index.md`, `docs/ARCHITECTURE.md` |
| **Phase B** | `analysis_service_hti.py`, `analysis_service_legacy.py`, facade `analysis_service.py`; `tests/conftest.py` auto-marks legacy modules; `pytest -m "not legacy"` for day-to-day (~761 tests) |

No `H_TI_core` or export-schema changes.

## 11. Remaining debt (intentional)

| Item | Status (2026-05-31) |
|------|---------------------|
| `ui/callbacks.py` | **Resolved** — split into `callbacks_hti`, `callbacks_legacy`, `callbacks_inspection`, `callback_helpers`; facade only |
| `analyzers/hti.py` | **Reduced** — orchestration only; features in `hti_window_features.py`, register in `hti_register_compactness.py` |
| `analyzers/timbral.py` | Event build → `symbolic_event_pipeline.py`; instrument/pitch → `symbolic_instrument_resolve.py`, `symbolic_pitch_resolve.py` |
| `docs/archive_legacy/*` | Unchanged — historical schema **2.9** preserved |
| `docs/H_TIMBRAL_*.md` | **Indexed** — `docs/H_TIMBRAL_DESIGN_INDEX.md` + MkDocs **Internal design** nav |
| Test overlap | **Resolved** — single `write_temp_csv` test in `test_ui_audit_csv.py` |
| Optional vs legacy clarity | **Added** — `docs/PRODUCT_SCOPE.md`, `LEGACY.md` optional-layer table, MkDocs nav tiers |

---

*End of cleanup report.*
