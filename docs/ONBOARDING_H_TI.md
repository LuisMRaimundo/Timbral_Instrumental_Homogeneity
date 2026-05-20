# Onboarding — H_TI product path

Short map for developers who want **families, instrument typology, and register proximity** without wading through multimetric legacy code.

## Three layers (do not conflate)

| Layer | Location | Keep for H_TI? |
|-------|----------|----------------|
| **Symbolic pipeline** | `analyzers/timbral.py`, `taxonomy/instrument_taxonomy.py`, `*_pairwise_timbral.py`, `notation_context.py`, `pitch_interpretation.py` | **Yes** — H_TI subclasses `TimbralHomogeneityAnalyzer` |
| **H_TI product** | `analyzers/hti.py`, `hti_*` helpers, `services/analysis_service_hti.py`, `ui/hti_ui_params.py`, Gradio `run_hti_app` | **Yes** |
| **Legacy metrics** | `homogeneity_analyser/legacy/`, `services/analysis_service_legacy.py`, JSON **1.8** combined exports | **Optional** — batch/tests/history only |

**`timbral.py` is not “legacy trash”.** It is the shared engine for score → events → taxonomy.  
**`legacy/` is “old metrics”** (H(t), H_timbral **number**, H_cluster, fusion, U(t)), not a second taxonomy.

## Reading order (H_TI only)

1. `README.md` and `QUICK_REFERENCE.md` — scope and exports (**schema 3.0**)
2. `analyzers/hti.py` — `H_TI_core`, register compactness
3. `analyzers/hti_export_rows.py` — CSV/JSON column order
4. `taxonomy/instrument_taxonomy.py` — canonical instrument and **family** (via `timbral.py`)
5. `services/analysis_service_hti.py` — `run_symbolic_ti_homogeneity_analysis`
6. `ui/hti_ui_params.py` + `ui/callbacks.py` (`run_hti_app` only)

Skip until needed: `legacy/`, `analysis_service_legacy.py`, `docs/archive_legacy/`, `docs/H_TIMBRAL_*.md` (design notes for the **H_timbral metric** and pairwise refinements).

## Tests (day-to-day)

```bash
# Product path (default)
python -m pytest tests/ -m "not legacy" -q

# Full suite including multimetric / combined JSON 1.8
python -m pytest tests/ -q
```

## Services split (phase B)

| Module | Exports |
|--------|---------|
| `analysis_service_hti.py` | `run_symbolic_ti_homogeneity_analysis` |
| `analysis_service_legacy.py` | `run_timbral_analysis`, `run_both_and_combine`, … |
| `analysis_service.py` | Facade — same imports as before |

See `LEGACY.md` and `MAINTAINERS.md`.
