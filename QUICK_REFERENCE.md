# Timbral_Instrumental_Homogeneity — Quick Reference

**Repository:** [Timbral_Instrumental_Homogeneity](https://github.com/LuisMRaimundo/Timbral_Instrumental_Homogeneity)

## What this software does

Computes $H_{\mathrm{TI,core}}(t)$ from **MusicXML / MXL / MIDI** **symbolic notation**: a timbral–instrumental homogeneity curve in sliding windows, plus **notated dynamic conditioning** (ordinal written dynamics, coherence, interpretive scalars, and a single **`dynamic_interpretation_label`** per window). The export column **`H_TI`** is the same scalar as **H_TI(t)**.

## What it does **not** do

- $H_{\mathrm{TI,core}}$ is **symbolic / score-centred** (notation overlap windows), **not** audio-derived homogeneity.
- **Not measured audio** — no waveform files, no microphones.
- **No FFT** of recordings, **no SPL**, **no spectral “fusion meter”** of sound pressure.
- **No claim** of **measured acoustic** or **perceptual** timbral fusion — outputs are **not acoustically validated fusion** predictions.
- **Dynamics** in the conditioning layer are **ordinal notated evidence**, **not** acoustic loudness.
- **Timbral affinity relief** is **optional**, **symbolic**, **literature-governed** (registry); it is **not** measured timbral similarity.
- **Harmonics** — default **conservative**: bowed-string **diamond/square** without XML roles → **candidate / unresolved** (no guessed sounding pitch); artificial inference only with explicit markup + policy **`infer_common_artificial`** and table match; unresolved states appear in **audit / warnings**.
- **Encoder dependency** — MusicXML/MIDI quality and exporter choices directly affect instruments, techniques, harmonics, and dynamics parsing.

JSON exports set **`not_audio_analysis: true`**.

For bibliography governance, see **`TECHNICAL_MANUAL.md`** §19 and the developer registry, if needed (`docs/bibliography/ACOUSTIC_SOURCE_REGISTRY.md`).

**Symbolic vocabulary (instruments, aliases, families, techniques, dynamics, harmonics, pitch modes, audit CSV columns):** see **`TECHNICAL_MANUAL.md` Appendix D** and **`docs/QUICK_REFERENCE_SYMBOLIC_NAMES.md`**.

## How to run

```bash
pip install -e .
python -m homogeneity_analyser
```

Upload a score → open **Window settings** → choose **`window_mode`** (**manual** default, or adaptive by excerpt length / target window count) and **`edge_policy`** → set **time step** / **window size** (manual) or ratio/clamp fields (adaptive) → **register reference profile** (or manual semitone override) → optional **component weights** → **Run analysis**. JSON **`parameters`** always include **`window_size_effective`**, **`time_step_effective`**, and related echoes so adaptive values are **never silent**.

## Inputs

- **MusicXML / MXL** (recommended) or **MIDI**.
- **Dynamics and techniques** depend on how the score was exported.
- **Pitch interpretation mode** (Gradio + `pitch_interpretation_mode` in exports): four modes — full MusicXML transpose; concert XML (no transpose); chromatic-only (drop octave multiples from transpose); **concert XML + −12 for double bass / contrabassoon** when the score is already in sounding pitch for Bb/F instruments but basses are notated one octave high.
- **`harmonic_pitch_policy`** (default `conservative`): **bowed strings only**. Artificial harmonics: **sounding** from **base→touching** interval via **`ARTIFICIAL_STRING_HARMONIC_INTERVALS`** (octave, 5th, 4th, major 3rd, minor 3rd; thirds = tempered partial approximations). **`infer_common_artificial`**: two-pitch chord + artificial markup + table match within **$0.25$** semitone on $|m_{\mathrm{touch}}-m_{\mathrm{base}}-\mathrm{target}|$. **Diamond/square** without XML roles = **harmonic_candidate** / **unresolved**; **natural** without explicit sounding = same (no node math). **`written_as_sounding`** = **risky**. Non-string **diamond/square** ignored. Audit **`harmonic_*`** before register conclusions. **Symbolic only**.

## Main output: $H_{\mathrm{TI,core}}$

The plot shows $H_{\mathrm{TI,core}}(t)$; exports also label the same series $H_{\mathrm{TI}}(t)$ (identical values). $H_{\mathrm{TI,strict}}(t)$ duplicates $H_{\mathrm{TI,core}}(t)$ — an explicit export alias so tools can compare **strict** vs optional **`H_TI_affinity_literature_relieved`** without ambiguity. **Implementation-aligned** headline scalar (see `TECHNICAL_MANUAL.md` §2.5):

$$
H_{\mathrm{TI,core}}(t)=\prod_{c\in C_t}\max\bigl(\varepsilon,x_c(t)\bigr)^{\tilde w_c}=\exp\Bigl(\sum_{c\in C_t}\tilde w_c\ln\max\bigl(\varepsilon,x_c(t)\bigr)\Bigr),
$$

then clipped to $\left[0,\,1\right]$.

With components $x_c\in\{U_{\mathrm{instr}},U_{\mathrm{fam}},U_{\mathrm{tech}},R_{\mathrm{compact}}\}$ on the active subset $C_t$, where $\tilde w_c$ are weights **renormalised** on $C_t$ (see §2.5 in the manual). **Technique** concentration uses **`technique_uniformity_key`** (e.g. `stopped`, `pizzicato`, `ordinary_default`), never instrument names; default-only windows use status **`ordinary_default_uniform`** with **technique_uniformity = 1.0**. The audit still exports the full **`technique_state_id`** fingerprint separately (**not** the Herfindahl bucket key for **`H_TI_core`** technique uniformity). Register compactness matches §2.4:

$$
R_{\mathrm{compact}}(t)=\sqrt{\max\bigl(\varepsilon,R_{\mathrm{span}}(t)\bigr)\cdot\max\bigl(\varepsilon,R_{\mathrm{pair}}(t)\bigr)},
$$

also clipped to $\left[0,\,1\right]$; the export column **`register_proximity`** equals **`register_compactness`** when pitched evidence exists. **`register_span_factor`** and **`register_pair_distance_factor`** mirror **`register_span_proximity`** and **`pairwise_interval_proximity`** (explicit names for the two **semitone-distance** compactness ingredients). **Interval-class symbolic favourability** (**`interval_class_blend_factor`**, **`interval_class_profile`** with stable keys such as **`seconds_sevenths`**, display twin **`interval_class_profile_display`**, literal diagnostic **`literal_interval_semitone_pair_mass`**, **`chromatic_mod12_pair_mass`**, **`interval_class_evidence_status`**) is a **separate optional layer** — not inside **$H_{\mathrm{TI,core}}$** — and must not be read as “intervallic fusion” inside register compactness. **Transparency** in dynamic diagnostics is separate from this homogeneity term.

**Intuition (orthogonal layers):** **C4–D4** can be **register-compact** yet only **moderately** favourable in the **symbolic interval-class** bucket **`seconds_sevenths`** (mod‑12 second class — **not** a claim that a seventh appears in the score); **C4–C5** is typically **less** register-compact but **high** octave-class favourability; **C4–G4** is **fifth-favourable**; **C4–F♯4** is **tritone-unfavourable** — all **score-based conventions**, not perceptual proof.

## Dynamic-conditioning diagnostics

Ordinal ladder (**not SPL**): distribution, **coherence** $C_{\mathrm{dyn}}(t)=\sum_{d\in D_t} q_d(t)^2$ (known classes), **intensity** $I_{\mathrm{dyn}}(t)$ / **softness** $S_{\mathrm{dyn}}(t)=1-I_{\mathrm{dyn}}(t)$, coverage (`explicit` / `partial` / `unavailable`), hairpin flags, divergence flag, **`soft_blend_potential`**, **`intra_family_convergence_potential`**, **`transparent_blend_potential`**, **`projection_divergence_risk`**, **`masked_tonal_mass_risk`**, **`bright_salience_risk`**, **`family_specific_projection_weight`**, **`masking_context_weight`**, **`dynamic_evidence_status`**, **`dynamic_interpretation_label`** — all **dynamic-conditioning** scalars, distinct from optional **`symbolic_blend_potential`** (see JSON bullet below).

Nested JSON block: **`dynamic_conditioning`** (H_TI bundle `schema_version` **3.0**).

**Optional literature-governed timbral affinity** (same bundle): **`timbral_affinity_relief_factor`**, **`timbral_affinity_profile`**, **`H_TI_affinity_literature_relieved`**, **`timbral_affinity_uniformity`**, dynamic qualifiers, and optional pairwise rows. **`H_TI_core`** / $H_{\mathrm{TI,core}}(t)$ stays unchanged; this layer is symbolic (taxonomy / organology / technique tags + registry `source_key` citations), **not** measured acoustic fusion. See `docs/TIMBRAL_AFFINITY_LITERATURE_AUDIT.md`.

**Optional symbolic interval-class / blend-potential** (`include_symbolic_blend_potential`; Gradio accordion separate from the acoustic proxy): adds **`interval_class_blend_factor`**, **`interval_class_profile`** / **`interval_class_profile_display`**, **`literal_interval_semitone_pair_mass`**, **`chromatic_mod12_pair_mass`**, **`symbolic_blend_potential`**, **`attack_compatibility_factor`**, etc. Key **`seconds_sevenths`** = mod‑12 bucket {1,2,10,11} — **not** “sevenths present in the score.” See **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`**. **Does not** modify **`H_TI_core`**; **not** audio, SPL, or perceptual validation.

**Optional acoustic-aligned timbral-affinity proxy** (`include_acoustic_proxy`; separate Gradio accordion): **`H_TA_acoustic_proxy`** = **`timbral_acoustic_affinity`** = $\sum_{ij} p_i p_j K(e_i,e_j)$ over **events** (not chord-tone duplicates); optional **`H_TA_acoustic_contextual`**. Export registry columns: **`timbral_acoustic_affinity_components`**, **`timbral_acoustic_affinity_profile`**, **`timbral_acoustic_affinity_evidence_status`**, **`timbral_acoustic_pairwise_summary`**, **`acoustic_proxy_not_audio_analysis`**, **`acoustic_proxy_validation_status`**. Orthogonal to Herfindahl **`instrument_uniformity`** and to interval-class / symbolic-blend columns; uses `taxonomy/acoustic_timbral_taxonomy.json`. Evidence tags align with **`timbral_acoustic_affinity_components`** and window **`dynamic_coverage_status`** / **`technique_coverage_status`**. See **`docs/H_TA_ACOUSTIC_PROXY.md`**.

## Adaptive windowing ($H_{\mathrm{TI}}$)

- **`window_mode`:** `manual` (default), `auto_by_excerpt_duration`, `auto_by_target_windows` — see `analyzers/hti_adaptive_windows.py` + `services/analysis_service.py` (orchestration only; $H_{\mathrm{TI,core}}$ formula unchanged).
- **`edge_policy`:** `include_partial_windows` (legacy feel), `drop_partial_windows` (omit centres whose nominal window extends past score end), `mark_partial_windows` (default: keep rows, flag **`edge_window`**, **`window_coverage_ratio`**).
- **Exports:** JSON **`parameters`** list `window_size_input`, `time_step_input`, effective sizes, `excerpt_duration_quarterLength`, ratios, clamps, `target_window_count`, `window_to_step_ratio`, `edge_policy`. Per-window JSON/CSV include **`window_start`**, **`window_end`**, **`edge_window`**, **`window_coverage_ratio`**.

## Dominant categories (ties)

Singular **`dominant_*`** columns remain for compatibility; for ties read **`dominant_*s`** and **`dominant_*_tie`** alongside the singular field.

## Comparability (`hti_comparability_class`)

Each window exports **`hti_comparability_class`**: which components entered the renormalised geometric mean for **`H_TI_core`**. Values: `full_4_component`, `no_technique`, `no_register`, `instrument_family_only`, `no_active_events`, `partial_other`. **Do not compare `H_TI_core` across windows with different classes** without stating the effective formula change. Cross-check **`active_weights`**, **`technique_coverage_status`**, and **`register_coverage_status`**.

## CSV columns

See `homogeneity_analyser.analyzers.hti_export_rows.HTI_CSV_COLUMNS` — includes **`hti_comparability_class`**, uniformities, technique coverage, **`register_compactness`**, **`register_span_proximity`** / **`register_span_factor`**, **`pairwise_interval_proximity`** / **`register_pair_distance_factor`**, optional symbolic-blend columns when enabled (**`interval_class_blend_factor`**, **`interval_class_profile`**, **`interval_class_profile_display`**, **`literal_interval_semitone_pair_mass`**, **`chromatic_mod12_pair_mass`**, **`symbolic_blend_potential`**, …), window geometry (**`window_start`**, **`window_end`**, **`edge_window`**, **`window_coverage_ratio`**), all dynamic / interpretive fields, JSON-encoded **`notated_dynamic_level_distribution`**, **`active_weights`**, etc.

## Symbolic inspection (Loaded XML inspection)

In the Gradio app, open the **Symbolic inspection** accordion under the main **H_TI** controls. When you change the upload **or** the **Pitch interpretation mode** dropdown, the **instrument inventory**, **event audit** (one row per chord tone / unpitched hit), and **vertical sonorities** tables update automatically, with CSV downloads. This is a **diagnostic parser readout** (same symbolic pipeline as **H_TI**), **not** an extra homogeneity tab. Missing dynamics in the score show as **unknown**, not inferred. **MIDI** and exporter quirks can leave gaps; there is **no PDF/image** or **audio** path.

## JSON structure

- `schema_version` **3.0**, `kind` / `metric_kind` for symbolic timbral–instrumental homogeneity; per-window **`pitch_interpretation_mode`** in `time_series`; root **`symbolic_homogeneity_scope_disclaimer`** repeats the non-audio / non-measured-fusion contract.
- Optional **`include_symbolic_blend_potential`** (parameters): when true, `time_series` adds **score-based symbolic** interval-class / blend-potential diagnostics only — **`interval_class_blend_factor`** (alias: **`pairwise_interval_blend_factor`**; orthogonal to **`register_compactness`** / **`H_TI_core`**), **`interval_class_profile`**, **`interval_class_profile_display`**, **`literal_interval_semitone_pair_mass`**, **`chromatic_mod12_pair_mass`**, **`interval_class_evidence_status`**, **`attack_compatibility_factor`**, **`attack_class_distribution`**, **`symbolic_blend_interval_profile`**, **`symbolic_blend_potential`**, **`symbolic_blend_components`**, etc. **Not** the acoustic proxy; **not** psychoacoustic validation.
- Optional **`include_acoustic_proxy`**: **`H_TA_acoustic_proxy`**, **`H_TA_acoustic_contextual`**, **`timbral_acoustic_affinity`**, **`timbral_acoustic_affinity_components`**, **`timbral_acoustic_affinity_profile`**, **`timbral_acoustic_affinity_evidence_status`**, **`timbral_acoustic_pairwise_summary`**, **`acoustic_proxy_not_audio_analysis`**, **`acoustic_proxy_validation_status`**, optional pairwise rows — see **`docs/H_TA_ACOUSTIC_PROXY.md`**.
- `parameters`, `active_weights_nominal`, **`time_series`**, **`dynamic_conditioning`** (model metadata + parallel time series), `warnings`, `technique_model_version`.

## Interpretation warnings

- High $H_{\mathrm{TI,core}}$ means **notational concentration**, not “players fused in a hall.”
- **Soft blend potential** is **symbolic**, not measured blend.
- **`insufficient_dynamic_evidence`** means written dynamics were too sparse to condition the reading — **do not** infer levels.

## User tutorial (full walkthrough)

For a **pedagogical** step-by-step guide (pitch modes, Symbolic inspection checklist, windowing, exports, common mistakes), see **`TECHNICAL_MANUAL.md`** → section **“Tutorial — How to use the analyser responsibly”**.

## Troubleshooting

- **Empty part names on MIDI** — prefer MusicXML.
- **Decimals in the UI** — use `0.25` or `0,25` per locale rules in `ui/validation.py`.
- **Plot export** — Plotly + Kaleido for PNG; HTML fallback if static export fails.

## Internal / regression only (not this quick guide)

Library code paths for **batch research** may still build **combined** JSON documents with **`schema_version` `1.8`**. Those paths are **not** the current **Gradio** product surface. Where those bundles attach **confidence** fields (`confidence_score`, `confidence_label`) to heuristic timbral branches, treat them as **notation-linked coverage** diagnostics — **not** empirical listening-test validation.
