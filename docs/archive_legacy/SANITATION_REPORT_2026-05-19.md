> **Historical.** Repository sanitation report (2026-05-19). Superseded by **`docs/CLEANUP_REPORT.md`** for later passes.

# Repository sanitation report — Homogeneity_analyser

**Date:** 2026-05-19  
**Pre-deletion inventory:** `SANITATION_INVENTORY.md`

## 1. Files deleted

| Path | Category |
|------|----------|
| `src/homogeneity_analyser.egg-info/` | Generated package metadata |
| All `**/__pycache__/` | Bytecode caches |
| `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` | Tool caches |
| `.coverage` | Local coverage artifact |
| `site/` | MkDocs build output |
| `dist_wheel_test/` | Empty/local wheel test dir |
| `recovery/` | Empty scratch dir |
| `docs.zip`, `TECHNICAL_MANUAL.zip` | Duplicate doc archives |
| `Readme.mhtml`, `REadme.pdf`, `Technical Manual.mhtml`, `Technical Manual.pdf` | Stale browser/PDF exports |
| `docs/METRIC_CODE_MAP.mhtml` | Stale metric-map export |
| `Homogeneity_analiser_install/portable/` | ~19k-file vendored PyInstaller tree (duplicate of `src/`; already gitignored) |
| `docs/project_cleanup_report.md` | Broken MkDocs snippet (missing `CLEANUP_REPORT.md`) |

**Not on disk:** `build/`, `dist/` at repo root.

## 2. Files moved to archive

Moved to `docs/archive_legacy/` with header *“This document is historical and is not the current specification.”*:

| From | To |
|------|-----|
| `docs/HOMOGENEITY_ANALYSER_MASTER_DOCUMENT.md` | `docs/archive_legacy/HOMOGENEITY_ANALYSER_MASTER_DOCUMENT.md` |
| `docs/SCIENTIFIC_TECHNICAL_AUDIT.md` | `docs/archive_legacy/SCIENTIFIC_TECHNICAL_AUDIT.md` |
| `docs/TECHNICAL_MANUAL_NARRATIVE_HTI_2026.md` | `docs/archive_legacy/TECHNICAL_MANUAL_NARRATIVE_HTI_2026.md` |

`docs/archive_legacy/README.md` updated with pointers.

## 3. Files edited

| File | Change |
|------|--------|
| `TECHNICAL_MANUAL.md` | H_TI JSON `schema_version` **2.9 → 3.0**; §10 adds **3.0 acoustic-proxy** note |
| `CURRENT_CODE_CHARACTERISTICS_REPORT.md` | Doc map: schema **3.0** + H_TA |
| `docs/ARCHITECTURE.md` | Schema **3.0** + H_TA pointer |
| `docs/H_TIMBRAL_*.md` (9 files) | Terminology header: **H_TI 3.0** |
| `docs/model_audit/H_TIMBRAL_ASSUMPTIONS_AUDIT.md` | Same terminology header |
| `mkdocs.yml` | Removed broken cleanup / archived nav; added **H_TA_ACOUSTIC_PROXY** |
| `.gitignore` | `dist_wheel_test/`, `recovery/`, `*.mhtml`, doc zips |
| `tests/test_gradio_wiring.py` | `run_hti_app` input count **28 → 31** (acoustic-proxy UI controls; wiring only) |

**No changes** to `src/homogeneity_analyser/analyzers/hti.py`, metric weights, or `H_TI_core` computation.

## 4. Documentation conflicts resolved

| Issue | Resolution |
|-------|------------|
| Active docs cited H_TI JSON **2.9** while code uses **3.0** | Updated root manual, architecture, characteristics report |
| Duplicate master doc / audit / narrative vs root manuals | Archived with historical header |
| Broken MkDocs cleanup page | Removed file and nav entry |
| H_TIMBRAL “blend” vs H_TI export fields | Headers now reference **H_TI 3.0**; `METRIC_CODE_MAP.md` already separates **H_TA_acoustic_proxy** from **timbral_affinity_*** relief |

**Intentionally unchanged in archive:** schema **2.9** mentions in `docs/archive_legacy/*` (historical snapshots).

## 5. Unused scripts/modules removed

**None.** `scripts/*` and `tools/emergency_restore_markdown.py` remain referenced by YAML, docs, or recovery workflow.

## 6. Generated/cached material removed

See §1. `.gitignore` now covers common re-generation paths.

## 7. `.gitignore` changes

Added: `dist_wheel_test/`, `recovery/`, `*.mhtml`, `docs.zip`, `TECHNICAL_MANUAL.zip`.

## 8. Tests and tooling

| Tool | Result |
|------|--------|
| **pytest** (full `tests/`) | **802 passed**, 3 skipped, 0 failed |
| **pytest** (metric guard subset) | 74 passed (docs + H_TA + H_TI refinement + JSON export) |
| **ruff check** `src` `tests` | **14 issues** (mostly E501/SIM102/I001; pre-existing style debt) |
| **mypy** `src/homogeneity_analyser` | **1 error** in 1 file (pre-existing; 80 files checked) |

Skipped by env (unchanged): `test_release_mode_technical_manual_narrative_still_clean`, `test_release_gate_no_stale_primary_timbral_tab_phrase` (need `HOMOGENEITY_ANALYSER_RELEASE_*` env vars).

## 9. Investigate (kept)

| Item | Reason |
|------|--------|
| `tools/emergency_restore_markdown.py` | Manual recovery; uses `_appendix_d_extract.md` |
| `_appendix_d_extract.md` | Appendix D source for recovery tool |
| Legacy analyzers (`timbral.py`, fusion heuristics, …) | Tests + combined JSON **1.8** paths |
| `archive/pre_consolidation_2026/` | Already labelled pre-consolidation |
| `private_sources/` | Local bibliography (gitignored) |
| `Homogeneity_analiser_install/` (non-portable) | May hold installer README/assets |

## 10. Obsolete material intentionally preserved

- **H_timbral** pairwise subsystem and `docs/H_TIMBRAL_*.md` — internal design for shared event construction.
- **Combined JSON `schema_version` `1.8`** — batch/tests; documented as non–user-facing.
- **Legacy UI callbacks** (`run_timbral`, combined runs) — backward compatibility in `callbacks.py`.
- **`docs/archive_legacy/report_legacy_multimetric.md`** — multi-tab / 1.5 narrative.

## 11. Numerical behaviour — H_TI_core / H_TI / H_TI_strict

**Confirmed unchanged.** Sanitation touched documentation, generated artifacts, archived stale docs, and Gradio **wiring test counts** only. No edits to `compute_H_TI`, Herfindahl weights, register compactness, or dynamic conditioning logic.

## 12. H_TA_acoustic_proxy

**Confirmed:** remains **optional** (`include_acoustic_proxy` default **false**); documented in `README.md`, `QUICK_REFERENCE.md`, `docs/H_TA_ACOUSTIC_PROXY.md`, and `TECHNICAL_MANUAL.md` §10 as a **score-derived acoustic-informed symbolic timbral-affinity proxy** — **not** audio, FFT, SPL, or perceptually validated fusion. Orthogonal to **timbral_affinity_*** literature relief on **H_TI**.

---

*End of sanitation report.*
