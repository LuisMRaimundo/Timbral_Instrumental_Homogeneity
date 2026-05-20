# Technical Manual — Homogeneity Analyser

This manual explains how the homogeneity analyser works, how to use it, and how to interpret its results. It is written to be clear, precise, and practical, with concrete examples.

**Full mathematics and algorithms** — see **§1c** (weighted \(H\), m1–m3, \(H_{\mathrm{timbral}}\), \(U\), segmentation, sensitivity). **Step-by-step tutorial** — **§3** (including §3.10–3.11).

---

## 0) H_TI — primary product (Gradio UI, symbolic only)

**H_TI_core(t)** (**symbolic timbral–instrumental homogeneity degree**) is the **structural**, **score-derived** curve produced by `SymbolicTIHomogeneityAnalyzer` (`analyzers/hti.py`). The headline export **H_TI(t)** equals **H_TI_core(t)** (same numeric series). Inputs are **MusicXML / MIDI** semantics only: canonical instrument, **instrumental subfamily** (the taxonomy `family` field, e.g. `flutes`, `brass`), **macrofamily** (strings / woodwinds / brass / … — a **coarser** diagnostic Herfindahl, separate from the default H_TI_core geometric mean unless you extend exports downstream), **`technique_state_id`**, **sounding MIDI** pitches for register span, and **written dynamics** / hairpins parsed by `technique_state` / `hti_dynamics.py` and **`hti_dynamic_conditioning.py`**.

**Not audio:** the pipeline does **not** claim measured acoustic fusion, spectral similarity, or “real” timbre distance. **H_TI_core** measures symbolic homogeneity from the score; **written dynamics do not directly change** that structural value — they **condition interpretation** via **notated dynamic conditioning** (literature-informed symbolic diagnostics: **symbolic fusion potential**, **transparent blend potential**, **projection-divergence risk**, **masked tonal-mass risk**). **Written dynamics** are **ordinal notational evidence**, not SPL; the dynamic layer is **not an empirically validated perception model**.

### 0a) H_TI core formula (per window)

Let overlap mass be summed **per sounding event** (same event pipeline as legacy timbral construction). Define Herfindahl **concentration** \(S=\sum p^2\) on instruments, on instrumental subfamilies, on `technique_state_id` when allowed, and register proximity \(R = 1/(1+\mathrm{span}/\mathrm{ref})\) from **all** `pitches` entries on each event (chord tones each contribute to span). **H_TI_core** is a **weighted geometric mean** of the **active** components; nominal weights default to **0.40 / 0.25 / 0.15 / 0.20** (instrument / subfamily / technique / register). **Technique** is omitted when `technique_coverage_status` is **`unavailable`** or **`ambiguous`**; **register** is omitted when there is no pitched evidence (`unavailable` register coverage). Remaining weights renormalise.

**Single reliable technique state:** if exactly one non-empty `technique_state_id` carries the mass, **technique_uniformity = 1.0** and the technique term **stays** in the mean. Status is **`explicit_uniform`** when any merged `technique_state` dict is non-default, otherwise **`default_inferred_uniform`**. Two or more ids ⇒ **`explicit_mixed`** with Herfindahl \(<1\) when spread.

### 0b) Macrofamily vs instrumental subfamily

The catalogue’s `family` string is the **instrumental subfamily** row (woodwind/brass families are split into flutes, oboes, clarinets, etc.). **Macrofamily** groups those rows (`woodwinds`, `strings`, …) for **`macrofamily_uniformity`** — useful when asking whether the orchestration is spread across coarse sections; it is **reported alongside** H_TI but is **not** part of the default four-way geometric mean unless you fork the service.

### 0c) Notated dynamic conditioning (interpretive layer)

`hti_dynamics.py` extracts overlap-mass-weighted **written** levels (including `pppp` … `ffff` where parsed), hairpins, `dynamic_coverage_status` (`explicit` / `partial` / `unavailable`), `notated_dynamic_coherence` (\(\sum p_d^2\)), `dynamic_intensity_ordinal` (fixed symbolic ladder), `dynamic_softness = 1 - \text{intensity}\), and `dynamic_divergence_detected` when two or more classes each hold non-trivial mass.

`hti_dynamic_conditioning.py` adds **family-sensitive** symbolic weights (brass / clarinet / flute / double reeds / strings / cross-family / percussion guardrails), `family_specific_projection_weight`, refined `masking_context_weight`, **`intra_family_convergence_potential`**, **`transparent_blend_potential`**, **`bright_salience_risk`**, **`dynamic_evidence_status`**, and **`dynamic_interpretation_label`** (single priority-chosen label per window). Core scalars include:

- `soft_blend_potential = H_TI_core × coherence × softness`
- `projection_divergence_risk` ≈ dynamic intensity × `same_family_mixed_instrument_mass` × `family_specific_projection_weight` (with bright-brass simultaneous boosts where applicable)
- `masked_tonal_mass_risk` ≈ dynamic intensity × `family_heterogeneity` × `masking_context_weight`

These are **literature-informed symbolic interpretations**, not empirical measurements of blend, projection, or masking.

### 0d) Register reference profiles

`strict` = 3 semitones, `balanced` = 7, `permissive` = 12, with optional numeric override (`services/constants.py`).

---

## 1) Purpose and Scope

**Scope (hard constraint):** This project works **only on symbolic notation** parsed from MusicXML or MIDI. It does **not** load, analyse, or synthesise **real audio** (no waveforms, microphones, or playback buffers). It does **not** compute FFTs from recordings, estimate radiated power in a concert hall, infer microphone angle, or capture performer-specific bow transients or room colouration. **H_timbral** is **symbolic timbral-instrumental / orchestration-register homogeneity** (see **§1d**); it is **not** acoustic timbre extraction.

The Gradio app and services expose **symbolic** metrics and **acoustic-informed heuristics** that still read **only** the score (see **§1e**). Core tools from a symbolic score (MusicXML or MIDI) include:

1. **Homogeneity H(t)** — A **continuous score in [0, 1]** where **1.0** = highly homogeneous texture and **0.0** = highly heterogeneous. Computed in sliding windows using:
   - **Intra‑window consistency** (duration & pitch entropy)  
   - **Inter‑window stability** (Wasserstein distance between pitch distributions)  
   - **Multi‑scale consistency** (density similarity across scales)

2. **Vertical cluster compactness H_cluster(t)** — Instrumentation-independent vertical pitch layout from **sounding MIDI**; **recommended** for pitch-object identity comparisons (see **§1e**).

3. **Symbolic orchestration uniformity H_orchestration_symbolic(t)** — Herfindahl-style concentration on instruments / families / technique-only buckets from timbral slices, **without** legacy fusion kernels (see **§1e**).

4. **Notation-derived fusion potential H_notated_fusion_potential(t)** — **General across all taxonomy instruments:** overlap-weighted Herfindahl on canonical **families**, **technique-only** buckets, and **sounding MIDI** pairwise register proximity, combined with an **instrument** axis that uses **distribution-only same-family relief** (no pairwise instrument tables, no family-specific affinity rules). Let \(p_i\) be normalized overlap mass on canonical instrument \(i\), \(P_f=\sum_{i\in f} p_i\). Then **instrument_uniformity** \(=\sum_i p_i^2\), **family_uniformity** \(=\sum_f P_f^2\), **same_family_cross_instrument_mass** \(=\max(0,\,\text{family_uniformity}-\text{instrument_uniformity})\), and **effective_instrument_uniformity** \(=\text{instrument_uniformity}+\rho\cdot\text{same_family_cross_instrument_mass}\) with user **same_family_relief** \(\rho\in[0,1]\) (default **balanced** profile **0.55**; **conservative** **0.45**). The scalar is a **weighted geometric mean** of **effective_instrument_uniformity**, family Herfindahl, technique-only Herfindahl, and register proximity (see **§1c.14**). **Not** measured audio, **not** FFT/spectral analysis, **not** legacy H_timbral family-specific pairwise kernels. Unpitched percussion contributes to the Herfindahl axes while register proximity uses **pitched pairs only**; diagnostics report **register coverage** instead of inventing pitch evidence.

5. **Acoustic-informed fusion heuristic H_fusion_acoustic_heuristic(t)** — Registry-linked profile distances plus a symbolic harmonic roughness **proxy**; **not** measured audio — interpret with **confidence** / **`source_keys`** only (see **§1e**).

6. **Legacy H_timbral (diagnostic)** — **Backward-compatible** symbolic **timbral-instrumental / orchestration-register** homogeneity (instrumentation, family, **sounding** register span, technique-state). **Not** measured audio, **not** acoustically validated fusion, **not** the recommended sole interpretive timbral metric (see **§1d**).

7. **Register uniformity U(t)** — How **evenly** pitches are **distributed within a user-defined register** (e.g. A1 to E7). A cluster in one part of the range → low U; a chord spread across the range → high U. **The user must set lower and upper register limits** (note names or MIDI numbers).

### 1b) Formal definitions (compact)

**H(t)** — At each time sample, let **m1** = intra-window consistency, **m2** = inter-window pitch stability, **m3** = multi-scale density consistency (each in [0, 1]). Then:

**H(t)** defaults to the **equal-weight geometric mean** **(m1 × m2 × m3)^(1/3)**. Optional **weights** `weight_m1`, `weight_m2`, `weight_m3` (any non-negative values, normalized to sum 1) define a **weighted geometric mean**: exp(w1·ln m1 + w2·ln m2 + w3·ln m3). Outputs include per-window **m1, m2, m3** in CSV when available.

- **m1** — For the window: build histogram PMFs for note durations, pitches, and joint (pitch, duration). Compute Shannon entropy (base 2) for each; normalize by the maximum possible entropy for that bin layout; take **1 − normalized entropy** for each; average the three.
- **m2** — Compare consecutive windows’ **pitch** PMFs on the same bin centers using the **1st Wasserstein distance** *W*; **m2 = exp(−W/σ)** with user **σ** (same units as pitch: MIDI semitones in absolute mode, or pitch-class space in pitch-class mode).
- **m3** — Compare **onset density** (or sustained overlap in sparse sustained textures) across three window widths (1×, 2×, 4× the base window). **m3 = 1 / (1 + mean |Δdensity|)** after aligning scales; optional handling when some scales are empty.

**H_timbral(t)** — **Symbolic timbral-instrumental / orchestration-register homogeneity:** same information classes as **§1d**, combined into a **[0, 1]** curve using the taxonomy, register span, family-wise pairwise modules, **chronological technique-state** where MusicXML / music21 exposes it, and a small **verified cross-family** layer (see **§1c.8** and `docs/H_TIMBRAL_SCORE_REPRESENTATION.md`). MIDI without part metadata may be weak.

**U(t)** — Within **[register_low, register_high]**, histogram pitches into **semitone bins**, compute **Shannon entropy** of that distribution (natural log), divide by log(*K*) for *K* bins to get **[0, 1]**; single pitch → 0; no notes in range → not a number (NaN).

**Pitch space** — `absolute` = MIDI pitch number; `pitch_class` = pitch class (mod 12). The API also accepts aliases **`chromatic`**, **`pc`** for pitch-class mode.

Exports are written under the system temp directory (or **`HOMOGENEITY_CACHE_DIR`**), with automatic cleanup of old files. Successful runs can also download **structured JSON** (e.g. `schema_version` **1.8** for combined exports with fusion + **H_notated_fusion_potential** diagnostics and export metadata; older docs may cite **1.1** … **1.7**) via `homogeneity_analyser.services.json_export` — see **§1c.13**.

### 1d) H_timbral semantics, symbolic scope, homogeneity vs identity

**What H_timbral is (precise):** **H_timbral** is **symbolic timbral-instrumental / orchestration-register homogeneity**. It summarises how uniform the **encoded orchestration** is (which instruments and families sound, how compact the **sounding** register is, and—when present—how aligned **technique playing states** are). It is **not** acoustic timbre extraction and does **not** read spectra, samples, or microphone signals.

**Homogeneity vs identity:** The scalar **H_timbral** rewards **uniformity** of orchestration and (where modelled) technique agreement inside a window. **Different playing identities can still be equally “homogeneous”:** e.g. four horns **open** and four horns **stopped** can both yield **high** H_timbral when each passage is internally uniform, because the **section is still one canonical instrument** with a **single** technique state. Those two situations differ in **`technique_state_id`** and in **`timbral_state_distribution` / `dominant_timbral_state`**, not necessarily in the headline H_timbral number. **Mixed** open/stopped (or mixed technique states) in the same window **lower** homogeneity because overlap mass is spread across distinct states (see **§1c.8** on concentration).

**Symbolic-only inputs (what the analyser can “see”):** Only what **music21** exposes after **MusicXML or MIDI** import, for example:

- Part / staff **names** and **instrument** objects where present  
- Staff **text directions** that import as `TextExpression` / rehearsal marks / dynamics (chronological persistence is handled in `technique_state.py`)  
- **Articulations** and other **symbolic** note/chord attachments music21 models (e.g. some **technical** markings, **notehead** shape where available)  
- **Expressions** attached to notes, and **lyrics** on notes (merged only as **note-local** context for technique heuristics when `notation_text_context_for_note(..., measure_text="none")` is used together with the direction stream—see `notation_context.py`)  

There is **no** PDF, bitmap, or scanned-image path: **visual** smears, handwritten marks, or layout-only cues that never become structured MusicXML **do not** enter the pipeline.

**Technique-state and exporter variability:** The same musical intention may appear as a **technical** element in one exporter, a **words** direction in another, or only as a **custom** text string. Dorico, Sibelius, Finale, MuseScore, etc. differ in how techniques are encoded. The project uses **regex keywording** on normalised text plus a finite set of music21 articulation hooks—**coverage is incomplete by design**. When a marking is missing from the import graph, the analyser cannot infer it.

**Test assumption labels (documentation convention):** Several tests label expectations with one of:

| Label | Meaning |
|-------|--------|
| **confirmed musical convention** | Widespread engraving / pedagogy wording or symbol use, still only validated **symbolically** here. |
| **project-specific convention** | A deliberate mapping or threshold chosen for this codebase (may differ from every publisher). |
| **ambiguous but intentionally accepted** | Real-world ambiguity acknowledged; the code picks one rule and tests lock that behaviour. |
| **provisional / needs corpus validation** | Heuristic or edge case left for future real-score corpora; not claimed as universal truth. |

Examples in code/tests include **§1c.8** items (bare `bass`, bare voice-role words, `cornetto` vs `cornett`, `+` stopped horn, diamond noteheads) and comments in `tests/test_audit_rigorous_timbral.py`, `tests/test_technique_state_timbral.py`, and related modules.

### 1e) Timbral model architecture: symbolic, cluster, and acoustic-informed layers

This subsection is **descriptive**; it does **not** replace the formal definitions in **§1c**. It groups the metrics so users do not conflate **vertical pitch geometry**, **symbolic orchestration**, **legacy blended timbral heuristics**, and **literature-linked proxies**.

| Layer | Metric(s) | Inputs | Role |
|-------|-----------|--------|------|
| **Symbolic texture** | **H(t)** | Durations, pitches, onset layout | Entropy / Wasserstein / multi-scale homogeneity (§1c.2–1c.6). |
| **Symbolic orchestration (legacy blend)** | **H_timbral** (legacy / symbolic / acoustic_heuristic *model modes* for the **same** scalar pipeline family) | Part names, taxonomy, register span, technique state, family pairwise tables | Headline timbral curve in the **H_timbral** tab; formulas in **§1c.8**. |
| **Vertical pitch cluster** | **H_cluster** | Sounding MIDI **only** | Chromatic compactness of the vertical multiset; **no** instrument names (see `analyzers/cluster.py`). |
| **Neutral symbolic orchestration** | **H_orchestration_symbolic** | Same timbral slices; Herfindahl on instrument / family / technique-only buckets | Isolates **layout uniformity** without legacy fusion matrices (`analyzers/orchestration_symbolic.py`). |
| **Notation-derived fusion potential** | **H_notated_fusion_potential** | Same timbral slices; Herfindahl on family + technique-only + register proximity; **instrument** axis uses **effective_instrument_uniformity** with **same_family_relief** on \((\sum_f P_f^2-\sum_i p_i^2)_+\) | One score-derived scalar joining orchestration-style concentration and register proximity; **no** legacy timbral pairwise kernels (`analyzers/notated_fusion_potential.py`; **§1c.14**). |
| **Acoustic-informed heuristic** | **H_fusion_acoustic_heuristic** | Symbolic slices + **default_profiles.json** feature vectors + harmonic roughness **proxy** | Optional cross-family interpretive layer; **not** audio DSP (`analyzers/fusion_acoustic_heuristic.py`, `acoustic_profiles/`). |

**Assumptions (all layers):** (i) MusicXML or MIDI is a faithful encoding of what the analyst should treat as “the score.” (ii) Exporters differ; missing directions are **unknown**, not “silently ordinary.” (iii) **Confidence** fields on fusion outputs are **internal model confidence** (coverage of profile tags, missing-feature penalties), **not** empirical validation against microphones.

**Acoustic literature (paraphrase only; no long quotations):** Laboratory and pedagogical references motivate **order-of-magnitude** shapes for registers of features (e.g. sustained brass vs bowed strings show different spectral slopes in aggregate studies). Early orchestral spectra and levels appear in Sivian, Dunn, and White ([1931](#18-bibliography), pp. 330–371 in the **journal** pagination stated in the registry entry—verify any private scan’s page map before citing PDF page numbers). Additional monographs and articles listed in **§18** support the **existence** of separate profile-vector families; many rows still use the registry page placeholder until pagination is verified on a held copy (**§18** introduction). Those citations justify **why** separate profile vectors exist; they do **not** prove that any particular MusicXML window matches a measured spectrum.

### 1f) Evidence and source registry

**Where the registry lives:** The canonical machine-readable bibliography and evidence metadata live in **`src/homogeneity_analyser/acoustic_profiles/source_registry.json`** (also described in YAML alongside for editors who prefer it). The loader is `homogeneity_analyser.acoustic_profiles.source_registry.load_source_registry`. Validation rules (unique `source_key`, quote length limits, release checks on page placeholders) live in `acoustic_profiles/source_validation.py`.

**Where numeric constants live:** Timbral / fusion defaults are versioned in **`src/homogeneity_analyser/acoustic_profiles/default_profiles.json`**, loaded by `acoustic_profiles/model_config.py`. Each constant row carries **`semantic_name`**, **`value`**, **`source_key`**, **`page_reference`**, **`rationale`**, **`evidence_status`**, and optional **`affects`** / **`model_role`**.

**How `source_key` links to the bibliography:** Every non-`project_specific` `source_key` in `default_profiles.json` must match a **`source_key`** field in `source_registry.json`. Diagnostics (`source_keys_used`, `provisional_constants_used`) surface which literature anchors and which knobs remain **project-specific** or **provisional**.

**How page references are validated:** `pages_consulted` is required for every registry row. Non-project literature rows whose pages are not yet verified on the private scan must use the sentinel string defined in `acoustic_profiles/source_validation.py` (same value as packaged JSON rows; not spelled out in this narrative so release doc scans stay clean). **`validate_source_registry(..., release_mode=True)`** rejects that sentinel for keys listed in `get_acoustic_model_governed_source_keys()` (currently empty, reserved for future governed binds). **§18 Bibliography** mirrors `pages_consulted` verbatim from JSON, including pending placeholders, so auditors can diff registry ↔ manual.

**Project-specific assumptions:** Constants tagged **`source_key: "project_specific"`** are engineering choices or legacy extractions; their `page_reference` and `rationale` fields explain scope. They are **not** claimed as universal acoustic truths.

**Provisional constants:** Entries with `evidence_status` in `provisional` / `needs_validation` (or marked `project_specific`) are listed separately in exports as **`provisional_constants_used`** so downstream audits can filter them.

### 1g) Why identical pitch clusters can receive different fusion estimates

Consider the **same concert-pitch multiset** in a window, e.g. **B3–C4–C#4–D4** (chromatic run), realised three ways:

1. **Four stopped horns** (uniform technique state if the score encodes stopped).  
2. **Four arco violins** (uniform arco).  
3. **Three B♭ clarinets + one bass clarinet** (distinct canonical instruments, possibly shared “ordinary” technique tail).

**H_cluster:** Depends only on sounding MIDI multisets and span. If the four concert pitches and multiplicities match, **H_cluster matches** across the three scenarios (subject to floating grid alignment).

**H_orchestration_symbolic:** Rewards overlap-weighted concentration on instruments / families / technique-only buckets. Uniform **four horns** or **four violins** tends toward **high** concentration on a single bucket per axis when shares are even; **three clarinets + bass clarinet** lowers instrument concentration because **two** canonical woodwind names share mass unless the window is dominated by one.

**H_notated_fusion_potential:** Uses the **same** overlap slices but combines **family** and **technique-only** Herfindahl axes with **register** proximity and an **instrument** axis based on **effective_instrument_uniformity** (default **balanced** profile \(\rho=0.55\)), so mass split across **different canonical instruments in the same taxonomy family** partially closes the gap between **instrument_uniformity** and **family_uniformity** without any instrument-pair matrix or clarinet/string-specific rules (see **§1c.14**).

**H_fusion_acoustic_heuristic:** May **differ** when `default_profiles.json` assigns different **profile vectors** or spectral slopes to horn, violin, and clarinet families, and when the harmonic roughness proxy (`acoustic_profiles/spectral_proxy.py`, template keyed as **`project_specific`**) penalises close partial trains differently as a function of those vectors. Differences are **permitted only** where the linked registry entry documents intent; otherwise treat divergence as a **bug**, not a feature.

**Legacy H_timbral:** Retains historical pairwise tables and cross-family boosts documented in **§1c.8**; it may therefore **not** coincide with **H_orchestration_symbolic** or **H_fusion_acoustic_heuristic** even when the vertical pitch content is identical. It remains the **compatibility** path for older CSV/JSON comparisons.

---

## 1c) Complete formulas and algorithms

This subsection matches the implementation in `homogeneity_analyser/analyzers/` and `homogeneity_analyser/services/analysis_service.py`. All times are in **music21 quarterLength** unless noted.

### 1c.1 Time grid

- Score duration: \(T = \texttt{highestTime}\) (quarter notes).
- Time step: \(\Delta t > 0\) (user **time_step**).
- Sample times: \(t_k = k \cdot \Delta t\) for \(k = 0, 1, \ldots\) while \(t_k \le T\) (floating grid; last point may equal \(T\) within numerical tolerance).

### 1c.2 Combining m1, m2, m3 into H(t)

Non-negative user weights \((\omega_1, \omega_2, \omega_3)\) are **normalized**:

\[
w_i = \frac{\max(0,\omega_i)}{w_1+w_2+w_3},\quad i\in\{1,2,3\}
\]

If the sum is zero (or invalid), use \(w_1=w_2=w_3=\tfrac{1}{3}\).

**Weighted geometric mean** (with \(\varepsilon = 10^{-15}\) to avoid \(\log 0\)):

\[
H(t) = \exp\left( w_1 \ln\max(m_1,\varepsilon) + w_2 \ln\max(m_2,\varepsilon) + w_3 \ln\max(m_3,\varepsilon) \right).
\]

Equal weights \(w_i=\tfrac{1}{3}\) give the **plain geometric mean** \((m_1 m_2 m_3)^{1/3}\).

**First time index:** there is no previous window; **\(m_2 := 1\)** for that sample only.

### 1c.3 Window and active notes (homogeneity)

For centre \(t\) and window **width** \(w\) (user **window_size**):

\[
I_t = \left[t - \frac{w}{2},\; t + \frac{w}{2}\right].
\]

A note/chord event with onset \(o\) and duration \(\ell\) is **active** in \(I_t\) iff \(o < t + w/2\) and \(o+\ell > t - w/2\).

If no event is active, **features are missing**; then:

- \(m_1 = s_{\mathrm{intra}}\) (**silence_intra_value**, default 0.5, clipped to \([0,1]\)),
- \(m_2 = s_{\mathrm{trans}}\) if exactly one of current/previous windows is silent (**silence_transition_value**),
- \(m_3\) follows the multi-scale rules below (often 1 if all scales empty).

### 1c.4 Metric m1 (intra-window)

From active events, build **histogram PMFs** (normalized counts):

- **Pitch** \(P_p\) over bins defined by **pitch_edges** (depends on **pitch_space** and **pitch_bin_step**):
  - `absolute`: bins step \(\Delta p\) semitones from \(\min(\text{pitch}) - 2\Delta p\) to \(\max(\text{pitch}) + 2\Delta p\); empty score uses MIDI-ish default span.
  - `pitch_class`: 12 bins for \(x = \texttt{ps} \bmod 12\).
- **Duration** \(P_d\) over fixed edges \((0, 0.25, 0.5, \ldots, 16)\) quarter lengths.
- **Joint** \(P_{pd}\) over pitch×duration 2D histogram, raveled to a vector.

Entropy (bits): \(\mathcal{H}(P) = -\sum_{i: P_i>0} P_i \log_2 P_i\).  
Max entropy: \(\mathcal{H}_{\max} = \log_2 K\) for \(K\) bins (or 0 if \(K\le 1\)).

Normalized concentration per channel: \(m_\ast = 1 - \mathcal{H}/\mathcal{H}_{\max}\) (or 1 if \(\mathcal{H}_{\max}=0\)).

\[
m_1 = \mathrm{clip}\left(\frac{m_{\mathrm{dur}} + m_{\mathrm{pitch}} + m_{\mathrm{joint}}}{3},\; 0,\; 1\right).
\]

### 1c.5 Metric m2 (inter-window)

Let \(P_{\mathrm{curr}}\) and \(P_{\mathrm{prev}}\) be pitch PMFs on the same **pitch_centers** \(c_j\).

- scipy **1st Wasserstein** distance \(W\) between discrete distributions on those centres with weights \(P_{\mathrm{curr}}(j)\), \(P_{\mathrm{prev}}(j)\).
- User scale **sigma** \(\sigma\):

\[
m_2 = \exp\left(-\frac{W}{\max(\sigma,\varepsilon)}\right)
\]

unless a silence rule applies (see §6.1). If either pitch PMF has zero mass, \(m_2 = 0\) when both are non-silent.

### 1c.6 Metric m3 (multi-scale)

Default scale factors \((1, 2, 4)\) multiply **window width** \(w\): for each \(s \in \{1,2,4\}\), features at \((t, s\cdot w)\).

For each scale-feature, compute **onset density** \(\rho_{\mathrm{onset}} = \#\text{onsets in } [t_s,t_e) / (s\cdot w)\) with \([t_s,t_e]\) the scaled window, and **sounding_density** = total overlap length of active notes in that window divided by window length.

- If **all** scales silent: \(m_3 = 1\).
- If **allow_partial_scales** is false and any scale is silent: \(m_3 = 0\).
- If partial allowed: drop silent scales; if \(\le 1\) scale left, \(m_3 = 1\).

Otherwise, **sustained** mode if **every** retained scale has \(\rho_{\mathrm{onset}} < 0.4\) and \(\rho_{\mathrm{snd}} > 0.3\); then use **sounding** differences between consecutive scales, else **onset** differences.

\[
m_3 = \frac{1}{1 + \overline{d}},\quad \overline{d} = \mathrm{mean}\bigl(|d_i|\bigr)\text{ across consecutive pairs.}
\]

### 1c.7 Single-aggregate mode

One evaluation at \(t = T/2\); \(m_2 := 1\); same \(m_1,m_3\) as above. Combine:

\[
H_{\mathrm{single}} = \exp(\cdots)\;\text{with}\;(m_1,\,1,\,m_3).
\]

Plot is a flat curve at \(H_{\mathrm{single}}\) over \([0,T]\).

### 1c.8 H_timbral (symbolic orchestration homogeneity)

User-facing definitions and scope are in **§1d** above. For each **part**, music21 resolves a raw instrument string; **`get_instrument_and_family`** maps it to **(canonical_instrument, family)** in `homogeneity_analyser/taxonomy/instrument_taxonomy.py` by **Unicode-normalised keys**, **longest-alias-first** iteration, **whole-token matching** for very short abbreviations (e.g. `bd`, `cl`), and **phrase-bounded** matching for longer aliases—**not** a naive substring search on arbitrary words (see tests in `tests/test_taxonomy.py`, `tests/test_audit_rigorous_timbral.py`).

Each note/chord tone yields a **timbral event**. Pitches used for the **register** term are taken in **concert sounding space** when the score supports it (`timbral_sounding_pitch.py`); unpitched percussion and mixed windows use the blended register rules in `timbral.py` (see `docs/H_TIMBRAL_SCORE_REPRESENTATION.md`).

**Baseline blend (instrument + register).** In window \(I_t\), collect active events; let \(N_I\) = number of distinct canonical instruments, \(N_F\) = distinct families, \(S\) = register span in semitones over the pitch set used for that window’s register term (\(\max-\min\); 0 if one pitch).

\[
C_I = \begin{cases}
1 & N_I = 1 \\
\beta_F & N_I>1 \land N_F = 1 \\
\dfrac{1}{1+(N_I-1)} & \text{otherwise}
\end{cases}
\]

\[
C_R = \frac{1}{1 + S / \max(r_{\mathrm{ref}},\,0.1)}
\]

\[
H_{\mathrm{baseline}} = \mathrm{clip}(w_I C_I + w_R C_R,\, 0,\, 1).
\]

Defaults: \(w_I=0.65\), \(w_R=0.35\), \(\beta_F=0.65\), \(r_{\mathrm{ref}}=3\) semitones.

**Implementation refinements** (applied in code after \(H_{\mathrm{baseline}}\)): **family-wise pairwise timbral modules** (strings, brass, flutes, clarinets, double reeds, saxophones, percussion); **notation context** for measure-level `TextExpression` / `RehearsalMark` / `Dynamic` when inferring techniques (`notation_context.py`); a small **verified cross-family additive layer** with explicit pair rules (`timbre_cross_relations.py`, documented in `docs/H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md`). The exported scalar series is the **final** \(H_{\mathrm{timbral}}\) after these steps.

**Technique-aware symbolic state (second generation).** `homogeneity_analyser/analyzers/technique_state.py` maintains **persistent playing directions per part** (e.g. `pizz.` until `arco`, `sul pont.` until `ord.` / `normale`, brass `bouché` / `open` / `cuivré`, mutes until `senza sord.`) by scanning each part in chronological order (directions before simultaneous notes).
**Note-local** lyrics / expressions on a single note (`notation_text_context_for_note(..., measure_text="none")`) are applied on a **copy** of the timeline for that note’s merge only—they **do not** advance persistent state, so a marking attached to one note does not carry to the next.
Each timbral event carries a **`technique_state_id`** (e.g. `horn|open`, `horn|stopped`, `horn|cuivre`, `violin|arco|sul_pont|muted`).
Window features include **`timbral_state_distribution`** (overlap-mass weighted), **`dominant_timbral_state`**, and **`timbral_state_concentration`** \(=\sum p_i^2\) over that distribution.
**Uniform** special techniques (four horns all stopped, four violins all sul ponticello) remain **high** pairwise technique agreement; **mixed** techniques (half open / half stopped) lower homogeneity.
The scalar \(H_{\mathrm{timbral}}\) blends the refined instrument component with **concentration** so mixed states reduce the score without penalising a uniformly scored section merely for being stopped or cuivré.
Only semantic MusicXML / music21 fields and text are used—no PDF or image inference.

**Project defaults (instrument names — not universal notation law).** These choices avoid false positives in sparse part names; refine part labels in the score if your genre differs:

- **Bare `bass`** (alone) → **double bass** (strings). Choral or vocal bass lines should be named e.g. **`bass voice`**.
- **Bare `alto`**, **`tenor`**, **`baritone`** (without `saxophone`, `flute`, etc.) → **voice** roles, not wind instruments.
- **`cornetto`** (common in PT/IT band naming) → **cornet**; early-music **cornett** remains the separate canonical **`cornett`**. Editors may still write “cornetto” for historical cornett—disambiguation is by part naming, not score-type inference.

**Project defaults (technique text / symbols — symbolic heuristics):**

- **Wind:** **`senza vibrato`**, **`non vibrato`**, etc. are matched **before** a bare **`vibrato`** token so the negation is not misclassified as vibrato.
- **Strings:** **`molto flautando`** is treated as **pressure / colour** (distinct from **`flautando`** / sul tasto **contact**). **`ord.` / `ordinario` / `normale`** (string reset) clears **harmonic** state as well as contact / tremolo defaults; **`con sord.`** mute handling remains separate.
- **`+` as stopped horn** is recognised only when parsed as **brass technique text** (isolated `+` or explicit “plus sign”), not inside arbitrary arithmetic-looking strings.
- **Diamond string noteheads** are treated as a **harmonic hint** for bowed strings when no other harmonic flag is set; this is **not** guaranteed semantic truth across all publishers.
- **`Stopped`** articulation on a note and other music21 articulations/expressions are interpreted in the **symbolic** layer only; meaning still depends on part/instrument context in the score.
- **Ambiguous but intentionally accepted (example):** **`senza sord.` on brass** is handled primarily as **mute** cancellation; it **does not** clear **hand-stopped** horn primary state in the shipped rules (see `tests/test_technique_state_timbral.py::test_senza_sord_does_not_clear_stopped_primary`).

Alias **collision** reporting: `get_alias_collision_log()` in the taxonomy module; tests require undocumented collisions to be empty unless explicitly allow-listed. Conventions above are asserted in **`tests/test_audit_rigorous_timbral.py`** and **`tests/test_taxonomy.py`** (with short comments on each questionable case).

**Silent window** (no notes): \(H_{\mathrm{timbral}} = 0.5\).

### 1c.9 Register uniformity U(t)

User bounds converted to MIDI pitch \(R_{\min}, R_{\max}\) (sorted). **Bin edges** on semitone strips from \(R_{\min}-0.5\) to \(R_{\max}+0.5\) → \(K\) bins.

In each window, collect pitches in \([R_{\min},R_{\max}]\). Let PMF \(p_i\) over bins (natural log entropy):

\[
\mathcal{H}(U) = -\sum_i p_i \ln p_i,\quad \mathcal{H}_{\max} = \ln(K).
\]

\[
U = \mathrm{clip}\left(\frac{\mathcal{H}(U)}{\max(\mathcal{H}_{\max},\varepsilon)},\; 0,\; 1\right).
\]

- No pitches in window: **NaN**.
- Single pitch: **0** (no spread across bins).

### 1c.10 Change-point segmentation

- **Z-threshold:** on differences \(d_j = |H_{j+1}-H_j|\); peaks where \(d_j > \mu + z \sigma\); minimum gap \(g\) between indices.
- **PELT:** least-squares cost per segment + penalty \(\beta\); minimum segment length \(L\); pruned exact linear-time search (see §6.1).

### 1c.11 Sensitivity analysis (homogeneity)

After the main run, recompute \(H\) with window widths \(0.75w\), \(w\), \(1.25w\); interpolate to the reference time grid; report Pearson **r** with reference \(H\) and mean/std of each curve.

### 1c.12 Combined CSV

`run_both_and_combine` aligns **H_timbral** (legacy), **H_cluster**, and **H_orchestration_symbolic** onto the homogeneity time grid by linear interpolation (fusion and confidence fields are **not** appended to this primary CSV; they live in **`combined_series`** inside combined JSON and in **`cluster_orch_fusion_diagnostics_csv`** — see §1c.13).

When **m1–m3** are present (default full run), the header is:

`t_quarterLength,H,m1,m2,m3,H_timbral`

followed optionally by **`H_cluster`**, **`H_orchestration_symbolic`**, and **`dominant_timbral_state`** when those series are available and length-matched. Example with all optional columns:

`t_quarterLength,H,m1,m2,m3,H_timbral,H_cluster,H_orchestration_symbolic,H_notated_fusion_potential,H_notated_fusion_potential_dynamic,dominant_timbral_state`

If **m1–m3** are absent, the base columns are `t_quarterLength,H,H_timbral` with the same optional **`H_cluster`**, **`H_orchestration_symbolic`**, **`H_notated_fusion_potential`**, **`H_notated_fusion_potential_dynamic`**, and **`dominant_timbral_state`**. The same alignment and CSV text appear inside the **combined** JSON export under **`combined_csv`** (see §1c.13).

### 1c.13 Structured JSON export

The module **`homogeneity_analyser.services.json_export`** builds machine-readable documents with **`schema_version`: `"1.8"`** (additive evolution from 1.0 → … → 1.6 → 1.7 → 1.8). Every document includes **`model_version`** (bundle identifier for the export layer), **`metric_kind`** (same string as **`kind`**, for consumers that prefer a neutral name), and **`not_audio_analysis`: `true`** (score-derived metrics only; no user audio waveforms). A **`kind`** discriminator selects the layout:

| `kind` | Builder | Typical contents (when `error` is absent) |
|--------|---------|-------------------------------------------|
| `homogeneity` | `build_homogeneity_export` | `parameters`, `results` / `plot_series`, `summary`, `change_point_indices`, `change_times`, `sensitivity`, optional `score_metadata` |
| `timbral` | `build_timbral_export` | `parameters`, `results`, `summary`, `timbral_homogeneity_note`, `timbral_state_series`, `primary_series`, optional `h_timbral_effective_parameters`, optional `score_metadata`, optional nested **`timbral_semantic_model`** (`model_version` there is the **timbral semantics** submodule id, distinct from top-level **`model_version`**) |
| `cluster` | `build_cluster_export` | `cluster_metric_note`, `parameters`, `results`, `primary_series`, optional `score_metadata` |
| `orchestration_symbolic` | `build_orchestration_symbolic_export` | `orchestration_symbolic_note`, `parameters`, `results`, `primary_series`, optional `score_metadata` |
| `notated_fusion_potential` | `build_notated_fusion_potential_export` | `notated_fusion_potential_note`, `parameters`, `results` (includes **`H_notated_fusion_potential_diagnostics`** with **`instrument_uniformity`**, **`family_uniformity`**, **`same_family_cross_instrument_mass`**, **`same_family_relief`**, **`effective_instrument_uniformity`**, **`dynamic_coherence`**, **`H_notated_fusion_potential_dynamic`**, …), `primary_series`, optional `score_metadata` (includes **`same_family_relief`**, **`same_family_relief_profile`**, override flag, evidence note, **`weight_notated_fusion_dynamic`**) |
| `fusion_acoustic_heuristic` | `build_fusion_acoustic_heuristic_export` | `fusion_acoustic_heuristic_note`, `parameters`, `results` (includes per-window **`H_fusion_acoustic_heuristic_diagnostics`** with **`confidence_score`** / **`confidence_label`** / **`sources_used`**), `primary_series`, optional `score_metadata`, **`source_keys`** (sorted union of diagnostic `sources_used` strings) |
| `register_uniformity` | `build_register_export` | `parameters` (includes resolved `register_*_midi_ps` when available), `results`, `summary`, optional `score_metadata` |
| `combined_homogeneity_timbral` | `build_combined_export` | `homogeneity_parameters`, `timbral_parameters`, metric notes, `summaries`, `combined_series` (**`H`**, legacy **`H_timbral`**, **`H_cluster`**, **`H_orchestration_symbolic`**, **`H_notated_fusion_potential`**, **`H_notated_fusion_potential_dynamic`**, **`H_fusion_acoustic_heuristic`**, **`legacy_H_timbral`**, aligned **`confidence_score`** / **`confidence_label`** / **`main_penalty_reason`**, optional **`U`** when register results are passed in), `combined_csv`, `cluster_orch_fusion_diagnostics_csv`, nested **`homogeneity`**, **`timbral`**, **`cluster`**, **`orchestration_symbolic`**, **`notated_fusion_potential`**, **`fusion_acoustic_heuristic`**, optional **`register_uniformity`**, and root-level **`source_keys`** (copy of the nested fusion export’s union when fusion is embedded) |

**Two different `model_version` fields:** On every export document, **top-level** **`model_version`** identifies the **JSON export bundle** (`JSON_EXPORT_MODEL_VERSION` in `json_export.py`). When present, the nested **`timbral`** object’s **`timbral_semantic_model.model_version`** identifies the **timbral semantics documentation** submodule (`TIMBRAL_MODEL_SEMANTICS_VERSION` in `timbral_semantics.py`). They answer different questions; do not merge them in downstream schemas without documenting both.

**`write_json_export(path, document)`** writes UTF-8 indented JSON. The Gradio UI offers **“Download full results (JSON)”** on each analysis tab after a successful run; plot export uses Plotly with **PNG via Kaleido** when available, else **standalone HTML** (see `pyproject.toml` pins).

### 1c.14 H_notated_fusion_potential (notation-derived fusion potential)

**Source events:** Same overlap construction as timbral / orchestration metrics (`TimbralHomogeneityAnalyzer` events → window slices with `overlap_ql`, canonical `instrument`, taxonomy `family`, `technique_state_id`, optional sounding `pitch` as MIDI).

**Mass normalisation:** Over a window, only slices with positive overlap contribute. Let total mass \(M=\sum \texttt{overlap\_ql}\). For each canonical instrument label \(i\), \(p_i\) is its share of \(M\) (same for families and technique-only keys from the same rows).

**Herfindahl-style uniformity inputs (each in \([0,1]\)\):**

- **instrument_uniformity** \(H_i = \sum_i p_i^2\) (concentration on canonical instruments).
- **family_uniformity** \(H_f = \sum_f P_f^2\) where \(P_f=\sum_{i\in f} p_i\) is total mass in family \(f\).
- **technique_only_uniformity** \(H_t\) — same Herfindahl on `technique_state_id` tails used elsewhere in the timbral stack.

**Same-family relief (distribution-only):**

\[
\text{same\_family\_cross\_instrument\_mass} = \max\bigl(0,\; H_f - H_i\bigr)
\]

\[
\text{effective\_instrument\_uniformity} = H_i + \rho \cdot \text{same\_family\_cross\_instrument\_mass}
\]

with **same_family_relief** \(\rho\) clamped to \([0,1]\). Named profiles in `SAME_FAMILY_RELIEF_PROFILES`: **strict** \(0\), **conservative** \(0.45\), **balanced** \(0.55\), **permissive** \(0.65\); default profile **balanced** (override via `same_family_relief_override`). There are **no** pairwise instrument tables and **no** special cases for particular instruments or families; any number of instruments and families is covered by the same formulas.

**Register proximity:** From pitched rows \((\texttt{pitch}, \texttt{overlap\_ql})\), a mass-weighted mean of \(1/(1+d_{ij}/r_{\mathrm{ref}})\) over unordered pairs \((i,j)\) with \(d_{ij}\) semitone distance and **`notated_fusion_register_ref_semitones`** \(r_{\mathrm{ref}}\) (default **12**). Unpitched-only windows yield register proximity **1.0** with coverage status **`no_pitched_pairs`** / **`insufficient_pairs`** in diagnostics.

**Scalar H_notated_fusion_potential:** Let \((w_i,w_f,w_t,w_r)\) be the normalised tuple from **`weight_notated_fusion_instrument`**, **`weight_notated_fusion_family`**, **`weight_notated_fusion_technique`**, **`weight_notated_fusion_register`** (defaults **0.30 / 0.15 / 0.25 / 0.30**). With \(\varepsilon\) tiny and **effective** instrument term \(H_i^{\mathrm{eff}}=\) **effective_instrument_uniformity**:

\[
H_{\mathrm{nf}} = \exp\bigl( w_i \ln H_i^{\mathrm{eff}} + w_f \ln H_f + w_t \ln H_t + w_r \ln R \bigr)
\]

clipped to \([0,1]\), where \(R\) is register proximity.

**Per-window diagnostics** (non-exhaustive): `instrument_uniformity`, `family_uniformity`, `technique_only_uniformity`, `register_proximity`, `same_family_cross_instrument_mass`, `same_family_relief`, `same_family_relief_profile`, `same_family_relief_delta`, `same_family_relief_applied`, `effective_instrument_uniformity`, `H_notated_fusion_potential`, `evidence_status`, distributions, register coverage, plus **notation-symbolic dynamic coherence** (`dynamic_coherence`, `dynamic_level_distribution`, `dynamic_process_distribution`, `crescendo_active`, `diminuendo_active`, `dynamic_divergence_detected`, `dynamic_coverage_status`, `dynamic_evidence_status`, `H_notated_fusion_potential_dynamic`) — see `compute_notated_fusion_potential_from_slices` / `compute_dynamic_coherence_bundle` in `analyzers/notated_fusion_potential.py` and `analyzers/notated_fusion_dynamic.py`.

**Bibliography-aware rationale (long form):** `docs/model_audit/H_NOTATED_FUSION_POTENTIAL_JUSTIFICATION.md`.

---

## 2) Quick Start

### Install
```bash
pip install -r requirements.txt
```
(`requirements.txt` installs the package in editable mode with dev tools: `-e ".[dev]"`.)

### Run
```bash
python -m homogeneity_analyser
```
(or, after install: `homogeneity-analyser`)

The Gradio interface opens in your browser. Upload a score and configure parameters. The **Loaded XML inspection** tab refreshes automatically when the shared upload changes (see **§3.0**).

---

## 3) Tutorial (step-by-step, pedagogical)

This section teaches you how to use the analyser from scratch. Each step explains **what you do**, **what you see**, and **why it matters**.

---

### 3.0 Gradio UI: shared upload, numeric input, and Loaded XML inspection

**Shared upload.** One control at the top — **“Upload score once…”** — feeds every tab: **Homogeneity H(t)**, **Legacy H_timbral (diagnostic)**, **H_orchestration_symbolic**, **Register uniformity U(t)**, **Combined**, and the **Loaded XML inspection** refresh on `file_shared.change` (`homogeneity_analyser.ui.gradio_app`). Each **Run** button passes that same component as its **first** callback input so the path always matches what you uploaded.

**Resolving the uploaded file.** `validate_uploaded_score` in `homogeneity_analyser.ui.validation` normalises whatever Gradio supplies to a filesystem path: plain `str` / `pathlib.Path`, a dict with **`path`** or **`name`**, an object with **`.path`** or **`.name`**, or a **single-element** list/tuple wrapping one of those. Allowed extensions remain **`.xml`**, **`.musicxml`**, **`.mxl`**, **`.mid`**, **`.midi`** (same rules as pre-parse validation).

**Numeric parameters.** Sliders and number boxes use **`parse_ui_float`** and **`coerce_float`** in `homogeneity_analyser.ui.validation` (same parsing rules). You may use either a **dot** or a **comma** as the decimal separator (e.g. **`0.25`** or **`0,25`** for the time step). Values that mix both separators in one token (e.g. **`1,234.5`**) are rejected as ambiguous. **Empty** optional fields still fall back to their defaults; **invalid non-empty** text (e.g. `abc`) **raises**—there is **no silent substitution** with the default. On the **H_timbral** tab, a **ValueError** from numeric parsing is caught and returned as a **visible summary** plus a stub plot so the rest of the UI does not collapse to a generic error. On **Homogeneity H(t)**, **H_orchestration_symbolic**, and **Combined**, invalid weights or other coerced numbers surface as a **Gradio error** with the same message text.

**Loaded XML inspection (tables + CSV).** The callback `run_loaded_xml_inspection` in `homogeneity_analyser.ui.callbacks` builds the same audit **dict** rows as before and writes the three audit CSVs via **`audit_rows_to_csv_string`** into temp files (`_write_temp_csv`, `pathlib.Path`). The three **Dataframe** outputs are **`pandas.DataFrame`** instances with fixed column order (`SCORE_AUDIT_INVENTORY_COLUMNS`, `SCORE_AUDIT_EVENT_COLUMNS`, `SCORE_AUDIT_VERTICAL_COLUMNS` from `services/score_audit.py`) so Gradio renders **columns and cells** correctly (not a single **`[object Object]`** column from raw dict rows). Empty audits still return **header-only** frames. Any cell that would otherwise hold a nested **dict** or **list** is JSON-stringified for display; CSV export logic is unchanged.

---

### 3.1 What the app does (in one sentence)

The app reads a **symbolic score** (MusicXML or MIDI) and draws a **curve H(t)** that tells you how “uniform” or “mixed” the music is over time: **high H** = stable, homogeneous texture; **low H** = change or variety. For **timbral/orchestration-style** questions, prefer **H_cluster**, **H_orchestration_symbolic**, and **H_fusion_acoustic_heuristic** from the **Combined** tab; **legacy H_timbral** is a **backward-compatible diagnostic** (see **§1d**), not measured audio and not acoustically validated fusion. **U(t)** measures how evenly pitches are spread within a register you set (cluster → low U, spread → high U).

---

### 3.2 First run: from zero to your first H(t) curve

**Goal:** Open the app, load a score, and see a homogeneity curve.

1. **Install and start**
   - In a terminal, go to the project folder and run:  
     `pip install -r requirements.txt`  
     then  
     `python -m homogeneity_analyser`
   - **What you see:** A URL (e.g. http://127.0.0.1:7860). Open it in your browser.
   - **Why:** The app runs as a small web interface (Gradio). You do everything in the browser.

2. **Upload one score**
   - At the top you see **“Upload score once…”**. Click it and choose a MusicXML (`.xml`, `.musicxml`, `.mxl`) or MIDI (`.mid`, `.midi`) file from your computer (e.g. an export from Sibelius or Dorico).
   - **What you see:** The file name appears. You do **not** need to upload again when you switch tabs.
   - **Why:** All tabs (Homogeneity, Timbral, Register uniformity, Combined) use this same file.
   - **Optional — inspect the parse:** Open **Loaded XML inspection** (updates when the upload changes). You get three tables (instrument inventory, per-pitch event audit, vertical sonority groups) and matching **CSV** downloads — useful to see what music21 read before interpreting metrics (**§3.0**).

3. **Open the “Homogeneity H(t)” tab**
   - Click the **Homogeneity H(t)** tab. You see several parameters; most have default values.
   - **What the main parameters mean (you can leave them as-is for the first run):**
     - **Time step** (default 0.25): How often we “measure” homogeneity along time. Smaller = finer curve, more points.
     - **Window size** (default 4.0): Length of each “slice” of the score we analyse (in quarter notes). Smaller = more local detail; larger = smoother.
     - **Sigma** (default 12.0): How sensitive we are to *changes* between consecutive windows. Lower sigma = more reactive to small changes.

4. **Run the analysis**
   - Click **“Run homogeneity analysis”**.
   - **What you see:**
     - **H(t) plot:** A line between 0 and 1 over time. Peaks = more homogeneous; dips = more heterogeneous or transitional.
     - **Summary:** Numbers (min/mean/max H, number of windows, **Change points** and **Change times**). Change points are the time indices where the algorithm detects a clear shift in homogeneity.
     - **Download CSV**, **Download plot image** (PNG or HTML for interactive Plotly when static PNG is unavailable), and **Download full results (JSON)** for parameters, series, summary, sensitivity, and score metadata.
   - **Why it’s useful:** You get an objective curve of “how uniform” the texture is, plus automatic segmentation (change points) you can use for analysis or labelling.

5. **How to read the curve**
   - **H close to 1:** That moment is very homogeneous (e.g. one chord, stable rhythm, similar pitches).
   - **H close to 0:** That moment is very mixed (many different pitches, durations, or a strong change from the previous window).
   - **Change times** in the summary tell you *where* the main shifts happen (in quarter-note time).

---

### 3.3 One number for a static chord: Single aggregate and the gauge

**Goal:** You have a score that is basically **one chord** or one sustained block (no real change over time). You want **one** homogeneity value and a clear visual (**gauge** / donut chart).

1. **Upload** that score (same as before).
2. **Stay in “Homogeneity H(t)”** and tick **“Single aggregate mode (one H value)”**.
3. Click **“Run homogeneity analysis”**.
4. **What you see:**
   - **H(t) plot:** A *horizontal* line at a single H value (the same for the whole piece).
   - **Homogeneity gauge:** A donut chart with that value (0–1) and the number in the centre.
   - **Summary:** One window; H min = mean = max; 0 change points.
5. **Optional:** Use **“Gauge color (static chord)”** to change the donut colour (Green, Blue, Teal, etc.).
6. **Why:** For static or quasi-static textures, one number and a gauge are easier to read than a long curve.

---

### 3.4 Legacy H_timbral (diagnostic): one instrument vs many

**Goal:** Debug the **backward-compatible legacy** orchestration-register scalar (one instrument vs same family vs many families). **Not** recommended as the sole interpretive timbral metric — use **Combined** for **H_cluster** / **H_orchestration_symbolic** / **H_fusion**.

1. **Upload** a score (MusicXML is best: Sibelius/Dorico export instrument names per part; MIDI often does not).
2. Open the **“Legacy H_timbral (diagnostic)”** tab.
3. Leave **Time step** and **Window size** as default (or match the Homogeneity tab if you want to compare).
4. Click **“Run legacy H_timbral diagnostic”**.
5. **What you see:**
   - **legacy H_timbral(t) plot:** High when only one instrument (or one family) sounds in the window; low when many different instruments sound.
   - **Summary:** Starts with a **WARNING** line; then min/mean/max of H_timbral (numeric series unchanged).
   - **Download CSV**, plot file, and **full-results JSON** (same pattern as the Homogeneity tab).
6. **Why:** You can study orchestration (e.g. “tutti vs soli”) and compare with the distribution homogeneity H(t) in the **Combined** tab.

---

### 3.5 Register uniformity U(t): evenness of pitch distribution in a register

**Goal:** Measure how **evenly** pitches are distributed within a **range you define** (e.g. A1 to E7). A cluster in one register → low U; a large chord spread across the range → high U.

1. **Upload** a score (same as before).
2. Open the **"Register uniformity U(t)"** tab.
3. **Set the register limits** (required):
   - **Lower register limit** — e.g. `A1` or `21` (MIDI). Note name or MIDI number.
   - **Upper register limit** — e.g. `E7` or `88` (MIDI).
4. Set **Time step** and **Window size** (defaults 0.25 and 4.0 are fine).
5. Click **"Run register uniformity analysis"**.
6. **What you see:** A curve **U(t)** in [0, 1]: high when pitches in each window are spread evenly across the range; low when they are concentrated in one part of the range. Summary (min/mean/max U), **Download CSV** (columns `t_quarterLength`, `U`), plot file, and **full-results JSON**.
7. **Why:** You can study registral distribution (e.g. "all in middle register" vs "spread from bass to treble") and the mutual distance between components within your chosen range.

### 3.6 Combined tab: aligned H, legacy H_timbral, H_cluster, H_orch, and fusion

**Goal:** Run **homogeneity H(t)**, **legacy H_timbral(t)**, **H_cluster(t)**, **H_orchestration_symbolic(t)**, and **H_fusion_acoustic_heuristic(t)** on one grid and export **combined CSV**, **diagnostics CSV**, plots, and **combined JSON**.

1. Open the **“Combined (H + H_timbral + H_cluster + H_orch + fusion)”** tab (exact Gradio label).
2. Set **Time step**, **Window size**, **Sigma**, and optional **H weights m1/m2/m3** (defaults: ⅓ each); optional **legacy H_timbral** and **H_orchestration_symbolic** weight fields match the standalone tabs.
3. Click **“Run combined analyses”**.
4. **What you see:** Plots ordered **H** → **H_cluster** → **H_orchestration_symbolic** → **H_fusion_acoustic_heuristic** → **legacy H_timbral** (diagnostic last); **combined CSV** (§1c.12); **cluster/orchestration/fusion diagnostics** table + CSV (**`legacy_H_timbral`** starts hidden in the Plotly overlay legend); **`confidence_score`**, **`confidence_label`**, **`main_penalty_reason`**; per-metric plot downloads; **Download full results (JSON)** with **`interpretation_guidance`**, nested documents, **`combined_series`**, and **`combined_csv`** text.
5. **Why:** Compare **texture homogeneity (H)** with the **recommended stack** (**H_cluster**, **H_orchestration_symbolic**, **H_fusion** with confidence) and keep **legacy H_timbral** only as a **backward-compatible diagnostic** — not acoustically validated fusion.

---

### 3.7 Pitch space: absolute vs pitch_class

**Goal:** Understand whether your homogeneity changes are due to **register** (octave) or only **pitch class** (note name).

- **Absolute (default):** Pitch is “full” (e.g. MIDI). Moving a chord up an octave **reduces** homogeneity (different register).
- **Pitch class:** Only note name matters (C, D, … mod 12). The same chord in different octaves is treated as **the same**; homogeneity stays high.
- **What to do:** Run the same score twice: once with **Pitch space: absolute**, once with **pitch_class**. Compare the curves. If they differ a lot, register is important; if they are similar, the effect is mostly harmonic.

---

### 3.8 Detecting a clear texture change

**Goal:** Make the curve react strongly at a known “break” in the piece.

- Set **Time step** to **0.1** and **Window size** to **0.75–1.0** (more local).
- Set **Sigma** to **2.0** (more sensitive).
- Run and check where **H(t)** drops; read **Change points** and **Change times** in the summary. They should be close to the real structural change.

---

### 3.9 Scores with many rests or sparse texture

If the score has long silences or very sparse writing:

- Set **Silence intra value** and **Silence transition value** to **0.5** (neutral) so silence does not dominate the curve.
- Keep **Allow partial scales in m3** checked so short or empty windows do not force H to 0 and the curve remains interpretable.

---

### 3.10 End-to-end tutorial (one score, all analyses)

Follow this order the first time you explore a piece:

1. **Prepare** — Export **MusicXML** from your notation program when possible (better part names than MIDI).
2. **Start the app** — `python -m homogeneity_analyser` (or `homogeneity-analyser`), open the local URL.
3. **Upload once** — Use the top **Upload score** control; the same file powers every tab.
4. **Homogeneity H(t)** — Run with defaults; download **CSV** / **JSON** and confirm columns include **`m1,m2,m3`** after **H** if you need to debug which term drops at a given bar.
5. **H_timbral** — Run with the **same** time step and window size as step 4 for easy comparison. If the curve is flat or odd, check instrument names in the score.
6. **Register U(t)** — Set **lower/upper** limits to the band you care about (e.g. full orchestral range vs vocal range). Interpret **U** as occupancy evenness, not voice-leading.
7. **Combined** — Run to obtain **combined CSV** (§1c.12), **diagnostics CSV** (cluster / orch / notated fusion / fusion / legacy), and **combined JSON** on one time grid. **`combined_series`** includes **H**, **m1–m3** (when the homogeneity run provides them), **H_timbral** (= **legacy** symbolic orchestration-register homogeneity), **`legacy_H_timbral`** (same values as **H_timbral**), **H_cluster**, **H_orchestration_symbolic**, **`H_notated_fusion_potential`**, **`H_notated_fusion_potential_dynamic`** (base scalar × **dynamic_coherence**^**weight_notated_fusion_dynamic**; penalises cross-part dynamic *divergence* only, not a shared level or shared hairpin), **H_fusion_acoustic_heuristic**, **`confidence_score`**, **`confidence_label`**, **`main_penalty_reason`**, and optional **`dominant_timbral_state`**. **Confidence** qualifies the **fusion heuristic**, not empirical truth about a recording.
8. **Optional** — Enable **Single aggregate** only for a single static chord or block texture; use the **gauge** for a single number.

### 3.11 Interpreting exported columns

**Primary combined CSV** (`combined_csv` in JSON; download from Combined tab) — see §1c.12:

| Column | Meaning |
|--------|---------|
| `t_quarterLength` | Time in quarter notes from the score start |
| `H` | Weighted geometric mean of **m1**, **m2**, **m3** |
| `m1` | Intra-window entropy consistency |
| `m2` | Inter-window Wasserstein stability (first sample: nominal 1) |
| `m3` | Multi-scale density agreement |
| `H_timbral` | **Legacy** symbolic timbral-instrumental / orchestration-register homogeneity (**not** measured audio) |
| `H_cluster` | Vertical pitch-object compactness from **sounding MIDI** (instrument-independent) |
| `H_orchestration_symbolic` | Neutral symbolic **instrument / family / technique** uniformity (Herfindahl) |
| `H_notated_fusion_potential` | Notation-derived fusion-potential proxy (Herfindahl + **same_family_relief** on instrument vs family concentration + sounding register proximity; **not** measured audio) |
| `H_notated_fusion_potential_dynamic` | Same base scalar adjusted by **dynamic_coherence** (shared pp/mf or shared hairpin → ~1; mixed levels/processes below 1); **not** SPL |
| `dominant_timbral_state` | Optional; dominant timbral state label when the timbral run supplies it |

**Cluster / orchestration / fusion diagnostics CSV** (separate download; also embedded as text in combined JSON):

| Column | Meaning |
|--------|---------|
| `H_cluster` | Vertical pitch-object compactness from **sounding MIDI** |
| `H_orchestration_symbolic` | Neutral symbolic **instrument / family / technique** uniformity (Herfindahl) |
| `H_notated_fusion_potential` | Notation-derived fusion-potential proxy (Herfindahl + **effective_instrument_uniformity** / register proximity) |
| `H_notated_fusion_potential_dynamic` | Base notated fusion × **dynamic_coherence** (cross-part dynamic divergence only) |
| `H_fusion_acoustic_heuristic` | Literature/profile-informed **proxy**; **not** measured audio |
| `legacy_H_timbral` | Same curve as **H_timbral** above; retained for direct comparison to fusion/cluster/orch |
| `confidence_score` | Internal model confidence for the fusion scalar (0–1) |
| `confidence_label` | Human-readable confidence band for fusion |
| `main_penalty_reason` | Which penalty dominated when fusion confidence was down-rated |

**Combined JSON only** (`combined_series` object):

| Field | Meaning |
|--------|---------|
| `legacy_H_timbral` | Alias of **H_timbral** on the aligned grid |
| `H_notated_fusion_potential` | Notation-derived fusion-potential scalar (same windowing as **H**); per-window JSON diagnostics include relief-related uniformity fields |
| `H_notated_fusion_potential_dynamic` | Dynamic-adjusted scalar (same windowing); diagnostics include **`dynamic_coherence`** |
| `H_fusion_acoustic_heuristic` | Fusion scalar (same windowing as **H**) |
| `confidence_score` / `confidence_label` / `main_penalty_reason` | Align fusion interpretability with each **t** sample |
| `source_keys` (root of combined document, when fusion is embedded) | Sorted union of fusion diagnostic **`sources_used`** tags |

**Register tab only:** `U` — register occupancy evenness.

---

## 4) Inputs

Supported files:
- **MusicXML**: `.xml`, `.musicxml`, `.mxl`
- **MIDI**: `.mid`, `.midi`

Key parameters:

| Parameter | Meaning | Typical Range |
|---|---|---|
| Time step | Time resolution for `H(t)` samples (quarterLength) | 0.05–0.5 |
| Window size | Size of each analysis window (quarterLength) | 0.5–4.0 |
| Sigma | Sensitivity of inter‑window stability | 0.5–6.0 |
| Pitch space | `absolute` or `pitch_class` | choose by goal |
| Pitch bin step | Semitone resolution for pitch bins | 0.5–2.0 |
| Silence intra value | m1 value when window is silent | 0.3–0.7 |
| Silence transition value | m2 value when one window is silent | 0.3–0.7 |
| Allow partial scales | If true, m3 ignores missing scales instead of dropping to 0 | True/False |
| **Single aggregate mode** | One H value for the whole score (static chord); shows gauge | Off for H(t), On for gauge |
| **Gauge color** | Colour of the homogeneity wedge (Green, Blue, Teal, etc.) | Any of the list |
| **Weight m1 / m2 / m3** | Non-negative; normalized to sum 1 for combining metrics | Default ⅓ each |
| **Register uniformity (U(t) tab)** | | |
| Lower register limit | Bottom of pitch range (note name e.g. A1, or MIDI e.g. 21) | Required for U(t) |
| Upper register limit | Top of pitch range (note name e.g. E7, or MIDI e.g. 88) | Required for U(t) |
| **`H_notated_fusion_potential` (library / `run_notated_fusion_potential_analysis`)** | | |
| `same_family_relief_profile` | Named calibration: **strict** / **conservative** / **balanced** / **permissive** | default **balanced** (\(\rho=0.55\)) |
| `same_family_relief_override` | Optional numeric override of \(\rho\) (`null`/omitted key/empty string = use profile only). **Combined Gradio tab:** one-line **text** field (default empty) so an unset field is not mistaken for `0.0`. | \([0,1]\) when set |
| `same_family_relief` | Resolved \(\rho\) passed to the analyzer (after override/profile resolution) | \([0,1]\) |
| `notated_fusion_register_ref_semitones` | \(r_{\mathrm{ref}}\) for register proximity denominator | positive; default **12** |
| `weight_notated_fusion_*` | \((w_i,w_f,w_t,w_r)\) before normalisation | non-negative, sum \(>0\); defaults **0.30 / 0.15 / 0.25 / 0.30** |

The Gradio **Combined** tab exposes **Same-family relief profile** and optional **numeric override**; other knobs use **`DEFAULT_NOTATED_FUSION_POTENTIAL_PARAMS`** in `services/constants.py` or merge overrides when calling **`run_both_and_combine`** / **`run_notated_fusion_potential_analysis`**.

Empty number fields (Time step, Window size, Sigma, etc.) are replaced by defaults (0.25, 4.0, 12.0, …) so the app does not error.

---

## 5) Conceptual Model

At each time sample the analyser computes three components **m1**, **m2**, **m3** \(\in [0,1]\) (see **§1c** for full definitions):

| Component | Idea |
|-----------|------|
| **m1** | Intra-window **concentration** of duration, pitch, and joint pitch×duration PMFs (normalized Shannon entropy in bits). |
| **m2** | **Stability** of the pitch PMF vs the previous window (1st Wasserstein → exponential decay with **sigma**). |
| **m3** | **Multi-scale** agreement of onset or sounding density across window widths \(w, 2w, 4w\). |

**Final H(t)** is a **weighted geometric mean** of \((m_1,m_2,m_3)\) with user weights normalized to sum 1; default equal weights give \((m_1 m_2 m_3)^{1/3}\). Any low component pulls \(H\) down.

---

## 6) Detailed Algorithm (reference)

For each time \(t_k\) on the grid (see **§1c** for formulas):

1. **Select active events** overlapping the window \([t_k - w/2,\, t_k + w/2]\).
2. **Build PMFs**: pitch, duration, joint pitch×duration; onset and sounding densities.
3. **m1** from three normalized entropies (bits); if the window is silent, use **silence_intra_value**.
4. **m2** from Wasserstein distance to the previous window (or silence / first-sample rules).
5. **m3** from multi-scale densities (optional **partial scales**).
6. **Combine** \(H(t_k) = \mathrm{WGM}(m_1,m_2,m_3; w_1,w_2,w_3)\).

Silent windows use the configured **silence** constants for **m1/m2**; they are **not** forced to \(H=1\) unless those constants are 1.0.

---

## 6.1) Formal Mathematical Specification

The following subsection gives the underlying formulas, constants, logic sequences, and input–output relationships in standard mathematical notation. The system computes all quantities from the symbolic score and the configured parameters; no procedural code is implied beyond the order of operations.

### Variable and symbol dictionary

| Python / internal | Mathematical symbol | Description |
|-------------------|---------------------|-------------|
| `time_step` | $\Delta t$ | Time resolution (quarterLength); default 0.25 |
| `window_size` | $w$ | Half-length of each analysis window (quarterLength); default 4.0 |
| `sigma` | $\sigma$ | Scale parameter for inter-window stability; default 12.0 |
| `pitch_bin_step` | $\Delta p$ | Semitone width of pitch bins (absolute space); default 1.0 |
| `silence_intra_value` | $s_{\mathrm{intra}}$ | m1 value when the window has no notes; default 0.5 |
| `silence_transition_value` | $s_{\mathrm{trans}}$ | m2 value when exactly one of current/previous window is silent; default 0.5 |
| `allow_partial_scales` | (flag) | If true, m3 ignores missing scales; if false, m3 = 0 when any scale is silent |
| `end_time` | $T$ | Score duration (quarterLength); $\max\{\text{offset} + \text{duration}\}$ over all events |
| `time_axis` | $t_k$ | $t_k = k \cdot \Delta t$ for $k = 0, 1, \ldots$ with $t_k \le T$; grid of analysis times |
| `pitch_edges` | $b_0, b_1, \ldots, b_K$ | Pitch bin boundaries (semitone or pitch-class); derived from score or fixed for pitch_class |
| `pitch_centers` | $c_j$ | $c_j = (b_j + b_{j+1})/2$; bin centres for Wasserstein |
| `dur_edges` | $d_0, d_1, \ldots, d_M$ | Duration bin boundaries (quarterLength); default (0, 0.25, …, 16) |
| `pitch_pmf` | $P_p$ | Probability mass function over pitch bins in the window |
| `dur_pmf` | $P_d$ | Probability mass function over duration bins |
| `pitch_dur_pmf` | $P_{pd}$ | Joint PMF over pitch×duration bins (raveled to a vector) |
| `density_scalar` | $\rho_{\mathrm{onset}}$ | Number of onsets in the window divided by $w$ |
| `sounding_density` | $\rho_{\mathrm{snd}}$ | Total sounding time in the window divided by $w$ |
| `scales` | $s_1, s_2, s_3$ | Multi-scale factors; default (1, 2, 4) |
| `weight_m1`, `weight_m2`, `weight_m3` | $\omega_1,\omega_2,\omega_3$ | Non-negative; normalized to $w_i$ for WGM of $(m_1,m_2,m_3)$; default $1/3$ each |
| `weight_instrument` | $w_I$ | Timbral weight for instrument component; default 0.65 |
| `weight_register` | $w_R$ | Timbral weight for register component; default 0.35 |
| `family_bonus` | $\beta_F$ | Timbral value when one family only; default 0.65 |
| `register_ref_semitones` | $r_{\mathrm{ref}}$ | Reference span (semitones) for register component; default 3.0 |
| `z_threshold` | $z$ | Threshold in standard-deviation units for z-based segmentation; default 2.5 |
| `min_gap` | $g$ | Minimum index spacing between change points (z method); default 4 |
| `penalty` (PELT) | $\beta$ | Penalty per change point in PELT; default 0.05 |
| `min_size` (PELT) | $L$ | Minimum segment length in PELT; default 4 |
| $\epsilon$ | $10^{-9}$ | Numerical guard to avoid division by zero where used |

---

### Pitch and window conventions

- **Pitch value** (per note or chord tone):  
  - Absolute: $x = \mathrm{ps}$ (pitch in semitones, e.g. MIDI).  
  - Pitch class: $x = \mathrm{ps} \bmod 12 \in [0,12)$.
- **Pitch bin bounds** (initialisation):  
  - Pitch class: $b_j = -0.5 + j$ for $j = 0,\ldots,12$ (12 bins).  
  - Absolute: $b_0, \ldots, b_K$ span $[\min(\text{pitches})-2\Delta p,\; \max(\text{pitches})+2\Delta p]$ with step $\Delta p$; if the score has no notes, bounds default to $[21, 108]$ (MIDI range).
- **Window** centred at $t$ with half-length $w$: $I_t = [t - w/2,\, t + w/2]$.  
  An event $e$ with onset $o_e$ and duration $\ell_e$ is **active** in $I_t$ iff  
  $$o_e < t + \frac{w}{2} \quad \text{and} \quad o_e + \ell_e > t - \frac{w}{2}.$$

---

### Homogeneity H(t): feature extraction per window

For window centre $t$ and half-length $w$:

1. **Active set**  
   $\mathcal{A}_t = \{ e : e \text{ active in } I_t \}$. If $\mathcal{A}_t = \emptyset$, the window is **silent**; no PMFs are computed and the window is handled by the silence constants below.

2. **Pitch and duration samples**  
   From each note or chord tone in $\mathcal{A}_t$, collect pitch value $x$ (absolute or mod 12) and duration $\ell$; chords contribute one ($x$, $\ell$) per pitch. Build:
   - Pitch histogram over bins $[b_j, b_{j+1})$ → counts $n_j$; then  
     $$P_p(j) = \frac{n_j}{\sum_j n_j}$$  
     (if $\sum_j n_j = 0$, $P_p$ is zero).
   - Duration histogram over $[d_m, d_{m+1})$ → $P_d(m)$ analogously.
   - Joint 2D histogram (pitch bin × duration bin) → $P_{pd}(j,m)$, normalised to sum 1.

3. **Densities**  
   - Onset density: $\rho_{\mathrm{onset}} = |\{ e : o_e \in [t - w/2,\, t + w/2) \}| \,/\, w$.  
   - Sounding density:  
     $$\rho_{\mathrm{snd}} = \frac{1}{w} \sum_{e \in \mathcal{A}_t} \max\bigl(0,\, \min(o_e + \ell_e,\, t + w/2) - \max(o_e,\, t - w/2) \bigr).$$

---

### Homogeneity H(t): metric m1 (intra-window consistency)

- **Silent window:** the system assigns $m_1 = s_{\mathrm{intra}}$ (configurable constant).
- **Non-silent window:**  
  Entropy for a discrete PMF $P$ with support size $K$:  
  $$\mathcal{H}(P) = -\sum_{i : P(i) > 0} P(i) \log_2 P(i).$$  
  Maximum entropy for $K$ bins: $\mathcal{H}_{\max}(K) = \log_2 K$ (or 0 if $K \le 1$).  
  Define normalized concentration:
  - $m_d = 1 - \dfrac{\mathcal{H}(P_d)}{\mathcal{H}_{\max}(|P_d|)}$ (duration), with $m_d = 1$ if $\mathcal{H}_{\max} = 0$.
  - $m_p = 1 - \dfrac{\mathcal{H}(P_p)}{\mathcal{H}_{\max}(|P_p|)}$ (pitch).
  - $m_{pd} = 1 - \dfrac{\mathcal{H}(P_{pd})}{\mathcal{H}_{\max}(|P_{pd}|)}$ (joint), with $P_{pd}$ raveled to a vector.
  Then  
  $$m_1 = \mathrm{clip}\left( \frac{m_d + m_p + m_{pd}}{3},\; 0,\; 1 \right).$$

---

### Homogeneity H(t): metric m2 (inter-window stability)

Let $P_{\mathrm{curr}}$ and $P_{\mathrm{prev}}$ be the pitch PMFs of the current and previous window (over the same bin centres $c_j$).

- If both windows are silent: $m_2 = 1$.
- If exactly one is silent: $m_2 = s_{\mathrm{trans}}$.
- If both have no positive mass: $m_2 = 0$.
- Otherwise: let $W$ denote the **1-Wasserstein distance** (earth mover’s distance) between the two discrete distributions with supports $\{c_j\}$ and weights $P_{\mathrm{curr}}(j)$, $P_{\mathrm{prev}}(j)$. Then  
  $$m_2 = \exp\left( -\frac{W}{\max(\sigma,\, \epsilon)} \right).$$

---

### Homogeneity H(t): metric m3 (multi-scale consistency)

- **Scale factors:** $s_1 = 1$, $s_2 = 2$, $s_3 = 4$ (default). For each scale $\ell \in \{1,2,3\}$, the system computes features for the window centred at $t$ with half-length $w \cdot s_\ell$ (same $t$, larger window).
- If all three scale-windows are silent: $m_3 = 1$.
- If any scale-window is silent and partial scales are not allowed: $m_3 = 0$.
- If any scale-window is silent and partial scales are allowed: drop silent scales; if at most one scale remains, $m_3 = 1$.
- Otherwise, define **sustained** as: for every retained scale $f$, $\rho_{\mathrm{onset}}^{(f)} < 0.4$ and $\rho_{\mathrm{snd}}^{(f)} > 0.3$.  
  - If sustained: $d_\ell = \bigl| \rho_{\mathrm{snd}}^{(\ell)} - \rho_{\mathrm{snd}}^{(\ell+1)} \bigr|$.  
  - If not sustained: $d_\ell = \bigl| \rho_{\mathrm{onset}}^{(\ell)} - \rho_{\mathrm{onset}}^{(\ell+1)} \bigr|$.  
  Then  
  $$m_3 = \frac{1}{1 + \overline{d}},\quad \overline{d} = \frac{1}{L-1}\sum_{\ell=1}^{L-1} d_\ell,$$  
  where $L$ is the number of retained scale-features. If there are no consecutive pairs, $m_3 = 1$.

---

### Homogeneity H(t): output curve

For each $t_k$, with $m_2 := 1$ when there is no previous window:

$$H(t_k) = \exp\left( \sum_{i=1}^{3} w_i \ln\max(m_i,\varepsilon)\right)$$

with normalized weights $(w_1,w_2,w_3)$ (§1c.2). Equal weights give $(m_1 m_2 m_3)^{1/3}$.

**Single-aggregate mode:** evaluate at $t = T/2$; $m_2 := 1$; combine $(m_1, 1, m_3)$ with the same weights; plot is constant over $[0,T]$.

---

### Segmentation: z-threshold method

- **Input:** homogeneity curve $H_0, H_1, \ldots, H_{n-1}$ (length $n \ge 3$).
- **Difference series:** $d_j = |H_{j+1} - H_j|$ for $j = 0, \ldots, n-2$.
- **Statistics:** $\mu = \frac{1}{n-1}\sum_j d_j$, $\varsigma = \sqrt{\frac{1}{n-1}\sum_j (d_j - \mu)^2}$ (sample mean and standard deviation).
- If $\varsigma \le \epsilon$, the procedure returns no change points.
- **Peak indices:** $\mathcal{P} = \{ j+1 : d_j > \mu + z \cdot \varsigma \}$ (indices in $\{1,\ldots,n-1\}$).
- **Minimum spacing:** from $\mathcal{P}$, retain only indices that are at least $g$ apart (first acceptable index is kept; subsequent ones are kept only if their distance to the last retained is $\ge g$). The resulting set is the **change point indices** (in index space). Change **times** are $t_{c}$ for each change point index $c$.

---

### Segmentation: PELT (Pruned Exact Linear Time)

- **Input:** homogeneity curve $H_0, \ldots, H_{n-1}$; penalty $\beta > 0$; minimum segment length $L$.
- **Cost of segment $[i, j)$ (sum of squared errors about mean):**  
  Let $n_{ij} = j - i$, $\bar{H}_{ij} = \frac{1}{n_{ij}}\sum_{k=i}^{j-1} H_k$, then  
  $$C(i,j) = \sum_{k=i}^{j-1} (H_k - \bar{H}_{ij})^2 = \sum_{k=i}^{j-1} H_k^2 - n_{ij} \bar{H}_{ij}^2.$$  
  Prefix sums allow $C(i,j)$ to be computed in $O(1)$ from $\sum_{k=i}^{j-1} H_k$ and $\sum_{k=i}^{j-1} H_k^2$.
- **Dynamic programme:** $F(t)$ = minimum total cost to segment $H_0, \ldots, H_{t-1}$ with changes allowed only at indices $\ge L$ apart, plus $\beta$ per change. Boundary: $F(0) = -\beta$, and for $t \ge L$,  
  $$F(t) = \min_{s \in \mathcal{R},\; t-s \ge L} \bigl\{ F(s) + C(s,t) + \beta \bigr\},$$  
  with pruning so that only candidates satisfying the PELT inequality remain in $\mathcal{R}$. The backtracking pointers yield the set of change indices; indices $0$ and $n$ are excluded from the returned list. If $n < 2L$, the procedure returns no change points.

---

### Legacy H_timbral (diagnostic) — \(H_{\mathrm{timbral}}(t)\) formula

The scalar below is **legacy H_timbral** (backward-compatible diagnostic; **not** acoustically validated fusion). **Per-note events:** each note (or chord tone) is assigned an instrument and a family from the score and the taxonomy. An event is a tuple (offset, end, pitches, instrument, family).
- **Window:** same as above: $I_t = [t - w/2,\, t + w/2]$. Collect all events overlapping $I_t$; from these, form the set of instruments $\mathcal{I}_t$, the set of families $\mathcal{F}_t$, and the multiset of pitch values (in semitones).
- **Silent window:** $H_{\mathrm{timbral}}(t) = 0.5$ (neutral).
- **Non-silent:**  
  - $N_I = |\mathcal{I}_t|$, $N_F = |\mathcal{F}_t|$.  
  - Pitch span: $S = \max(\text{pitches}) - \min(\text{pitches})$ (semitones); if a single pitch, $S = 0$.  
  - **Instrument component:**  
    $$C_I = \begin{cases} 1 & N_I = 1 \\ \beta_F & N_F = 1 \text{ and } N_I > 1 \\ \dfrac{1}{1 + (N_I - 1)} & \text{otherwise} \end{cases}$$  
  - **Register component:**  
    $$C_R = \frac{1}{1 + S / \max(r_{\mathrm{ref}}, 0.1)}$$  
  - **Output:**  
    $$H_{\mathrm{timbral}}(t) = \mathrm{clip}\bigl( w_I \, C_I + w_R \, C_R,\; 0,\; 1 \bigr).$$

---

### Combined output (aligned homogeneity, legacy timbral, cluster, orch, fusion)

- **Inputs:** homogeneity result (including $m_1,m_2,m_3$ when computed), timbral (**legacy H_timbral**) result, cluster result, orchestration-symbolic result, and fusion-heuristic result on possibly different grids.
- **Alignment:** homogeneity time grid is reference; linearly interpolate $H_{\mathrm{timbral}}$, $H_{\mathrm{cluster}}$, $H_{\mathrm{orch}}$, and $H_{\mathrm{fusion}}$ (and fusion confidence fields) onto it.
- **Primary CSV columns:** see **§1c.12** (`t_quarterLength`, `H`, optional `m1–m3`, `H_timbral`, optional `H_cluster`, `H_orchestration_symbolic`, optional `dominant_timbral_state`). **Fusion** scalars and **confidence** appear in **`combined_series`** (JSON) and in **cluster/orchestration/fusion diagnostics CSV**, not in the minimal `combined_csv` row unless you regenerate exports from those structures downstream.

---

### Sensitivity (window-size robustness)

For window-size factors $f \in \{0.75, 1, 1.25\}$, the system computes the homogeneity curve with window half-length $w \cdot f$. If the resulting time grid differs from the reference grid, $H$ is interpolated onto the reference grid. Then the **Pearson correlation** between the reference $H$ and the rescaled-window $H$ is computed; the procedure also reports mean and standard deviation of the rescaled curve. This yields a mapping: window size multiplier → (correlation, mean, std). No change to the main homogeneity formula; this is a post-hoc diagnostic.

---

### Validation mapping (change-point checks)

- **Input:** predicted change-point indices or times $\{c_p\}$, expected change-point times $\{e_q\}$, tolerance $\tau$ (in the same units as times).
- **Matching:** for each expected $e_q$, if there exists a predicted $c_p$ with $|c_p - e_q| \le \tau$, that prediction is matched to $e_q$ (each prediction used at most once).
- **Precision:** $P = \dfrac{\text{number of matched predictions}}{\max(|\{c_p\}|, 1)}$.  
- **Recall:** $R = \dfrac{\text{number of matched expectations}}{\max(|\{e_q\}|, 1)}$.  
  There is no transformation matrix; the relationship is set membership with a distance threshold $\tau$.

---

### Order of operations (homogeneity pipeline)

1. Parse score; build flat list of note/chord events and $T$.
2. Compute time grid $\{t_k\}$ from $\Delta t$ and $T$.
3. Compute pitch and duration bin boundaries from score (or defaults) and $\Delta p$ / duration edges.
4. For $k = 0, 1, \ldots$ (each $t_k$):
   - Determine active set $\mathcal{A}_{t_k}$; if empty, apply silence rules for $m_1,m_2$ and scale logic for $m_3$.
   - Else: extract PMFs and densities for window at $t_k$.
   - Compute $m_1$, $m_2$ (Wasserstein vs previous, or first-sample / silence), $m_3$.
   - $H(t_k) = \mathrm{WGM}(m_1,m_2,m_3; w_1,w_2,w_3)$.
5. Optionally run z-threshold or PELT segmentation on $\{H(t_k)\}$.
6. **Single-aggregate:** one evaluation at $t=T/2$, $m_2=1$, same WGM; optional sensitivity sweep over window size.

---

### Order of operations (timbral pipeline)

1. Parse score; for each part, resolve instrument and family; build list of events (offset, end, pitches, instrument, family).
2. Compute time grid $\{t_k\}$ from $\Delta t$ and $T$.
3. For each $t_k$, determine events overlapping $I_{t_k}$; extract $\mathcal{I}_t$, $\mathcal{F}_t$, and pitch set; compute $N_I$, $N_F$, $S$, then $C_I$, $C_R$, and $H_{\mathrm{timbral}}(t_k) = \mathrm{clip}(w_I C_I + w_R C_R, 0, 1)$ (or 0.5 if silent).

---

## 7) Pitch Space Options

### `absolute`
- Uses absolute pitch (MIDI‑like values).
- Better for **register‑dependent** texture changes.
- Example: octave shifts reduce homogeneity.

### `pitch_class`
- Uses pitch class (mod 12).
- Better for **harmonic‑class** comparisons.
- Example: a C‑major triad in different octaves is treated as similar.

---

## 8) Parameter Guidance

### Time step
- Smaller = more detail (but more computation).
- Use **0.1–0.25** for most scores.

### Window size
- Short = sensitive to local changes.  
- Long = smoother global behavior.  
- Use **1.0–2.0** for chord‑level analysis.

### Sigma (inter‑window stability)
- **Low sigma** → sensitive to small changes.
- **High sigma** → tolerant of changes.
- Use **2.0–4.0** as a start.

### Pitch bin step
- Smaller = more resolution (microtonal detail).  
- Larger = smoother/less sensitive.  
- For pitch‑class mode, bins are always 12 classes.

### Silence intra value (m1)
- Controls how silence is treated inside a window.
- **0.5** is neutral; **1.0** treats silence as maximally homogeneous.

### Silence transition value (m2)
- Controls transitions between sound and silence.
- **0.5** prevents artificial drops to 0 when a single window is silent.

### Allow partial scales (m3)
- If **True**, m3 ignores missing scales instead of collapsing to 0.
- Recommended for sparse textures or frequent rests.

---

## 9) Example Workflows

### Example A — Homogeneous arpeggio
**Goal:** detect stable texture in a repeated arpeggio.

Recommended:
- Time step: **0.1**
- Window size: **1.0**
- Sigma: **3.0**
- Pitch space: **absolute**
- Silence intra value: **0.5**
- Silence transition value: **0.5**
- Allow partial scales: **True**

Expected:
`H(t)` stays near **0.7–0.9**, with small dips at structural changes.

### Example B — Sudden texture change
**Goal:** detect a switch from sparse to dense writing.

Recommended:
- Time step: **0.1**
- Window size: **0.75**
- Sigma: **2.0**
- Pitch space: **absolute**
- Silence intra value: **0.5**
- Silence transition value: **0.5**
- Allow partial scales: **True**

Expected:
sharp drop in `H(t)` around the change, plus a large slope in the segmentation view.

### Example C — Harmonic similarity across registers
**Goal:** treat octave shifts as equivalent.

Recommended:
- Time step: **0.2**
- Window size: **1.5**
- Sigma: **3.0**
- Pitch space: **pitch_class**
- Silence intra value: **0.5**
- Silence transition value: **0.5**
- Allow partial scales: **True**

Expected:
`H(t)` remains smoother even when the register changes.

---

## 9.5 Timbral (instrumental) homogeneity H_timbral(t)

A **second, complementary tool** in the same app measures **H_timbral**: **symbolic timbral-instrumental / orchestration-register homogeneity** (see **§1d**). It is **not** acoustic timbre extraction.

### What H_timbral(t) means

- **1.0** — One canonical **instrument** only (e.g. all flutes), narrow **sounding** register (e.g. within a minor third), and—where modelled—**aligned** technique states within the window.  
- **~0.65** — Same **family** (e.g. oboes + cor anglais, or several clarinets), but not the same instrument; register still matters.  
- **Lower** — Several instruments from different families, wide register, and/or **mixed** technique states that split overlap mass.

So: **same instrument** > **same family** > **mixed families**. A **narrow register** (small pitch span in semitones) increases H_timbral further.

**Homogeneity vs identity:** Uniform **four horns open** and uniform **four horns stopped** can both produce **high** H_timbral; they differ in **`technique_state_id`** and **`timbral_state_distribution`**, not necessarily in the headline scalar. **Mixed** open/stopped in one window lowers homogeneity (see **§1c.8**).

### Formula

For each window, the analyser collects every sounding note and its **instrument** (from the score part). Instruments are mapped to **families** (e.g. strings, flutes, oboes, clarinets, bassoons, saxophones, brass, keyboard, percussion, voice) via the built‑in taxonomy.

- **Instrument component:**  
  - 1 instrument only → 1.0  
  - 1 family only (several instruments) → **family_bonus** (default 0.65)  
  - Several families → 1 / (1 + (number of instruments − 1))
- **Register component:** 1 / (1 + span_semitones / ref_span), with **ref_span** default 3 (minor 3rd). Span is computed from **sounding** pitches when the parser supplies transposition; unpitched percussion uses the register rules in code (see `docs/H_TIMBRAL_SCORE_REPRESENTATION.md`).
- **Baseline H_timbral** = **weight_instrument** × instrument_component + **weight_register** × register_component  
  Default weights: 0.65 and 0.35. The shipped curve is this baseline **plus** family refinements, optional technique context, and the small verified cross-family layer (**§1c.8**).

Silent windows get H_timbral = 0.5 (neutral).

### Families (taxonomy)

Instrument names from the score (MusicXML or MIDI) are normalised and matched to **canonical instrument** and **family**. The same file is used for both **Homogeneity H(t)** and **Timbral homogeneity**; upload once and run either (or both) from the tabs.

### Full instrument and family list

The following list is the **complete taxonomy** used for timbral homogeneity. Score part names (e.g. "Violin 1", "Bass Clarinet") are matched to a **canonical instrument** and **family**; instruments in the same family contribute to higher H_timbral when they sound together.

| Family | Instruments (canonical / recognised names) |
|--------|--------------------------------------------|
| **strings** | violin, viola, cello, double bass, harp, guitar (acoustic/electric/classical/bass), lute, theorbo, mandolin, mandola, banjo, ukulele, zither, dulcimer, viola da gamba, viol, baryton, cittern, vihuela, sitar, koto, shamisen, erhu, guzheng, pipa |
| **flutes** | flute, piccolo, alto flute, bass flute, traverso, fife, pan flute, shakuhachi, dizi, bansuri, tin whistle, ocarina |
| **recorders** | recorder, sopranino/soprano/alto/tenor/bass recorder, blockflöte |
| **oboes** | oboe, oboe d'amore, oboe da caccia, cor anglais (english horn), bass oboe, musette, shawm, duduk, suona |
| **clarinets** | clarinet (soprano, B♭, A, E♭), bass clarinet, alto clarinet, contrabass clarinet, basset horn |
| **bassoons** | bassoon, contrabassoon, fagott, dulcian, racket, crumhorn |
| **saxophones** | sopranino/soprano/alto/tenor/baritone/bass saxophone, sax |
| **brass** | trumpet, horn (French / valve horn), natural horn, bass trumpet, trombone (alto/tenor/bass/soprano), tuba, bass tuba, cornet (**part-name `cornetto`** is mapped to **cornet** as a **project default** for PT/IT band naming), flugelhorn, euphonium, baritone horn, cimbasso, Wagner tuba, natural trumpet, serpent, sackbut, **cornett** (historical, distinct from cornet), mellophone, sousaphone, ophicleide, bugle, alphorn, didgeridoo |
| **keyboard** | piano (grand, upright, fortepiano, electric), organ, pipe organ, harpsichord, clavichord, celesta, accordion, harmonium, bandoneon, concertina, harmonica, synthesizer, clavinet, virginal, spinet |
| **percussion** | timpani, glockenspiel, xylophone, marimba, vibraphone, crotales, tubular bells (chimes), steelpan, snare drum, bass drum, tom-tom, tambourine, triangle, cymbal, gong, tam-tam, castanets, claves, cowbell, wood block, temple block, bongos, congas, djembe, tabla, cajón, rototom, wind chimes, drum set/kit, percussion |
| **voice** | soprano, mezzo-soprano, alto, contralto, tenor, baritone, bass (voice), countertenor, voice, vocals, choir, chorus |

**Note:** Names are matched **case-insensitively**, with **accent folding** and many **abbreviations** and **Portuguese** (and other) aliases (canonical table **`_CANONICAL_INSTRUMENTS`**, flattened to **`_INSTRUMENT_MAP`** in `instrument_taxonomy.py`). Unlisted names go to family **other**. Duplicate normalised aliases are logged at import via **`get_alias_collision_log()`**; the shipped tests expect that log to be empty unless an allow-list is documented. Orchestration conventions that are **policy** (bare `bass`, bare voice-role words, `cornetto`, short-token matching) are summarised in **§1c.8** above and in test comments.

### Configurable parameters (Timbral tab)

In the **Timbral homogeneity** tab you can optionally set:

- **Weight instrument** (default 0.65)  
- **Weight register** (default 0.35)  
- **Family bonus** (default 0.65) — value when all instruments are in the same family but not the same instrument  
- **Register ref. semitones** (default 3) — reference span for the register bonus  

Leave fields empty to use defaults.

### Combined export (Combined tab)

The **Combined** tab runs **H**, legacy **H_timbral**, **H_cluster**, **H_orchestration_symbolic**, **H_notated_fusion_potential**, and **H_fusion_acoustic_heuristic** and produces a **combined CSV** as in **§1c.12** (including optional **`dominant_timbral_state`**), plus **combined JSON** (`kind`: `combined_homogeneity_timbral`; `schema_version` **1.8**) with nested payloads and the same CSV text under **`combined_csv`**.

---

## 9.6 Register uniformity U(t)

A **third tool** in the same app measures **register uniformity**: how evenly pitches are **distributed within a user-defined pitch range**. The user **must** set **lower** and **upper** register limits (e.g. A1 and E7); only notes within that range are considered.

### What U(t) means

- **Low U (≈ 0):** Notes in the window are **clustered** in one part of the register (e.g. all in middle register, or all in top register). One or few semitone bins are filled; entropy is low.
- **High U (≈ 1):** Notes are **spread** across the range (e.g. a large chord from A1 to E7). Many bins are filled more evenly; entropy is high (normalized to [0, 1]).

So: **cluster in one section** → low uniformity; **spread across the range** → high uniformity. The **mutual distance** between components is reflected because even spread across bins implies larger intervals.

### Formula

- **Input:** Score path, time step, window size, **register_low**, **register_high** (note names like `A1`, `E7` or MIDI numbers). The range is converted to MIDI pitch space (e.g. A1 → 21, E7 → 88).
- **Per window:** Collect all pitches (from notes/chords) that fall in the window and **within [register_low, register_high]**.
- **Binning:** The range is divided into **semitone bins**. Count how many pitches fall in each bin.
- **Entropy:** PMF over bins → **natural-log** Shannon entropy \(\mathcal{H} = -\sum_i p_i \ln p_i\). Maximum \(\mathcal{H}_{\max} = \ln K\) for \(K\) bins.
- **Output:** \(U = \mathcal{H} / \mathcal{H}_{\max}\), clamped to [0, 1]. Empty window → **NaN**; single pitch → **0**.

### When to use U(t)

- Study **registral distribution**: e.g. "passage stays in middle register" (low U) vs "chord spread from bass to treble" (high U).
- Compare **texture spread** with H(t) and H_timbral(t).
- Use the **same score** as for the other tabs; set the register limits to match the piece (e.g. full keyboard A0–C8, or a vocal range).

### API (Register uniformity)

From Python, without the UI:

```python
from homogeneity_analyser.services import run_register_uniformity_analysis

out = run_register_uniformity_analysis("/path/to/score.xml", {
    "time_step": 0.25,
    "window_size": 4.0,
    "register_low": "A1",   # or 21
    "register_high": "E7",  # or 88
}, progress_callback=None)  # optional: (frac, desc) -> None, frac in [0, 1]
if out.get("error"):
    print(out["error"])
else:
    results = out["results"]  # {"t": [...], "U": [...]}
    summary = out["summary"]
```

Optional **progress_callback(frac, desc)** is supported for progress reporting (e.g. in UIs). The same optional callback is available for `run_homogeneity_analysis` and `run_timbral_analysis`.

To use the analyzer class directly: `from homogeneity_analyser.analyzers import RegisterUniformityAnalyzer, note_name_to_midi_ps`. Analyzer methods `analyze_score` / `analyze_timbral` accept an optional `progress_callback` for incremental progress.

---

### When to use H_timbral (Timbral tab)

- Study **orchestration**: passages with one instrument or one family vs mixed colours.  
- Compare **homogeneity of pitch/duration** (H) with **symbolic orchestration homogeneity** (H_timbral).  
- Best with **MusicXML** (instrument names per part); MIDI often has no or generic instrument names.

---

## 10) Outputs

When you run an analysis (Homogeneity, Timbral, or Register uniformity), the UI shows a **progress bar** and short status text (e.g. “A carregar partitura…”, “Homogeneity H(t)”, “Concluído”) until the run finishes.

The UI provides:

- **H(t) plot** — homogeneity over time (or a horizontal line in Single aggregate mode)
- **Homogeneity gauge (static chord)** — donut chart with one H value when Single aggregate mode is on; otherwise a placeholder
- **Summary** — windows count, duration, H min/mean/max, parameters, change points and times, sensitivity (if not single aggregate)
- **Download CSV** — `t_quarterLength`, `H`, and **`m1,m2,m3`** (metric breakdown) per row when available
- **Download plot image** — PNG when using matplotlib, or PNG from Plotly via Kaleido when the interactive stack is compatible; otherwise a standalone **HTML** plot file
- **Download full results (JSON)** — `schema_version` **1.8**; includes parameters, series, summary, change points/times, sensitivity (homogeneity), `model_version`, `metric_kind`, `not_audio_analysis`, and optional score metadata (`json_export.py`)

**Legacy H_timbral tab:** legacy H_timbral(t) plot, summary (with legacy **WARNING** line), CSV (t, H_timbral), plot file, JSON (`legacy_warning`, `interpretation_status`, `timbral_model_mode`, `timbral_homogeneity_note`, `timbral_state_series`, optional `h_timbral_effective_parameters`; diagnostic rows may include `evidence_status`).

**Register uniformity tab:** U(t) plot, summary (including register range), CSV (t_quarterLength, U), plot file, JSON. Lower and upper register limits are required.

**Combined tab:** Plots **H** → **H_cluster** → **H_orchestration_symbolic** → **H_notated_fusion_potential** → **H_fusion** → **legacy H_timbral**; optional **per-plot** downloads; combined CSV (see **§1c.12**); diagnostics CSV; combined JSON (`kind`: **`combined_homogeneity_timbral`**, `schema_version` **1.8**) with **`interpretation_guidance`**, nested documents, **`combined_csv`** text, and **`source_keys`** when fusion is embedded.

Typical summary values:
- Mean H, Min / Max H
- Change points and change times (when not in Single aggregate mode)

---

## 11) Validation

Run:
```bash
python validation/run_validation.py
```

Includes:
- A synthetic series with known change points
- A MusicXML fixture with a known density shift

Use this to sanity‑check parameter changes.

---

## 12) Interpretation Notes

- **Test assumption labels** used in module / test docstrings (**confirmed musical convention**, **project-specific convention**, **ambiguous but intentionally accepted**, **provisional / needs corpus validation**) are defined in **§1d**; they describe **test and documentation epistemology**, not legal or acoustic certification.
- **High H(t)** can mean either stability or silence (by design).
- **Low H(t)** can reflect:
  - pitch instability,
  - duration variety,
  - density changes,
  - or abrupt transitions.
- **m2** is the most sensitive to **sudden changes**.
- **m1** is sensitive to **distribution spread** inside a window.
- If your score has many rests, adjust **silence intra/transition values** to avoid bias.

---

## 13) Common Pitfalls

- **Too small window size** → noisy curve.
- **Too large window size** → smooth curve that hides short events.
- **Sigma too small** → frequent dips even with minor changes.
- **Pitch class mode** can hide register‑based texture changes.

---

## 14) Package layout and module map

Installable package under **`src/homogeneity_analyser/`**. From the repository root: `pip install -r requirements.txt` (editable install `-e ".[dev]"` including pytest, Ruff, mypy, coverage).

- **`analyzers/`**  
  Core analysis only (no Gradio). `homogeneity.py` (`HomogeneityAnalyzer`), `timbral.py` (`TimbralHomogeneityAnalyzer`), `register.py` (`RegisterUniformityAnalyzer`); shared helpers in `common.py`, `parsing_bridge.py`; timbral helpers **`timbral_sounding_pitch.py`**, **`notation_context.py`**, **`timbre_cross_relations.py`**, and family pairwise modules (`string_pairwise_timbral.py`, `brass_pairwise_timbral.py`, `flute_pairwise_timbral.py`, `clarinet_pairwise_timbral.py`, `double_reed_pairwise_timbral.py`, `saxophone_pairwise_timbral.py`, `percussion_pairwise_timbral.py`). Each analyzer’s main method (`analyze_score` or `analyze_timbral`) accepts an optional **progress_callback(frac, desc)**. Parsing forces MusicXML for `.xml`/`.musicxml`/`.mxl`. Public imports: `from homogeneity_analyser.analyzers import HomogeneityAnalyzer, ...`.

- **`services/`**  
  `analysis_service.py`: `run_homogeneity_analysis()`, `run_timbral_analysis()`, `run_register_uniformity_analysis()`, `run_both_and_combine()`; also `result_assembly.py`, **`json_export.py`** (structured JSON), `window_pipeline.py`, `constants.py`. Public imports: `from homogeneity_analyser.services import run_homogeneity_analysis, ...`.

- **`ui/`**  
  Gradio app (`gradio_app.py`), callbacks (`callbacks.py` — includes **`run_loaded_xml_inspection`**, **`_rows_to_dataframe`** for audit tables, **`_write_temp_csv`** for audit CSV paths), validation (`validation.py` — **`validate_uploaded_score`**, **`gradio_upload_to_path`**, **`parse_ui_float`** / **`coerce_float`**), components. Run handlers use **Gradio Progress** (`gr.Progress()`).

- **`taxonomy/`**  
  `instrument_taxonomy.py`: instrument → family and canonical name; `get_timbral_config()`, `set_timbral_config()`.

- **`io/`**, **`models/`**, **`plotting/`**, **`utils/`**  
  Score load/validation, typed models, plotting helpers, export/cache paths (`output_paths.py`).

- **`__main__.py`**  
  Entry point for `python -m homogeneity_analyser`. Console script **`homogeneity-analyser`** is defined in `pyproject.toml`.

- **`validation/`**  
  Fixtures and `run_validation.py`. After install, from repo root: `python validation/run_validation.py`.

- **`tests/`**  
  e.g. `test_analyzers.py`, `test_taxonomy.py`, `test_analysis_service.py`. Run: `pytest tests/ -v`.

- **`docs/`**  
  `ARCHITECTURE.md`, `METRIC_CODE_MAP.md`, `QUICK_REFERENCE_SYMBOLIC_NAMES.md` (canonical instruments + technique/articulation IDs), `H_TIMBRAL_SCORE_REPRESENTATION.md`, `H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md`, `model_audit/H_TIMBRAL_ASSUMPTIONS_AUDIT.md` (hard-coded timbral constants and policy tags), `model_audit/TIMBRAL_MODEL_REVISION_SUMMARY.md` (metric split + JSON 1.5 + compatibility), and family-specific H_timbral notes (`H_TIMBRAL_STRINGS.md`, `H_TIMBRAL_BRASS.md`, …).

- **`requirements.txt`**  
  Points at `-e ".[dev]"` (runtime + dev dependencies).

---

## 15) Extending the Model

Common extensions:
- Add a **fourth metric** (e.g., harmonic‑set similarity).
- Replace the geometric mean with a weighted fuzzy AND.
- Compute **consensus curves** from multiple parameter sets.

---

## 16) Minimal Repro Example (CLI)

Run the app:
```bash
python -m homogeneity_analyser
```

Then:
1. Upload a small MusicXML file.
2. Set `Window size = 1.0`, `Time step = 0.1`, `Sigma = 3.0`.
3. Compare `absolute` vs `pitch_class`.

You should see different levels of stability based on register handling.

---

## 17) Development and API overview

### Running tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Tests cover: analyzers (extract_features, metrics, segmentación, Register uniformity and `note_name_to_midi_ps`), instrument taxonomy, the service layer (`run_homogeneity_analysis`, `run_timbral_analysis`, `run_register_uniformity_analysis`, `run_both_and_combine`), **JSON export** (`test_json_export.py`), **UI validation and audit plumbing** (`test_ui_validation.py`, `test_ui_audit_csv.py`, `test_parse_ui_float.py`), and Gradio wiring. Edge cases include empty score (no notes), single-note score, invalid register bounds, and Register uniformity with note-name bounds (e.g. C4–C5).

### Validation (change-point fixtures)

```bash
python validation/run_validation.py
```

### Using the API without the UI

From Python you can call the **service layer** with a score path and parameter dict; no Gradio required:

```python
from homogeneity_analyser.services import run_homogeneity_analysis, run_timbral_analysis

out = run_homogeneity_analysis("/path/to/score.xml", {"window_size": 4.0, "sigma": 12.0})
if out.get("error"):
    print(out["error"])
else:
    results = out["results"]  # {"t": [...], "H": [...]}
    summary = out["summary"]
```

Same pattern for `run_timbral_analysis(score_path, params)`, `run_register_uniformity_analysis(score_path, params)` (with `register_low` and `register_high` in params), and `run_both_and_combine(score_path, ...)`. All three run functions accept an optional **progress_callback(frac, desc)** (e.g. for UIs) with `frac` in [0, 1] and `desc` a short status string.

To persist the same JSON shape the UI downloads:

```python
from pathlib import Path

from homogeneity_analyser.services import run_homogeneity_analysis
from homogeneity_analyser.services.json_export import (
    build_homogeneity_export,
    write_json_export,
)

out = run_homogeneity_analysis("/path/to/score.xml", {"window_size": 4.0, "sigma": 12.0})
doc = build_homogeneity_export("/path/to/score.xml", {"window_size": 4.0, "sigma": 12.0}, out)
write_json_export(Path("/tmp/homogeneity_export.json"), doc)
```

Use `build_timbral_export`, `build_register_export`, or `build_combined_export` for the other tabs.

To use the **analyzer classes** directly (e.g. for custom pipelines or segmentation), import from the analyzers package:  
`from homogeneity_analyser.analyzers import HomogeneityAnalyzer, TimbralHomogeneityAnalyzer, RegisterUniformityAnalyzer, note_name_to_midi_ps`.

### CI

If the project is in a Git repository, `.github/workflows/tests.yml` on push/PR to `main` or `master` runs **Ruff** (lint + format check), **mypy** on `src/homogeneity_analyser`, **pytest** with coverage (fail-under 60%), and **`python validation/run_validation.py`** after `pip install -e ".[dev]"`.

