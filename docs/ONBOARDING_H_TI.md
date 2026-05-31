# Onboarding — H_TI product path

Short map for developers who want **families, instrument typology, and register proximity** without wading through multimetric legacy code.

## Three layers (do not conflate)

| Layer | Location | Keep for H_TI? |
|-------|----------|----------------|
| **Symbolic pipeline** | `symbolic_score_analyzer.py`, `symbolic_event_pipeline.py`, `symbolic_instrument_resolve.py`, `symbolic_pitch_resolve.py`, `timbral_event_build.py`, `taxonomy/instrument_taxonomy.py`, `pitch_interpretation.py`, `technique_state.py` | **Yes** — builds `_events` via `SymbolicScoreAnalyzer` |
| **H_TI product** | `hti.py` (orchestration), `hti_window_features.py`, `hti_register_compactness.py`, `hti_active_weights.py`, `hti_analyze_series.py`, `services/analysis_service_hti.py`, `ui/callbacks_hti.py` | **Yes** |
| **Legacy metrics** | `homogeneity_analyser/legacy/`, `services/analysis_service_legacy.py`, `timbral.py` (**H_timbral** number only), JSON **1.8** combined exports | **Optional** — batch/tests/history only |

**`timbral.py` is not “legacy trash”.** It subclasses ``SymbolicScoreAnalyzer`` and implements the **H_timbral** pairwise metric for multimetric runs. Event building lives in ``symbolic_event_pipeline.py``.  
**`legacy/` is “old metrics”** (H(t), H_cluster, fusion, U(t)), not a second taxonomy.

See **`docs/PRODUCT_SCOPE.md`** (Tier 1 vs optional vs legacy) and **`docs/HTI_SYMBOLIC_PIPELINE.md`** (full stage → module map).

## Reading order (H_TI only)

1. `README.md` and `QUICK_REFERENCE.md` — scope and exports (**schema 3.0**)
2. **`docs/HTI_SYMBOLIC_PIPELINE.md`** — where each stage lives
3. `analyzers/hti.py` — public API (`analyze_hti`, `compute_H_TI`); implementation in `hti_*` helpers
4. `analyzers/hti_export_rows.py` — CSV/JSON column order
5. `taxonomy/instrument_taxonomy.py` — canonical instrument and **family**
6. `services/analysis_service_hti.py` — `run_symbolic_ti_homogeneity_analysis`
7. `ui/hti_ui_params.py` + `ui/callbacks_hti.py` (re-exported as `callbacks.run_hti_app`)

Skip until needed: `legacy/`, `analysis_service_legacy.py`, `docs/archive_legacy/` (historical paths), `docs/H_TIMBRAL_*.md` (design notes for **H_timbral** pairwise refinements).

## Tests (day-to-day)

```bash
# Product path (default)
python -m pytest tests/ -m "not legacy" -q

# Full suite including multimetric / combined JSON 1.8
python -m pytest tests/ -q
```

Pipeline parity: `tests/test_symbolic_event_pipeline.py`.

## Services split (phase B)

| Module | Exports |
|--------|---------|
| `analysis_service_hti.py` | `run_symbolic_ti_homogeneity_analysis` |
| `analysis_service_legacy.py` | `run_timbral_analysis`, `run_both_and_combine`, … |
| `analysis_service.py` | Facade — same imports as before |

See `LEGACY.md` and `MAINTAINERS.md`.
