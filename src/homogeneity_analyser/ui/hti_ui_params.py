"""
Pure H_TI UI → analysis-parameter mapping and CSV row assembly (no Gradio).

Tested independently of ``callbacks.py`` so Gradio glue stays thin.
"""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.analyzers.hti_export_rows import HTI_CSV_COLUMNS, hti_csv_row_dict
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS
from homogeneity_analyser.ui.validation import parse_ui_float


def _ui_float(value: Any, *, default: float, field_name: str) -> float:
    parsed = parse_ui_float(value, default=default, field_name=field_name)
    return float(default if parsed is None else parsed)


def build_hti_analysis_params_from_ui(
    *,
    window_mode: Any = None,
    edge_policy: Any = None,
    time_step: Any = None,
    window_size: Any = None,
    window_ratio: Any = None,
    step_ratio: Any = None,
    min_window_size: Any = None,
    max_window_size: Any = None,
    min_time_step: Any = None,
    max_time_step: Any = None,
    target_window_count: Any = None,
    window_to_step_ratio: Any = None,
    register_ref_profile: Any = None,
    register_ref_override: Any = None,
    pitch_interpretation_mode: Any = None,
    harmonic_pitch_policy: Any = None,
    weight_instrument_uniformity: Any = None,
    weight_family_uniformity: Any = None,
    weight_technique_uniformity: Any = None,
    weight_register_proximity: Any = None,
    same_subfamily_relief_factor: Any = None,
    timbral_affinity_profile: Any = None,
    timbral_affinity_relief_factor: Any = None,
    dynamic_affinity_enabled: Any = None,
    export_affinity_pairs: bool = False,
    include_symbolic_blend_potential: bool = False,
    include_acoustic_proxy: bool = False,
    acoustic_proxy_profile: Any = None,
    acoustic_proxy_pairwise_export: bool = False,
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Map Gradio/UI field values to ``run_symbolic_ti_homogeneity_analysis`` params.

    Raises ``ValueError`` on invalid numeric input (caller may wrap as ``gr.Error``).
    """
    base = dict(defaults or DEFAULT_HTI_PARAMS)
    wm = str(window_mode or base.get("window_mode") or "manual").strip()
    epol = str(edge_policy or base.get("edge_policy") or "mark_partial_windows").strip()
    ts = _ui_float(time_step, default=float(base["time_step"]), field_name="time step")
    ws = _ui_float(window_size, default=float(base["window_size"]), field_name="window size")
    prof = str(register_ref_profile or base.get("register_ref_profile") or "balanced").strip().lower()
    ovr: float | None = None
    if register_ref_override is not None and str(register_ref_override).strip() != "":
        ovr = _ui_float(register_ref_override, default=0.0, field_name="register reference override")
        if ovr <= 0:
            raise ValueError("Manual register reference override must be > 0 when set.")
    wi = (
        _ui_float(weight_instrument_uniformity, default=0.40, field_name="weight instrument uniformity")
        if weight_instrument_uniformity is not None
        else float(base["weight_instrument_uniformity"])
    )
    wf = (
        _ui_float(weight_family_uniformity, default=0.25, field_name="weight family uniformity")
        if weight_family_uniformity is not None
        else float(base["weight_family_uniformity"])
    )
    wtc = (
        _ui_float(weight_technique_uniformity, default=0.15, field_name="weight technique uniformity")
        if weight_technique_uniformity is not None
        else float(base["weight_technique_uniformity"])
    )
    wrg = (
        _ui_float(weight_register_proximity, default=0.20, field_name="weight register proximity")
        if weight_register_proximity is not None
        else float(base["weight_register_proximity"])
    )
    if wm == "manual" and (ts <= 0 or ws <= 0):
        raise ValueError("Time step and window size must be > 0 when window_mode is manual.")
    wr = _ui_float(window_ratio, default=float(base["window_ratio"]), field_name="window ratio (adaptive)")
    sr = _ui_float(step_ratio, default=float(base["step_ratio"]), field_name="step ratio (adaptive)")
    min_w = _ui_float(
        min_window_size,
        default=float(base["min_window_size"]),
        field_name="min window size (adaptive clamps)",
    )
    max_w = _ui_float(
        max_window_size,
        default=float(base["max_window_size"]),
        field_name="max window size (adaptive clamps)",
    )
    min_ts = _ui_float(
        min_time_step,
        default=float(base["min_time_step"]),
        field_name="min time step (adaptive clamps)",
    )
    max_ts = _ui_float(
        max_time_step,
        default=float(base["max_time_step"]),
        field_name="max time step (adaptive clamps)",
    )
    twc = _ui_float(
        target_window_count,
        default=float(base["target_window_count"]),
        field_name="target window count",
    )
    wtsr = _ui_float(
        window_to_step_ratio,
        default=float(base["window_to_step_ratio"]),
        field_name="window to step ratio",
    )
    if min_w <= 0 or max_w <= 0 or min_ts <= 0 or max_ts <= 0:
        raise ValueError("Adaptive min/max window and step must be > 0.")
    if max_w + 1e-12 < min_w or max_ts + 1e-12 < min_ts:
        raise ValueError("max_window_size must be ≥ min_window_size; max_time_step must be ≥ min_time_step.")

    pim = str(pitch_interpretation_mode or base.get("pitch_interpretation_mode") or "musicxml_sounding")
    hpol = str(harmonic_pitch_policy or base.get("harmonic_pitch_policy") or "conservative").strip().lower()
    if same_subfamily_relief_factor is None:
        sfr = float(base["same_subfamily_relief_factor"])
    else:
        sfr = _ui_float(same_subfamily_relief_factor, default=0.0, field_name="same-subfamily relief")
        if sfr < 0.0 or sfr > 1.0:
            raise ValueError("Same-subfamily relief must be between 0 and 1.")

    params: dict[str, Any] = {
        "window_mode": wm,
        "edge_policy": epol,
        "window_ratio": wr,
        "step_ratio": sr,
        "min_window_size": min_w,
        "max_window_size": max_w,
        "min_time_step": min_ts,
        "max_time_step": max_ts,
        "target_window_count": twc,
        "window_to_step_ratio": wtsr,
        "time_step": ts,
        "window_size": ws,
        "register_ref_profile": prof,
        "register_ref_semitones": ovr,
        "pitch_interpretation_mode": pim.strip(),
        "harmonic_pitch_policy": hpol,
        "weight_instrument_uniformity": wi,
        "weight_family_uniformity": wf,
        "weight_technique_uniformity": wtc,
        "weight_register_proximity": wrg,
        "same_subfamily_relief_factor": sfr,
        "timbral_affinity_profile": str(
            timbral_affinity_profile or base.get("timbral_affinity_profile") or "conservative"
        ).strip(),
        "timbral_affinity_relief_factor": (
            float(base["timbral_affinity_relief_factor"])
            if timbral_affinity_relief_factor is None
            else _ui_float(
                timbral_affinity_relief_factor,
                default=0.0,
                field_name="timbral affinity relief",
            )
        ),
        "dynamic_affinity_enabled": bool(base["dynamic_affinity_enabled"])
        if dynamic_affinity_enabled is None
        else bool(dynamic_affinity_enabled),
        "export_affinity_pairs": bool(export_affinity_pairs),
        "include_symbolic_blend_potential": bool(include_symbolic_blend_potential),
        "include_acoustic_proxy": bool(include_acoustic_proxy),
        "acoustic_proxy_profile": str(
            acoustic_proxy_profile or base.get("acoustic_proxy_profile") or "conservative"
        ).strip(),
        "acoustic_proxy_pairwise_export": bool(acoustic_proxy_pairwise_export),
    }
    tar_chk = float(params["timbral_affinity_relief_factor"])
    if tar_chk < 0.0 or tar_chk > 1.0:
        raise ValueError("Timbral affinity relief must be between 0 and 1.")
    return params


def hti_results_plot_title(
    *,
    window_size_effective: float,
    time_step_effective: float,
    window_mode: str,
) -> str:
    return (
        f"H_TI(t) — symbolic timbral–instrumental homogeneity "
        f"(window={window_size_effective}, step={time_step_effective}; mode={window_mode})"
    )


def build_hti_csv_rows_from_results(results: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """One CSV-ready dict per window (JSON-encoded dict/list columns applied)."""
    n = len(results["t"])
    rows: list[dict[str, Any]] = []
    for i in range(n):
        row: dict[str, Any] = {}
        for col in HTI_CSV_COLUMNS:
            if col == "t_quarterLength":
                row[col] = results["t"][i]
            else:
                row[col] = results[col][i]
        rows.append(hti_csv_row_dict(row))
    return rows
