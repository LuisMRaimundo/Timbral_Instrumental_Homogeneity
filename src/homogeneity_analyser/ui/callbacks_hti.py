"""Gradio callback: primary H_TI product path."""

from __future__ import annotations

from typing import Any

import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd

from homogeneity_analyser.analyzers.hti_export_rows import HTI_CSV_COLUMNS
from homogeneity_analyser.plotting import make_hti_figure, make_hti_figure_plotly
from homogeneity_analyser.services.analysis_service import run_symbolic_ti_homogeneity_analysis
from homogeneity_analyser.services.json_export import build_hti_export, write_json_export
from homogeneity_analyser.ui.callback_helpers import export_plotly_figure_static
from homogeneity_analyser.ui.hti_ui_params import (
    build_hti_analysis_params_from_ui,
    build_hti_csv_rows_from_results,
    hti_results_plot_title,
)
from homogeneity_analyser.ui.validation import validate_uploaded_score
from homogeneity_analyser.utils.output_paths import new_export_path

def run_hti_app(
    progress=gr.Progress(),
    file_obj=None,
    window_mode=None,
    edge_policy=None,
    time_step=None,
    window_size=None,
    window_ratio=None,
    step_ratio=None,
    min_window_size=None,
    max_window_size=None,
    min_time_step=None,
    max_time_step=None,
    target_window_count=None,
    window_to_step_ratio=None,
    register_ref_profile=None,
    register_ref_override=None,
    pitch_interpretation_mode=None,
    harmonic_pitch_policy=None,
    weight_instrument_uniformity=None,
    weight_family_uniformity=None,
    weight_technique_uniformity=None,
    weight_register_proximity=None,
    same_subfamily_relief_factor=None,
    timbral_affinity_profile=None,
    timbral_affinity_relief_factor=None,
    dynamic_affinity_enabled=None,
    export_affinity_pairs=False,
    include_symbolic_blend_potential=False,
    include_acoustic_proxy=False,
    acoustic_proxy_profile=None,
    acoustic_proxy_pairwise_export=False,
    interactive_plot=False,
):
    """Symbolic timbral–instrumental homogeneity H_TI(t) — single primary metric."""
    progress_callback = lambda frac, desc: progress(frac, desc=desc) if progress else None
    score_path = validate_uploaded_score(file_obj)
    try:
        params = build_hti_analysis_params_from_ui(
            window_mode=window_mode,
            edge_policy=edge_policy,
            time_step=time_step,
            window_size=window_size,
            window_ratio=window_ratio,
            step_ratio=step_ratio,
            min_window_size=min_window_size,
            max_window_size=max_window_size,
            min_time_step=min_time_step,
            max_time_step=max_time_step,
            target_window_count=target_window_count,
            window_to_step_ratio=window_to_step_ratio,
            register_ref_profile=register_ref_profile,
            register_ref_override=register_ref_override,
            pitch_interpretation_mode=pitch_interpretation_mode,
            harmonic_pitch_policy=harmonic_pitch_policy,
            weight_instrument_uniformity=weight_instrument_uniformity,
            weight_family_uniformity=weight_family_uniformity,
            weight_technique_uniformity=weight_technique_uniformity,
            weight_register_proximity=weight_register_proximity,
            same_subfamily_relief_factor=same_subfamily_relief_factor,
            timbral_affinity_profile=timbral_affinity_profile,
            timbral_affinity_relief_factor=timbral_affinity_relief_factor,
            dynamic_affinity_enabled=dynamic_affinity_enabled,
            export_affinity_pairs=export_affinity_pairs,
            include_symbolic_blend_potential=include_symbolic_blend_potential,
            include_acoustic_proxy=include_acoustic_proxy,
            acoustic_proxy_profile=acoustic_proxy_profile,
            acoustic_proxy_pairwise_export=acoustic_proxy_pairwise_export,
        )
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    ws = float(params["window_size"])
    ts = float(params["time_step"])
    wm = str(params["window_mode"])
    out = run_symbolic_ti_homogeneity_analysis(score_path, params, progress_callback=progress_callback)
    if out.get("error"):
        raise gr.Error(out["error"])
    results = out["results"]
    summary = out["summary"]
    pout = out.get("parameters") or {}
    w_disp = pout.get("window_size_effective", ws)
    ts_disp = pout.get("time_step_effective", ts)
    title = hti_results_plot_title(
        window_size_effective=float(w_disp),
        time_step_effective=float(ts_disp),
        window_mode=str(pout.get("window_mode", wm)),
    )
    if interactive_plot:
        fig = make_hti_figure_plotly(results, title=title)
        plot_path = export_plotly_figure_static(fig, "hti_plot_")
    else:
        fig = make_hti_figure(results, title=title)
        plot_path = new_export_path("hti_plot_", ".png")
        fig.savefig(plot_path, dpi=200)
        plt.close(fig)

    csv_rows = build_hti_csv_rows_from_results(results)
    csv_path = new_export_path("hti_", ".csv")
    pd.DataFrame(csv_rows, columns=list(HTI_CSV_COLUMNS)).to_csv(csv_path, index=False)

    json_path = new_export_path("hti_data_", ".json")
    write_json_export(json_path, build_hti_export(score_path, out))
    pair_rows = results.get("affinity_pair_rows") or []
    if pair_rows:
        ap_path = new_export_path("hti_affinity_pairs_", ".csv")
        pd.DataFrame(pair_rows).to_csv(str(ap_path), index=False)
        summary = f"{summary}\n\nPairwise timbral affinity rows: {ap_path}"
    return fig, summary, str(csv_path), str(plot_path), str(json_path)
