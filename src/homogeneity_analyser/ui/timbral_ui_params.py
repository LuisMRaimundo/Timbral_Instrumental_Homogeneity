"""Pure UI helpers for legacy H_timbral diagnostic path (no Gradio)."""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.ui.validation import coerce_float, parse_ui_float

TIMBRAL_PARSE_ERROR_STUB: dict[str, list[float]] = {"t": [0.0], "H_timbral": [0.5]}


def timbral_config_from_optional(
    weight_instrument: Any,
    weight_register: Any,
    family_bonus: Any,
    register_ref_semitones: Any,
) -> dict[str, float] | None:
    """Build ``timbral_config`` when any H_timbral tuning field is set in the UI."""
    if (
        weight_instrument is None
        and weight_register is None
        and family_bonus is None
        and register_ref_semitones is None
    ):
        return None
    timbral_config: dict[str, float] = {}
    if weight_instrument is not None:
        timbral_config["weight_instrument"] = coerce_float(weight_instrument, 0.65, field_name="weight_instrument")
    if weight_register is not None:
        timbral_config["weight_register"] = coerce_float(weight_register, 0.35, field_name="weight_register")
    if family_bonus is not None:
        timbral_config["family_bonus"] = coerce_float(family_bonus, 0.65, field_name="family_bonus")
    if register_ref_semitones is not None:
        timbral_config["register_ref_semitones"] = coerce_float(
            register_ref_semitones, 3.0, field_name="register_ref_semitones"
        )
    return timbral_config


def build_timbral_analysis_params_from_ui(
    *,
    time_step: Any = None,
    window_size: Any = None,
    weight_instrument: Any = None,
    weight_register: Any = None,
    family_bonus: Any = None,
    register_ref_semitones: Any = None,
    include_timbral_diagnostics: bool = False,
) -> dict[str, Any]:
    """Raises ``ValueError`` on invalid numeric input."""
    ts = parse_ui_float(time_step, default=0.25, field_name="time step")
    ws = parse_ui_float(window_size, default=4.0, field_name="window size")
    if ts is None or ws is None or ts <= 0 or ws <= 0:
        raise ValueError("Time step and window size must be > 0.")
    timbral_config = timbral_config_from_optional(
        weight_instrument, weight_register, family_bonus, register_ref_semitones
    )
    want_diag = bool(include_timbral_diagnostics)
    return {
        "time_step": float(ts),
        "window_size": float(ws),
        "timbral_config": timbral_config,
        "return_components": want_diag,
    }


def timbral_plot_title(*, window_size: float, time_step: float) -> str:
    return f"Legacy H_timbral (diagnostic) — window={window_size}, step={time_step}"


def timbral_parse_error_plot_title(message: str) -> str:
    return f"Legacy H_timbral (diagnostic) — input error: {message}"


def timbral_parse_error_summary(message: str) -> str:
    return (
        "**Could not run legacy H_timbral** (numeric input).\n\n"
        f"{message}\n\n"
        "Use a single decimal separator: **0.25** (dot) or **0,25** (comma). "
        "Do not mix both in one value (e.g. 1,234.5)."
    )


def timbral_export_params_dict(analysis_params: dict[str, Any]) -> dict[str, Any]:
    """Params dict passed to ``build_timbral_export`` (mirrors analysis call)."""
    return {
        "time_step": analysis_params["time_step"],
        "window_size": analysis_params["window_size"],
        "timbral_config": analysis_params.get("timbral_config"),
        "return_components": analysis_params.get("return_components", False),
    }
