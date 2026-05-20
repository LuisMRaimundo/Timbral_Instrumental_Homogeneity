# H_TA_acoustic_proxy — score-derived timbral-acoustic affinity



## Purpose



**`H_TA_acoustic_proxy`** (alias **`timbral_acoustic_affinity`**) is an **optional**, **orthogonal** diagnostic to **`H_TI_core`**.



| Metric | Role |

|--------|------|

| **`H_TI_core`** | Strict **symbolic concentration** (Herfindahl on canonical instruments, subfamily, technique key, **register_compactness**). **Unchanged** when the proxy is enabled. |

| **`H_TA_acoustic_proxy`** | **Event-level** \(A(t)=\sum_{ij} p_i p_j K(e_i,e_j)\) with organology-informed kernel \(K\). |

| **`timbral_affinity_*`** (literature relief) | **Different** optional layer that replaces only the **instrument** axis in a relieved **H_TI** variant — not the same as **`H_TA`**. |

| **`symbolic_blend_potential`** / **`interval_class_blend_factor`** | **Different** optional layer (`include_symbolic_blend_potential`) — interval-class and blend-tendency diagnostics; Gradio accordion is **separate** from the acoustic proxy. See **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`** for export fields and **`seconds_sevenths`** semantics. |



Neither **`H_TI_core`** nor **`H_TA`** is measured audio, perceptual fusion, FFT, or SPL.

When **`acoustic_proxy_include_interval_class`** is true, the H_TA kernel may read **`interval_class_symbolic`** weights keyed like **`seconds_sevenths`**. Those keys name **mod‑12 equivalence buckets** (shared with `symbolic_blend_layers.interval_class_key_for_d12`); they do **not** assert that literal sevenths appear in the score.



## Formula (per window)



- Events = **overlap entities** from the H_TI pipeline (not chord-tone rows).

- \(p_i = \text{overlap\_mass}_i / \sum_k \text{overlap\_mass}_k\) (renormalised if needed).

- \(K(e_i,e_j)\in[0,1]\), symmetric, \(K(e_i,e_i)=1\).

- Missing kernel components are **omitted** from the weighted geometric mean (not treated as high-confidence “ordinary”).

- Single-event windows: \(A=1\) with evidence **`single_event_self_similarity_only`**.



## Register logic (important)



- **`register_compactness`** (in **H_TI_core**) = outer span × pairwise semitone proximity over chord tones.

- **`register_tessitura`** (in **H_TA**) = distance attenuation + coarse instrument-relative zones; **does not** treat chromatic semitone clusters as inherently better “blend”.

- Optional **`interval_class`** kernel weight is **off by default** and labelled **symbolic** when enabled.



## Brass vs woodwind



Encoded via **`source_mechanism`** in `taxonomy/acoustic_timbral_taxonomy.json`:



- Brass ordinary: **`lip_reed`** (labrosone).

- Woodwinds: **`air_jet_edge`**, **`single_reed`**, **`double_reed`** — not one homogeneous woodwind bucket.



## Evidence & confidence



### `timbral_acoustic_affinity_components`



Mass-weighted summary of kernel factors that **contributed** to cross-event pairs in the window (pair mass \(p_i p_j\), normalised per component key). Typical keys: `source_mechanism`, `instrument_family`, `register_tessitura`, `technique`, `dynamic`, `attack_envelope`, optional `interval_class`.



**This dict is authoritative** for whether a component was used in the window-level summary. A short-circuit pair rule (e.g. same canonical instrument with \(K=1\)) may still record `technique` / `dynamic` in **components** for evidence without changing \(K\).



### `timbral_acoustic_affinity_evidence_status`



Semicolon-separated tags built from **`timbral_acoustic_affinity_components`** and window coverage flags passed from H_TI features (`dynamic_coverage_status`, `technique_coverage_status`).



| Tag | When used |

|-----|-----------|

| **`dynamic_used_explicit_notated`** | `"dynamic"` present in **components** and window **`dynamic_coverage_status`** is `explicit` or `partial` |

| **`dynamic_active`** | `"dynamic"` present in **components** but dynamics coverage is not explicit/partial |

| **`dynamic_omitted`** | `"dynamic"` **not** in **components** (insufficient notated dynamic marks on events for the kernel) |

| **`technique_default_only`** | `"technique"` in **components** at ~1.0 and **`technique_coverage_status`** is `explicit_uniform` |

| **`technique_no_special_evidence`** | `"technique"` in **components** at ~1.0 otherwise (ordinary/default technique, no special mismatch) |

| **`technique_active`** | `"technique"` in **components** with similarity below ~1.0 (mixed or special techniques affect pairs) |

| **`technique_omitted`** | no `"technique"` in **components** and technique coverage `unavailable` / `unknown` |

| **`technique_omitted_or_partial`** | no `"technique"` in **components** otherwise |

| **`taxonomy_fallback_or_unknown`** | any event used family fallback or unknown instrument taxonomy |

| **`single_event_self_similarity_only`** | one event in the window |

| **`disabled`** | proxy not requested (`include_acoustic_proxy` false) |



**Consistency rule:** if `"dynamic"` appears in **`timbral_acoustic_affinity_components`**, status must **not** include **`dynamic_omitted`**. If `"technique"` is present at ~1.0 with uniform ordinary technique, prefer **`technique_default_only`** over **`technique_omitted_or_partial`**.



### Other export fields



- **`acoustic_proxy_validation_status`**: **`score_derived_unvalidated`**

- **`acoustic_proxy_not_audio_analysis`**: **`true`**

- **`taxonomy_confidence`** per event (in pairwise detail when exported): `explicit_instrument_row` | `family_fallback_low_confidence` | `unknown_instrument_low_confidence`



## Parameters (defaults)



| Parameter | Default |

|-----------|---------|

| `include_acoustic_proxy` | `false` |

| `acoustic_proxy_profile` | `conservative` |

| `acoustic_proxy_pairwise_export` | `false` |



## Gradio UI



Controls live in the accordion **Acoustic-aligned symbolic timbral-affinity proxy**, **separate** from **Optional symbolic interval-class / blend-potential diagnostics**.



## Implementation & tests



- `src/homogeneity_analyser/analyzers/timbral_acoustic_proxy.py` — `_build_timbral_acoustic_affinity_evidence_status`

- `tests/test_timbral_acoustic_proxy_ranking.py`

- `tests/test_timbral_acoustic_proxy_audit.py` — evidence/component consistency tests



## JSON schema



H_TI bundle **`schema_version` `3.0`** adds acoustic-proxy columns; combined/legacy bundles remain **`1.8`** (internal/batch only).


