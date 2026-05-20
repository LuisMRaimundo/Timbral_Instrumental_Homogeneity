# Timbral / fusion validation corpus

Small **MusicXML** scores plus **`timbral_fusion_cases.csv`** describe orchestration and pitch layouts used to sanity-check **H_cluster**, **H_orchestration_symbolic**, and **H_fusion_acoustic_heuristic** after refactors.

## Files

| File | Purpose |
|------|---------|
| `timbral_fusion_cases.csv` | Human-readable expectations (`case_id`, fixture path, narrative fields, **bands**, minimum fusion confidence). |
| `bands.py` | Shared mapping from `[0, 1]` scalars to the seven **band** labels used in the CSV. |
| `cf*.xml` | Minimal **score-partwise** MusicXML (one measure, whole notes) built for each scenario. |

## Bands

Seven equal-width bins on **[0, 1]** (see `bands.py`):

`very_low`, `low`, `medium_low`, `medium`, `medium_high`, `high`, `very_high`.

## Rules enforced by tests

1. **H_cluster** — For cases **cf01–cf05**, the **sounding** MIDI multiset is the same chromatic run; the first-window **H_cluster** must be **identical** across those fixtures (instrumentation-independent).
2. **H_orchestration_symbolic** — **Very high** when one canonical instrument family and uniform technique (cf01, cf02); **high** (not top bin) when technique or instrument layout splits mass (cf03–cf05).
3. **H_fusion_acoustic_heuristic** — May track profile + roughness; expectations are **tight bands** derived from the current implementation. **Confidence** is **model** confidence (`confidence_score` in fusion diagnostics), not empirical acoustic proof: tests only enforce `confidence_score >= expected_confidence_min`.
4. **`source_keys`** — Column lists literature or `project_specific` keys relevant to the rationale; fusion window diagnostics must expose non-empty **`sources_used`** (registry-linked or `project_specific`).

## Running analyses locally

Use the same windowing as tests (`time_step=0.25`, `window_size=4.0` quarter lengths) via `homogeneity_analyser.services.analysis_service`:

- `run_cluster_analysis`
- `run_orchestration_symbolic_analysis`
- `run_fusion_acoustic_heuristic_analysis`

## Extending the corpus

Add a new `cfXX_*.xml` under this folder, append a CSV row, extend `tests/test_timbral_fusion_corpus_validation.py`, and re-run **pytest**. Prefer **paraphrase** in `rationale` (no long quotations from private PDFs).
