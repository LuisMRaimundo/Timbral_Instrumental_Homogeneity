# Technical Manual — Symbolic Timbral–Instrumental Homogeneity Analyser

This manual describes the **score-centred** pipeline: **$H_{\mathrm{TI},\mathrm{core}}(t)$** (structural symbolic homogeneity) and **notated dynamic conditioning** (interpretive layer). The headline export series **H_TI(t)** is numerically identical to **$H_{\mathrm{TI},\mathrm{core}}(t)$** (column **`H_TI`** / **`H_TI_core`**). Inputs are **MusicXML / MXL / MIDI** semantics only. The software does **not** load audio (**not measured audio**), perform **FFT** on recordings, estimate **SPL**, or claim **measured acoustic or perceptual timbral fusion**.

**Implementation contract (read before citing results):**

- **H_TI_core** — **symbolic**, **notation-derived** only; same event pipeline as timbral / symbolic inspection.
- **Dynamics** — parsed to an **ordinal** ladder and overlap distributions; **not** SPL or measured loudness.
- **Optional timbral affinity** — **off by default**; when enabled, literature-governed **symbolic** similarity weights that **replace only the instrument axis** in a relieved **H_TI** variant; **not** acoustic timbre vectors or listening tests.
- **Optional H_TA_acoustic_proxy** — **off by default**; event-level pairwise **timbral-acoustic affinity** kernel (`timbral_acoustic_affinity`); **orthogonal** to **H_TI_core** Herfindahl concentration; **not** measured audio (see **`docs/H_TA_ACOUSTIC_PROXY.md`**).
- **Harmonic pitch** — **conservative** default: bowed-string **diamond/square** without MusicXML roles → **harmonic_candidate** / **unresolved**; **artificial** sounding inferred only under **`infer_common_artificial`** with explicit artificial markup and **interval-table** match; unresolved harmonic pitch is **audited and warned**, not silently overwritten.
- **MusicXML / MIDI** — output quality depends on the **exporter** and format richness; gaps are surfaced as **unknown** / warnings where possible.

---

## 1) Purpose and methodological scope

The analyser estimates how **uniform** orchestration and playing-state evidence appear **inside sliding time windows** on a discrete **symbolic notation** timeline (MusicXML / MIDI semantics). **Homogeneity** here means *concentration of overlap mass* on instruments, instrumental subfamilies (taxonomy `family` rows), technique ids, and compact **sounding-pitch** register — not “fusion” measured in a hall.

**H_TI_core** is computed only from notation-derived events. **Written dynamics** enter a **separate** conditioning layer: they **do not** rescale **H_TI_core**; they qualify how analysts might read homogeneity alongside **ordinal** dynamic evidence (**not** acoustic loudness).

---

## Tutorial — How to use the analyser responsibly

This tutorial is for **regular users** who want reliable results without reading the full formal specification first. It sits alongside the rest of the manual: recommendations here follow the same **symbolic, score-derived** scope as the implementation (no audio analysis, no measured fusion, no SPL).

### T.1 What the analyser is for

The software **reads symbolic scores** (MusicXML / MXL, or MIDI as a fallback). In each sliding time window it estimates how **concentrated** the active notation is on:

- **Which instruments** are playing (canonical names after taxonomy normalisation),
- **Which instrumental subfamilies** (taxonomy `family` rows such as strings or clarinets),
- **Which technique buckets** (when the file encodes them),
- **How compact the sounding register is** (from notated / inferred **sounding MIDI**, not from a microphone).

It **does not listen** to sound files, **does not perform FFT** or spectral analysis of recordings, and **does not measure acoustic fusion** or validate perception. It helps you **compare notated orchestral textures** in a disciplined way—provided the score encoding is trustworthy.

**Short intuition (not a guarantee of any particular number):** a passage scored for **four clarinets in a narrow register** will *tend toward* **higher** **H_TI_core** than a **large tutti** with flutes, oboes, clarinets, brass, strings, and **wide** chord spacing, which will *tend toward* **lower** **H_TI_core** because more categories and wider register spread dilute concentration. Always confirm with **Symbolic inspection** and your chosen pitch mode.

### T.2 Before you begin

You need:

1. A **MusicXML** or **MXL** file when possible—**export quality matters** (instrument names, techniques, dynamics, harmonics).
2. **MIDI** only as a **fallback**; many MIDI files lack rich part metadata, so instruments and techniques may map poorly.
3. Clarity on **transposition**: whether the file is **transposed as in the printed score** or already **concert pitch**, and whether **double bass** and **contrabassoon** are written **an octave above sounding pitch** (common in full scores).
4. A quick plan to verify **harmonics**, **microtones**, and **special techniques** in the exporter output—not everything that appears on paper is encoded the same way in XML.

If any of the above are wrong, **H_TI_core** can still compute, but **register** and **instrument** evidence may misrepresent the score.

### T.3 Step-by-step workflow

1. **Open the application** (for example `python -m homogeneity_analyser` or the packaged launcher you were given).
2. **Upload** the score (or set a file path if the UI offers it).
3. Choose **`pitch_interpretation_mode`** (see **T.4**).
4. Choose **`harmonic_pitch_policy`** (conservative default is safest until you audit harmonics).
5. Open **Symbolic inspection** so it runs on the same parse as **H_TI**.
6. Read **Instrument inventory**: parts → canonical instrument / subfamily / macrofamily.
7. Read **Event audit**: one row per chord tone; check **effective_sounding_midi**, dynamics, techniques, harmonic fields.
8. Read **Vertical sonorities**: what sounds together at each vertical slice; quick register sanity check.
9. Choose **window settings**: manual vs adaptive mode, **edge_policy** (see **T.6**).
10. Choose **register reference profile** (or numeric override—see **T.7**).
11. **Keep default weights** on first runs (see **T.8**).
12. **Run H_TI analysis** and wait for completion.
13. **Inspect the plot** (see **T.10**).
14. **Download CSV and JSON** for archiving.
15. **Write down** every parameter you used (modes, window effective values, profile, weights, affinity flags)—replication without this metadata is weak.

### T.4 Choosing the pitch interpretation mode

Four modes are implemented (`pitch_interpretation.py`):

| Mode | Plain-language idea |
|------|---------------------|
| **`musicxml_sounding`** | Apply instrument transpositions as encoded (typical **transposed score** export). |
| **`xml_pitch_as_real`** | Treat written pitches as **already sounding**; no transposition applied. |
| **`ignore_octave_transpositions_only`** | Apply only the **chromatic** part of encoded transposition (strip octave multiples). |
| **`xml_pitch_as_real_with_octave_transposers`** | Like concert pitch for many B♭/F instruments, but still apply **octave** correction for **double bass** and **contrabassoon** when they are notated an octave high. |

**Practical start:** for a normal **transposed orchestral** MusicXML from a major notation program, begin with **`musicxml_sounding`**. If you know the file was exported **already in concert pitch**, use **`xml_pitch_as_real`**. If B♭/F parts are already real but low strings still need octave correction, try **`xml_pitch_as_real_with_octave_transposers`**.

**Always verify** in **Event audit** that solo lines and tutti chords sit at plausible **sounding MIDI** values.

**Warning:** the wrong pitch mode can **strongly distort** **`register_span_semitones`**, **`register_span_proximity`**, **`pairwise_interval_proximity`**, and therefore **`register_compactness`** and **H_TI_core**.

### T.5 Checking the Symbolic inspection

Three tables (see **§9b** for column lists):

- **Instrument inventory** — Confirms how each part was mapped to **canonical_instrument**, **instrumental_subfamily**, and **macrofamily**. Use it to catch misnamed parts (“Violin I” vs desk labels, percussion unpitched status, etc.).
- **Event audit** — Confirms **notes**, **effective_sounding_midi**, **dynamics**, **techniques**, **harmonic_*** fields, and **microtonal** columns. Chords appear as **one row per chord tone**.
- **Vertical sonorities** — Lists what is active at each grouped vertical time; useful to eyeball **register span** and **compactness** diagnostics before trusting the curve.

**Quick checklist**

- Do desk / section labels still map to the intended **canonical** instruments?
- Are **cello** and **double bass** distinct and plausible?
- Do **transposing** instruments show plausible **sounding** MIDI?
- Are **microtones** shown as **fractional** MIDI where the score encodes them?
- For harmonics: **`harmonic_sounding_status`** **`explicit`** or **`inferred_common_artificial`** vs **`unresolved`** / candidate?
- Are missing dynamics **`unknown`** rather than invented loudness?
- Are techniques present only where the **XML** attached them?

### T.6 Choosing window settings

**Manual mode** (`window_mode = manual`): you set **window size** and **time step** in quarter lengths. **Best** when you need **strict comparability** across excerpts—use the **same** window and step for every file you want to compare on an absolute time grid.

**`auto_by_excerpt_duration`:** window and step scale with **excerpt length** (within clamps). Useful when excerpts differ greatly in length and you want **proportionally similar** windows.

**`auto_by_target_windows`:** chooses a step from **duration / target count**, then derives window width from **window_to_step_ratio**. Useful when you want **similar number of sample points** per excerpt.

**Edge policy** (`edge_policy`):

- **`include_partial_windows`** — keeps edge centres; **`edge_window`** stays false even when the nominal window sticks out past the score (coverage still computed).
- **`drop_partial_windows`** — **drops** centres whose full symmetric window would extend past the excerpt end.
- **`mark_partial_windows`** (default) — keeps centres but sets **`edge_window`** and **`window_coverage_ratio`** when the window is clipped—**inspect these** near the start/end of the score.

**Recommendations:** start **manual** for controlled studies; use **`mark_partial_windows`** when exploring; in reports always cite **`window_size_effective`**, **`time_step_effective`**, and mode from the JSON **parameters** block.

### T.7 Choosing the register reference profile

The UI maps a **register reference profile** to a reference semitone span $r$ used in $R_{\mathrm{span}}$ and $R_{\mathrm{pair}}$ (§2.4), i.e. the same $r$ in $\bigl(1+\mathrm{span}(t)/r\bigr)^{-1}$ and $\bigl(1+d_{ab}/r\bigr)^{-1}$ (`gradio_app.py`: strict $r=3$, balanced $r=7$, permissive $r=12$). Smaller $r$ means a **stronger** penalty for the same physical span—**stricter** concentration demand on register.

- **strict** — smaller reference; **narrow** register is required for high register proximity.
- **balanced** — default middle value.
- **permissive** — wider register tolerated before proximity drops.

**Numeric override:** advanced users may set an explicit **`register_ref_semitones`** when the UI allows; if you do, **document it**.

Changing **ref** changes **register_compactness** and therefore **H_TI_core**—treat it as a **sensitivity parameter**, not a neutral display option.

### T.8 Choosing weights

Default combination in **H_TI_core** (unless you change them in the UI or API):

| Component | Default weight |
|-----------|----------------|
| Instrument uniformity | **0.40** |
| Instrumental subfamily (`family`) | **0.25** |
| Technique uniformity (when included) | **0.15** |
| Register compactness (when pitched) | **0.20** |

**Guidance:** keep **defaults** for first analyses. If you change weights, **report the exact values** in any publication or appendix. For research, run **sensitivity checks** (small perturbations) rather than a single arbitrary reweighting.

### T.9 Running the analysis

When you run **H_TI**, the pipeline (high level): builds **notation events**; for each window centre computes **overlap masses**; forms **Herfindahl-style** uniformities where applicable; computes **register compactness** from sounding MIDI; combines active components with the **weighted geometric mean** → **H_TI_core**; then attaches **notated dynamic conditioning** (labels and scalars that **do not rescale** **H_TI_core**). **CSV** and **JSON** exports bundle parameters and time series.

### T.10 Reading the plot

- **Higher H_TI / H_TI_core** → more **symbolic concentration** on fewer instruments/families/techniques and/or **tighter** register (given your pitch mode and register reference).
- **Lower** values → **more spread** across categories or register.
- A **flat** stretch often means a **stable** orchestration layout in that region.
- A **falling** curve often means **loss of concentration** (more families/instruments, wider register, or omitted components returning).
- A **rising** curve often means **increasing concentration**—but **check** **`edge_window`** and **`window_coverage_ratio`**: clipped windows at the excerpt boundary can behave differently.

**Do not** describe higher **H_TI** as “more **acoustic** fusion” or “more **blend** in the hall.” The metric is **notation-derived** only.

### T.11 Reading common output fields

| Field | Meaning | How to read it |
|-------|---------|----------------|
| **H_TI** | Headline series | Same numeric series as **H_TI_core** in normal runs. |
| **H_TI_core** | Structural **notation-derived** symbolic timbral–instrumental homogeneity | Weighted geometric mean of active components; **not** a fusion metric and **not** measured acoustic or perceptual fusion. |
| **H_TI_strict** | Strict reference column | Same as **H_TI_core** here; used alongside relieved variants in exports. |
| **instrument_uniformity** | $U_{\mathrm{instr}}(t)=\sum_i P_i(t)^2$ | Closer to **1** → fewer instruments sharing the mass. |
| **family_uniformity** | $U_{\mathrm{fam}}(t)=\sum_f P_f(t)^2$ | Closer to **1** → fewer subfamilies. |
| **macrofamily_uniformity** | Coarse family Herfindahl | **Diagnostic**; not in default core mean. |
| **technique_uniformity** | Technique Herfindahl or 1.0 / NaN | See **`technique_coverage_status`**. |
| **register_compactness** | Pitch-space **proximity / dispersion** (geometric mean of span + pairwise **semitone-distance** factors) | **H_TI_core** register factor only; **does not** encode interval-class consonance. **`register_proximity`** duplicates it. |
| **register_span_factor** | Same numeric as **`register_span_proximity`** | Explicit alias: **span-based** registral compactness **component**. |
| **register_pair_distance_factor** | Same numeric as **`pairwise_interval_proximity`** | Explicit alias: **pairwise semitone-distance** compactness **component** (still **not** mod‑12 interval-class). |
| **register_span_semitones** | Outer pitch span | Wider → usually lower span proximity. |
| **pairwise_interval_proximity** | Pairwise **semitone-distance** tightness vs `ref` | Lower if chord tones are far apart in **absolute** semitones; orthogonal to **`interval_class_blend_factor`**. |
| **interval_class_blend_factor** | **Symbolic interval-class favourability** (optional) | Same value as legacy **`pairwise_interval_blend_factor`** when enabled; from `symbolic_blend_layers.py` + `taxonomy/symbolic_blend_conditioning.json`; **not** in **H_TI_core**. |
| **interval_class_profile** | Active interval-class mass distribution | Stable JSON keys (e.g. **`seconds_sevenths`**) name **chromatic mod‑12 equivalence buckets**, not literal interval qualities in the score. Parallel to **`symbolic_blend_interval_profile`** when enabled. |
| **interval_class_profile_display** | Same masses as **`interval_class_profile`**, human-readable keys | e.g. **`second-class / seventh-class equivalence group`** for **`seconds_sevenths`** — does **not** imply a notated seventh is present. |
| **literal_interval_semitone_pair_mass** | Overlap-weighted pair mass by **absolute** semitone distance (pre–mod‑12) | Keys are integer semitone counts as strings (`"2"`, `"12"`, …). Use to see literal seconds vs sevenths before class grouping. |
| **chromatic_mod12_pair_mass** | Overlap mass by chromatic distance mod 12 (`"0"`…`"11"`) | Diagnostic bridge between literal distances and **`interval_class_profile`** buckets. |
| **interval_class_evidence_status** | Provenance for interval mapping | Default **`symbolic_convention`** unless a rule is page-verified elsewhere. |
| **symbolic_blend_potential** | **Optional score-based symbolic blend-tendency diagnostic** | Exported only when **`include_symbolic_blend_potential`**; **not** SPL-based or psychoacoustically validated fusion. |
| **H_TA_acoustic_proxy** | Optional timbral-acoustic affinity | Same numeric value as **`timbral_acoustic_affinity`** when `include_acoustic_proxy`; **does not** change **H_TI_core**. |
| **timbral_acoustic_affinity_components** | Mass-weighted mean of kernel factors used in the window | Keys such as `source_mechanism`, `register_tessitura`, `technique`, `dynamic` — see **`docs/H_TA_ACOUSTIC_PROXY.md`**. |
| **timbral_acoustic_affinity_evidence_status** | Coverage tags for the proxy layer | Semicolon-separated; must agree with **components** (e.g. `dynamic_used_explicit_notated` when `dynamic` is present and window dynamics are explicit). |
| **technique_coverage_status** | Technique layer gate | **`unavailable`** / **`ambiguous`** → technique term omitted from core mean. |
| **dynamic_interpretation_label** | One symbolic reading | **Interpretive**; not SPL; can be **`insufficient_dynamic_evidence`**. |
| **dynamic_evidence_status** | Strength of rule evidence | **`strong`** / **`moderate`** / **`insufficient`**. |
| **dominant_instruments** (plural) | Tied top instrument(s) | Prefer plural + **`dominant_instrument_tie`** over **`dominant_instrument`** alone. |
| **dominant_families** / **dominant_macrofamilies** | Same pattern | Use **`*_tie`** flags when ties exist. |
| **edge_window** | Boundary flag | **true** → nominal window clipped; interpret cautiously. |
| **window_coverage_ratio** | Clipped overlap / nominal width | Low values near edges → partial coverage. |

### T.12 Reading dynamics responsibly

Written dynamics are **symbols on a fixed ordinal ladder**—**not** measured loudness, **not** SPL, **not** dB. **`dynamic_interpretation_label`** and related scalars **qualify** how a human might narrate the score; they **do not** prove blend or masking in a room.

- **`insufficient_dynamic_evidence`** means the tool **does not** have enough reliable written-dynamic coverage to drive family-specific narrative rules—**do not** force a story.
- Labels such as **soft blend potential** or **masked tonal mass risk** are **symbolic** readings tied to **notation** and coverage flags.

**Examples (cautious):** a **same-family**, **low-dynamic** window might align with **soft blend potential** language; a **cross-family**, **high-dynamic** window might align with **masked tonal mass risk** language—**only when** the label is actually emitted and evidence status is not **`insufficient`**. **Unknown** dynamics must stay **unknown**; never infer **pp** or **ff** from silence in the XML.

### T.13 Harmonics, microtones, and special techniques

**Harmonics (bowed strings):** diamond / square noteheads without explicit MusicXML roles are **candidates**, often **`unresolved`** under the default **conservative** policy—**do not** trust register around them until **`harmonic_sounding_status`** is **`explicit`** or **`inferred_common_artificial`**. Natural harmonics without explicit sounding pitch are **not** guessed from noteheads alone.

**Microtones:** fractional **MIDI** is normal when quarter tones are encoded; **unknown** accidental text does **not** silently invent new alter values.

**Techniques:** only **encoded** techniques appear. Missing technique rows mean **missing in the file**, not “the player definitely did not do it on the printed part.”

### T.14 Interpreting three typical cases

**Example 1 — homogeneous strings:** Mostly strings, one subfamily, narrow register → **moderate / high** **H_TI_core** is plausible. The curve **drops** if register widens sharply or **technique_coverage_status** becomes **`explicit_mixed`** (e.g. col legno vs arco both active).

**Example 2 — cross-family tutti:** Many instruments and macrofamilies, wide span → **low** **H_TI_core** is plausible. If dynamics are **high** and labels fire, a phrase like **masked tonal mass risk** is a **symbolic** caution—**not** a measurement of masking.

**Example 3 — mixed family, missing dynamics:** **H_TI_core** can still be **well-defined** from instruments / families / register. If **`dynamic_evidence_status`** is **`insufficient`**, treat **dynamic_interpretation_label** as **non-authoritative** for that window.

### T.15 Exporting and reporting results

**Save:** the **original** score file; **HTI** CSV/JSON (names depend on your export dialog); **plot** image if available; **instrument_inventory.csv**, **event_audit.csv**, **vertical_sonorities.csv** from Symbolic inspection.

**Minimum reporting checklist for papers / theses:**

- Software **version** or **git commit**
- **H_TI JSON `schema_version`** (currently **3.0** for the H_TI bundle)
- **`pitch_interpretation_mode`**, **`harmonic_pitch_policy`**
- **`window_mode`**, **`edge_policy`**, **`window_size_effective`**, **`time_step_effective`**
- **`register_ref_profile`** / **`register_ref_semitones`**
- Component **weights**; **`same_subfamily_relief_factor`**; whether **`timbral_affinity_relief_factor` > 0** and which **profile**
- Any **warnings** or **`edge_window`** pattern you relied on

### T.16 Common mistakes

- Treating **H_TI** as **acoustic** or **perceptual** fusion.
- Skipping **Symbolic inspection** when instruments or pitch are non-trivial.
- Using the **wrong pitch interpretation mode**.
- Trusting **register** where **harmonics** are **`unresolved`**.
- Comparing **adaptive** runs without publishing **effective** window and step.
- Ignoring **`edge_window`** and low **`window_coverage_ratio`** at boundaries.
- Changing **weights** without reporting them.
- Preferring **MIDI** when a clean **MusicXML** exists.
- Treating **missing** dynamics as **soft** or **loud**.
- Reading only **`dominant_instrument`** when **`dominant_instrument_tie`** is **true**—use **`dominant_instruments`**.

### T.17 Troubleshooting

| Problem | Practical check |
|---------|-------------------|
| Instruments land in **`other`** / odd taxonomy | Part names in the exporter; **Instrument inventory**; taxonomy aliases. |
| **Register span** looks wrong | Pitch mode; transposition; **double bass / contrabassoon**; **harmonic** columns. |
| Dynamics mostly **`unknown`** | Open the MusicXML in an editor or re-export with dynamics attached to notes. |
| Techniques missing | Exporter may flatten techniques to text only—verify in native notation software. |
| Curve **rises** oddly at the end | **`edge_window`**, **`window_coverage_ratio`**, partial windows. |
| Harmonics **`unresolved`** | Add explicit harmonic roles in the exporter, or accept conservative register for those bars. |

### T.18 Minimal responsible interpretation template

Copy and fill in the brackets:

> The passage was analysed with **[software version or commit]**, H_TI JSON schema **[e.g. 3.0]**, pitch interpretation mode **[mode]**, harmonic pitch policy **[policy]**, window mode **[manual / auto…]**, effective window **$w$** quarter lengths, effective step **$\Delta t$** quarter lengths, edge policy **[policy]**, register reference profile **[strict / balanced / permissive or numeric $r$]**, weights **[0.40 / 0.25 / 0.15 / 0.20 or as changed]**, same-subfamily relief **[factor]**, timbral affinity relief **[off or factor + profile]**. **H_TI_core** is interpreted as **symbolic concentration** of notated timbral–instrumental evidence in sliding windows, **not** as measured acoustic fusion or validated perceptual blend. Symbolic inspection confirmed **[brief facts: mapping, sounding MIDI sanity, harmonic statuses]**. The time series suggests **[qualitative reading]**, with limitations **[unknown dynamics, unresolved harmonics, edge windows, exporter gaps]**.

---

**Where to go next in this manual**

- Formal **definitions, formulas, and thresholds** — **Section 2** (Mathematical specification).
- **Data pipeline** overview — **Section 3**.
- **CSV columns** — **Section 9**; **JSON export** — **Section 10**.
- **Limitations** — **Section 11**.
- **Bibliography and literature governance** — **Section 19**.

---

## 2) Mathematical specification (code-aligned)

This section states **only** what `src/homogeneity_analyser` implements. Symbols follow `analyzers/hti.py`, `analyzers/hti_dynamics.py`, `analyzers/hti_dynamic_conditioning.py`, `analyzers/hti_adaptive_windows.py`, `analyzers/pitch_interpretation.py`, `analyzers/harmonic_pitch.py`, `analyzers/timbral_affinity.py`, `analyzers/dominant_distribution.py`, and `services/score_audit.py`. Constants such as `_EPS = 1e-12` and default weights are taken from source.

### 2.1) Sliding windows and overlap mass

Let **quarterLength** be the score time unit (music21). Fix a window centre $t$ and full width $w$ (both in quarterLength). The **nominal window** is the closed interval


$$
W_t=\bigl[t-\tfrac{w}{2},\,t+\tfrac{w}{2}\bigr].
$$

**Event geometry:** each active event $e$ has onset `offset` $o_e$ and end $z_e$ (code: `end`). The **overlap duration** $\ell_e(t,w)$ against $W_t$ is (implementation: `_event_overlap_ql` in `SymbolicTIHomogeneityAnalyzer`)


$$
\ell_e(t,w)=\max\Bigl(0,\,\min\Bigl(z_e,\,t+\tfrac{w}{2}\Bigr)-\max\Bigl(o_e,\,t-\tfrac{w}{2}\Bigr)\Bigr).
$$

**Overlap mass** for that event in the window is $m_e=\ell_e(t,w)$; the same scalar is reused for every pitch duplicate of the event when building register lists. For **event-level** normalised shares over the active set $E_t=\{e:\ell_e>0\}$,


$$
p_e(t)=\frac{\ell_e(t,w)}{\sum_{e'\in E_t}\ell_{e'}(t,w)}.
$$

**Instrument Herfindahl** uses a different normalisation (shares $p_i$ relative to total **instrument** overlap mass); see **§2.2**.

Aggregates use **non-negative** masses; empty or zero-total windows yield no **H_TI** row (`extract_hti_window` returns `None`).

### 2.2) Category shares and Herfindahl uniformity

For any finite multiset of categories $c$ with masses $M_c \ge 0$ and total $T=\sum_c M_c > 0$, define shares $p_c = M_c / T$. The implemented Herfindahl concentration is


$$
U(t) = \sum_{c\in C_t} P_c(t)^2.
$$

When $|C_t|\ge 1$ and all represented shares are positive, $\sum_{c\in C_t} P_c(t)^2\in[1/|C_t|,\,1]$ (equality $1$ iff one category carries all mass). **`_herfindahl_from_masses`** returns this sum **clipped to** $\left[0,\,1\right]$ after `numpy` handling, where $P_c(t)$ denotes the **category share** for that aggregation.

**Instrument uniformity** $U_{\mathrm{instr}}(t)$: let $M_i$ be the sum of $\ell_e(t,w)$ over events whose **canonical instrument** is $i$, and $T_{\mathrm{inst}}=\sum_i M_i$. Then $P_i(t)=M_i/T_{\mathrm{inst}}$ and


$$
U_{\mathrm{instr}}(t) = \sum_{i\in I_t} P_i(t)^2.
$$

Shares $P_i$ are **relative to instrument mass total** `tot_inst` in code (not the raw overlap sum across unrelated categories).

**Instrumental subfamily uniformity** $U_{\mathrm{fam}}(t)$ (exported as both `instrumental_subfamily_uniformity` and **`family_uniformity`**): taxonomy **`family`** rows (e.g. `clarinets`, `brass`) as categories $f$ with masses $M_f$, shares $P_f(t)=M_f/\sum_{f'}M_{f'}$, and


$$
U_{\mathrm{fam}}(t) = \sum_{f\in F_t} P_f(t)^2.
$$

**Macrofamily uniformity** maps each instrumental subfamily through `macrofamily_from_instrumental_subfamily` to coarse buckets (e.g. `strings`, `woodwinds`); the same Herfindahl form applies on those masses. **Not** included in the default **H_TI_core** geometric mean — diagnostic / export only.

### 2.3) Technique uniformity key vs technique state id

- **`technique_state_id`:** full merged playing-state fingerprint on an event (includes instrument-specific context). Used in legacy timbral diagnostics and exports as `technique_state_distribution` is keyed by **`technique_uniformity_key`** in H_TI windows — see below.
- **`technique_uniformity_key`:** **instrument-free** bucket string from `compute_technique_uniformity_key_from_event` (`technique_state.py`). **Technique uniformity** $U_{\mathrm{tech}}(t)$ applies Herfindahl to overlap masses grouped by this key **when** the technique layer is admitted: with technique buckets $k\in K_t$ and shares $Q_k(t)$,


$$
U_{\mathrm{tech}}(t) = \sum_{k\in K_t} Q_k(t)^2.
$$

**Coverage and inclusion rule** (`extract_hti_window`): let $T_{\mathrm{ol}}=\sum_e m_e$, let $M_{\mathrm{nonempty}}$ be the overlap mass on events with non-empty technique key, and $M_{\mathrm{empty}}=\max(0,\,T_{\mathrm{ol}}-M_{\mathrm{nonempty}})$. Let `any_special` = any event with a **special** explicit technique (`event_has_special_explicit_technique`), and $K$ = number of distinct non-empty keys with positive mass among special/default mix.

| `technique_coverage_status` | Technique term in H_TI_core |
|----------------------------|-----------------------------|
| `unavailable` | $m_{\mathrm{nonempty}}\le 10^{-12}$: **omitted** (weight dropped, renormalised). |
| `ambiguous` | $m_{\mathrm{empty}}/T_{\mathrm{ol}}>0.15$ **and** $m_{\mathrm{nonempty}}/T_{\mathrm{ol}}>0.15$: **omitted**. |
| `ordinary_default_uniform` | no special techniques: **uniformity = 1.0**, term **included** (does not duplicate instrument concentration). |
| `explicit_uniform` | special present, $K=1$: **uniformity = 1.0**, term **included**. |
| `explicit_mixed` | special present, $K\ge 2$: Herfindahl on `tech_mass`, term **included**. |

If status is `unavailable` or `ambiguous`, `technique_uniformity` is **NaN** and the component is removed from the geometric mean (`compute_H_TI`).

### 2.4) Register compactness (span + pairwise, geometric blend)

Let $r$ be **`register_ref_semitones`** (default **7.0** semitones if non-finite or $r\le 0$). Input list `pitch_occurrences` lists pairs $(m_a,\omega_a)$: one entry per **chord tone** / sounding pitch carrying the parent event’s overlap mass $\omega_a$ (code stores MIDI in $m_a$). **Unpitched** percussion excluded when `is_percussion_family` and ontology `PitchStatus.UNPITCHED` (`extract_hti_window`).

Let $M_t=\{m_a\}$ be the multiset of active sounding MIDI values in the window. The **register span** (semitones) is


$$
\mathrm{span}(t) = \max(M_t) - \min(M_t),
$$

with $\mathrm{span}(t)=0$ if there is only one pitch. **Span proximity** is


$$
R_{\mathrm{span}}(t)=\bigl(1+\mathrm{span}(t)/r\bigr)^{-1}.
$$

For unordered pitch pairs with $a \lt b$, let $d_{ab}=|m_a-m_b|$ and pair weights $\omega_{ab}=\omega_a\omega_b$. **Pairwise interval proximity** is


$$
R_{\mathrm{pair}}(t)=\frac{\sum_{a<b}\omega_{ab}(t)\bigl(1+d_{ab}/r\bigr)^{-1}}{\sum_{a<b}\omega_{ab}(t)}.
$$

For fewer than two pitched rows, code sets $R_{\mathrm{pair}}=1$ and `pairwise_interval_coverage_status` = **`insufficient_pairs`**. If there are no pitched rows at all → **`unpitched_only`**, NaN span/pair/compactness, **`register_coverage_status`** = `unpitched_only`, register term **omitted** from **H_TI_core**. With $\varepsilon=10^{-12}$ (**`_EPS`** in `hti.py`), **register compactness** is


$$
R_{\mathrm{compact}}(t)=\sqrt{\max\bigl(\varepsilon,R_{\mathrm{span}}(t)\bigr)\cdot\max\bigl(\varepsilon,R_{\mathrm{pair}}(t)\bigr)}.
$$

clipped to $\left[0,\,1\right]$. **`register_proximity`** equals **`register_compactness`** (backward-compatible export name).

### 2.5) H_TI_core — weighted geometric mean (unchanged formula)

Let the nominal positive weights be $w_{\mathrm{inst}}=0.40$, $w_{\mathrm{fam}}=0.25$, $w_{\mathrm{tech}}=0.15$, $w_{\mathrm{reg}}=0.20$ (overridable via constructor / run parameters). Let $C_t$ be the **active** component keys after omissions:

- Always: `instrument_uniformity`, `family_uniformity`.
- Add `technique_uniformity` iff technique status **not** `unavailable`/`ambiguous` and value finite.
- Add `register_proximity` iff `register_coverage_status == "pitched"` and value finite.

**Renormalised weights** $\tilde w_c$ on the active key set $C_t$ satisfy

$$
\tilde w_c = \frac{w_c}{\sum_{j\in C_t} w_j}.
$$

For each active component $c\in C_t$, let $x_c(t)\in(0,1]$ be the uniformity or register factor; the implementation floors each base at $\varepsilon$ before the log-sum. The **weighted geometric mean** satisfies


$$
H_{\mathrm{TI},\mathrm{core}}(t)=\prod_{c\in C_t}\max\bigl(\varepsilon,x_c(t)\bigr)^{\tilde w_c}=\exp\Bigl(\sum_{c\in C_t}\tilde w_c\ln\max\bigl(\varepsilon,x_c(t)\bigr)\Bigr),
$$

then clipped to $\left[0,\,1\right]$. The headline series match the core scalar in non-empty windows:


$$
H_{\mathrm{TI}}(t)=H_{\mathrm{TI},\mathrm{core}}(t)=H_{\mathrm{TI},\mathrm{strict}}(t).
$$

**`H_TI_subfamily_relieved`** uses an **effective** instrument uniformity $(1-r)U_{\mathrm{instr}}+r U_{\mathrm{fam}}$ with relief factor $r=$ `same_subfamily_relief_factor`, but the **declared core** column remains the strict **H_TI_core** path.

### 2.6) Optional symbolic timbral affinity (literature-governed)

When `timbral_affinity_relief_factor` $r_{\mathrm{aff}}>0$, for the same window let


$$
p_e(t)=\frac{m_e}{\sum_{e'\in E_t} m_{e'}}
$$

be **event-level** overlap shares (not instrument Herfindahl shares). Define pairwise **symbolic** similarity $S_{ee'}\in[0,1]$ from `pairwise_similarity` in `timbral_affinity.py` (registry + tag rules; **not** measured spectra). Then



$$
U_{\mathrm{affinity}}(t) = \sum_{e\in E_t}\sum_{e'\in E_t} p_e(t)\, p_{e'}(t)\, S_{ee'}.
$$

**Effective instrument uniformity** for the relieved scalar:


$$
U^{\mathrm{eff}}_{\mathrm{instr}} = (1-r_{\mathrm{aff}})\, U_{\mathrm{instr}} + r_{\mathrm{aff}}\, U_{\mathrm{affinity}}(t).
$$

**`H_TI_affinity_literature_relieved`** recomputes the same weighted geometric mean as **H_TI_core** but substitutes $U^{\mathrm{eff}}_{\mathrm{instr}}$ into the instrument slot (`compute_timbral_affinity_bundle_for_window`).

**Profiles** `strict` < `conservative` < `moderate` < `exploratory` gate which symbolic rules fire (`PROFILE_ORDER`). **`finalize_timbral_affinity_dynamic`** adds **interpretive** `timbral_affinity_dynamic_factor` / `H_TI_affinity_dynamic_conditioned`; these **do not** alter **H_TI_core**.

### 2.7) Notated dynamic conditioning (ordinal; does not rescale core)

Overlap-weighted mass per parsed dynamic token (plus optional `__unknown__` in the **export** distribution when marks are missing). Let $q_d(t)$ be the share of **known** (not unknown) mass on dynamic class $d\in D_t$ (unknown excluded from the coherence sum; `hti_dynamics.py`). **Notated dynamic coherence** is


$$
C_{\mathrm{dyn}}(t) = \sum_{d\in D_t} q_d(t)^2.
$$

Let $v_d$ denote the fixed ordinal ladder value for class $d$ (**not** SPL). With known-token masses $m_d$ on the known subset, **dynamic intensity** and **dynamic softness** are


$$
I_{\mathrm{dyn}}(t)=\frac{\sum_{d\in D_t} m_d\, v_d}{\sum_{d\in D_t} m_d},\quad S_{\mathrm{dyn}}(t)=1-I_{\mathrm{dyn}}(t)
$$

when finite. **`dynamic_coverage_status`:** `explicit` if known fraction $\ge 0.72$; `partial` if $\ge 0.08$; else `unavailable`. For **divergence**, let $\tilde q_d(t)$ be each **known** dynamic class’s share of **total** window overlap mass (same denominator as `notated_dynamic_level_distribution` including unknown when present). **`dynamic_divergence_detected`** is true iff there exist distinct $d_1,d_2$ with


$$
\tilde q_{d_1}(t)\ge 0.12 \;\wedge\; \tilde q_{d_2}(t)\ge 0.12 \;\wedge\; d_1\neq d_2
$$

(`hti_dynamics.py`).

**Interpretive scalars** (`apply_notated_dynamic_conditioning`, `FAMILY_RULES_VERSION = "hti_dynamic_conditioning_v1"`): use **H_TI_core** value $h$, **`notated_dynamic_coherence`** $\mathrm{ndc}$, **`dynamic_softness`** $\mathrm{ds}$, **`dynamic_intensity_ordinal`** $\mathrm{di}$, **`same_family_mixed_instrument_mass`** $\mathrm{sfm}$, **`family_specific_projection_weight`** $\mathrm{fspw}$, **`masking_context_weight`** $\mathrm{mk}$, **`n_macrofamilies`** $N_{\mathrm{macro}}$, **`clarinet_overlap_fraction`** $c_f$, etc. Implemented examples:

- **`soft_blend_potential`:** $h \cdot \max(\varepsilon,\mathrm{ndc}) \cdot \max(\varepsilon,\mathrm{ds})$ (with `_EPS` when $\mathrm{ndc}$ or $\mathrm{ds}$ is non-finite).
- **`projection_divergence_risk`:** $\mathrm{di}\cdot \mathrm{sfm}\cdot \mathrm{fspw}\cdot B$ where $B$ is the finite **`bright_boost`** factor (up to **1.22** when simultaneous trumpet-class + trombone overlap and $\mathrm{di}>0.70$).
- **`family_heterogeneity`:** $\mathrm{clip}_{[0,1]}\bigl(1 - U_{\mathrm{fam}}(t)\bigr)$.
- **`masked_tonal_mass_risk`:** $\mathrm{di}\cdot \mathrm{clip}_{[0,1]}\bigl(1-U_{\mathrm{fam}}(t)\bigr)\cdot \mathrm{mk}$ (finite guard; same inner clip as **`family_heterogeneity`** above).
- **`intra_family_convergence_potential`**, **`transparent_blend_potential`**, **`bright_salience_risk`** — see source; cross-macrofamily factor **`cross`** $=\min\bigl(1,\max(0,(N_{\mathrm{macro}}-1)/3)\bigr)$ when $N_{\mathrm{macro}}\ge 2$.

These scalars **do not** change $h$ used as **H_TI_core** in the same row; they are appended after `compute_H_TI`.

### 2.8) Pitch interpretation (per chord tone)

`interpret_pitch_tone` (`pitch_interpretation.py`): **`effective_written_midi`** = letter-octave base MIDI (`_base_midi_letter_octave`, naturals only) + **`effective_alter`** from `compute_effective_alter` (MusicXML `alter` plus recognised accidental text; unknown text does not invent microtones beyond explicit `alter`).

Transpose bookkeeping from the part interval: **`chromatic_transpose_detected`**, **`octave_transpose_detected`** = `decompose_transpose_semitones` on raw part transposition semitones. **`total_transpose_applied`** and applied chromatic/octave parts depend on **`pitch_interpretation_mode`**:

| Mode | Behaviour (implemented) |
|------|-------------------------|
| `musicxml_sounding` | If transposition absent: sounding = written. Else transpose written pitch by music21 interval → **`effective_sounding_midi`**; **`total_transpose_applied`** = sounding − written. |
| `xml_pitch_as_real` | **`total_transpose_applied = 0`**, sounding = written. |
| `ignore_octave_transpositions_only` | Apply only chromatic part of detected interval to written pitch. |
| `xml_pitch_as_real_with_octave_transposers` | Like real pitch, but if canonical instrument ∈ {double bass, contrabassoon}, add detected **octave** component only (`−12` convention). |

**Fractional MIDI** flows through `pitch.ps`-style arithmetic; audit cells format integers when within $10^{-4}$ of an integer (`score_audit._format_audit_midi_cell`).

### 2.9) Harmonic pitch interpretation (audit + conditional replacement)

Policies: `conservative` (default), `infer_common_artificial`, `written_as_sounding` (`harmonic_pitch.py`). Fields per tone include `harmonic_state`, `harmonic_type`, `harmonic_pitch_role`, `harmonic_detection_source`, `harmonic_base_midi`, `harmonic_touching_midi`, `harmonic_touching_interval_semitones`, `harmonic_interval_rule_id`, `harmonic_sounding_midi`, `harmonic_sounding_status`, `harmonic_pitch_policy`, `harmonic_warning`.

**Artificial table:** rows `octave`, `perfect_fifth`, `perfect_fourth`, `major_third`, `minor_third` with **`touching_interval_semitones`** and **`sounding_interval_above_base`**. Match $|m_{\mathrm{touch}}-m_{\mathrm{base}}-\mathrm{target}|\le 0.25$ semitone (`INTERVAL_MATCH_TOLERANCE_SEMITONES`), first best in fixed row order. In **written** MIDI space, matched artificial harmonics satisfy


$$
m_{\mathrm{sounding}} = m_{\mathrm{base}} + \Delta_{\mathrm{sounding}},
$$

where $\Delta_{\mathrm{sounding}}$ is the table’s **`sounding_interval_above_base`** for the matched rule; this is then mapped to **`effective_sounding_midi`** with `sounding_midi_from_baked_written_ps` (applies pitch mode + transposition).

**Replacement rule:** `finalize_harmonic_pitches_for_note` overwrites `effective_sounding_midi` / `pits[i]` **only** when `harmonic_sounding_status` ∈ {`explicit`, `inferred_common_artificial`}. **`unresolved`** / candidate states **do not** silently change `effective_sounding_midi` (no `_apply_effective_sounding_midi` merge).

### 2.10) Adaptive window orchestration

`resolve_hti_windowing` (`hti_adaptive_windows.py`) returns effective **`window_size_effective`**, **`time_step_effective`**, and echo parameters. Let $L$ be **`excerpt_duration_quarterLength`** (excerpt span in quarter lengths). Write $\mathrm{clip}(x,a,b)=\min(b,\max(a,x))$ (clamp $x$ to $\left[a,\,b\right]$).

- **manual:** effective sizes equal user `window_size` and `time_step`.
- **auto_by_excerpt_duration:** with window ratio $\rho_w$, step ratio $\rho_s$, and bounds $\left[w_{\min},\,w_{\max}\right]$, $\left[s_{\min},\,s_{\max}\right]$,
  

$$
w_{\mathrm{eff}}=\mathrm{clip}(L\rho_w,w_{\min},w_{\max}),\quad s_{\mathrm{eff}}=\mathrm{clip}(L\rho_s,s_{\min},s_{\max}).
$$

Defaults (see `DEFAULT_HTI_PARAMS` / `resolve_hti_windowing` in `hti_adaptive_windows.py`): $\rho_w=0.15$ (**`window_ratio`**), $\rho_s=0.01$ (**`step_ratio`**), $w_{\min}=0.5$ (**`min_window_size`**), $w_{\max}=8$ (**`max_window_size`**), $s_{\min}=1/16$ (**`min_time_step`**), $s_{\max}=1$ (**`max_time_step`**).

- **auto_by_target_windows:** with target count $N_{\mathrm{target}}$ and window-to-step ratio $\rho_{w/s}$,
  

$$
s_{\mathrm{eff}}=\mathrm{clip}\left(\frac{L}{N_{\mathrm{target}}},s_{\min},s_{\max}\right),\quad w_{\mathrm{eff}}=\mathrm{clip}\left(s_{\mathrm{eff}}\rho_{w/s},w_{\min},w_{\max}\right).
$$

Defaults: $N_{\mathrm{target}}=100$ (**`target_window_count`**), $\rho_{w/s}=10$ (**`window_to_step_ratio`**) (same clamp bounds as above).

**`build_hti_window_centers`:** uniform grid from $0$ with step $s_{\mathrm{eff}}$; if **`edge_policy`** = `drop_partial_windows`, drop centres with $t+w_{\mathrm{eff}}/2 > L$ (numerical tolerance $10^{-9}$).

**`hti_window_row_geometry`:** nominal bounds `window_start` $=t-w/2$, `window_end` $=t+w/2$; overlap with excerpt $\left[e_s,\,e_e\right]$ gives **`effective_window_overlap_duration`**; **`window_coverage_ratio`** is overlap divided by $w$; **`edge_window`** is false if policy is `include_partial_windows`, else true when the nominal window extends outside the excerpt.

### 2.11) Dominant categories and ties

`dominant_with_ties` (`dominant_distribution.py`, default tolerance $\tau=10^{-9}$): let $P_{\max}$ be the maximum category share. Categories $a$ with $|P_a-P_{\max}|\le\tau$ are **tied tops**; **`dominant_all`** lists them in **Unicode code-point order** (Python `sorted` on `str`, case-sensitive), **`dominant_primary`** is the first entry (backward-compatible single field), and **`tie`** is true iff there are at least two. Let $P_{\mathrm{second}}$ be the second-largest **distinct** positive share among distribution values (or $0$ if only one distinct share exists). The helper returns **`margin_to_second`**: $P_{\max}-P_{\mathrm{second}}$ when `tie` is **false**, and **`0.0`** when two or more categories tie at the top (`tie` true). H_TI time series mirror this in fields such as **`dominant_instrument_margin`**, **`dominant_family_margin`**, **`dominant_macrofamily_margin`**, **`dominant_timbral_state_margin`**, and **`dominant_dynamic_margin`**.

### 2.12) Symbolic inspection (diagnostic pipeline)

`build_symbolic_inspection_tables` constructs `TimbralHomogeneityAnalyzer` events (same pipeline as H_TI), then **`instrument_inventory`**, flattened **`event_audit`** (one row per **chord tone** / pitch with `effective_sounding_midi`, harmonic columns, `active_dynamic`, technique fields), and **`vertical_sonorities`** grouped by rounded `offset_quarterLength`. Column orders: `SCORE_AUDIT_*_COLUMNS` in `score_audit.py`. **Field-by-field glossary:** **Appendix D.13**. **Not** a homogeneity metric.

---

## 3) Data pipeline

1. **Upload / path** — `io/score_validation.py` guards size and extensions; `parse_score()` (music21) loads MusicXML or MIDI.
2. **Parts and instruments** — part names, `Instrument` objects, and note-local overrides resolve to **canonical_instrument** + **instrumental subfamily** via `taxonomy/instrument_taxonomy.py` (aliases included).
3. **Sounding pitch** — `analyzers/pitch_interpretation.py` builds **effective written / sounding MIDI** from step/octave, **`pitch_interpretation_mode`** (full transpose; concert XML; chromatic-only strip; **concert XML + −12 for double bass / contrabassoon**), **`decompose_transpose_semitones`** (chromatic vs octave **detected** vs **applied** in the audit), and **`compute_effective_alter`** (MusicXML **`alter`** plus accidental-text inference for quarter tones; unknown signs are not invented). For ordinary notes, in the same pitch-interpretation frame,


$$
m_{\mathrm{sounding}} = m_{\mathrm{written}} + \Delta_{\mathrm{transpose}},
$$

i.e. **`effective_sounding_midi` = `effective_written_midi` + `total_transpose_applied`** in export columns.
   **String harmonics** (`harmonic_pitch.py`, **`harmonic_pitch_policy`**) — **`harmonic_*`** audit fields (including **`harmonic_touching_interval_semitones`**, **`harmonic_interval_rule_id`**) and replacement of **`effective_sounding_midi`** / chord-tone **`pitches`** only when **`harmonic_sounding_status`** is **`explicit`** or **`inferred_common_artificial`**. **`ARTIFICIAL_STRING_HARMONIC_INTERVALS`**: touching−base semitones → sounding offset (**octave, perfect fifth, perfect fourth, major third, minor third**; **0.25** semitone tolerance; **`harmonic_division`** / **`intonation_note`** in code; third rows: tempered-partial warnings). **Natural** harmonics: explicit sounding only; else **`harmonic_candidate`** / **`unresolved`**. **Diamond / square** on bowed strings without XML roles: **`harmonic_type`** **`unknown`**. Chart: **Violin Harmonics — arranged by Agatha Mallett** (`docs/STRING_HARMONIC_INTERVAL_REFERENCE.md`). **`written_as_sounding`**: no silent register remap. Non-string diamond/square: audit warning only.
   Chords enumerate **all** chord tones for register span.
4. **Unpitched percussion** — register pitch lists follow the same rule as **timbral** slices: only **percussion-family** parts with ontology **`UNPITCHED`** status skip `pitches` for register; other instruments always contribute sounding MIDI to span / pairwise terms.
5. **Technique / articulation / directions** — `notation_context.py` and `technique_state.py` merge measure directions and note attachments into persistent **`TechniqueState`**; **`technique_state_id`** is the full fingerprint (`instrument|…`); **`technique_uniformity_key`** is the instrument-free bucket used for **technique_uniformity** and for **`technique_state_distribution`** in H_TI exports.
6. **Dynamics** — written marks and hairpins are carried on events; `hti_dynamics.py` aggregates overlap-mass distributions per window.
7. **H_TI_core** — `SymbolicTIHomogeneityAnalyzer` (`analyzers/hti.py`) subclasses `TimbralHomogeneityAnalyzer` (`timbral.py`) to **reuse the event list** without exposing legacy pairwise **H_timbral** as a user product.
8. **Conditioning** — `hti_dynamic_conditioning.py` attaches family-aware interpretive scalars and a single **`dynamic_interpretation_label`** per window.
9. **Exports** — CSV column order in `hti_export_rows.py` (`HTI_CSV_COLUMNS`, `hti_csv_row_dict`); Gradio writes files in `callbacks.py`; JSON via `services/json_export.build_hti_export` (`schema_version` **3.0**). `analyzers/hti.py` re-exports column tuples for backward-compatible imports.

### 3.1) Adaptive window orchestration (optional; formula unchanged)

**H_TI_core** math (Herfindahl components, geometric mean, renormalisation) is **unchanged**. Adaptive logic only selects **window centre times** and **window width** before calling the same `extract_hti_window` / `compute_H_TI` path.

- **Module:** `analyzers/hti_adaptive_windows.py` — `resolve_hti_windowing` (effective `window_size` / `time_step` from **`window_mode`** and excerpt span in quarter lengths), `build_hti_window_centers` (uniform centres from 0; optional drop of partial trailing windows), `hti_window_row_geometry` (nominal **`window_start`** / **`window_end`**, overlap **`window_coverage_ratio`**, **`edge_window`** flag vs **`edge_policy`**).
- **`window_mode`:** `manual` (default; user **`time_step`** + **`window_size`**), `auto_by_excerpt_duration` (ratio × duration + clamps), `auto_by_target_windows` (`excerpt_duration / target_window_count` step, × **`window_to_step_ratio`** window, then clamps).
- **`edge_policy`:** `include_partial_windows` (do not flag edge in **`edge_window`**), `drop_partial_windows` (omit centres past excerpt when the full symmetric window would extend beyond the score end), `mark_partial_windows` (default: keep centres, set **`edge_window`** and coverage fields when the nominal window extends outside the excerpt).
- **Service wiring:** `run_symbolic_ti_homogeneity_analysis` merges resolved fields into export **`parameters`** (`window_size_input`, `time_step_input`, `window_size_effective`, `time_step_effective`, `excerpt_duration_quarterLength`, ratios, clamps, `target_window_count`, `window_to_step_ratio`, `edge_policy`, …). Each **`analyze_hti`** row includes **`window_start`**, **`window_end`**, **`edge_window`**, **`window_coverage_ratio`**, **`effective_window_overlap_duration`** (JSON time series; CSV includes the first four).
- **Reading:** adaptive modes improve **proportional** comparison across scores of different lengths; they **reduce strict comparability** of absolute time-grid results unless readers normalise by the reported effective step/window.

**Dominant categories:** singular **`dominant_*`** fields are retained for compatibility; ties are visible in **`dominant_*s`** lists and **`dominant_*_tie`** booleans — prefer plural + tie fields for analytical interpretation.

---

## 4) H_TI_core formal definition (summary)

Canonical equations, thresholds, and omission rules are in **§2**. This subsection restates the user-facing structure.

Work in **quarterLength** time. The nominal window is $W_t=\bigl[t-\tfrac{w}{2},\,t+\tfrac{w}{2}\bigr]$ (§2.1).

- Build **active sounding events** with overlap mass $m_e=\ell_e(t,w)>0$ against $W_t$ (§2.1).
- **instrument_uniformity** $U_{\mathrm{instr}}(t)=\sum_{i\in I_t} P_i(t)^2$ with instrument shares $P_i(t)$ (§2.2).
- **family_uniformity** (instrumental subfamily) $U_{\mathrm{fam}}(t)=\sum_{f\in F_t} P_f(t)^2$ on taxonomy `family` rows (e.g. `clarinets`, `brass`).
- **macrofamily_uniformity** — same Herfindahl pattern on coarse buckets (`strings`, `woodwinds`, `brass`, …) from `hti_taxonomy.py`; **reported as a diagnostic**, not part of the default **H_TI_core** geometric mean unless you fork the service.
- **technique_uniformity** $U_{\mathrm{tech}}(t)$ — Herfindahl on **`technique_uniformity_key`** when **`technique_coverage_status`** is neither `unavailable` nor `ambiguous` (§2.3). If **`ordinary_default_uniform`**, the value is **1.0**. With special explicit techniques, **one** distinct key with mass ⇒ **1.0**; several keys ⇒ $U_{\mathrm{tech}} \lt 1$ (`explicit_mixed`).
- **register_span_proximity** $R_{\mathrm{span}}(t)$ — Eq. in §2.4, using semitone span over **all** chord tones / `pitches` on active pitched events (sounding MIDI from the timbral pipeline; unpitched percussion excluded).
- **pairwise_interval_proximity** $R_{\mathrm{pair}}(t)$ — Eq. in §2.4 (overlap-weighted mean of $\bigl(1+d_{ab}/r\bigr)^{-1}$).
- **register_compactness** $R_{\mathrm{compact}}(t)$ — Eq. in §2.4; this is the register factor in **H_TI_core**. The CSV/JSON column **`register_proximity`** duplicates **`register_compactness`** for backward compatibility.
- **pairwise_interval_coverage_status** — `sufficient_pairs` / `insufficient_pairs` (including a single pitched occurrence) / `unpitched_only`.

**Homogeneity vs transparency:** wide internal spacing can favour **transparent blend** readings in the dynamic-conditioning layer; it **lowers** register compactness and thus **H_TI_core**, because homogeneity here encodes registral **concentration**, not acoustic transparency.

**H_TI_core** is the **weighted geometric mean** of active components (defaults **0.40 / 0.25 / 0.15 / 0.20**); see §2.5. Missing layers drop out and nominal weights **renormalise** on the remaining keys.

The headline series satisfy $H_{\mathrm{TI}}(t)=H_{\mathrm{TI},\mathrm{core}}(t)=H_{\mathrm{TI},\mathrm{strict}}(t)$ (same numeric array in CSV/JSON/plots). **H_TI_strict** is a **strict-reference** column for consumers that juxtapose the core scalar against optional relieved series (**H_TI_affinity_literature_relieved**, subfamily-relieved variants if enabled) without redefining **H_TI_core**.

**Optional symbolic timbral-affinity relief:** when **`timbral_affinity_relief_factor` > 0**, the analyser exports **`timbral_affinity_uniformity`** (pairwise overlap-weighted $U_{\mathrm{affinity}}(t)$ from §2.6), **`instrument_affinity_effective_uniformity`**, and **`H_TI_affinity_literature_relieved`** — the same weighted geometric mean as **H_TI_core** but with the **instrument** slot replaced by the effective uniformity blend $U^{\mathrm{eff}}_{\mathrm{instr}}$. **Profiles** (`strict` / `conservative` / `moderate` / `exploratory`) gate rule tiers; **dynamics** add interpretive qualifiers only (`timbral_affinity_dynamic_factor`, `H_TI_affinity_dynamic_conditioned`). This is **notation-derived**, **not** measured acoustic or perceptual fusion; see `docs/TIMBRAL_AFFINITY_LITERATURE_AUDIT.md`.

---

## 5) Technique-state semantics

Per-event audit / timbral events include **`explicit_technique`**, **`explicit_technique_detected`** (boolean), **`technique_uniformity_key`** (instrument-free; default-only maps to **`ordinary_default`**), and the composite **`technique_state_id`** (full fingerprint). Vertical sonority rows add **`technique_coverage_status`** for that slice.

| Status | Meaning |
|--------|--------|
| `ordinary_default_uniform` | No **special** playing-state contrast (default brass **open**, **arco**, **ordinario**, etc. all collapse to **`ordinary_default`**); **technique_uniformity = 1.0**. |
| `explicit_uniform` | At least one **special** explicit technique and **one** distinct **`technique_uniformity_key`** with overlap mass; **technique_uniformity = 1.0**. |
| `explicit_mixed` | Two or more distinct **`technique_uniformity_key`** values among special/default mixes. Herfindahl is taken over **all** active technique buckets. |
| `unavailable` | No **`technique_uniformity_key`** could be resolved on active overlap mass — technique term **omitted**. |
| `ambiguous` | Large empty vs non-empty technique-key mix — technique term **omitted**. |

---

## 6) Notated dynamic conditioning (formal)

Implemented in `hti_dynamics.py` + `hti_dynamic_conditioning.py`.

- **Ordinal ladder** — fixed symbolic map for `pppp` … `ffff` (not SPL).
- **notated_dynamic_level_distribution** — overlap shares per parsed mark (+ optional `__unknown__` bucket in exports when mass lacks a mark).
- **notated_dynamic_coherence** — $C_{\mathrm{dyn}}(t)=\sum_{d\in D_t} q_d(t)^2$ over **notated** dynamic classes (unknown excluded from this sum).
- **dynamic_intensity_ordinal** — $I_{\mathrm{dyn}}(t)$ (§2.7).
- **dynamic_softness** — $S_{\mathrm{dyn}}(t)=1-I_{\mathrm{dyn}}(t)$ when finite.
- **dynamic_coverage_status** — `explicit` / `partial` / `unavailable`.
- **crescendo_active** / **diminuendo_active** — hairpin flags on active mass.
- **dynamic_divergence_detected** — as in §2.7: at least two distinct known classes with $\tilde q_d(t)\ge 0.12$ each (shares of **total** overlap mass).

Derived interpretive scalars (examples): **soft_blend_potential**, **intra_family_convergence_potential**, **transparent_blend_potential**, **projection_divergence_risk**, **masked_tonal_mass_risk**, **bright_salience_risk**, **family_specific_projection_weight**, **masking_context_weight**, **dynamic_evidence_status**, **dynamic_interpretation_label**.

These are **literature-informed symbolic** readings — **not** measured blend, projection, or masking.

---

## 7) Family-sensitive interpretation rules (conservative)

Brass, clarinet, flute, double reeds, strings, cross-family orchestration, and percussion each follow **narrow** heuristics documented in code comments in `hti_dynamic_conditioning.py` (`FAMILY_RULES_VERSION = "hti_dynamic_conditioning_v1"`). Evidence tiers: **strong**, **moderate**, **insufficient** (especially percussion-only windows).

---

## 8) Interpretation labels (priority)

One **`dynamic_interpretation_label`** per window, chosen in strict priority order (see source: `pick_dynamic_interpretation_label`). Examples include: `insufficient_dynamic_evidence`, `string_mixed_technique_heterogeneity`, `cross_family_masked_tonal_mass_risk`, `brass_projection_divergence_risk`, `clarinet_bright_projection_salience`, `cross_family_transparent_blend_potential`, `soft_brass_intra_family_convergence_potential`, `clarinet_soft_blend_potential`, `flute_soft_blend_potential`, `flute_moderate_projection_salience`, `double_reed_soft_blend_potential`, `double_reed_projection_salience`, `string_sectional_soft_blend`, `string_sectional_mass`, `percussion_dynamic_salience_insufficient_fusion_evidence`, `structural_homogeneity_dynamic_neutral`.

**dynamic_evidence_status** summarises how strong the symbolic evidence is for family-specific rules (`strong` / `moderate` / `insufficient`).

---

## 9) CSV output

Columns follow `homogeneity_analyser.analyzers.hti_export_rows.HTI_CSV_COLUMNS` (also importable from `analyzers.hti` for compatibility) (time, measure, **`pitch_interpretation_mode`**, **H_TI**, **H_TI_core**, uniformities, technique coverage, **register_proximity** (= **register_compactness**), **register_span_proximity**, **register_span_factor**, **pairwise_interval_proximity**, **register_pair_distance_factor**, **pairwise_interval_coverage_status**, **register_span_semitones**, **register_coverage_status**, dynamic fields, interpretive scalars, **`dynamic_interpretation_label`**, **`dynamic_evidence_status`**, optional interval-class / symbolic-blend columns when **`include_symbolic_blend_potential`** is enabled, optional acoustic-proxy columns when **`include_acoustic_proxy`** is enabled (including **`timbral_acoustic_affinity_evidence_status`**), JSON-encoded dict columns for distributions / `active_weights`).

**Register vs interval-class (orthogonal):** e.g. **C4–D4** can show **high** **register_compactness** yet **moderate** **interval_class_blend_factor** (bucket **`seconds_sevenths`** — mod‑12 second class only; check **`literal_interval_semitone_pair_mass`** for literal `"2"` semitones); **C4–C5** is typically **less** register-compact but **high** octave-class favourability; **C4–G4** is **fifth-favourable**; **C4–F♯4** is **tritone-unfavourable** in the symbolic mapping. These are **score-reading conventions**, not perceptual proof. Full key/display semantics: **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`**.

---

## 9b) Symbolic inspection (Loaded XML inspection)

The Gradio UI includes an accordion **Symbolic inspection (Loaded XML inspection)** below the shared upload and **H_TI** controls. On every upload **or pitch-interpretation mode** change, `ui/callbacks.run_loaded_xml_inspection` parses the score once via `services/score_audit.build_symbolic_inspection_tables`, which builds `TimbralHomogeneityAnalyzer` events (same notation pipeline as **H_TI_core**) and materialises three **pandas**/**Gradio Dataframe** tables plus UTF-8 CSV files: **`instrument_inventory.csv`**, **`event_audit.csv`**, **`vertical_sonorities.csv`**. No **H_TI** windowing run is required.

The Symbolic inspection report shows what the parser actually found in the uploaded score. It is intended to verify instrument mapping, sounding pitch, dynamics, techniques, articulations, effects, and vertical sonorities before interpreting **H_TI**. It is **diagnostic only** — not a metric, not part of **H_TI_core**, and not a revived legacy metric tab.

Stable column orders are `SCORE_AUDIT_INVENTORY_COLUMNS`, `SCORE_AUDIT_EVENT_COLUMNS`, and `SCORE_AUDIT_VERTICAL_COLUMNS` in `services/score_audit.py` (**Appendix D.13** lists every column name). The **event audit** expands chords to one row per sounding pitch and includes **`raw_xml_alter`**, **`accidental_text`**, **`effective_alter`**, **`effective_sounding_midi`**, transpose audit fields, **`pitch_interpretation_mode`**, **harmonic pitch fields** (`harmonic_state`, `harmonic_type`, `harmonic_pitch_role`, `harmonic_detection_source`, `harmonic_base_*`, `harmonic_touching_*`, `harmonic_touching_interval_semitones`, `harmonic_interval_rule_id`, `harmonic_sounding_*`, `harmonic_sounding_status`, `harmonic_pitch_policy`, `harmonic_warning`), and **`technique_harmonic_marker`** (technique-state `harmonic:…` fingerprint, distinct from pitch-harmonic columns). **Unpitched** percussion rows use **`unknown`** for written/sounding MIDI rather than invented concert pitches. **Active dynamic** uses the same parsed ladder as the timbral carrier when present; otherwise **`unknown`**. **Vertical sonorities** group rows by rounded `offset_quarterLength`, add **`harmonic_summary`** / **`harmonic_unresolved_count`**, and include register-span / compactness diagnostics from **`effective_sounding_midi`** / **`sounding_midi`** on each audit row (which reflect harmonic resolution only when status is **`explicit`** or **`inferred_common_artificial`**).

**Limitations:** MusicXML **exporter** differences affect techniques and dynamics; **MIDI** often lacks rich metadata; absent notation is **unknown**, not silently inferred; **no PDF/image** inference; **no audio analysis**.

---

## 9c) Gradio optional diagnostics (UI layout)

The **H_TI** parameter column in `ui/gradio_app.py` exposes three **orthogonal** optional layers (defaults **off**; none rescale **H_TI_core**):

| UI region | Parameter(s) | Exports (when enabled) |
|-----------|----------------|------------------------|
| Inline **timbral affinity relief** controls | `timbral_affinity_relief_factor`, `timbral_affinity_profile`, `dynamic_affinity_enabled`, optional pairwise export | **`H_TI_affinity_literature_relieved`**, timbral-affinity diagnostics — literature-governed **symbolic** relief, **not** **H_TA** |
| Accordion **Optional symbolic interval-class / blend-potential diagnostics** | `include_symbolic_blend_potential` | **`interval_class_blend_factor`**, **`symbolic_blend_potential`**, **`attack_compatibility_factor`**, … — **separate** from the acoustic proxy |
| Accordion **Acoustic-aligned symbolic timbral-affinity proxy** | `include_acoustic_proxy`, `acoustic_proxy_profile`, `acoustic_proxy_pairwise_export` | **`H_TA_acoustic_proxy`**, **`timbral_acoustic_affinity`**, evidence columns — see **`docs/H_TA_ACOUSTIC_PROXY.md`** |

**Symbolic inspection** is a fourth accordion (parser audit only; no homogeneity metric).

**Repository hygiene:** **Authoritative code** is only under **`src/homogeneity_analyser/`**. Generated **`build/`**, **`build/lib/`**, **`dist/`**, and **`*.egg-info/`** must not be edited or mistaken for the product tree (see **`docs/ARCHITECTURE.md`**).

---

## 10) JSON output

`build_hti_export` returns:

- `schema_version` **3.0** (H_TI bundle; constant `HTI_EXPORT_SCHEMA_VERSION` in `json_export.py`), `metric_kind: symbolic_timbral_instrumental_homogeneity`, `not_audio_analysis: true`, and a single root-level **`symbolic_homogeneity_scope_disclaimer`** string (same contract as `homogeneity_analyser.services.constants.SYMBOLIC_HOMOGENEITY_SCOPE_DISCLAIMER`).
- `parameters`, `active_weights_nominal`, `time_series` (full per-window rows), nested **`dynamic_conditioning`** (`model_scope`, `warning`, `dynamic_scale`, `family_rules_version`, slimmer `time_series`), `warnings`, `technique_model_version`.

| Identifier | Typical meaning | Authoritative symbol (Python) |
|------------|-----------------|-------------------------------|
| **Python package version** | setuptools / wheel release | `homogeneity_analyser.__version__` (**1.0.0** in `__init__.py`) |
| **H_TI JSON `schema_version`** | Breaking / additive evolution of the **H_TI** export shape | **`"3.0"`** (`HTI_EXPORT_SCHEMA_VERSION`) |
| **Combined / legacy JSON `schema_version`** | Older multi-metric bundles | **`"1.8"`** (`JSON_EXPORT_SCHEMA_VERSION` in `json_export.py`) |
| **Top-level JSON `model_version`** | Export wrapper / bundle semantics | `JSON_EXPORT_MODEL_VERSION` (**`"1.0"`**) |
| **`technique_model_version`** inside H_TI diagnostics | Technique-state + conditioning fingerprint | `TECHNIQUE_MODEL_VERSION` in `hti.py` (e.g. **`technique_state_id_v3_dynamic_conditioning`**) |
| **Nested timbral `timbral_semantic_model.model_version`** | Documentation submodule for legacy timbral semantics | `TIMBRAL_MODEL_SEMANTICS_VERSION` in `models/timbral_semantics.py` (only when nested timbral object emitted) |

### Why this is still symbolic (non-negotiable scope)

Nothing in the pipeline consumes microphone waveforms or claims validated perceptual fusion. **$H_{\mathrm{TI,core}}(t)$** remains a **notation-overlap** concentration statistic (instruments, taxonomy subfamilies, explicit technique buckets where encoded, and register compactness from **sounding MIDI** in the score). Optional layers—literature-conditioned timbral affinity relief, interval-class blend factors, attack-class compatibility, and enriched dynamic-conditioning scalars—are **explicitly labelled symbolic** or **literature-conditioned symbolic proxies**. They may borrow orchestration vocabulary (e.g. “blend potential”) only as **score-reading aids**, never as acoustic measurements.

### What changed and why: 2.8 governance refresh, retained through 3.0

| Topic | Change | Rationale |
|-------|--------|-----------|
| **Interval class** | Optional **`interval_class_blend_factor`** (alias **`pairwise_interval_blend_factor`**), **`interval_class_profile`** (+ **`interval_class_profile_display`**, **`literal_interval_semitone_pair_mass`**, **`chromatic_mod12_pair_mass`**), **`symbolic_blend_interval_profile`**, **`interval_class_evidence_status`** from `taxonomy/symbolic_blend_conditioning.json` | Separates **symbolic interval-class favourability** from **semitone-distance** **`pairwise_interval_proximity`** / **`register_pair_distance_factor`** used inside **`register_compactness`** / **`H_TI_core`** (unchanged). Key **`seconds_sevenths`** groups mod‑12 classes {1,2,10,11} and must not be read as “seconds and sevenths both occur in the excerpt.” |
| **Attack compatibility** | New optional **`attack_compatibility_factor`** and **`attack_class_distribution`** | Notation-derived **onset / envelope class** overlap heuristic for simultaneous events; **outside** **`H_TI_core`**. |
| **Families / registers** | Events expose **`clarinet_register_zone`** and **`brass_symbolic_blend_tendency`**; string harmonic vs ordinary bowing penalised in affinity identity rows | Clarifies register splits and prevents harmonics from collapsing to ordinary arco in pairwise symbolic affinity. |
| **Evidence governance** | Registry rows with **`source_key_only`** / **`needs_page_verification`** do **not** fire under **`strict`** / **`conservative`** affinity profiles; exports add **`literature_affinity_unverified_rule_blocked`** and richer pairwise provenance when affinity pairs are exported | Aligns firing rules with bibliography auditability; conservative profiles stay defensible. |

### What changed (2.9 register vs interval-class exports)

- **Explicit register columns:** **`register_span_factor`** and **`register_pair_distance_factor`** mirror **`register_span_proximity`** and **`pairwise_interval_proximity`** in CSV/JSON; **`register_compactness`** and **`H_TI_core`** are unchanged.
- **Interval-class naming:** **`interval_class_blend_factor`**, **`interval_class_profile`** (stable keys), **`interval_class_profile_display`** (prose labels), **`literal_interval_semitone_pair_mass`** / **`chromatic_mod12_pair_mass`** (pre-bucket diagnostics), **`interval_class_evidence_status`** (default **`symbolic_convention`**) document the orthogonal interval-class layer; **`pairwise_interval_blend_factor`** remains the same numeric value for backwards compatibility. See **`interval_class_semantics_note`** in `taxonomy/symbolic_blend_conditioning.json`.
- **Optional `symbolic_blend_potential`:** uses a **normalized geometric mean** of available **H_TI_core**, interval-class, attack-compatibility, and (when dynamic coverage is not **`unavailable`**) ordinal dynamic-conditioning factors. **`timbral_affinity_uniformity`** is retained only inside **`symbolic_blend_components`** for audit, not multiplied into the headline scalar.

### What changed (3.0 acoustic-proxy exports)

- **Optional `H_TA_acoustic_proxy` / `timbral_acoustic_affinity`:** event-level pairwise organology kernel when `include_acoustic_proxy` is true; default **off**. **`H_TI_core`**, **`H_TI`**, and **`H_TI_strict`** are **unchanged**. Not audio, FFT, SPL, or perceptually validated fusion — see **`docs/H_TA_ACOUSTIC_PROXY.md`**.
- **`timbral_acoustic_affinity_evidence_status`:** semicolon-separated tags derived from **`timbral_acoustic_affinity_components`** (authoritative for which kernel factors contributed) and window **`dynamic_coverage_status`** / **`technique_coverage_status`**. When the dynamic component is present and dynamics are explicit, status uses **`dynamic_used_explicit_notated`** or **`dynamic_active`** — not **`dynamic_omitted`**. When technique is applied at ~1.0 with uniform ordinary technique, status may use **`technique_default_only`** instead of **`technique_omitted_or_partial`**.

**Library-only** combined / fusion bundles emit **`schema_version` `1.8`** for the combined wrapper — see `JSON_EXPORT_SCHEMA_VERSION` in `json_export.py`.

**Two different `model_version` fields:** On every export document that still uses the **legacy combined** nesting, **top-level** **`model_version`** identifies the **JSON export bundle** (`JSON_EXPORT_MODEL_VERSION` in `json_export.py`). When present, the nested **`timbral`** object’s **`timbral_semantic_model.model_version`** identifies the **timbral semantics documentation** submodule (`TIMBRAL_MODEL_SEMANTICS_VERSION` in `timbral_semantics.py`). They answer different questions; do not merge them in downstream schemas without documenting both.

### Legacy combined JSON — `model_version` vs export wrapper

Some **combined** export payloads distinguish:

- **`model_version`** on nested **timbral** objects — ties to **`timbral_semantic_model`** / profile semantics.
- **`JSON_EXPORT_MODEL_VERSION`** — export wrapper version for the JSON document as a whole.

H_TI-only JSON does not reproduce the full combined nesting; the distinction matters only when calling **`build_combined_export`** from tests or programmatic batch tools.

---

## 11) Limitations

- **Exporter differences** — Dorico / Sibelius / MuseScore encode techniques and dynamics differently; missing MusicXML semantics cannot be recovered.
- **MIDI** often lacks rich part metadata — instrument and technique fidelity drop.
- **Dynamics are symbolic ordinals**, not loudness in dB; the model does **not** claim that **pp** “causes fusion” or **ff** “destroys fusion”.
- **Family rules** are **not** empirically calibrated predictions — they organise cautionary reading only.
- **Acoustic-informed profiles** (`acoustic_profiles/`) exist for **legacy** heuristic analysers still in the package; they are **not** used to claim measured fusion inside **H_TI_core**.

---

## 12) Bibliographic rationale (concise)

Qualitative reading of orchestration and dynamics draws on widely cited orchestration and acoustics texts — **Meyer** (performance acoustics), **Campbell / Gilbert / Myers** (brass science), **Benade** and **Fletcher & Rossing** (instrument acoustics), **Rossing** (string instrument science), and handbooks on musical acoustics. The implementation stays **notation-first**: the canonical machine-readable bibliography lives in **`src/homogeneity_analyser/acoustic_profiles/source_registry.json`** (also described in YAML for editors); citations there support **registry governance** for legacy heuristic code paths, not empirical fusion measurement in **H_TI_core**.

For **machine-readable** citation stubs mirrored for auditors, see **§19) Bibliography** below. For **canonical symbolic vocabularies** (instruments, families, techniques, dynamics, harmonics, pitch modes, and symbolic inspection CSV columns), see **Appendix D**.

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

## Appendix C — Algorithms (pseudocode)

Pseudocode mirrors control flow in source; it is **normative** only insofar as it matches the implementation.

### C.1) Full H_TI analysis pipeline (one score)

```
load score (MusicXML / MIDI) → validate (size, extension)
build TimbralHomogeneityAnalyzer / SymbolicTIHomogeneityAnalyzer events
resolve window_mode → window_size_effective, time_step_effective, edge_policy
centres ← build_hti_window_centers(excerpt_end, time_step_effective, window_size_effective, edge_policy)
for each centre t:
    geom ← hti_window_row_geometry(t, window_size, excerpt_start, excerpt_end, edge_policy)
    feats ← extract_hti_window(t, window_size)  # overlap masses, Herfindahls, register, dynamics
    h_strict, diag, active_weights ← compute_H_TI(feats, nominal weights…)
    optionally: H_TI_subfamily_relieved with instrument_effective uniformity blend
    optionally: timbral_affinity bundle → H_TI_affinity_literature_relieved
    attach_dynamic_conditioning_for_window(feats, h_strict, contrib, masses, pitches, span)
    finalize affinity dynamic qualifiers (interpretive only)
    append one time-series row (H_TI = H_TI_core = h_strict when feats present)
emit CSV / JSON via hti_export_rows.HTI_CSV_COLUMNS and build_hti_export
```

### C.2) Event overlap for one window

```
function overlap_ql(event, t_lo, t_hi):
    return max(0, min(event.end, t_hi) - max(event.offset, t_lo))
```

**Mathematical form (implementation-aligned):** with $z_e$ as **`event.end`** and $o_e$ as **`event.offset`**,


$$
\ell_e(t,w)=\max\Bigl(0,\,\min\Bigl(z_e,\,t+\tfrac{w}{2}\Bigr)-\max\Bigl(o_e,\,t-\tfrac{w}{2}\Bigr)\Bigr).
$$

### C.3) Component uniformities for one window

```
for each active event with overlap > 0:
    accumulate overlap into inst_mass[instrument], fam_mass[family], macro_mass[macrofamily( family )]
    tuk ← compute_technique_uniformity_key_from_event(event)
    if tuk non-empty: tech_mass[tuk] += overlap
    for each sounding pitch of event (unless unpitched-percussion skip):
        pitch_occurrences.append( (midi, overlap) )
instrument_uniformity ← Herfindahl(inst_mass)
family_uniformity ← Herfindahl(fam_mass)
macrofamily_uniformity ← Herfindahl(macro_mass)
(technique_uniformity, technique_coverage_status) ← policy in §2.3
register bundle ← compute_register_compactness_fields(pitch_occurrences, ref)
```

### C.4) Register compactness

```
if no pitch rows after unpitched filter:
    return NaNs, statuses unpitched_only
span ← max(midis) - min(midis)   # 0 if one pitch
R_span ← 1 / (1 + span/ref)
if n_pitch < 2:
    R_pair ← 1; status ← insufficient_pairs
else:
    R_pair ← weighted_mean_{i<j}( 1/(1+d_ij/ref), weights m_i*m_j )
R_compact ← sqrt( max(eps,R_span) * max(eps,R_pair) )
register_proximity ← R_compact
```

**Mathematical form:** with $\varepsilon=10^{-12}$ (`_EPS` in `hti.py`),


$$
R_{\mathrm{compact}}(t)=\sqrt{\max(\varepsilon,R_{\mathrm{span}}(t))\cdot\max(\varepsilon,R_{\mathrm{pair}}(t))}.
$$

The export alias satisfies $R_{\mathrm{prox}}(t)=R_{\mathrm{compact}}(t)$.

### C.5) H_TI_core weighted geometric mean

```
active ← {instrument_uniformity, family_uniformity}
if technique admitted: active += technique_uniformity
if register pitched:     active += register_proximity
renormalise weights on active keys only
return exp( sum_c w'_c * log(max(eps, x_c)) ), clipped to [0,1]
```

**Mathematical form:** with $\tilde w_c$ as in §2.5,


$$
H_{\mathrm{TI},\mathrm{core}}(t)=\exp\Bigl(\sum_{c\in C_t}\tilde w_c\ln\max\bigl(\varepsilon,x_c(t)\bigr)\Bigr).
$$

The implementation clips this value to $\left[0,\,1\right]$.

### C.6) Adaptive window resolution

```
if manual: effective sizes ← user inputs
elif auto_by_excerpt_duration:
    w ← clip(D*window_ratio, min_window_size, max_window_size)
    dt ← clip(D*step_ratio, min_time_step, max_time_step)
elif auto_by_target_windows:
    dt ← clip(D/target_window_count, min_time_step, max_time_step)
    w ← clip(dt*window_to_step_ratio, min_window_size, max_window_size)
validate edge_policy ∈ {include_partial_windows, drop_partial_windows, mark_partial_windows}
```

**Mathematical form:** with $\mathrm{clip}$ as in §2.10, the adaptive branch matches $w_{\mathrm{eff}}$ and $s_{\mathrm{eff}}$ given there.

### C.7) Harmonic pitch resolution (per note)

```
interpret_note_sounding_pitch_ps_list → base metas + pits
policy ← normalize_harmonic_pitch_policy(user)
if two-pitch artificial chord path matches: apply inferred_common_artificial to all tones; return
for each tone index:
    merge harmonic bundle from MusicXML StringHarmonic / notehead heuristics / policies
    if status in {explicit, inferred_common_artificial} and apply_ps finite:
        overwrite effective_sounding_midi and pits[i]
    else: leave pre-harmonic sounding MIDI (unresolved does not remap)
```

### C.8) Symbolic inspection tables

```
analyzer ← TimbralHomogeneityAnalyzer(score, pitch_interpretation_mode, harmonic_pitch_policy)
events ← flatten_timbral_events(analyzer)
inventory ← per-part taxonomy + counts from events
vertical ← group events by round(offset_quarterLength); aggregate dynamics, techniques, register diagnostics
return (inventory, events, vertical)
```

---

## 19) Bibliography

Canonical machine-readable records live in **`src/homogeneity_analyser/acoustic_profiles/source_registry.json`**. Each subsection heading is the `source_key` string used in `default_profiles.json` and in diagnostics.

**Page placeholders (development / audit):** Many literature rows still list **`pages_consulted: PAGE_REQUIRED_DO_NOT_RELEASE`** in JSON until a maintainer records verified pagination from a held copy. Those subsections are **mirrored verbatim** here so auditors can diff registry ↔ manual. They are **not** offered as page-grounded evidence for **release-governed** numeric binds (`get_acoustic_model_governed_source_keys()` is currently empty). **README.md** and **QUICK_REFERENCE.md** intentionally omit the raw sentinel string; this **§19** section and `docs/bibliography/ACOUSTIC_SOURCE_REGISTRY.md` carry the honest pending state for developers.

### `sivian_dunn_white_1931_absolute_amplitudes_spectra`

- **Citation line:** Sivian, L. J.; Dunn, H. K.; White, S. D. (1931). *Absolute Amplitudes and Spectra of Certain Musical Instruments and Orchestras*. The Journal of the Acoustical Society of America.
- **Publisher:** Acoustical Society of America (AIP Publishing)
- **Volume / issue:** 2, no. 3
- **Article page span (metadata):** 330-371
- **DOI / URL:** https://doi.org/10.1121/1.1915260
- **Pages used in this project (`pages_consulted`):** 330-371 (journal pagination; verify scan numbering before citing as PDF page numbers)
- **Private PDF basename (consultation only; not redistributed):** `ABSOLUTE AMPLITUDES AND SPECTRA OF CERTAIN MUSICAL INSTRUMENTS AND ORCHESTRAS.pdf`
- **Evidence type:** `measured_acoustic_data`; **reliability:** `high`

### `physical_correlates_brass_instrument_tones_pending`

- **Citation line:** Unverified from this repository (open private PDF title page to curate). *Physical Correlates of Brass-Instrument Tones*. Peer-reviewed article (venue to be confirmed from document).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Physical Correlates of Brass-Instrument Tones.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `low`

### `campbell_gilbert_myers_2021_science_of_brass_instruments`

- **Citation line:** Campbell, Murray; Gilbert, Joël; Myers, Arnold (2021). *The Science of Brass Instruments*. Springer Nature (Modern Acoustics and Signal Processing).
- **Publisher:** Springer
- **Edition note:** 1
- **DOI / URL:** https://doi.org/10.1007/978-3-030-55686-0
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Campbel, Murray_The Science of Brass Instruments.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `high`

### `meyer_acoustics_performance_of_music`

- **Citation line:** Meyer, Jürgen (2009). *Acoustics and the Performance of Music*. Book (English-language reference edition; verify imprint against held copy).
- **Publisher:** Springer / Focal (imprint varies by edition; verify)
- **Edition note:** Verify against held copy
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `IMP_Acoustics and the Performance of music_(Jürgen Meyer) (z-lib.org).pdf`
- **Evidence type:** `orchestration_performance_acoustics`; **reliability:** `medium`

### `fletcher_rossing_1998_physics_of_musical_instruments`

- **Citation line:** Fletcher, Neville H.; Rossing, Thomas D. (1998). *The Physics of Musical Instruments*. Springer-Verlag New York (2nd ed. commonly catalogued).
- **Publisher:** Springer
- **Edition note:** 2
- **DOI / URL:** https://doi.org/10.1007/978-0-387-21603-4
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `The_Physics_of_Musical_Instruments.pdf`
- **Evidence type:** `theoretical_acoustics`; **reliability:** `high`

### `rossing_2010_science_of_string_instruments`

- **Citation line:** Rossing, Thomas D. (editor); multiple contributors (2010). *The Science of String Instruments*. Springer Science+Business Media.
- **Publisher:** Springer
- **Edition note:** 1
- **DOI / URL:** https://doi.org/10.1007/978-1-4419-7110-4
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Thomas D. Rossing_The Science of String Instruments.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `high`

### `rossing_et_al_science_of_sound_pearson`

- **Citation line:** Rossing, Thomas D.; Wheeler, Paul A.; Fahy, Frank (editions vary) (2014). *Science of Sound (Pearson international edition; title varies by printing)*. Pearson Education (international editions catalogued under similar titles).
- **Publisher:** Pearson
- **Edition note:** Verify printing (e.g., 4th or New International Edition)
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `IMP_The-Science-of-Sound-Pearson-New-International-Edition-by-Thomas-1.pdf`
- **Evidence type:** `psychoacoustics`; **reliability:** `medium`

### `benade_1976_fundamentals_musical_acoustics`

- **Citation line:** Benade, Arthur H. (1976). *Fundamentals of Musical Acoustics*. Oxford University Press.
- **Publisher:** Oxford University Press
- **Edition note:** 1
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Fundamentals of Musical Acoustics -- Benade.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `high`

### `analysis_musical_instrument_tones_pending`

- **Citation line:** Unverified (see PDF title page). *Analysis of Musical Instrument Tones (exact title per document)*. Article or chapter (venue pending curation).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `IMP_Analysis of Musical Instrument Tones.pdf`
- **Evidence type:** `signal_analysis`; **reliability:** `low`

### `campbell_acoustics_musical_instruments_pending`

- **Citation line:** Campbell, M. (initials/affiliation unverified in registry). *Acoustics of Musical Instruments (exact title per document)*. Monograph or proceedings (verify imprint).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `IMP_CAMPBELL-M-Acoustics-of-Musical-Instruments.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `low`

### `discrimination_musical_instrument_sounds_pending`

- **Citation line:** Unverified (see PDF title page). *Discrimination of musical instrument sounds (exact title per document)*. Peer-reviewed article (venue pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `IMP_Discrimination of musical instrument sounds r.pdf`
- **Evidence type:** `psychoacoustics`; **reliability:** `low`

### `fixed_average_spectra_orchestral_instrument_tones_pending`

- **Citation line:** Unverified (see PDF title page). *Fixed Average Spectra of Orchestral Instrument Tones*. Peer-reviewed article (venue pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `IMP_Fixed Average Spectra of Orchestral Instrument Tones.pdf`
- **Evidence type:** `measured_acoustic_data`; **reliability:** `medium`

### `sound_power_timbre_dynamic_strength_orchestral_pending`

- **Citation line:** Unverified (see PDF title page). *Sound power and timbre as cues for the dynamic strength of orchestral instruments*. Peer-reviewed article (venue pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `IMP_Sound power and timbre as cues for the dynamic strength of orchestral instruments.pdf`
- **Evidence type:** `orchestration_performance_acoustics`; **reliability:** `medium`

### `statistical_analysis_musical_instruments_pending`

- **Citation line:** Unverified (see PDF title page). *Statistical Analysis of Musical Instruments (exact title per document)*. Article or report (venue pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `IMPPPP_Statistical Analysis of Musical Instruments.pdf`
- **Evidence type:** `signal_analysis`; **reliability:** `low`

### `index_relative_quality_musical_instruments_pending`

- **Citation line:** Unverified (see PDF title page). *Index for the Relative Quality among Musical Instruments*. Unknown venue (curate from document).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Index for the Relative Quality among Musical Instruments.pdf`
- **Evidence type:** `instrument_classification`; **reliability:** `low`

### `musical_instrument_timbres_classification_spectral_pending`

- **Citation line:** Unverified (see PDF title page). *Musical Instrument Timbres Classification with Spectral Features*. Conference or journal (pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Musical Instrument Timbres Classification with Spectral Features.pdf`
- **Evidence type:** `instrument_classification`; **reliability:** `medium`

### `musical_instrument_classification_higher_order_spectra_pending`

- **Citation line:** Unverified (see PDF title page). *Musical instrument classification using higher order spectra*. Conference or journal (pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Musical_instrument_classification_using_higher_order_spectra.pdf`
- **Evidence type:** `instrument_classification`; **reliability:** `medium`

### `relevance_spectral_features_instrument_classification_pending`

- **Citation line:** Unverified (see PDF title page). *On the relevance of spectral features for instrument classification*. Conference or journal (pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `On the relevance of spectral features for instrument classification.pdf`
- **Evidence type:** `spectral_features`; **reliability:** `medium`

### `science_percussion_instruments_pending`

- **Citation line:** Unverified (see PDF title page). *Science of Percussion Instruments*. Book or monograph (pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Science of Percussion Instruments.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `medium`

### `sound_production_double_reed_pending`

- **Citation line:** Unverified (see PDF title page). *Sound Production Analysis of a Double Reed Instrument*. Thesis or article (pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Sound_Production_Analysis_of_a_Double_Reed_Instrument.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `low`

### `statistical_study_spectral_parameters_pending`

- **Citation line:** Unverified (see PDF title page). *Statistical study of spectral parameters in musical instrument (full title per PDF)*. Peer-reviewed article (pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Statistical study of spectral parameters in musical instrument.pdf`
- **Evidence type:** `spectral_features`; **reliability:** `low`

### `clarinet_spectrum_theory_experiment_pending`

- **Citation line:** Unverified (see PDF title page). *The clarinet spectrum: theory and experiment (punctuation per PDF)*. Peer-reviewed article (pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `The clarinet spectrum Theory and experiment.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `medium`

### `tonal_spectra_wind_instruments_pending`

- **Citation line:** Unverified (see PDF title page). *Tonal Spectra of Wind Instruments*. Peer-reviewed article (pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Tonal Spectra of Wind Instruments.pdf`
- **Evidence type:** `measured_acoustic_data`; **reliability:** `medium`

### `viola_tonnerre_pending`

- **Citation line:** Unverified (see PDF title page). *Viola Tonnerre (exact title per PDF)*. Unknown venue (likely French-language; pending).
- **Pages used in this project (`pages_consulted`):** PAGE_REQUIRED_DO_NOT_RELEASE
- **Private PDF basename (consultation only; not redistributed):** `Viola_Tonnerre.pdf`
- **Evidence type:** `musical_instrument_acoustics`; **reliability:** `low`

### `homogeneity_analyser_timbral_fusion_evidence_stub`

- **Citation line:** Homogeneity Analyser project (2026). *Internal evidence map for symbolic timbral and planned fusion layers*. Project documentation (this repository).
- **Pages used in this project (`pages_consulted`):** N/A (project documentation; no private PDF)
- **Evidence type:** `project_specific`; **reliability:** `medium`

### `same_family_relief_rationale_sources`

- **Citation line:** Homogeneity Analyser project (2026). *Bibliographic cluster for H_notated_fusion_potential same-family relief calibration*. Synthetic registry grouping (this repository).
- **Pages used in this project (`pages_consulted`):** N/A (metadata group; consult individual `source_key` rows and `docs/archive_legacy/model_audit/H_NOTATED_FUSION_POTENTIAL_JUSTIFICATION.md`)
- **Evidence type:** `project_specific`; **reliability:** `medium`
