This document is historical and is not the current specification.

# Narrative companion — \(H_{\mathrm{TI,core}}\) and H_TI exports

This companion summarizes how **root `TECHNICAL_MANUAL.md`** describes **notation-derived** symbolic timbral–instrumental homogeneity. **Authoritative equations** live in **`TECHNICAL_MANUAL.md` §2** (especially §2.4–2.7).

**H_TI_core** is **score-based symbolic** timbral–instrumental homogeneity (overlap-mass concentration on instruments, taxonomy subfamilies, technique buckets, and **register compactness**). It is **not** a measured acoustic or perceptual fusion metric.

**Register compactness** combines **span-based** and **pairwise semitone-distance** factors on **sounding MIDI** — **pitch-space proximity / dispersion** only. **`register_span_factor`** and **`register_pair_distance_factor`** are explicit export aliases for those two ingredients. This layer is **orthogonal** to **interval_class_blend_factor** (mod‑12 **symbolic interval-class favourability** from `symbolic_blend_layers.py`), which is **optional** and **outside** **H_TI_core**.

**Intuition:** **C4–D4** can be **register-compact** yet only **moderately** favourable in the interval-class table; **C4–C5** is often **less** compact in register space but **high** in octave-class favourability; **C4–G4** is **fifth-favourable**; **C4–F♯4** is **tritone-unfavourable** under the default **symbolic convention** — **not** perceptual proof.

**symbolic_blend_potential** is an **optional score-based symbolic blend-tendency diagnostic**, exported only when **`include_symbolic_blend_potential`** is enabled. It is **not** SPL-based blend and **not** psychoacoustic validation.

Derived interpretive scalars from dynamics (examples): **soft_blend_potential**, **intra_family_convergence_potential**, **transparent_blend_potential**, **projection_divergence_risk**, **masked_tonal_mass_risk**, **bright_salience_risk**, **family_specific_projection_weight**, **masking_context_weight**, **dynamic_evidence_status**, **dynamic_interpretation_label**.

These are **literature-informed symbolic** readings — **not** measured blend, projection, or masking.

---

## 6) Family-sensitive interpretation rules (conservative)

Brass, clarinet, flute, double reeds, strings, cross-family orchestration, and percussion each follow **narrow** heuristics documented in code comments in `hti_dynamic_conditioning.py` (`FAMILY_RULES_VERSION = "hti_dynamic_conditioning_v1"`). Evidence tiers: **strong**, **moderate**, **insufficient** (especially percussion-only windows).

---

## 7) Interpretation labels (priority)

One **`dynamic_interpretation_label`** per window, chosen in strict priority order (see source: `pick_dynamic_interpretation_label`). Examples include: `insufficient_dynamic_evidence`, `string_mixed_technique_heterogeneity`, `cross_family_masked_tonal_mass_risk`, `brass_projection_divergence_risk`, `clarinet_bright_projection_salience`, `cross_family_transparent_blend_potential`, `soft_brass_intra_family_convergence_potential`, `clarinet_soft_blend_potential`, `flute_soft_blend_potential`, `flute_moderate_projection_salience`, `double_reed_soft_blend_potential`, `double_reed_projection_salience`, `string_sectional_soft_blend`, `string_sectional_mass`, `percussion_dynamic_salience_insufficient_fusion_evidence`, `structural_homogeneity_dynamic_neutral`.

**dynamic_evidence_status** summarises how strong the symbolic evidence is for family-specific rules (`strong` / `moderate` / `insufficient`).

---

## 8) CSV output

Columns follow `homogeneity_analyser.analyzers.hti.HTI_CSV_COLUMNS` (time, measure, **H_TI**, **H_TI_core**, uniformities, technique coverage, **register_proximity** (= **register_compactness**), **register_span_proximity**, **register_span_factor**, **pairwise_interval_proximity**, **register_pair_distance_factor**, **pairwise_interval_coverage_status**, **register_span_semitones**, **register_coverage_status**, dynamic fields, interpretive scalars, **`dynamic_interpretation_label`**, **`dynamic_evidence_status`**, optional symbolic-blend columns when enabled (**`interval_class_blend_factor`**, **`pairwise_interval_blend_factor`**, **`symbolic_blend_potential`**, **`interval_class_profile`**, **`interval_class_evidence_status`**, **`symbolic_blend_components`**, **`attack_compatibility_factor`**, **`attack_class_distribution`**), JSON-encoded dict columns for distributions / `active_weights`).

---

## 9) JSON output

`build_hti_export` returns:

- `schema_version` **2.9** (H_TI bundle), `metric_kind: symbolic_timbral_instrumental_homogeneity`, `not_audio_analysis: true`.
- `parameters`, `active_weights_nominal`, `time_series` (full per-window rows), nested **`dynamic_conditioning`** (`model_scope`, `warning`, `dynamic_scale`, `family_rules_version`, slimmer `time_series`), `warnings`, `technique_model_version`.

**Library-only** combined / fusion bundles may still emit **`schema_version` `1.8`** — see `JSON_EXPORT_SCHEMA_VERSION` in `json_export.py`.

**Two different `model_version` fields:** On every export document that still uses the **legacy combined** nesting, **top-level** **`model_version`** identifies the **JSON export bundle** (`JSON_EXPORT_MODEL_VERSION` in `json_export.py`). When present, the nested **`timbral`** object’s **`timbral_semantic_model.model_version`** identifies the **timbral semantics documentation** submodule (`TIMBRAL_MODEL_SEMANTICS_VERSION` in `timbral_semantics.py`). They answer different questions; do not merge them in downstream schemas without documenting both.

### Legacy combined JSON — `model_version` vs export wrapper

Some **combined** export payloads distinguish:

- **`model_version`** on nested **timbral** objects — ties to **`timbral_semantic_model`** / profile semantics.
- **`JSON_EXPORT_MODEL_VERSION`** — export wrapper version for the JSON document as a whole.

H_TI-only JSON does not reproduce the full combined nesting; the distinction matters only when calling **`build_combined_export`** from tests or programmatic batch tools.

---

## 10) Limitations

- **Exporter differences** — Dorico / Sibelius / MuseScore encode techniques and dynamics differently; missing MusicXML semantics cannot be recovered.
- **MIDI** often lacks rich part metadata — instrument and technique fidelity drop.
- **Dynamics are symbolic ordinals**, not loudness in dB; the model does **not** claim that **pp** “causes fusion” or **ff** “destroys fusion”.
- **Family rules** are **not** empirically calibrated predictions — they organise cautionary reading only.
- **Acoustic-informed profiles** (`acoustic_profiles/`) exist for **legacy** heuristic analysers still in the package; they are **not** used to claim measured fusion inside **H_TI_core**.

---

## 11) Bibliographic rationale (concise)

Qualitative reading of orchestration and dynamics draws on widely cited orchestration and acoustics texts — **Meyer** (performance acoustics), **Campbell / Gilbert / Myers** (brass science), **Benade** and **Fletcher & Rossing** (instrument acoustics), **Rossing** (string instrument science), and handbooks on musical acoustics. The implementation stays **notation-first**: the canonical machine-readable bibliography lives in **`src/homogeneity_analyser/acoustic_profiles/source_registry.json`** (also described in YAML for editors); citations there support **registry governance** for legacy heuristic code paths, not empirical fusion measurement in **H_TI_core**.

For **machine-readable** citation stubs mirrored for auditors, see **§19) Bibliography** in the root `TECHNICAL_MANUAL.md`.

---

## Appendix A — Legacy / internal metrics (not user-facing)

The Python package retains **internal** implementations used by tests, research scripts, and shared infrastructure:

| Module (examples) | Role |
|-------------------|------|
| `analyzers/homogeneity.py` | Legacy **H(t)** entropy / Wasserstein texture curve. |
| `analyzers/cluster.py` | **H_cluster** on vertical MIDI. |
| `analyzers/orchestration_symbolic.py` | **H_orchestration_symbolic**. |
| `analyzers/notated_fusion_potential.py` | **H_notated_fusion_potential** (+ dynamic branch helpers). |
| `analyzers/fusion_acoustic_heuristic.py` | **H_fusion_acoustic_heuristic** (literature-linked distances; **not** waveform analysis). |
| `analyzers/register.py` | **U(t)** register uniformity. |

These are **not acoustically validated fusion** products in the current Gradio workflow. **H_TI** reuses **`TimbralHomogeneityAnalyzer`** event construction only.

Where legacy **combined** JSON (**`schema_version` `1.8`**) still exposes **`confidence_score`** / **`confidence_label`** on heuristic branches, interpret them as **internal notation-linked coverage** — **not** empirical validation against microphones or audiences.

---

## Appendix B — CI and validation

When a Git repository is present, `.github/workflows/tests.yml` runs **ruff**, **mypy** (scoped), **pytest** with coverage, and `validation/run_validation.py` after `pip install -e ".[dev]"`.

---
