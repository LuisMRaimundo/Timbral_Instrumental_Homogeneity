# `ui/` — Gradio callback boundary

| Module | Role |
|--------|------|
| `callbacks.py` | Facade — re-exports entry points for Gradio wiring |
| `callbacks_hti.py` | **Product** H_TI path (`run_hti_app`) |
| `callbacks_legacy.py` | Legacy multimetric paths (H, H_timbral, U, combined JSON 1.8) |
| `callbacks_inspection.py` | Loaded XML score audit (`run_loaded_xml_inspection`) |
| `callback_helpers.py` | Plotly/matplotlib static export, timbral parse-error tuple |
| `hti_ui_params.py` | H_TI parameter dict + CSV rows + plot title |
| `legacy_ui_params.py` | Legacy H(t) homogeneity parameters + CSV arrays |
| `timbral_ui_params.py` | Legacy H_timbral parameters + parse-error copy |
| `legacy_multimetric_ui_params.py` | H_orchestration_symbolic, U(t), combined-run params/summaries |
| `callback_result_formatting.py` | Audit table cells, temp CSV paths |
| `validation.py` | Upload path + `parse_ui_float` |

Analysis remains in `services/` and `analyzers/`. Legacy **analyzers** live under `homogeneity_analyser.legacy` (see repo `LEGACY.md`).

**Tests:** smoke tests patch submodules (`callbacks_hti`, `callbacks_legacy`); `write_temp_csv` is covered via `_write_temp_csv` in `tests/test_ui_audit_csv.py`.
