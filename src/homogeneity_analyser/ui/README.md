# `ui/` — Gradio callback boundary

| Module | Role |
|--------|------|
| `callbacks.py` | Gradio entry points (`run_hti_app`, `run_app`, `run_timbral_app`, …) — orchestration only |
| `hti_ui_params.py` | H_TI parameter dict + CSV rows + plot title |
| `legacy_ui_params.py` | Legacy H(t) homogeneity parameters + CSV arrays |
| `timbral_ui_params.py` | Legacy H_timbral parameters + parse-error copy |
| `legacy_multimetric_ui_params.py` | H_orchestration_symbolic, U(t), combined-run params/summaries |
| `callback_result_formatting.py` | Audit table cells, temp CSV paths |
| `validation.py` | Upload path + `parse_ui_float` |

Analysis remains in `services/` and `analyzers/`. Legacy **analyzers** live under `homogeneity_analyser.legacy` (see repo `LEGACY.md`).

**Not extracted (TODO):** `run_loaded_xml_inspection` and Plotly/matplotlib save paths stay in `callbacks.py` because they depend on plotting backends and Gradio return types.
