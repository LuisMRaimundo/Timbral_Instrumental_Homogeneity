# Orchomogeneity

**Orchomogeneity** is an H-TI analyser for timbral–instrumental homogeneity analysis in MusicXML/MXL/MIDI orchestral scores.

Python package **`homogeneity-analyser`** and **Gradio** app computing **H_TI** / **H_TI_core** — score-derived, symbolic homogeneity from notation (not audio analysis).

---

## Quick start

| Audience | Action |
|----------|--------|
| **No Python** (Windows 10/11) | Double-click [`instalers/windows/INSTALL.bat`](instalers/windows/INSTALL.bat) |
| **No Python** (macOS / Linux) | See [`instalers/README.md`](instalers/README.md) → `install-easy.sh` |
| **Developers** | `pip install -r requirements.txt` then `homogeneity-analyser` (or `pip install -e .`) |

First end-user install may take **10–25 minutes** (Internet required).

---

## Legal and citation

| File | Purpose |
|------|---------|
| [`NOTICE.md`](NOTICE.md) | Copyright and use terms (proprietary; no open-source licence granted). |
| [`CITATION.cff`](CITATION.cff) | Citation metadata for software recognition. |

---

## Installers (optional)

**Repository:** https://github.com/LuisMRaimundo/orchomogeneity

End users without Python: see [`instalers/`](instalers/) — especially on Windows, double-click **`instalers/windows/INSTALL.bat`** (installs Python 3.11, downloads this repo, installs libraries, creates shortcuts).

Reference installer layout (same pattern as [SoundSpectrAnalyse](https://github.com/LuisMRaimundo/SoundSpectrAnalyse)):

| Folder | Standard install | Portable build (PyInstaller) |
|--------|------------------|------------------------------|
| `instalers/windows/` | `INSTALL.bat` | `Build-All.ps1` |
| `instalers/mac/` | `install-easy.sh` | `build-all.sh` |
| `instalers/linux/` | `install-easy.sh` | `build-all.sh` |

Built `.exe` / `.app` / `.dmg` / `.tar.gz` files are **not** in git — use [GitHub Releases](https://github.com/LuisMRaimundo/orchomogeneity/releases) if you distribute frozen builds.

Maintainer builds: [`packaging/windows/`](packaging/windows/).

---

## Acknowledgements

This project was developed by **Luís Raimundo** with the support and funding of the **Fundação para a Ciência e a Tecnologia (FCT)** and **Universidade NOVA de Lisboa**.

**Funding DOI:** https://doi.org/10.54499/2020.08817.BD

The author also gratefully acknowledges **Isabel Pires** for her support throughout the development of this work.

---

## Technical reference

---

## Purpose

$H_{\mathrm{TI},\mathrm{core}}(t)$ summarises, in each sliding window, how concentrated **active sounding overlap mass** is on:

- **Canonical instruments** (Herfindahl $U_{\mathrm{instr}}(t)=\sum_i P_i(t)^2$; taxonomy-normalised names and aliases),
- **Instrumental subfamilies** ($U_{\mathrm{fam}}(t)=\sum_f P_f(t)^2$ on the taxonomy `family` field, e.g. `clarinets`, `brass`),
- **Technique** (when admitted): **technique_uniformity** $U_{\mathrm{tech}}(t)=\sum_{k\in K_t} Q_k(t)^2$ groups overlap mass by the instrument-free **`technique_uniformity_key`** only,
- **Register compactness** $R_{\mathrm{compact}}(t)$ from **sounding MIDI** span and pairwise proximity vs a reference semitone span $r$ (export column **`register_proximity`** aliases the same value).

**Technique evidence:** **`H_TI_core`** uses the instrument-free **`technique_uniformity_key`** for **`technique_uniformity`** when the technique layer is admitted. The fuller **`technique_state_id`** remains available in symbolic inspection / audits and legacy diagnostics as a complete event-level fingerprint, but **it is not** the direct **`H_TI_core`** grouping key for **`technique_uniformity`**.

The headline series satisfy $H_{\mathrm{TI}}(t)=H_{\mathrm{TI},\mathrm{core}}(t)$ in exports (and $H_{\mathrm{TI},\mathrm{strict}}(t)$ duplicates the same array). The CSV/JSON column **`H_TI`** is the same scalar as **H_TI(t)**.

---

## Scope (what this software does **not** do)

- **`H_TI_core`** / $H_{\mathrm{TI},\mathrm{core}}$ **is symbolic and score-derived only** — overlap mass on notation events in sliding windows; it is **not** an acoustic homogeneity meter.
- **Not measured audio** — no audio files, no waveform buffers, microphones, or listening tests.
- **No FFT** of recordings, no **spectral analysis of audio**, no **SPL** estimation.
- **No measured timbral fusion** and **no perceptual validation** of blend or masking.
- **Notated dynamics** in the conditioning layer are **ordinal symbolic evidence** (fixed ladder `pppp` … `ffff`), **not** loudness in dB or SPL-derived levels.
- **Optional timbral-affinity relief** (parameter **`timbral_affinity_relief_factor`** strictly positive) is **symbolic**, **literature-governed** (registry `source_key` entries), and **not** measured timbral similarity or listening-validated fusion.
- **Optional acoustic-aligned timbral-affinity proxy** (**`H_TA_acoustic_proxy`** / **`timbral_acoustic_affinity`**, `include_acoustic_proxy`) is a **separate** event-level pairwise organology kernel — **not** a replacement for **`H_TI_core`**, **not** audio/FFT/SPL, **not** perceptually validated. See **`docs/H_TA_ACOUSTIC_PROXY.md`**.
- **Harmonic pitch handling is conservative by default** (`harmonic_pitch_policy`): **diamond / square** noteheads on **bowed strings only** mark **harmonic candidates** without inventing sounding pitch; **artificial** inference requires explicit MusicXML roles **or** (when enabled) a two-pitch chord with artificial markup and a **table-matched** base–touching interval; **unresolved** harmonic pitch is **reported in the event audit and JSON warnings**, not silently replaced.
- **MusicXML / MIDI limitations** — results depend on the **encoder / exporter** (how instruments, techniques, harmonics, and dynamics are attached). **MIDI** often lacks rich metadata; **MusicXML** is preferred. Missing data surfaces as **unknown** or parser warnings where possible, not as invented notation.
- **Adaptive windows (optional):** **`window_mode`** defaults to **`manual`** (your **time step** and **window size**). **`auto_by_excerpt_duration`** and **`auto_by_target_windows`** derive **effective** window and step from excerpt length (with configurable clamps). JSON **`parameters`** and CSV/JSON time series echo **`window_size_effective`**, **`time_step_effective`**, input echoes, ratios, and **`edge_policy`** (`include_partial_windows` / `drop_partial_windows` / **`mark_partial_windows`** default). Each window row adds **`window_start`**, **`window_end`**, **`edge_window`**, **`window_coverage_ratio`** (and overlap duration in JSON) so boundary behaviour is **not hidden**. This is **orchestration only** — it does **not** change the $H_{\mathrm{TI},\mathrm{core}}$ formula. Adaptive sampling aids **proportional** comparison across excerpts but weakens **strict absolute-time** comparability; always report **effective** window/step and mode in papers.
- **Dominant categories (ties):** Singular **`dominant_*`** fields remain for backward compatibility; when ties occur, use plural **`dominant_*s`** lists and **`dominant_*_tie`** booleans for analytical reading.

The JSON flag **`not_audio_analysis: true`** is set on **H_TI** exports.

Point-in-time audit snapshots (may predate schema **3.0**) live under **`docs/archive_legacy/`** (e.g. **`SCIENTIFIC_TECHNICAL_AUDIT.md`**). For current behaviour, prefer this README, **`QUICK_REFERENCE.md`**, **`TECHNICAL_MANUAL.md`**, and **`FINAL_VERIFICATION_REPORT.md`**.

For bibliography governance, see **`TECHNICAL_MANUAL.md`** §19 and the developer registry, if needed (`docs/bibliography/ACOUSTIC_SOURCE_REGISTRY.md`).

**Maintainers:** The only authoritative package source is **`src/homogeneity_analyser/`**. Do **not** edit **`build/lib/`** or ship stale copies from **`build/`** / **`dist/`** / **`*.egg-info/`**—those directories are **generated** (setuptools, PyInstaller, pip, etc.) and may **diverge** from `src/`. See **`docs/ARCHITECTURE.md`** (“Source of truth”).

---

## Main metric — $H_{\mathrm{TI},\mathrm{core}}(t)$

**Structural components** (weighted **geometric mean** when evidence is present; nominal weights $(w_{\mathrm{inst}},w_{\mathrm{fam}},w_{\mathrm{tech}},w_{\mathrm{reg}})=(0.40,0.25,0.15,0.20)$, **renormalised** on active keys $C_t$):

| Component | Meaning |
|-----------|--------|
| **instrument_uniformity** | $U_{\mathrm{instr}}(t)=\sum_{i\in I_t} P_i(t)^2$ on canonical instruments. |
| **family_uniformity** | $U_{\mathrm{fam}}(t)=\sum_{f\in F_t} P_f(t)^2$ on instrumental **subfamily** (`family` rows). |
| **technique_uniformity** | $U_{\mathrm{tech}}(t)=\sum_{k\in K_t} Q_k(t)^2$ on **`technique_uniformity_key`** (never the instrument name). When every active event is only default-like playing (`ordinary_default_uniform`), the value is **1.0** so this term does not duplicate **instrument_uniformity**. |
| **register_compactness** | $R_{\mathrm{compact}}(t)$: square root of the product of span and pairwise register proximity (each floored at $\varepsilon$); explicit form in **§2.4** of `TECHNICAL_MANUAL.md`. **`register_proximity`** in exports is the same value (legacy column name). |

**Macrofamily** (strings / woodwinds / brass / …) is reported as an **extra diagnostic** Herfindahl — **not** part of the default four-way core mean unless you fork the analyser.

**Renormalisation:** if technique or register is **omitted** (`unavailable` / `ambiguous` technique; unpitched-only register), its nominal weight is dropped and the remaining weights **renormalise**.

**Pitch interpretation (register evidence only):** **`pitch_interpretation_mode`** controls how written pitches become **sounding MIDI** for register span, pairwise interval proximity, register compactness, symbolic inspection, and exports. **`musicxml_sounding`** applies full instrument transposition (default). **`xml_pitch_as_real`** treats encoded pitches as already concert/sounding (no transpose). **`ignore_octave_transpositions_only`** applies only the chromatic part of each transpose interval (octave multiples stripped). **`xml_pitch_as_real_with_octave_transposers`** treats the score as **real pitch for ordinary Bb/F transposing instruments** (clarinet, bass clarinet, horn, trumpet: no chromatic shift) but still applies **−12** for **double bass** and **contrabassoon** when they are written one octave above sounding pitch. Event audit columns separate **chromatic / octave transpose detected** (from the part’s interval) from **… applied** (what the active mode actually adds to **effective_written_midi**); **`effective_sounding_midi` = effective_written_midi + total_transpose_applied`** for ordinary notes. **String harmonics:** Artificial harmonics are **notated inconsistently** (normal notehead = stopped/base; **diamond** or **square** often = touched node; small notehead sometimes = sounding). **Sounding** pitch follows the **base-to-touching interval**, not necessarily the diamond pitch. The analyser uses **`ARTIFICIAL_STRING_HARMONIC_INTERVALS`** in `analyzers/harmonic_pitch.py` with rows **octave, perfect fifth, perfect fourth, major third, minor third** (major/minor third rows are **tempered approximations** of partials). Source note: **Violin Harmonics — arranged by Agatha Mallett** (`violin_harmonics_chart.pdf`; practical chart, not peer-reviewed theory—see `docs/STRING_HARMONIC_INTERVAL_REFERENCE.md`). **`harmonic_pitch_policy`**: **`conservative`** (default) uses **explicit** harmonic sounding from MusicXML only; **diamond/square-only** stays **unresolved**; **natural** harmonics without explicit sounding are **not** computed from noteheads. **`infer_common_artificial`** infers when a two-pitch chord has artificial markup and the interval matches the table within **$0.25$** semitone. **`written_as_sounding`** is **risky** (exporter-specific). **Inference is bowed strings only**; check **event audit** `harmonic_*` before trusting register around harmonics. Microtonal accidentals prefer non-zero **`<alter>`**; when **`alter`** is missing or zero, common quarter-tone accidentals can be inferred from accidental text; unknown signs are **not** guessed. The **H_TI_core** formula and weights are unchanged.

---

## Notated dynamic conditioning

Written dynamics and hairpins are parsed into **ordinal** symbolic quantities (fixed ladder `pppp` … `ffff`; **not** loudness in dB). Per window the export includes, among others:

- `notated_dynamic_level_distribution`, `notated_dynamic_coherence` $C_{\mathrm{dyn}}(t)=\sum_{d\in D_t} q_d(t)^2$ over known classes,
- `dynamic_intensity_ordinal` $I_{\mathrm{dyn}}(t)$, `dynamic_softness` $S_{\mathrm{dyn}}(t)=1-I_{\mathrm{dyn}}(t)$,
- `soft_blend_potential`, `intra_family_convergence_potential`, `transparent_blend_potential`,
- `projection_divergence_risk`, `masked_tonal_mass_risk`, `bright_salience_risk`,
- `dynamic_interpretation_label`, `dynamic_evidence_status`.

These diagnostics are **literature-informed symbolic interpretations** — **not** claims of measured acoustic fusion, **not** SPL or loudness, and **not** the same fields as optional **`symbolic_blend_potential`**: scalars such as **`soft_blend_potential`** belong to the **ordinal dynamic-conditioning** readout only, whereas **`symbolic_blend_potential`** (when **`include_symbolic_blend_potential`** is enabled) is a separate **optional score-based symbolic blend-tendency** bundle in exports.

### Optional interval-class diagnostics (`include_symbolic_blend_potential`)

Separate from **register compactness** inside **`H_TI_core`** (which uses absolute semitone distance). When enabled, exports add interval-class favourability and related profiles:

- **`interval_class_blend_factor`** (alias **`pairwise_interval_blend_factor`**)
- **`interval_class_profile`** — stable keys such as **`seconds_sevenths`** (mod‑12 equivalence buckets; **not** literal interval names in the score)
- **`interval_class_profile_display`** — human-readable labels (e.g. *second-class / seventh-class equivalence group*)
- **`literal_interval_semitone_pair_mass`** — pair mass by absolute semitone distance before grouping
- **`chromatic_mod12_pair_mass`** — pair mass by chromatic class 0…11

The key **`seconds_sevenths`** groups mod‑12 classes {1, 2, 10, 11} only; a passage with seconds but no sevenths may still show mass in that bucket. See **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`**.

**Homogeneity vs transparency:** $H_{\mathrm{TI},\mathrm{core}}$ rewards **register compactness** $R_{\mathrm{compact}}$ (close-packed chord tones and narrow internal intervals, given the same outer span). Wide registral spacing may improve **transparent blend** in the dynamic-conditioning readout; that is **not** the same as higher timbral–instrumental homogeneity.

---

## Inputs

- **MusicXML**, **.musicxml**, **.mxl**, **MIDI** (via music21).
- **Encoding quality** matters: exporters differ in how techniques and dynamics are attached.
- **Register reference profile**: `strict` (3 semitones), `balanced` (7), `permissive` (12), or a **manual semitone override**.

---

## Outputs

- **Plot** — **`H_TI_core`** / $H_{\mathrm{TI},\mathrm{core}}(t)$ (same as **`H_TI`** / $H_{\mathrm{TI}}(t)$ curve).
- **CSV** — per-window diagnostics (see `HTI_CSV_COLUMNS` in `analyzers/hti_export_rows.py`; re-exported from `hti.py`), including **`window_start`**, **`window_end`**, **`edge_window`**, **`window_coverage_ratio`** when adaptive or edge marking is used (manual mode still exports the same geometry columns).
- **JSON** — `schema_version` **3.0** (H_TI bundle), `time_series`, nested `dynamic_conditioning`, optional **timbral affinity** fields (`H_TI_affinity_literature_relieved`, …), optional **`H_TA_acoustic_proxy`** / **`timbral_acoustic_affinity`** (and related evidence columns) when `include_acoustic_proxy`, optional **interval-class / symbolic blend-potential** diagnostics when `include_symbolic_blend_potential` is enabled (`interval_class_profile`, `interval_class_profile_display`, `literal_interval_semitone_pair_mass`, `chromatic_mod12_pair_mass`, … — see **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`**), root **`symbolic_homogeneity_scope_disclaimer`**, `warnings`. Combined/legacy research JSON remains **`1.8`** (internal/batch only).
- **Symbolic inspection** (optional Gradio accordion *Symbolic inspection (Loaded XML inspection)*) — three tables (**instrument inventory**, **event audit**, **vertical sonorities**) with UTF-8 CSV downloads (`instrument_inventory.csv`, `event_audit.csv`, `vertical_sonorities.csv`). Tables refresh when the upload, **pitch interpretation mode**, or **harmonic pitch policy** changes; **no H_TI run is required**.

The Symbolic inspection report shows what the parser actually found in the uploaded score. It is intended to verify instrument mapping, sounding pitch, dynamics, techniques, articulations, effects, and vertical sonorities before interpreting H_TI. It is a **parser audit**, not a homogeneity metric.

**Limitations:** MusicXML exporters differ in how they attach metadata; **MIDI** may lack instrument and technique detail; missing written dynamics or techniques appear as **unknown** (not silently invented); **no PDF or image** score input; **no audio analysis**.

---

## Interpretation (reading the curves)

| Signal | Plain-language reading |
|--------|-------------------------|
| **High $H_{\mathrm{TI},\mathrm{core}}$** | Concentrated orchestration / technique / register layout in the window (symbolic). |
| **Low $H_{\mathrm{TI},\mathrm{core}}$** | Spread across instruments, families, techniques, or wide register (symbolic). |
| **High soft_blend_potential** | High core homogeneity **and** soft, coherent written dynamics — **symbolic** dynamic-conditioning “soft blend” *potential* (ordinal written dynamics), **not** measured blend, **not** SPL, **not** the same field as optional **`symbolic_blend_potential`**. |
| **High projection_divergence_risk** | Louder notated level **and** same-subfamily multi-instrument mass **and** projection-weight heuristics — **not** SPL. |
| **High masked_tonal_mass_risk** | Louder level **and** subfamily heterogeneity **and** dense-register heuristic — cautionary **masking** narrative only. |
| **insufficient_dynamic_evidence** label | Little or no reliable written dynamic mass — do **not** invent dynamics. |

---

## Installation and running

```bash
pip install -e ".[dev]"
python -m homogeneity_analyser
# or, after install:
homogeneity-analyser
```

---

## Development / tests

```bash
ruff check src tests
ruff format --check src tests
pytest -m "not legacy"   # H_TI / product path (day-to-day)
pytest                   # full suite including multimetric JSON 1.8
pytest --cov=homogeneity_analyser --cov-report=term-missing  # product-path gate: fail_under 77 (see pyproject.toml)

**Onboarding (H_TI only):** `docs/ONBOARDING_H_TI.md`. Golden `H_TI_core`: `tests/test_hti_core_golden_outputs.py`. Legacy map: **`LEGACY.md`**. Analyzer layout: `analyzers/README.md`.
mypy  # optional; see pyproject.toml for scope
```

---

## Legacy / internal code (not the user-facing product)

Implementation is under **`src/homogeneity_analyser/legacy/`** (see **`legacy/README.md`**). Metrics include **H(t)**, **H_cluster**, **H_orchestration_symbolic**, **H_notated_fusion_potential**, **H_fusion_acoustic_heuristic**, and **U(t)**. **`homogeneity_analyser.analyzers.<module>`** paths are **compatibility shims** for existing imports.

Combined / batch JSON still uses **`schema_version` `1.8`** via `services/analysis_service.py` and `json_export.py`. These metrics are **not acoustically validated fusion**; heuristic branches may expose **`confidence_score` / `confidence_label`** as **notation-linked** diagnostics only.

Long-form audit notes for superseded **fusion-potential** justification live under **`docs/archive_legacy/`**.

---

## Windows distribution (frozen build)

Maintainers: PyInstaller spec, Inno Setup draft, build scripts, and smoke test live under **`packaging/windows/`** — see **`packaging/windows/README.md`**. End users without Python are the target.

**Distribution drop folder (after you build):** **`Homogeneity_analiser_install\`** — place **`HomogeneityAnalyserSetup.exe`**, **`README_INSTALLATION.txt`**, and optionally the **`portable\`** onedir copy for ZIP-only distribution. Build scripts populate this folder automatically; it must not contain tests, caches, or development-only files.

---

## Gradio — optional diagnostics (separate layers)

All optional layers default **off** and **do not** change **`H_TI_core`**, **`H_TI`**, or **`H_TI_strict`**.

| UI block | Parameter | Role |
|----------|-----------|------|
| Timbral affinity relief (inline controls) | `timbral_affinity_relief_factor`, profile, … | Literature-governed **symbolic** relief on the instrument axis → **`H_TI_affinity_literature_relieved`** |
| Accordion **Optional symbolic interval-class / blend-potential diagnostics** | `include_symbolic_blend_potential` | **`interval_class_blend_factor`**, **`interval_class_profile`** (+ display / literal-semitone diagnostics), **`symbolic_blend_potential`**, attack compatibility — **not** the acoustic proxy; see **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`** |
| Accordion **Acoustic-aligned symbolic timbral-affinity proxy** | `include_acoustic_proxy` | **`H_TA_acoustic_proxy`** / **`timbral_acoustic_affinity`** — see **`docs/H_TA_ACOUSTIC_PROXY.md`** |

---

## More documentation

- **`QUICK_REFERENCE.md`** — one-page operator guide.
- **`TECHNICAL_MANUAL.md`** — methodology, pipeline, formal definitions, CSV/JSON, limitations, **Appendix D** (full recognised symbolic vocabulary and audit column glossary), and **§19 bibliography** mirror. For a **step-by-step user tutorial** (workflow, parameters, inspection, responsible interpretation), see the section **“Tutorial — How to use the analyser responsibly”** near the start of that file.
- **`docs/H_TA_ACOUSTIC_PROXY.md`** — acoustic-informed proxy formula, evidence status tags, parameters.
- **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`** — interval-class keys, **`seconds_sevenths`** semantics, literal vs mod‑12 export profiles.
- **`MAINTAINERS.md`** — where to change metrics, export registries, weights, UI copy, and tests.
- **`docs/QUICK_REFERENCE_SYMBOLIC_NAMES.md`** — short index of the same vocabulary (instruments, families, technique dimensions, parser notes); the canonical tables live in **Appendix D**.
- **`docs/ARCHITECTURE.md`** — package layout.
- **`docs/METRIC_CODE_MAP.md`** — code entry points.
- **`CURRENT_CODE_CHARACTERISTICS_REPORT.md`** — developer inventory aligned with the current product.
- **`FINAL_VERIFICATION_REPORT.md`** — latest full-test / lint / doc-alignment verification pass.
