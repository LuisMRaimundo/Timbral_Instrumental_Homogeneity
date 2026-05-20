# Legacy multimetric analysers

Internal **research / batch / test** metrics. The Gradio product surface is **H_TI** only.

| Module | Metric / role |
|--------|----------------|
| `homogeneity.py` | **H(t)** — distribution homogeneity |
| `cluster.py` | **H_cluster** — vertical cluster |
| `orchestration_symbolic.py` | **H_orchestration_symbolic** |
| `notated_fusion_potential.py` | **H_notated_fusion_potential** (+ dynamic companion in `notated_fusion_dynamic.py`) |
| `fusion_acoustic_heuristic.py` | **H_fusion_acoustic_heuristic** |
| `register.py` | **U(t)** — register uniformity |

Imports: prefer `homogeneity_analyser.legacy` for new code. Existing paths under `homogeneity_analyser.analyzers.<name>` remain as **compatibility shims**.

Orchestration: `services/analysis_service.py` (combined runs). JSON: `services/json_export.py` (**1.8** bundles).
