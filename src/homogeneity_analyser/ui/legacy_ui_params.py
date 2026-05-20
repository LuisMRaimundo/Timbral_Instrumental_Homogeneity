"""Pure UI helpers for legacy homogeneity H(t) (no Gradio)."""

from __future__ import annotations

from typing import Any

import numpy as np

from homogeneity_analyser.ui.validation import coerce_float, parse_ui_float


def _ui_float(value: Any, *, default: float, field_name: str) -> float:
    parsed = parse_ui_float(value, default=default, field_name=field_name)
    return float(default if parsed is None else parsed)


def build_homogeneity_params_from_ui(
    *,
    time_step: Any = None,
    window_size: Any = None,
    sigma: Any = None,
    pitch_space: Any = "absolute",
    pitch_bin_step: Any = None,
    silence_intra_value: Any = None,
    silence_transition_value: Any = None,
    allow_partial_scales: bool = True,
    single_aggregate: bool = False,
    weight_m1: Any = None,
    weight_m2: Any = None,
    weight_m3: Any = None,
) -> dict[str, Any]:
    """Map UI fields to ``run_homogeneity_analysis`` params. Raises ``ValueError`` on invalid input."""
    ts = _ui_float(time_step, default=0.25, field_name="time step")
    ws = _ui_float(window_size, default=4.0, field_name="window size")
    sig = _ui_float(sigma, default=12.0, field_name="sigma")
    pbs = _ui_float(pitch_bin_step, default=1.0, field_name="pitch bin step")
    s_intra = _ui_float(silence_intra_value, default=0.5, field_name="silence intra value")
    s_trans = _ui_float(silence_transition_value, default=0.5, field_name="silence transition value")
    if ts <= 0 or ws <= 0:
        raise ValueError("Time step and window size must be > 0.")
    if sig <= 0:
        raise ValueError("Sigma must be > 0.")
    if pbs <= 0:
        raise ValueError("Pitch bin step must be > 0.")
    return {
        "time_step": ts,
        "window_size": ws,
        "sigma": sig,
        "pitch_space": pitch_space,
        "pitch_bin_step": pbs,
        "silence_intra_value": s_intra,
        "silence_transition_value": s_trans,
        "allow_partial_scales": allow_partial_scales,
        "single_aggregate": single_aggregate,
        "weight_m1": coerce_float(weight_m1, 1.0 / 3.0, field_name="weight m1"),
        "weight_m2": coerce_float(weight_m2, 1.0 / 3.0, field_name="weight m2"),
        "weight_m3": coerce_float(weight_m3, 1.0 / 3.0, field_name="weight m3"),
    }


def homogeneity_plot_title(*, window_size: float, time_step: float, sigma: float) -> str:
    return f"Homogeneity H(t) — window={window_size}, step={time_step}, sigma={sigma}"


def homogeneity_csv_save_arrays(results: dict[str, Any]) -> tuple[np.ndarray, str]:
    """Return ``(column_stack, header)`` for legacy H(t) CSV export."""
    t_arr = np.array(results["t"])
    h_arr = np.array(results["H"])
    if "m1" in results and len(results["m1"]) == len(h_arr):
        data = np.column_stack(
            [t_arr, h_arr, np.array(results["m1"]), np.array(results["m2"]), np.array(results["m3"])]
        )
        header = "t_quarterLength,H,m1,m2,m3"
    else:
        data = np.column_stack([t_arr, h_arr])
        header = "t_quarterLength,H"
    return data, header
