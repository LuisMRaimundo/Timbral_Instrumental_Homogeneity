$\sum_i p_i^2$$\sum_f P_f^2$; named profiles **strict** / **conservative** (0.45) / **balanced** (0.55) / **permissive** (0.65), optional numeric override). **Distribution-based** across any number of instruments/families; **no** pairwise instrument tables, **no** legacy H_timbral pairwise kernels.

- **Combined workflow** — one run aligns **H**, **H_timbral**, **H_cluster**, **H_orchestration_symbolic**, **`H_notated_fusion_potential`**, **`H_notated_fusion_potential_dynamic`**, **H_fusion_acoustic_heuristic**, **`legacy_H_timbral`** (alias of **H_timbral** in `combined_series`), fusion **confidence** fields, and an extended **diagnostics** CSV for side-by-side review.

- **JSON export (`schema_version` 1.8; was 1.6 / 1.7)** — all export documents now include:
  - `schema_version`, `model_version` (export-bundle id), `metric_kind` (duplicate of `kind` for neutral consumers), `not_audio_analysis: true`.
  - For **`kind: "timbral"`** in **legacy** mode: **`legacy_warning`**, **`interpretation_status`: `"legacy_diagnostic"`**, **`timbral_model_mode`**, and per-window **`evidence_status`** when `source_keys_used` is empty while **`provisional_constants_used`** is non-empty.
  - For **fusion** exports (and **combined** bundles when fusion is embedded): top-level **`source_keys`** = sorted union of per-window diagnostic **`sources_used`**; fusion **results** still carry full per-window diagnostics including **confidence** and **`sources_used`**. **Combined** exports add **`interpretation_guidance`**.

- **Documentation / UI** — terminology aligned so nothing implies **waveform measurement** or **microphone capture**. **README.md**, **TECHNICAL_MANUAL.md**, **METRIC_CODE_MAP.md**, and Gradio intro copy distinguish **symbolic**, **MIDI-vertical**, **Herfindahl symbolic**, **literature-informed heuristic** layers, and **legacy H_timbral** as **diagnostic-only** (Combined tab is the recommended interpretation path).

## What did not change

- **Default timbral pipeline** remains **`timbral_model_mode: "legacy"`**; existing scores and expectations for **H_timbral** curves are preserved unless users opt into other modes.
- **Standalone legacy H_timbral tab** (renamed for clarity), **H_timbral-only CSV** (`t`, `H_timbral`), and **homogeneity-only** workflows are unchanged numerically.
- **Older JSON field names** inside nested payloads (e.g. `H_timbral`, `results`, `timbral_state_series`) remain; additive fields only.
- **Existing tests** for numeric behaviour of **H_timbral** kernels, fusion math, and orchestration Herfindahl remain valid; new tests cover the **validation corpus** and export shape.

## Compatibility notes

| Consumer | Expectation |
|----------|--------------|
| Parsers keyed on `kind` | Unchanged; **`metric_kind`** mirrors **`kind`**. |
| Parsers keyed on `schema_version` | Current **1.8** extends **1.7** with **`H_notated_fusion_potential_dynamic`**, **`dynamic_coherence`**, and related notated-fusion metadata; **1.7** extends **1.6** with **`same_family_relief_profile`** and richer **`H_notated_fusion_potential_diagnostics`**; treat **1.6** / **1.5** / **1.4** as subsets. |
| Combined CSV column order | Base columns unchanged; optional **`H_cluster`**, **`H_orchestration_symbolic`** appended as before; extended metrics and **`legacy_H_timbral`** live in **`combined_series`** (JSON) and **diagnostics CSV**, not necessarily in the minimal legacy CSV row shape. |
| `timbral_semantic_model.model_version` | Still the **timbral semantics submodule** version (e.g. `1.0` from `timbral_semantics.py`), **not** the same token as top-level JSON **`model_version`** (export bundle id). |

## How to interpret old vs new metrics

- **Use `H_timbral` when** you need continuity with **earlier publications, plots, or CSVs**, or when you want the **full legacy blend** (including family pairwise tables and controlled cross-family boosts).
- **Use `H_orchestration_symbolic` when** you want a **transparent symbolic concentration** index comparable across layouts without legacy kernel baggage.
- **Use `H_cluster` when** you care only about **vertical pitch content** (e.g. chromatic density vs wide span), independent of orchestration labels.
- **Use `H_notated_fusion_potential` when** you want a **score-only** scalar that joins **family** / **technique** Herfindahl with **register** proximity and a **distribution-based** same-family softening on the instrument axis (**`same_family_relief`** in JSON parameters / `score_metadata`; per-window **`H_notated_fusion_potential_diagnostics`**). It is **not** measured audio and does **not** use legacy pairwise kernels.
- **Use `H_fusion_acoustic_heuristic` when** you want a **single scalar** that folds registry-based profile distance and roughness proxy — always read **`confidence_score`**; **low confidence ≠ weak music**, it means **weak evidential support for the proxy** from the current notation slice.

## Known limitations

- **No audio** — Nothing in this repository analyses user recordings; “acoustic” in metric names means **literature-linked proxies** or **register/spectral placeholders**, not measured spectra.
- **MIDI / sparse part names** — **H_timbral** and fusion rely on **instrument identity** when present; MIDI without part metadata can deflate orchestration-facing metrics or confidence.
- **Heuristic fusion** — Feature vectors and roughness are **symbolic approximations**; they do not capture room, bow noise, mute material, or player-specific timbre.
- **Dual `model_version`** — Top-level **`model_version`** identifies the **export bundle**; nested **`timbral_semantic_model.model_version`** identifies **timbral semantics documentation**; do not merge them in downstream schemas without documenting the distinction.
