# `services/` — analysis orchestration

| Module | Role |
|--------|------|
| `analysis_service.py` | **Facade** — same imports as before the split |
| `analysis_service_hti.py` | `run_symbolic_ti_homogeneity_analysis` (H_TI product) |
| `analysis_service_legacy.py` | H(t), H_timbral **metric**, cluster, fusion, U(t), `run_both_and_combine` |
| `json_export.py`, `result_assembly.py`, `constants.py`, `param_validation.py` | Exports and validation |

See `docs/ONBOARDING_H_TI.md` and **`docs/HTI_SYMBOLIC_PIPELINE.md`** (module map).
