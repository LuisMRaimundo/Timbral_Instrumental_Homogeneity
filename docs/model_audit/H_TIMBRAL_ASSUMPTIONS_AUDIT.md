# H_timbral — Assumptions and Hard-Coded Constants Audit

> **Legacy / internal audit** — constants and rules still affect the **shared timbral event pipeline** used by **H_TI_core**; this file is **not** part of the current user-facing workflow description.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

**Scope:** Symbolic **H_timbral** only (notation-derived orchestration / register / technique homogeneity).  
**Purpose:** Inventory every **hard-coded** acoustic-inspired, instrumental, family-wise, register-wise, and technique-wise **constant or rule** that can move the scalar **H_timbral** or its diagnostics **without** changing pitch clusters.  
**Non-goals:** This document does **not** restate full formulas from `TECHNICAL_MANUAL.md` §1c.8; it points to **code** and classifies **policy**.

**Classification legend**

| Tag | Meaning |
|-----|---------|
| **(a)** | **Symbolic classification** — discrete labels from notation / taxonomy (no claim of measured spectrum). |
| **(b)** | **Acoustic-inspired heuristic** — numeric shape inspired by timbre/register overlap metaphors, **not** fitted to audio data in this repo. |
| **(c)** | **Empirical / project-specific** — tuned matrix weights, thresholds, or blends chosen for stability and tests. |
| **(d)** | **Undocumented elsewhere** — not described in `TECHNICAL_MANUAL.md` / family `docs/H_TIMBRAL_*.md` at the time of this audit (only in code comments or nowhere). |

**Pitch-cluster invariance:** “Otherwise identical pitch clusters” means **same concert MIDI ps per note event** after `sounding_pitch_ps_list`. Many rows below **still change H_timbral** because they depend on **instrument name**, **family**, **part layout**, **technique_state_id**, or **overlap mass weighting** — not on pitch alone.

---

## 1. Core pipeline — `analyzers/timbral.py`

| Constant / rule | Value | Affected scope | Mathematical effect | Tag | Notes |
|-----------------|-------|----------------|------------------------|-----|-------|
| `_DEFAULT_WEIGHT_INSTRUMENT` | `0.65` | All | Weight on final **instrument axis** (after pairwise + technique + cross boost) vs register. | (c) | Duplicated in `taxonomy/instrument_taxonomy._DEFAULT_TIMBRAL_CONFIG`. |
| `_DEFAULT_WEIGHT_REGISTER` | `0.35` | All | Weight on **global** register component. | (c) | Same. |
| `_DEFAULT_FAMILY_BONUS` | `0.65` | Same-family, multi-instrument | Legacy factor when `n_families == 1` and `n_instruments > 1`. | (c) | Documented in manual §1c.8 narrative. |
| `_DEFAULT_REGISTER_REF_SEMITONES` | `3.0` | Register term | Divisor in `1 / (1 + span/ref)` for **global** span. | (c) | Manual §1c.8. |
| `_REGISTER_GLOBAL_DAMPEN_FOR_PAIRWISE_COVERAGE` | `0.12` | Register term when specialist families present | `register_component *= 1 - 0.12 * coverage` with `coverage = min(1, sum specialist masses / total_mass)`; percussion mass **excluded** from specialist sum. | (d) | Comment in code; **not** in TECHNICAL_MANUAL formula block as a numeric coefficient. |
| Legacy `n_instruments == 1` | `legacy_instr = 1.0` | Single canonical instrument | Sets baseline instrument factor before pairwise blend. | (a)+(c) | Count is **distinct canonical** names in window. |
| Legacy `n_families == 1`, `n_instruments > 1` | `legacy_instr = family_bonus` | Same family, multiple canonical instruments | Strong floor for “section” scoring. | (c) | Explains clarinet + bass clarinet vs four identical clarinets (see §6). |
| Legacy multi-family | `1 / (1 + (n_instr - 1))` | Multi-family windows | Harmonic-style penalty on instrument count. | (c) | Documented in manual. |
| `technique_component` | `0.18 + 0.82 * conc` | All windows with notes | Multiplies **already pairwise-refined** `instr_pairwise` before cross boost. `conc` = Herfindahl on `technique_state_id` masses. | (c)+(d) | **0.18 / 0.82** not spelled out in TECHNICAL_MANUAL §1c.8 (qualitative “concentration” only). |
| `instr_final` | `clip(instr_after_tech + cross_boost, 0, 1)` | Cross-family pairs in registry | Additive capped boost from `timbre_cross_relations`. | (c) | `_MAX_ADDITIVE_CROSS_BOOST` in cross module. |
| Empty / invalid features | `H_timbral = 0.5` | Silent / no features | Neutral output. | (c) | Documented as neutral silence behaviour. |
| Pairwise blend `F` | `min(1, sum_k m_k / M_total)` | Family branches | `(1-F)*legacy + F*h_bar`. | (c) | In-code docstring; aligns with manual narrative. |
| Branch `<2` events | use `legacy_instr` for that branch | Sparse family slice | Avoids `pairwise_*` returning `1.0` vacuously dominating. | (c) | `timbral.py` `_combine_family_pairwise_homogeneity_detail`. |
| Percussion-heavy register override | `pm/tot >= 0.88` **and** `pun/tot >= 0.72` | Mostly unpitched percussion | Blend global register with `unpitched_percussion_register_proxy`; `w_blend = clip((pun/tot)*(pm/tot)*1.12, 0, 1)`. | (d) | Thresholds **0.88**, **0.72**, scale **1.12** are code-only. |
| `1e-12`, `1e-15` | numeric guards | All | Avoid division by zero in mass ratios. | (c) | Implementation detail. |

**Module:** `TimbralHomogeneityAnalyzer` — event construction uses `notation_text_context_for_note(..., measure_text="none")` while family technique helpers may use `measure_text="prior"` (see `notation_context.py`); **policy** (a)/(c) for *what text attaches to which note*.

---

## 2. Taxonomy defaults — `taxonomy/instrument_taxonomy.py`

| Constant | Value | Effect | Tag |
|----------|-------|--------|-----|
| `_DEFAULT_TIMBRAL_CONFIG["weight_instrument"]` | `0.65` | Global default until overridden | (c) |
| `_DEFAULT_TIMBRAL_CONFIG["weight_register"]` | `0.35` | | (c) |
| `_DEFAULT_TIMBRAL_CONFIG["family_bonus"]` | `0.65` | Clamped to `[0,1]` on `set_timbral_config` | (c) |
| `_DEFAULT_TIMBRAL_CONFIG["register_ref_semitones"]` | `3.0` | | (c) |
| Alias tables `_CANONICAL_INSTRUMENTS`, `_INSTRUMENT_MAP`, `_sorted_keys`, `_alias_matches` | (large) | **Which raw part name maps to which canonical + family** — changes H_timbral if exporter renames part. | (a)+(c) |
| Unknown fallback | `("unknown", FAMILY_OTHER)` | Weak family / instrument identity | (a) |

---

## 3. Technique timeline and concentration — `analyzers/technique_state.py`

| Constant / rule | Value / behaviour | Effect | Tag |
|-----------------|-------------------|--------|-----|
| `TechniqueState` field defaults | e.g. `primary="ordinary"`, `mute="none"`, … | Baseline state before merge | (a) |
| `technique_state_id` construction | family-specific string concatenation | Buckets for **Herfindahl** concentration | (a) |
| Brass branch: open if no other tags | appends `"open"` when only one part | Forces distinct ids open vs stopped | (c) |
| `technique_state_similarity` cross-family | returns **`0.55`** if `a.family != b.family` | **Pan-family state similarity** (rarely used in pairwise paths that already filter by family) | (d) |
| `_string_state_similarity` sub-scores | e.g. pizz↔arco **`0.12`**, contact mismatch **`0.72`**, mute diff **`0.25`**, harmonic mismatch **`0.5`**, pressure **`0.65`**, trem off **`0.82`** | Product of factors caps string **state** similarity | (c)+(d) | Many coefficients **not** duplicated in TECHNICAL_MANUAL. |
| `_brass_state_similarity` | delegates to `brass_technique_similarity` + flutter adj **`0.88`** | Brass state similarity | (c) |
| Winds generic branch | `0.85` if same `primary`; `0.35` if both in `{ordinario, unknown}` else `0.45` | Flute/clarinet/oboe/bassoon/sax when not in string/brass special paths | (d) |
| Percussion branch | `0.7` if all dims match else `0.4` | Coarse percussion state similarity | (d) |
| Default other | `0.75` / `0.5` by primary equality | Fallback | (d) |
| `timbral_state_concentration_from_distribution` | `sum (p_i^2)` | **Herfindahl** on overlap mass by `technique_state_id` | (b)+(c) | Maps to “how split is playing state”. |
| `merge_note_technique_state` / `TechniqueStateContext` | music21 articulation hooks | Which symbols flip stopped / pizz / harmonic / wind harmonic | (a)+(c) |

---

## 4. Sounding pitch — `analyzers/timbral_sounding_pitch.py`

| Rule | Effect | Tag |
|-------|--------|-----|
| Transposition / concert pitch resolution per part | Register span and all pairwise **pitch** inputs use **concert** `ps` where available | (a) | Documented in `docs/H_TIMBRAL_SCORE_REPRESENTATION.md`. |
| Fallbacks when transposition unknown | May differ by instrument; affects span and tessitura gates | (c) | See same doc. |

---

## 5. Pairwise family modules (matrices and tessitura)

All pairwise modules use **overlap-weighted** mean of **products** of (at least) **section/subtype similarity × register similarity × technique similarity** unless noted. Constants below are **(b)/(c)** unless they only relabel symbols (**(a)**).

### 5.1 `analyzers/string_pairwise_timbral.py`

| Name | Values | Instruments | Effect |
|------|--------|-------------|--------|
| `BOWED_ORCHESTRAL_STRINGS` | violin, viola, cello, double bass | Only these enter string pairwise | (a) |
| `_SECTION_SIM` | 4×4 matrix (e.g. violin–cello **0.68**, violin–bass **0.50**, cello–bass **0.90**) | Section × section | (c) |
| `section_similarity` default | **`0.35`** if pair not in matrix | Unknown pair fallback | (d) |
| `register_similarity_pitch` | `exp(-|Δps|/tau)`, default `tau=7.5` | Register proximity in semitones | (b)+(c) |
| `_TECH_MAT` | 8×8 technique matrix (arco, trem, sul pont, …) | String technique labels | (c) | See file for full grid. |
| `blend_string_and_legacy_instrument_component` | `f = string_mass/total` | Strings mixed with non-strings | Linear mix pairwise vs legacy | (c) | **Exported** to other families as `_blend_overlap_timbral_component`. |

**Multistate path:** uses `technique_state_similarity` (product-style string state factors) instead of `_TECH_MAT` when `technique_state` dict present on events.

### 5.2 `analyzers/brass_pairwise_timbral.py`

| Name | Values | Effect |
|------|--------|--------|
| `_BRASS_INST_TO_SECTION` | maps canonicals to section index 0–4 | Section similarity matrix |
| `_TESS_BOUNDS` | MIDI-ish ranges per section | `_norm_height`, `_tessitura_zone` |
| `_SECTION_SIM` | 5×5 (e.g. trumpet–horn **0.72**, trombone–bass trombone **0.92**) | |
| `_TECH_MAT` | 10×10 brass techniques (open/stopped/cup/…; **stopped–open 0.15**) | Strong dissimilarity stopped vs open |
| `brass_register_similarity` | same section: `(1,0.88,0.62,0.42)` by zone distance; mix **`0.78/0.22`**; cross-section **`0.52/0.48`** with `exp(-|Δ|/36)` / `22` | Tessitura | (c)+(d) | Zone count **4**, coefficients in code only. |

### 5.3 `analyzers/clarinet_pairwise_timbral.py`

| Name | Values | Effect |
|------|--------|--------|
| `_CLAR_INST_TO_IDX` | subtype index | Drives `_SUBTYPE_SIM` |
| `_CLAR_TESS_BOUNDS` | per-subtype MIDI ranges | Height + register zones |
| `_SUBTYPE_SIM` | 10×10 (e.g. B♭ clar ↔ bass clar **0.52**, E♭ row **0.28** to B♭) | **Penalises** mixed clarinet choir vs uniform subtype |
| `_TECH_MAT` | 7×7 clarinet techniques | |
| `_register_zone` thresholds | soprano-line: `<66` chalumeau, `<80` clarion, else altissimo; others use `t*3` thirds | Discrete register buckets | (c)+(d) |
| `clarinet_register_similarity` | same subtype: `0.8*sim_z + 0.2*exp(-|Δ|/28)`; cross: `0.55*align + 0.45*exp(-|Δ|/22)` | | (d) |

### 5.4 `analyzers/flute_pairwise_timbral.py`, `double_reed_pairwise_timbral.py`, `saxophone_pairwise_timbral.py`

Each defines analogous **`_INST` / `_TESS` / `_SECTION` or subtype matrices**, **`_TECH_MAT`**, register decay exponents, and **oboe–bassoon macro** handling in double reeds (see file + `docs/H_TIMBRAL_DOUBLE_REEDS.md`). All numeric cells are **(c)**; oboe–bassoon policy is **(a)+(c)** with bibliography notes in `docs/H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md`.

### 5.5 `analyzers/percussion_pairwise_timbral.py`

| Name | Role | Tag |
|------|------|-----|
| `_MACRO_CROSS` | 8×8 macro-class similarity (symmetrised, diagonal 1) | (c) |
| `_SAME_MACRO_DEFAULT` | per-class same-macro default | (c) |
| `_INSTRUMENT_PAIR` | pairwise overrides (e.g. bass drum–tom **0.95**) | (c) |
| `unpitched_percussion_register_proxy` | (function) | Proxy register when global span excluded | (b)+(c) | See `docs/H_TIMBRAL_PERCUSSION.md`. |

---

## 6. Cross-family additive layer — `analyzers/timbre_cross_relations.py`

| Constant | Value | Effect | Tag |
|----------|-------|--------|-----|
| `_MAX_ADDITIVE_CROSS_BOOST` | `0.068` | Cap on sum of boosts | (c) | Mentioned in module doc; not in main manual table. |
| `_ST_TENOR_SAX_CLARINET` | `0.14` | etc. | (c) | Each relation gated by instrument + MIDI band (see functions `_tenor_sax_clarinet_strength`, …). |
| `_SOPRANO_CLARINET_FOR_CROSS` | frozenset of four canonicals | Restricts which clarinets participate in **high clarinet ↔ flute** and tenor sax rules | (a)+(c) |

Tessitura gates (e.g. `56–84`, `|Δ|<=26`) are **(b)+(d)** — documented only in code + `H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md`.

---

## 7. Family-specific technique labelers

Modules: `string_technique.py`, `brass_technique.py`, `flute_technique.py`, `clarinet_technique.py`, `double_reed_technique.py`, `saxophone_technique.py`, `percussion_technique.py`, `percussion_ontology.py`.

**Assumption:** Keyword / articulation → discrete **bucket** string feeding matrices or `TechniqueState`. Mostly **(a)** symbolic; keyword lists and default buckets **(c)** project-specific; incomplete coverage **(d)** relative to “all engraved techniques” (acknowledged in TECHNICAL_MANUAL §1d).

---

## 8. Services and UI (no formula change in analyzer, but defaults affect runs)

| Location | What | Tag |
|----------|------|-----|
| `services/constants.py` `DEFAULT_TIMBRAL_PARAMS` | `time_step`, `window_size`, `timbral_config=None` | (c) |
| `services/param_validation.py` | Validates timbral overrides against `get_timbral_config()` keys | (a) |
| `services/json_export.py` | `TIMBRAL_HOMOGENEITY_NOTE`, `_h_timbral_effective_parameters` reflection | (a) — documentation payload only |
| `services/analysis_service.py` | Wiring, summaries, diagnostics keys | (a) |
| `ui/callbacks.py` / `ui/gradio_app.py` | Default Gradio numbers for timbral optional weights (`0.65`, `0.35`, …) | (c) | Must match taxonomy defaults for UX consistency. |

---

## 9. Tests as specification anchors

Files such as `tests/test_string_timbral.py`, `test_brass_timbral.py`, `test_clarinet_timbral.py`, … lock many matrix entries and edge behaviours. Those expectations are **(c)** project contracts; changing matrices without updating tests is intentionally guarded.

---

## 10. Explicit answers to comparison questions (policy, not audio truth)

### 10.1 Why might **four stopped horns** yield **higher H_timbral** than **four arco violins** on the **same** B3–C4–C#4–D4 cluster?

Contributing factors **in the current code** (any subset may dominate a window):

1. **Distinct canonical instrument count (`n_instruments`).**  
   Four horn parts that all normalise to canonical **`horn`** give **`n_instruments == 1`** → legacy instrument factor **`1.0`**.  
   Four string parts mapped to **violin, viola, cello, double bass** give **`n_instruments == 4`** with **one family** → legacy factor equals **`family_bonus` (0.65)** before pairwise refinement. **Same pitches, different orchestration labels** → different legacy baseline. **Tag:** (a) taxonomy + (c) legacy rule.

2. **String pairwise `section_similarity`.**  
   Violin–cello / violin–bass pairs use **< 1** off-diagonal section similarities (`_SECTION_SIM`), lowering overlap-weighted pairwise product even when all arco. Horns share one **brass section index** (all `horn`) → **brass section self-similarity 1.0**. **Tag:** (c).

3. **Brass vs string technique matrices.**  
   Stopped–stopped uses high diagonal similarity in `_TECH_MAT`; arco–arco is high for strings but multiplied by **section** and **register_similarity_pitch` with `tau=7.5`**. Spreads across Vn/Va/Vc/Vb registers still decay. **Tag:** (b)+(c).

4. **`technique_component` and `technique_state_id` bucketing.**  
   If horn states collapse to a **single** `technique_state_id` mass, `conc=1` → `technique_component=1`. If string states split (e.g. bow lane + contact micro-differences), `conc<1` → **extra down-weight** on `instr_pairwise`. **Tag:** (c) + notation parsing (a).

This is **not** a claim that stopped horns are acoustically “more homogeneous” than arco strings; it is the **concatenation of symbolic counting rules and fixed matrices**.

### 10.2 Why are **three B♭ clarinets + one bass clarinet** penalised vs **four identical** clarinets?

1. **Legacy same-family rule:** `n_instruments == 2` still yields `legacy_instr = family_bonus = 0.65` (same as any multi-instrument single-family window) **vs** `1.0` when all events share one canonical.  
2. **Clarinet subtype matrix `_SUBTYPE_SIM`:** B♭ clarinet index vs bass clarinet index gives **off-diagonal similarity < 1** (see matrix row/col in file — e.g. **0.52** in the shipped matrix for that pair). Pairwise average **drops** relative to four identical B♭ clarinets. **Tag:** (c).  
3. **Register zone logic** differs by subtype (`_register_zone`, `_CLAR_TESS_BOUNDS`), so identical MIDI clusters can still score different **register_similarity** if instruments differ. **Tag:** (b)+(c).

### 10.3 Does **technique concentration** double-penalise **instrument** mixtures?

**Partially yes, by construction:**

- **Pairwise family models** already multiply in **technique** (via `timbral_event_technique_pair_similarity` → `TechniqueState` or discrete matrix) for many branches (e.g. brass, strings multistate).
- After blending pairwise branches, the pipeline sets  
  `instr_after_tech = clip(instr_pairwise * (0.18 + 0.82 * conc), 0, 1)`  
  where `conc` is the **Herfindahl** of overlap mass over **`technique_state_id`**.

So **technique spread** reduces the instrument axis **again**, on top of pairwise technique factors. That is **not** the same as “instrument mixture” alone: a **single** instrument with **many** simultaneous technique ids (mixed playing states) also lowers `conc`. **Tag:** (c) **composition choice**; the **0.18 / 0.82** split is **(d)** in the main technical manual.

---

## 11. Undocumented-in-manual summary (high signal)

The following are **meaningful for results** but **not** carried as explicit numeric policy in `TECHNICAL_MANUAL.md` §1c.8 prose/table (they appear in **code** and/or family docs only):

- `timbral.py`: `_REGISTER_GLOBAL_DAMPEN_FOR_PAIRWISE_COVERAGE`, percussion override thresholds **`0.88` / `0.72` / `1.12`**, **`technique_component = 0.18 + 0.82*conc`**.
- `technique_state.py`: wind / percussion / cross-family similarity **fallback constants**; many **`_string_state_similarity`** scalars.
- All pairwise modules: full **matrix cells**, tessitura **zone counts**, and **`exp(-|Δ|/σ)`** denominators (e.g. brass `36` / `22`, clarinet `28` / `22`, string `tau=7.5`).
- `timbre_cross_relations.py`: MIDI band gates and `_MAX_ADDITIVE_CROSS_BOOST`.
- `percussion_pairwise_timbral.py`: macro cross matrix and instrument-pair overrides.

---

## 12. Change control

- **This audit:** documentation only (`docs/model_audit/H_TIMBRAL_ASSUMPTIONS_AUDIT.md`).
- **Analyzers / formulas:** unchanged at the time of writing.
- **Tests:** unchanged; numerical regression remains defined by existing test suite.

---

*Generated as a static code audit. When constants move, update this file alongside `TECHNICAL_MANUAL.md` §1c.8 or the relevant `docs/H_TIMBRAL_*.md` note.*
