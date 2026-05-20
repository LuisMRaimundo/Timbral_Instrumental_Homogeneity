"""Pure UI helpers for orchestration, register, and combined legacy runs (no Gradio)."""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.ui.legacy_ui_params import _ui_float
from homogeneity_analyser.ui.validation import coerce_float, parse_ui_float


def build_orchestration_symbolic_params_from_ui(
    *,
    time_step: Any = None,
    window_size: Any = None,
    weight_orch_instr: Any = None,
    weight_orch_fam: Any = None,
    weight_orch_tech: Any = None,
) -> dict[str, Any]:
    ts = parse_ui_float(time_step, default=0.25, field_name="time step")
    ws = parse_ui_float(window_size, default=4.0, field_name="window size")
    if ts is None or ws is None or ts <= 0 or ws <= 0:
        raise ValueError("Time step and window size must be > 0.")
    return {
        "time_step": float(ts),
        "window_size": float(ws),
        "weight_orchestration_instrument": coerce_float(
            weight_orch_instr, 0.45, field_name="orchestration instrument weight"
        ),
        "weight_orchestration_family": coerce_float(
            weight_orch_fam, 0.25, field_name="orchestration family weight"
        ),
        "weight_orchestration_technique": coerce_float(
            weight_orch_tech, 0.30, field_name="orchestration technique weight"
        ),
    }


def orchestration_symbolic_plot_title(*, window_size: float, time_step: float) -> str:
    return f"H_orchestration_symbolic(t) — window={window_size}, step={time_step}"


def validate_register_limits(register_low: Any, register_high: Any) -> tuple[str, str]:
    if not register_low or not str(register_low).strip():
        raise ValueError("Enter a lower register limit (e.g. A1 or MIDI number).")
    if not register_high or not str(register_high).strip():
        raise ValueError("Enter an upper register limit (e.g. E7 or MIDI number).")
    return str(register_low).strip(), str(register_high).strip()


def build_register_params_from_ui(
    *,
    register_low: Any,
    register_high: Any,
    time_step: Any = None,
    window_size: Any = None,
) -> dict[str, Any]:
    lo, hi = validate_register_limits(register_low, register_high)
    ts = _ui_float(time_step, default=0.25, field_name="time step")
    ws = _ui_float(window_size, default=4.0, field_name="window size")
    if ts <= 0 or ws <= 0:
        raise ValueError("Time step and window size must be > 0.")
    return {
        "time_step": ts,
        "window_size": ws,
        "register_low": lo,
        "register_high": hi,
    }


def register_plot_title(*, register_low: str, register_high: str, window_size: float) -> str:
    return f"Register uniformity U(t) — [{register_low}, {register_high}], window={window_size}"


def build_combined_homogeneity_weight_params(
    *,
    weight_m1: Any = None,
    weight_m2: Any = None,
    weight_m3: Any = None,
) -> dict[str, float]:
    return {
        "weight_m1": coerce_float(weight_m1, 1.0 / 3.0, field_name="weight m1"),
        "weight_m2": coerce_float(weight_m2, 1.0 / 3.0, field_name="weight m2"),
        "weight_m3": coerce_float(weight_m3, 1.0 / 3.0, field_name="weight m3"),
    }


def build_combined_orchestration_weight_params(
    *,
    weight_orch_instr: Any = None,
    weight_orch_fam: Any = None,
    weight_orch_tech: Any = None,
) -> dict[str, float]:
    return {
        "weight_orchestration_instrument": coerce_float(
            weight_orch_instr, 0.45, field_name="orchestration instrument weight"
        ),
        "weight_orchestration_family": coerce_float(
            weight_orch_fam, 0.25, field_name="orchestration family weight"
        ),
        "weight_orchestration_technique": coerce_float(
            weight_orch_tech, 0.30, field_name="orchestration technique weight"
        ),
    }


def parse_notated_fusion_relief_ui(
    nf_relief_profile: str = "balanced",
    nf_relief_override: str | None = None,
) -> dict[str, Any]:
    nfd: dict[str, Any] = {"same_family_relief_profile": str(nf_relief_profile or "balanced")}
    raw_ov = "" if nf_relief_override is None else str(nf_relief_override).strip()
    if raw_ov != "":
        try:
            v = float(raw_ov.replace(",", "."))
        except (TypeError, ValueError) as exc:
            raise ValueError("same_family_relief override must be a number in [0, 1] when provided.") from exc
        if not (0.0 <= v <= 1.0):
            raise ValueError("same_family_relief override must be between 0 and 1.")
        nfd["same_family_relief_override"] = v
    return nfd


def combined_summary_preamble() -> str:
    return (
        "**Recommended for interpretation (timbral / orchestration-style):** **H_cluster**, "
        "**H_orchestration_symbolic**, **H_notated_fusion_potential** (notation-derived register + family/technique "
        "Herfindahl + **effective_instrument_uniformity** / **same_family_relief**; not measured audio), then "
        "**H_fusion_acoustic_heuristic** (use JSON `confidence_*` / "
        "`source_keys`). **legacy H_timbral** is a backward-compatible diagnostic only — not measured audio and not "
        "acoustically validated fusion.\n\n"
        "Plots below are ordered: **H(t)** → **H_cluster** → **H_orchestration_symbolic** → "
        "**H_notated_fusion_potential** → **H_fusion** → **legacy H_timbral** (diagnostic last).\n\n---\n\n"
    )


def build_combined_summary_text(
    *,
    out_h_summary: str,
    out_t_summary: str,
    out_c_summary: str,
    out_o_summary: str,
    out_nf_summary: str,
    out_f_summary: str,
) -> str:
    return (
        combined_summary_preamble()
        + out_h_summary
        + "\n\n---\n\n"
        + out_t_summary
        + "\n\n---\n\n"
        + (out_c_summary or "")
        + "\n\n---\n\n"
        + (out_o_summary or "")
        + "\n\n---\n\n"
        + (out_nf_summary or "")
        + "\n\n---\n\n"
        + (out_f_summary or "")
        + "\n\n---\n\n"
        + "Export: combined CSV includes `H`, `H_timbral`, `H_cluster`, `H_orchestration_symbolic`, "
        + "`H_notated_fusion_potential`, and `dominant_timbral_state` when available. "
        + "**Combined diagnostics**: overlay plot + `cluster_orch_fusion_diagnostics.csv` + table — `H_cluster`, "
        + "`H_orchestration_symbolic`, `H_notated_fusion_potential`, `H_fusion_acoustic_heuristic`, "
        + "`legacy_H_timbral`, fusion confidence, dominant timbral state, fusion `main_penalty_reason`. "
        + "Full nested analyses and `combined_series` are in the combined JSON (`schema_version` 1.8)."
    )


def cluster_orch_fusion_plot_bundle(combined_series: dict[str, Any]) -> dict[str, list[Any]]:
    legacy_t = combined_series.get("legacy_H_timbral") or combined_series.get("H_timbral") or []
    return {
        "t": combined_series.get("t", []),
        "H_cluster": combined_series.get("H_cluster", []),
        "H_orchestration_symbolic": combined_series.get("H_orchestration_symbolic", []),
        "H_notated_fusion_potential": combined_series.get("H_notated_fusion_potential", []),
        "H_fusion_acoustic_heuristic": combined_series.get("H_fusion_acoustic_heuristic", []),
        "legacy_H_timbral": legacy_t,
    }


def cluster_orch_fusion_plot_title(*, window_size: float, time_step: float) -> str:
    return f"Cluster / orch / notated fusion / fusion / legacy H_timbral — window={window_size}, step={time_step}"


def cluster_plot_title(*, window_size: float) -> str:
    return f"Vertical cluster H_cluster(t) — window={window_size}"


def homogeneity_combined_plot_title(*, window_size: float, time_step: float) -> str:
    return f"Homogeneity H(t) — window={window_size}, step={time_step}"
