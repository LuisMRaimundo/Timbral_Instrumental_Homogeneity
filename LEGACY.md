# Legacy multimetric code

The **Gradio product** is **H_TI** (`SymbolicTIHomogeneityAnalyzer`). Everything below is
**research / batch / combined JSON 1.8** — not the primary user surface.

## Where the code lives

| Import (preferred) | Implementation |
|--------------------|----------------|
| `homogeneity_analyser.legacy` | `src/homogeneity_analyser/legacy/*.py` |
| `homogeneity_analyser.analyzers.homogeneity` (etc.) | **Shim only** — three-line re-export |

Do **not** open shim files expecting logic; open `legacy/` instead.

## Metrics (internal)

- **H(t)** — `legacy.homogeneity`
- **H_cluster** — `legacy.cluster`
- **H_orchestration_symbolic** — `legacy.orchestration_symbolic`
- **H_notated_fusion_potential** — `legacy.notated_fusion_potential`
- **H_fusion_acoustic_heuristic** — `legacy.fusion_acoustic_heuristic`
- **U(t)** — `legacy.register`

Orchestration: `services/analysis_service.py`, `services/json_export.py` (`schema_version` **1.8**).

Coverage: legacy modules are **omitted** from the product-path coverage gate; see `tests/test_legacy_package.py`.

**Onboarding (H_TI only):** `docs/ONBOARDING_H_TI.md` — how taxonomy/register/families relate to `symbolic_score_analyzer.py` vs `legacy/`.

**Services:** multimetric runs live in `services/analysis_service_legacy.py`; H_TI in `services/analysis_service_hti.py` (facade: `analysis_service.py`).

## Optional H_TI layers (not legacy, but off by default)

These ship in the **H_TI analyzer** but are **not** part of the default Gradio product surface:

| Layer | Default | Enable |
|-------|---------|--------|
| Timbral affinity relief | on (configurable factors) | analyzer kwargs / UI advanced |
| Symbolic blend / interval-class columns | **off** | `include_symbolic_blend_potential=True` |
| H_TA acoustic proxy | **off** | `include_acoustic_proxy=True` |

See `docs/PRODUCT_SCOPE.md` (Tier 2). Wrong use — e.g. comparing runs with proxy enabled vs disabled — is a **methodology** mistake, not a legacy API issue.

## UI split (2026-05)

| Module | Role |
|--------|------|
| `ui/callbacks.py` | Facade re-exports |
| `ui/callbacks_hti.py` | H_TI product path |
| `ui/callbacks_legacy.py` | Multimetric + JSON 1.8 |
| `ui/callbacks_inspection.py` | Loaded XML audit |
| `ui/callback_helpers.py` | Plot save, float parse shims |
