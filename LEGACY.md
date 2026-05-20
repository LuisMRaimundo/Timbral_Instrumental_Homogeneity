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

**Onboarding (H_TI only):** `docs/ONBOARDING_H_TI.md` — how taxonomy/register/families relate to `timbral.py` vs `legacy/`.

**Services:** multimetric runs live in `services/analysis_service_legacy.py`; H_TI in `services/analysis_service_hti.py` (facade: `analysis_service.py`).
