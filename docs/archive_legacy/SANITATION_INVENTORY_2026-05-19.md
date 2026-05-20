> **Historical.** Repository sanitation inventory (2026-05-19). Superseded by **`docs/CLEANUP_REPORT.md`** for later passes.

# Repository sanitation inventory (pre-deletion)

**Date:** 2026-05-19  
**Authoritative source:** `src/homogeneity_analyser/` only.

## 1. Keep

| Category | Paths |
|----------|--------|
| Package source | `src/homogeneity_analyser/**` |
| Tests | `tests/**`, fixtures under `tests/fixtures/` |
| Validation | `validation/**` |
| Packaging (maintainer) | `packaging/**`, `pyproject.toml`, `requirements*.txt`, `run.bat` |
| Active docs (root) | `README.md`, `QUICK_REFERENCE.md`, `TECHNICAL_MANUAL.md`, `CURRENT_CODE_CHARACTERISTICS_REPORT.md` |
| Active docs (`docs/`) | `H_TA_ACOUSTIC_PROXY.md`, `METRIC_CODE_MAP.md`, `ARCHITECTURE.md`, `index.md`, `STRING_HARMONIC_INTERVAL_REFERENCE.md`, `TIMBRAL_AFFINITY_LITERATURE_AUDIT.md`, `QUICK_REFERENCE_SYMBOLIC_NAMES.md`, `Instrumental articulation catalogue.md`, MkDocs wrappers `project_*.md` (snippets) |
| H_TIMBRAL design notes | `docs/H_TIMBRAL_*.md`, `docs/H_TIMBRAL_SCORE_REPRESENTATION.md`, `docs/H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md` — **internal/legacy module** docs; terminology headers to be updated to H_TI **3.0** |
| Bibliography | `docs/bibliography/**` |
| Model audit (internal) | `docs/model_audit/H_TIMBRAL_ASSUMPTIONS_AUDIT.md` |
| Scripts | `scripts/build_acoustic_source_registry_json.py`, `scripts/build_default_timbral_profile_json.py`, `scripts/make_release_zip.ps1` — referenced in YAML/comments/docs |
| Tools | `tools/emergency_restore_markdown.py` — recovery utility; uses `_appendix_d_extract.md` |
| Appendix extract | `_appendix_d_extract.md` — recovery source for manual appendix D |
| CI | `.github/**` |
| Pre-consolidation archive | `archive/pre_consolidation_2026/**` |
| Legacy archive | `docs/archive_legacy/**` |
| Legacy analyzers (tests/batch) | `timbral.py`, `fusion_acoustic_heuristic.py`, `notated_fusion_potential.py`, family pairwise modules — referenced by tests and combined export |

## 2. Delete (generated / transient / duplicate)

| Path | Reason |
|------|--------|
| `src/homogeneity_analyser.egg-info/` | setuptools generated metadata |
| `**/__pycache__/` | bytecode caches |
| `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` | tool caches |
| `.coverage` | local coverage run |
| `site/` | MkDocs build output |
| `dist_wheel_test/` | empty/local wheel smoke dir (not source) |
| `recovery/` | empty recovery scratch dir |
| `docs.zip`, `TECHNICAL_MANUAL.zip` | duplicate archives of docs |
| `Readme.mhtml`, `REadme.pdf`, `Technical Manual.mhtml`, `Technical Manual.pdf` | stale browser/PDF exports (canonical: `.md`) |
| `docs/METRIC_CODE_MAP.mhtml` | stale export of metric map |
| `Homogeneity_analiser_install/portable/` | ~19k vendored PyInstaller tree; **gitignored**; duplicates `src/`; not authoritative |

**Not present on disk:** `build/`, `dist/` at repo root (already absent).

## 3. Archive (move or relabel as historical)

| Path | Action |
|------|--------|
| `docs/HOMOGENEITY_ANALYSER_MASTER_DOCUMENT.md` | Move to `docs/archive_legacy/` — duplicates root manuals with stale schema **2.9** |
| `docs/SCIENTIFIC_TECHNICAL_AUDIT.md` | Move to `docs/archive_legacy/` — point-in-time audit snapshot (2.9-era) |
| `docs/TECHNICAL_MANUAL_NARRATIVE_HTI_2026.md` | Move to `docs/archive_legacy/` — excluded from MkDocs; stale 2.9 |
| `docs/project_cleanup_report.md` | Remove from MkDocs nav — broken snippet (`CLEANUP_REPORT.md` missing) |

## 4. Investigate (keep unless proven obsolete)

| Path | Why kept |
|------|----------|
| `private_sources/` | gitignored; local bibliography PDFs — do not delete |
| `Homogeneity_analiser_install/` (except `portable/`) | may contain README/setup assets |
| `tools/emergency_restore_markdown.py` | not in CI; intentional recovery |
| Legacy UI callbacks (`run_timbral`, combined paths in `callbacks.py`) | tests + backward compatibility |
| `docs/SCIENTIFIC_*` after archive | MkDocs nav updated |

## 5. Documentation conflicts to fix (active only)

- **Stale H_TI JSON schema `2.9`** in active docs → **`3.0`** (`HTI_EXPORT_SCHEMA_VERSION` in code).
- **`CURRENT_CODE_CHARACTERISTICS_REPORT.md`** table row still says schema 2.9 for README.
- **H_TIMBRAL_* headers** say “H_TI 2.9” → “H_TI 3.0” (terminology disclaimer only; no metric change).
- **`docs/project_cleanup_report.md`**: broken MkDocs include.
- **`METRIC_CODE_MAP.md`**: H_timbral rows are correct **legacy map** entries; add note that H_TA is separate from timbral_affinity relief.

## 6. `.gitignore` additions planned

- `dist_wheel_test/`, `recovery/`, `*.mhtml`, `docs.zip`, `TECHNICAL_MANUAL.zip`, `*.pdf` (root manual exports already partially covered)
