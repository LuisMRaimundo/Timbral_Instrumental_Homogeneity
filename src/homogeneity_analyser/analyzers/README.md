# `analyzers/` — product vs legacy shims

## Product path (read these for H_TI)

| Module | Role |
|--------|------|
| `hti.py` | **Orchestration only** — `SymbolicTIHomogeneityAnalyzer`, `analyze_hti` loop |
| `hti_window_features.py` | Per-window Herfindahl + register + dynamics feature dict |
| `hti_window_overlap.py` | Event/window overlap mass |
| `hti_register_compactness.py` | `compute_register_compactness_fields`, pitched occurrence collection |
| `hti_score_lookup.py` | Measure number at quarter length |
| `hti_active_weights.py` | H_TI_core component weights / geometric mean |
| `hti_comparability.py` | `hti_comparability_class` (effective formula fingerprint per window) |
| `hti_analyze_series.py` | Time-series row append + optional layers |
| `hti_technique_coverage.py` | `technique_coverage_status` resolution |
| `hti_concentration.py` | Herfindahl helpers |
| `hti_export_rows.py` | **Canonical** `HTI_CSV_COLUMNS`, `hti_csv_row_dict`, `HTI_EXPORT_TIME_SERIES_KEYS` (also re-exported from `hti.py`) |
| `hti_adaptive_windows.py`, `hti_dynamics.py`, `hti_dynamic_conditioning.py`, `hti_taxonomy.py` | Windowing, dynamics, taxonomy |
| `timbral.py` | Symbolic score → event list (shared pipeline) |
| `timbral_event_build.py` | Pure helpers for symbolic event dict assembly |
| `pitch_interpretation.py`, `harmonic_pitch.py`, `technique_state.py` | Pitch / technique normalization |
| `symbolic_blend_layers.py`, `timbral_acoustic_proxy.py` | Optional export registries |

Maintainer map: **`docs/HTI_SYMBOLIC_PIPELINE.md`**.

## Legacy shims (do not edit logic here)

These files only re-export from `homogeneity_analyser.legacy.*`:

`homogeneity.py`, `cluster.py`, `orchestration_symbolic.py`, `notated_fusion_potential.py`,
`notated_fusion_dynamic.py`, `fusion_acoustic_heuristic.py`, `register.py`

**New code:** `from homogeneity_analyser.legacy import HomogeneityAnalyzer` (or lazy
`from homogeneity_analyser.analyzers import HomogeneityAnalyzer` — same object).

See repo root **`LEGACY.md`** and `legacy/README.md`.
