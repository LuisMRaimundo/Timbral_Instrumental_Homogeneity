# Architecture (Timbral_Instrumental_Homogeneity)

This repository is a **Python package** (`homogeneity_analyser`) under a **src layout**. All application logic lives under `src/homogeneity_analyser/`.

## Layout

| Area | Path | Role |
|------|------|------|
| Score I/O | `homogeneity_analyser/io/` | Pre-parse validation (size, extension, MXL zip metadata), `parse_score()` wrapping music21 |
| Analyzers | `homogeneity_analyser/analyzers/` | **H_TI** orchestration (`hti.py`); shared score holder `symbolic_score_analyzer.py`; window/register/series in `hti_window_features.py`, `hti_register_compactness.py`, `hti_analyze_series.py`. Score → events: `symbolic_event_pipeline.py`, `symbolic_instrument_resolve.py`, `symbolic_pitch_resolve.py`, `timbral_event_build.py`; **H_timbral** metric in `timbral.py`. Map: **`docs/HTI_SYMBOLIC_PIPELINE.md`**. Optional layers — **`docs/SYMBOLIC_INTERVAL_CLASS_LAYER.md`**, **`docs/H_TA_ACOUSTIC_PROXY.md`**. |
| Legacy multimetric | `homogeneity_analyser/legacy/` | **H(t)**, **H_cluster**, orchestration / fusion heuristics, **U(t)** — combined JSON **1.8**; shims at `analyzers/<name>.py`. |
| Taxonomy | `homogeneity_analyser/taxonomy/` | Part-name → family / canonical instrument; **`symbolic_blend_conditioning.json`** (interval-class weights + display labels + **`interval_class_semantics_note`**) |
| Services | `homogeneity_analyser/services/` | **H_TI:** `analysis_service_hti.py` — **legacy metrics:** `analysis_service_legacy.py` — facade `analysis_service.py`; CSV (`result_assembly.py`), JSON (`json_export.py`), `window_pipeline.py`, `constants.py` |
| Models | `homogeneity_analyser/models/` | Dataclasses for series results + small enums (`PitchSpaceMode`) |
| Plotting | `homogeneity_analyser/plotting/` | Matplotlib / Plotly figures (`time_series.py`, `summaries.py`, `common.py`) |
| UI | `homogeneity_analyser/ui/` | Gradio app (`gradio_app.py`); **`callbacks.py`** = facade re-exporting **`callbacks_hti.py`** (product), **`callbacks_legacy.py`**, **`callbacks_inspection.py`**, **`callback_helpers.py`**; parameter helpers: **`hti_ui_params.py`**, **`legacy_ui_params.py`**, **`timbral_ui_params.py`**, **`legacy_multimetric_ui_params.py`**, **`callback_result_formatting.py`** (`ui/README.md`); **`validation.py`**, **`components.py`** |
| Utils | `homogeneity_analyser/utils/` | Export path helpers (`output_paths.py`) |
| Tests | `tests/` | Pytest + unittest-style modules; **no** `sys.path` hacks — install package first. Requires **`iav`** (Interval-Homogeneity-Analyser) for `cardinality` tests. |
| Validation | `validation/` | Scripted checks against annotated fixtures |

## Entry points

- **CLI / module:** `python -m homogeneity_analyser` or console script `timbral-instrumental-homogeneity` (legacy: `homogeneity-analyser`; after `pip install -e .`).
- **Development:** `pip install "git+https://github.com/LuisMRaimundo/Interval-Homogeneity-Analyser.git"` then `pip install -e ".[dev]"`, then `pytest`, optional `ruff check .`, `mypy`.

## Static typing (mypy)

The rest of the package is type-checked. **`analyzers/homogeneity.py` is excluded** via `pyproject.toml` because mypy 1.17 can hit an internal error while analysing `numpy.histogram2d` in `extract_features`. Runtime behaviour is unchanged; see tests in `tests/test_analyzers.py`.

## Tests and coverage

CI enforces a **minimum total line coverage** (`fail_under = 77` in `pyproject.toml`; `legacy/*` omitted). **CircleCI** runs the full suite on Python 3.10 and 3.11; **GitHub Actions** runs `pytest -m "not legacy"`. Both install **`iav`** before the editable package. Typical full suite: **975** tests (~80% coverage on `homogeneity_analyser`).

## Scientific scope (unchanged)

Symbolic MusicXML/MIDI only. **H_TI_core** is **score-based symbolic** homogeneity — **not** measured acoustic or perceptual fusion. **H_timbral** uses notation-encoded part/instrument names, not waveforms. **H_TI-only JSON** uses **`schema_version` `3.0`** (`HTI_EXPORT_SCHEMA_VERSION` in `json_export.py`). Optional **`H_TA_acoustic_proxy`** columns when `include_acoustic_proxy` — see **`docs/H_TA_ACOUSTIC_PROXY.md`**. See `README.md`, `QUICK_REFERENCE.md`, and `TECHNICAL_MANUAL.md`.
