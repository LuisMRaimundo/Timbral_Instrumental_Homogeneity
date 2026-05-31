# Symbolic interval-class layer (optional)

Optional diagnostics when **`include_symbolic_blend_potential`** is enabled (`symbolic_blend_layers.py`, weights in `taxonomy/symbolic_blend_conditioning.json`). They are **orthogonal** to **`register_compactness`** and **`H_TI_core`**, which use **absolute semitone distance**, not mod‑12 interval-class buckets.

## What this layer is not

- **Not** measured acoustic fusion, SPL, or perceptual validation.
- **Not** a claim that every interval quality named in a bucket appears in the score (see **`seconds_sevenths`** below).
- **Not** the same as **`pairwise_interval_proximity`** / **`register_pair_distance_factor`** inside register compactness.

## Stable keys vs display labels

Exports keep **backward-compatible** JSON keys in **`interval_class_profile`** (and the parallel alias **`symbolic_blend_interval_profile`**). Human-readable keys are in **`interval_class_profile_display`**.

| Stable key (`interval_class_profile`) | Display label (`interval_class_profile_display`) | Mod‑12 classes grouped |
|--------------------------------------|--------------------------------------------------|-------------------------|
| `unison_octave` | unison / octave equivalence class | 0 |
| `fifth_twelfth` | fifth / twelfth equivalence class | 7 |
| `fourth_class` | fourth equivalence class | 5 |
| `thirds_sixths` | third-class / sixth-class equivalence group | 3, 4, 8, 9 |
| `tritone` | tritone equivalence class | 6 |
| `seconds_sevenths` | second-class / seventh-class equivalence group | **1, 2, 10, 11** |

### `seconds_sevenths` (common misread)

The key **`seconds_sevenths`** names a **single symbolic favourability bucket** for chromatic interval classes {1, 2, 10, 11}. It does **not** mean that literal major/minor sevenths and seconds both occur in the excerpt, nor that the analyser detected a seventh in the notation.

**Example:** **C4–D4** (major second) yields overlap mass only in **`seconds_sevenths`** in **`interval_class_profile`**, while **`literal_interval_semitone_pair_mass`** shows mass on **`"2"`** (two semitones) and **no** mass on **`"11"`**.

Canonical prose for exports is also in **`interval_class_semantics_note`** and **`interval_class_display_labels`** inside `symbolic_blend_conditioning.json` (profile version **1.2+**).

## Diagnostic mass profiles (pre-bucket)

When pairwise pitched evidence exists, each window also exports:

| Field | Meaning |
|-------|---------|
| **`literal_interval_semitone_pair_mass`** | Overlap-weighted pair mass by **absolute** semitone distance (string keys: `"1"`, `"2"`, `"12"`, …) **before** mod‑12 grouping. |
| **`chromatic_mod12_pair_mass`** | Same mass by chromatic distance mod 12 (`"0"` … `"11"`). Bridges literal distances and **`interval_class_profile`** buckets. |

Use **`literal_interval_semitone_pair_mass`** when prose or plots must reflect **what distances actually appear**; use **`interval_class_profile`** / **`interval_class_profile_display`** for **symbolic interval-class favourability** only.

## Related scalars

| Field | Role |
|-------|------|
| **`interval_class_blend_factor`** | Scalar favourability from overlap-weighted pairs (alias: **`pairwise_interval_blend_factor`**). |
| **`interval_class_evidence_status`** | Provenance (default **`symbolic_convention`**). |
| **`symbolic_blend_potential`** | Optional geometric blend of **H_TI_core**, interval-class, attack, and (when available) dynamic-conditioning factors. |

## Acoustic proxy note

If **`acoustic_proxy_include_interval_class`** is enabled on the **H_TA** layer, the kernel reuses the same stable keys via **`interval_class_key_for_d12`** and weights in `acoustic_timbral_taxonomy.json` → **`interval_class_symbolic`**. That is still **score-derived** and subject to the same **`seconds_sevenths`** semantics — not literal interval detection.

## Code entry points

- `interval_class_key_for_d12`, `interval_class_display_label`, `compute_interval_class_blend_factor` — `analyzers/symbolic_blend_layers.py`
- CSV / JSON columns — `HTI_CSV_COLUMNS`, `HTI_EXPORT_TIME_SERIES_KEYS` in `analyzers/hti_export_rows.py` (re-exported from `hti.py`); series keys in `hti_analyze_series.py`
- Operator summary — `QUICK_REFERENCE.md`, formal tables — `TECHNICAL_MANUAL.md` (metric glossary + §9 export notes)
