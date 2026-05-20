This document is historical and is not the current specification.

# Scientific, technical, and documentation audit — Homogeneity_analyser

**Repository:** `Homogeneity_analyser`  
**Audit date:** 2026-04-30 (validation refresh)  
**Method:** Read codebase and docs; run `pytest`, `ruff check`, `ruff format --check`, `mypy`; map claims to tests. The **\(H_{\mathrm{TI,core}}\)** formula is unchanged by optional **adaptive window orchestration** (centre list + effective width/step only).

---

## 1. Executive verdict

The package is a **serious symbolic orchestration-analysis tool** with **strong regression coverage** for its stated scope (MusicXML/MIDI → event windows → **\(H_{\mathrm{TI,core}}\)** + dynamic conditioning + pitch interpretation + optional literature-governed affinity relief + conservative harmonic pitch audit + optional adaptive windowing + optional symbolic blend diagnostics). **770+ tests pass** (3 skipped) on the latest validation pass; re-run `pytest` after substantive changes. The design **explicitly disclaims** measured audio and perceptual fusion in multiple places (README, QUICK_REFERENCE, TECHNICAL_MANUAL, `docs/STRING_HARMONIC_INTERVAL_REFERENCE.md`).

It is **not** publication-grade psychoacoustic or acoustic-measurement software, and it **must not** be sold as validated perceptual science. Static gates (**`ruff check`**, **`ruff format --check`**, **`mypy src/homogeneity_analyser`**) are **green** on the current tree; residual risk remains in large partly-untyped surfaces (e.g. **`timbral.py`**, Gradio callbacks) and third-party deprecation noise. **Doctoral use** is defensible **only** with clear framing as symbolic / heuristic and with external validation for any empirical claim. **Public distribution** is acceptable as open tooling **if** limitations and non-audio scope stay prominent.

---

## 2. What works well

- **Deterministic pipeline:** music21 ingest → timbral events → overlap weighting → Herfindahl-style components → weighted geometric **\(H_{\mathrm{TI,core}}\)**; same path drives symbolic inspection tables.
- **Separation of concerns:** core scalar vs notated-dynamic **interpretation** layer vs optional **affinity relief** (default off).
- **Pitch interpretation modes** are implemented and **tested** (`tests/test_pitch_interpretation.py`) including `musicxml_sounding`, `xml_pitch_as_real`, `ignore_octave_transpositions_only`, `xml_pitch_as_real_with_octave_transposers`.
- **Microtonal / alter** handling has targeted tests (effective MIDI, vertical sonorities).
- **Exports:** dual schema — combined JSON **1.8** vs H_TI bundle **2.9** — documented in TECHNICAL_MANUAL, QUICK_REFERENCE, and tests.
- **Symbolic inspection** without running windowed H_TI: `build_symbolic_inspection_tables`, CSV outputs, column tests.
- **Affinity registry** is data-driven JSON with `rule_id`, tier, `profile_minimum`, `confidence`, `source_keys`, `release_status`.

---

## 3. What is scientifically strong

- **Symbolic coherence:** Instrument → subfamily → technique key → register evidence is a **consistent** decomposition for score-derived homogeneity.
- **Cautionary framing:** README / QUICK_REFERENCE / TECHNICAL_MANUAL stress **not audio**, **not measured fusion**; JSON carries `not_audio_analysis`.
- **Dynamic layer as interpretation:** Labels (e.g. soft blend potential, projection divergence risk) are tied to **notated** dynamics and coverage flags, not to waveform features.
- **Taxonomy-backed identity:** Unknown or ambiguous instruments are not given spurious high affinity in tests and affinity design.

---

## 4. What is scientifically weak or risky

- **No empirical calibration:** Component weights and similarity constants are **design choices**, not fit to listening data or ensemble recordings.
- **music21 dependence:** Parser quirks, part naming, and missing directions change events; **reproducibility across encoders** is a known MusicXML problem.
- **Heuristic fusion-adjacent metrics** (`H_notated_fusion_potential`, acoustic heuristic) remain in the codebase for research; they are easy to **misread** if users ignore “legacy / internal” labelling.
- **Literature links for affinity:** Most rules are **`source_key_only`** — bibliographic keys exist, but **page-verified** citations are not the default state; exploratory rules are explicitly weak.
- **Dynamic “interpretation”** is plausible orchestration language but **not validated** against scores of measured blend or masking.

---

## 5. Implementation risks

- **Stale `build/` / `dist/` trees:** If present locally, they are **generated only**; **`src/homogeneity_analyser/`** is the sole authoritative tree. **Maintainers must not** edit or release from `build/lib/` (see `docs/ARCHITECTURE.md`). Repository policy: ignore these paths (`.gitignore`) and delete them when cleaning a checkout.
- **Type safety:** `mypy src/homogeneity_analyser` passed on the validation pass; **`homogeneity_analyser.analyzers.homogeneity`** may still be under **`ignore_errors`** in config — revisit when refactoring.
- **Lint/format:** **`ruff check src tests`** and **`ruff format --check src tests`** were **clean** on the validation pass; future drift should be caught if CI enforces these gates.
- **Gradio / websockets:** Deprecation warning from dependency (pytest warnings); not a logic failure but **upgrade debt**.
- **Large surface in `timbral.py`:** Partial typing notes; high complexity increases regression risk when editing.

---

## 6. Documentation gaps fixed (this audit)

- **`docs/ARCHITECTURE.md`:** H_TI JSON version aligns with **`HTI_EXPORT_SCHEMA_VERSION`** (currently **2.9**); optional affinity and optional symbolic blend layers noted; `H_TI` vs `H_TI_core` vs relieved variant clarified.
- **`docs/METRIC_CODE_MAP.md`:** H_TI / register vs interval-class table + **2.9** export note; timbral affinity implementation paths.
- **`docs/TIMBRAL_AFFINITY_LITERATURE_AUDIT.md`:** Expanded to **one row per JSON `pair_rules` entry**, with tier, similarity, `profile_minimum`, release status, and **“safe when relief > 0?”** column.
- **`README.md`:** Pointer to this audit document.
- **`QUICK_REFERENCE.md` / `TECHNICAL_MANUAL.md`:** **`H_TI_strict`** documented as the numeric alias of **`H_TI_core`** for strict vs relieved comparisons in exports.
- **`tests/test_timbral_affinity_literature.py`:** Line length (E501) fixed to reduce noise in ruff output.
- **Adaptive windows (validation refresh):** README / QUICK_REFERENCE / `TECHNICAL_MANUAL.md` §2.10 and §3.1, `docs/ARCHITECTURE.md`, `docs/METRIC_CODE_MAP.md`, harmonic / affinity audit cross-notes; `tests/test_hti_adaptive_windows.py` + Gradio test fake fixes.

---

## 7. Tests run and results

| Command | Result (validation pass; re-run after edits) |
|--------|--------|
| `python -m pytest -q` | **755 passed**, **3 skipped** |
| Skipped | `test_documentation_consistency.py` (2): release-mode env vars not set; `test_technical_manual_bibliography.py` (1): conditional skip |
| Warnings | 1× `websockets.legacy` DeprecationWarning (third-party) |
| `ruff check src tests` | **Clean** |
| `ruff format --check src tests` | **Clean** |
| `mypy src/homogeneity_analyser` | **Success** (78 files); notes only on unchecked untyped defs in some modules |

**H_TI workflow impact:** **pytest** and static gates were **green** on this pass. Adaptive windowing adds **`tests/test_hti_adaptive_windows.py`** and export columns; it does **not** alter **\(H_{\mathrm{TI,core}}\)** numerics in **manual** mode (regression-tested against direct `analyze_hti`).

---

## 8. Remaining failures / warnings

- **Third-party:** `websockets.legacy` DeprecationWarning under pytest (Gradio dependency).
- **Skipped tests** require `HOMOGENEITY_ANALYSER_RELEASE_DOCUMENTATION=1` / `HOMOGENEITY_ANALYSER_RELEASE_GATE=1` for full release narrative scans.

---

## 9. Before / after corrections

| Item | Before | After |
|------|--------|--------|
| ARCHITECTURE H_TI JSON version | 2.3 | **2.9** |
| METRIC_CODE_MAP affinity | absent | **Row added** |
| Literature audit vs registry | Partial rows | **All `pair_rules` tabulated** |
| README audit trail | — | **Link to this file** |
| test E501 | Long line | **Wrapped** |

---

## 10. Core scientific behaviour vs tests (mapping)

| Scenario | Primary test / module evidence |
|----------|--------------------------------|
| A — identical instruments, compact | `test_clarinet_timbral.py`, `test_hti_refinement.py`, overlap/register suites |
| B — clarinet + bass clarinet | `test_timbral_affinity_literature.py`, `test_clarinet_timbral.py` |
| C — oboe + bassoon vs oboe + EH | affinity pairwise ordering tests |
| D — cross-family | `test_orchestration_symbolic.py`, timbral robustness / fusion corpus tests |
| E — arco + pizz | `test_string_timbral.py`, `test_technique_uniformity_hti.py` |
| F — no explicit techniques | `test_technique_uniformity_hti.py`, timbral affinity “do not invent” tests |
| G — register compactness sparse vs dense | `test_hti_register_compactness.py`, `test_overlap_homogeneity_register.py` |
| H — microtons | `test_pitch_interpretation.py` |
| I — pitch modes | `test_pitch_interpretation.py`, `test_musicxml_symbolic_corpus.py` |
| J — dynamics | `test_hti_dynamic_conditioning.py`, `test_notated_fusion_dynamic.py`, `test_timbral_affinity_literature.py` (dynamic guards) |

**Symbolic inspection:** `test_pitch_interpretation.py` (event audit columns, vertical sonorities fractional MIDI), `test_symbolic_inspection_callbacks.py`, `test_score_audit.py`, `TECHNICAL_MANUAL.md` § UI.

**JSON/CSV:** `test_json_export.py` (`not_audio_analysis`, schema, affinity keys), `test_ui_audit_csv.py`.

---

## 11. Rating table (1–100, strict scale)

| Criterion | Score | Comment |
|-----------|------:|---------|
| **A. Scientific / methodological validity** (symbolic claim only) | **72** | Coherent decomposition; weights and S-values not empirically calibrated. |
| **B. Symbolic-score modelling coherence** | **84** | Internally consistent; pitch + technique + register paths align. |
| **C. Acoustic / psychoacoustic caution** | **81** | Good disclaimers; legacy “fusion” naming elsewhere still demands careful reading. |
| **D. Implementation robustness** | **68** | Tests pass; mypy/ruff debt and large modules. |
| **E. Test coverage** | **86** | Broad pytest suite for H_TI and edge cases; not formal coverage % gate in this audit. |
| **F. Documentation quality** | **78** | Strong manuals; some secondary docs lagged (fixed in §6); dual schema confuses newcomers. |
| **G. Usability (non-technical)** | **62** | Gradio helps; concepts remain specialist; parameter surface is large. |
| **H. Reproducibility / auditability** | **74** | JSON exports + tests; encoder variance and unverified literature keys limit audit strength. |
| **I. Doctoral research readiness** | **71** | Usable as **tool + appendix** with explicit limits; not standalone perceptual evidence. |
| **J. Public distribution readiness** | **69** | OK as OSS-style tool with warnings; clean ruff/mypy/CI would be expected for “polished” release. |

---

## 12. Overall score

**Weighted judgement — Overall: 74 / 100**

Interpretation: **Strong prototype / research-grade engineering** with honest scope boundaries, **not** “95+ publication-ready validated science.”

---

## 13. What must be fixed before calling the software “final”

1. **CI quality bar:** `ruff check` clean (or scoped allowlist with justification), `ruff format` applied, **mypy** trending to zero or documented per-module policy (not broad `ignore_errors` without narrative).
2. **Remove or isolate stale `build/` artifacts** from packaging instructions so users never confuse generated lib with `src/`.
3. **Page-verified bibliography** for any rule marketed as “strong evidence” beyond taxonomy.
4. **Optional:** pandas-stubs / stricter UI typing to shrink mypy noise in `callbacks.py`.

---

## 14. What can remain as documented limitation

- **No audio analysis** — permanent product boundary.
- **Encoder-dependent MusicXML semantics** — document and version-test fixtures.
- **Optional affinity relief** — symbolic, profile-gated, default **off**; `source_key_only` rules stay labelled honestly.
- **Legacy internal metrics** — acceptable if confined to tests/scripts and clearly labelled in docs.

---

## Revision history

| Date | Change |
|------|--------|
| 2026-04-30 | Initial audit after full pytest + ruff + mypy survey; doc fixes listed in §6. |
