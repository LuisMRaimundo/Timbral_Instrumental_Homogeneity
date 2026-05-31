"""Gradio callbacks: legacy multimetric paths (H, H_timbral, U, combined JSON 1.8)."""

from __future__ import annotations

from typing import Any

import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from homogeneity_analyser.plotting import (
    make_cluster_figure,
    make_cluster_figure_plotly,
    make_cluster_orch_fusion_diagnostics_figure,
    make_cluster_orch_fusion_diagnostics_figure_plotly,
    make_fusion_acoustic_heuristic_figure,
    make_fusion_acoustic_heuristic_figure_plotly,
    make_gauge_figure,
    make_gauge_placeholder,
    make_homogeneity_figure,
    make_homogeneity_figure_plotly,
    make_notated_fusion_potential_figure,
    make_notated_fusion_potential_figure_plotly,
    make_orchestration_symbolic_figure,
    make_orchestration_symbolic_figure_plotly,
    make_register_figure,
    make_register_figure_plotly,
    make_timbral_figure,
    make_timbral_figure_plotly,
)
from homogeneity_analyser.services.analysis_service import (
    TIMBRAL_DIAGNOSTIC_TABLE_HEADERS,
    flatten_timbral_diagnostic_row,
    run_both_and_combine,
    run_homogeneity_analysis,
    run_orchestration_symbolic_analysis,
    run_register_uniformity_analysis,
    run_timbral_analysis,
    write_timbral_diagnostics_csv,
)
from homogeneity_analyser.services.json_export import (
    build_combined_export,
    build_homogeneity_export,
    build_orchestration_symbolic_export,
    build_register_export,
    build_timbral_export,
    enrich_timbral_diagnostics_list,
    write_json_export,
)
from homogeneity_analyser.services.result_assembly import CLUSTER_ORCH_FUSION_DIAGNOSTICS_COLUMNS
from homogeneity_analyser.ui.callback_helpers import (
    export_plotly_figure_static,
    timbral_parse_error_return,
    ui_float_gradio,
)
from homogeneity_analyser.ui.legacy_multimetric_ui_params import (
    build_combined_homogeneity_weight_params,
    build_combined_orchestration_weight_params,
    build_combined_summary_text,
    build_orchestration_symbolic_params_from_ui,
    build_register_params_from_ui,
    cluster_orch_fusion_plot_bundle,
    cluster_orch_fusion_plot_title,
    cluster_plot_title,
    homogeneity_combined_plot_title,
    orchestration_symbolic_plot_title,
    parse_notated_fusion_relief_ui,
    register_plot_title,
)
from homogeneity_analyser.ui.legacy_ui_params import (
    _ui_float,
    build_homogeneity_params_from_ui,
    homogeneity_csv_save_arrays,
    homogeneity_plot_title,
)
from homogeneity_analyser.ui.timbral_ui_params import (
    build_timbral_analysis_params_from_ui,
    timbral_config_from_optional,
    timbral_export_params_dict,
    timbral_plot_title,
)
from homogeneity_analyser.ui.validation import validate_uploaded_score
from homogeneity_analyser.utils.output_paths import new_export_path

def run_app(
    progress=gr.Progress(),
    file_obj=None,
    time_step=0.25,
    window_size=4.0,
    sigma=12.0,
    pitch_space="absolute",
    pitch_bin_step=1.0,
    silence_intra_value=0.5,
    silence_transition_value=0.5,
    allow_partial_scales=True,
    weight_m1=None,
    weight_m2=None,
    weight_m3=None,
    interactive_plot=False,
    single_aggregate=False,
    gauge_color=None,
):
    progress_callback = lambda frac, desc: progress(frac, desc=desc) if progress else None
    score_path = validate_uploaded_score(file_obj)
    try:
        params = build_homogeneity_params_from_ui(
            time_step=time_step,
            window_size=window_size,
            sigma=sigma,
            pitch_space=pitch_space,
            pitch_bin_step=pitch_bin_step,
            silence_intra_value=silence_intra_value,
            silence_transition_value=silence_transition_value,
            allow_partial_scales=allow_partial_scales,
            single_aggregate=single_aggregate,
            weight_m1=weight_m1,
            weight_m2=weight_m2,
            weight_m3=weight_m3,
        )
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    time_step = float(params["time_step"])
    window_size = float(params["window_size"])
    sigma = float(params["sigma"])
    out = run_homogeneity_analysis(score_path, params, progress_callback=progress_callback)
    if out.get("error"):
        raise gr.Error(out["error"])
    results = out["results"]
    plot_results = out["plot_results"]
    summary = out["summary"]
    H = np.array(results["H"], dtype=float)

    title = homogeneity_plot_title(window_size=window_size, time_step=time_step, sigma=sigma)
    if interactive_plot:
        fig = make_homogeneity_figure_plotly(plot_results, title=title)
        plot_path = export_plotly_figure_static(fig, "homogeneity_plot_")
    else:
        fig = make_homogeneity_figure(plot_results, title=title)
        plot_path = new_export_path("homogeneity_plot_", ".png")
        fig.savefig(plot_path, dpi=200)
        plt.close(fig)
    csv_path = new_export_path("homogeneity_", ".csv")
    csv_data, csv_header = homogeneity_csv_save_arrays(results)
    np.savetxt(csv_path, csv_data, delimiter=",", header=csv_header, comments="")
    if single_aggregate:
        gauge_fig = make_gauge_figure(
            float(H[0]), title="Homogeneity degree (static chord)", gauge_color=gauge_color or "Green"
        )
    else:
        gauge_fig = make_gauge_placeholder()
    json_path = new_export_path("homogeneity_data_", ".json")
    write_json_export(json_path, build_homogeneity_export(score_path, params, out))
    return fig, gauge_fig, summary, csv_path, plot_path, json_path


def run_timbral_app(
    progress=gr.Progress(),
    file_obj=None,
    time_step=None,
    window_size=None,
    interactive_plot=None,
    weight_instrument=None,
    weight_register=None,
    family_bonus=None,
    register_ref_semitones=None,
    include_timbral_diagnostics=False,
):
    """Legacy H_timbral diagnostic run (backward compatibility). Best with MusicXML."""
    progress_callback = lambda frac, desc: progress(frac, desc=desc) if progress else None
    score_path = validate_uploaded_score(file_obj)
    try:
        t_params = build_timbral_analysis_params_from_ui(
            time_step=time_step,
            window_size=window_size,
            weight_instrument=weight_instrument,
            weight_register=weight_register,
            family_bonus=family_bonus,
            register_ref_semitones=register_ref_semitones,
            include_timbral_diagnostics=include_timbral_diagnostics,
        )
    except ValueError as exc:
        return timbral_parse_error_return(interactive_plot, str(exc))
    time_step = float(t_params["time_step"])
    window_size = float(t_params["window_size"])
    out = run_timbral_analysis(score_path, t_params, progress_callback=progress_callback)
    if out.get("error"):
        raise gr.Error(out["error"])
    results_t = out["results"]
    summary_t = out["summary"]
    title_t = timbral_plot_title(window_size=window_size, time_step=time_step)
    if interactive_plot:
        fig_t = make_timbral_figure_plotly(results_t, title=title_t)
        plot_path_t = export_plotly_figure_static(fig_t, "timbral_plot_")
    else:
        fig_t = make_timbral_figure(results_t, title=title_t)
        plot_path_t = new_export_path("timbral_plot_", ".png")
        fig_t.savefig(plot_path_t, dpi=200)
        plt.close(fig_t)
    csv_path_t = new_export_path("timbral_", ".csv")
    np.savetxt(
        csv_path_t,
        np.column_stack([np.array(results_t["t"]), np.array(results_t["H_timbral"])]),
        delimiter=",",
        header="t_quarterLength,H_timbral",
        comments="",
    )
    export_params = timbral_export_params_dict(t_params)
    json_path_t = new_export_path("timbral_data_", ".json")
    write_json_export(json_path_t, build_timbral_export(score_path, export_params, out))

    diag_rows: list[dict[str, Any]] = []
    diag_csv_path: str | None = None
    if t_params.get("return_components") and results_t.get("H_timbral_diagnostics"):
        tlist = list(results_t["t"])
        dlist = list(enrich_timbral_diagnostics_list(list(results_t["H_timbral_diagnostics"])) or [])
        diag_csv_p = new_export_path("timbral_diagnostics_", ".csv")
        write_timbral_diagnostics_csv(diag_csv_p, tlist, dlist)
        diag_csv_path = str(diag_csv_p)
        diag_rows = [flatten_timbral_diagnostic_row(t, d) for t, d in zip(tlist, dlist, strict=True)]

    return (
        fig_t,
        summary_t,
        csv_path_t,
        plot_path_t,
        json_path_t,
        gr.update(value=diag_rows, headers=TIMBRAL_DIAGNOSTIC_TABLE_HEADERS),
        gr.update(value=diag_csv_path),
    )


def run_orch_symbolic_app(
    progress=gr.Progress(),
    file_obj=None,
    time_step=None,
    window_size=None,
    interactive_plot=None,
    weight_orch_instr=None,
    weight_orch_fam=None,
    weight_orch_tech=None,
):
    """Herfindahl-only symbolic orchestration H_orchestration_symbolic (not H_timbral)."""
    progress_callback = lambda frac, desc: progress(frac, desc=desc) if progress else None
    score_path = validate_uploaded_score(file_obj)
    try:
        params = build_orchestration_symbolic_params_from_ui(
            time_step=time_step,
            window_size=window_size,
            weight_orch_instr=weight_orch_instr,
            weight_orch_fam=weight_orch_fam,
            weight_orch_tech=weight_orch_tech,
        )
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    time_step = float(params["time_step"])
    window_size = float(params["window_size"])
    out = run_orchestration_symbolic_analysis(score_path, params, progress_callback=progress_callback)
    if out.get("error"):
        raise gr.Error(out["error"])
    results_o = out["results"]
    summary_o = out["summary"]
    title_o = orchestration_symbolic_plot_title(window_size=window_size, time_step=time_step)
    if interactive_plot:
        fig_o = make_orchestration_symbolic_figure_plotly(results_o, title=title_o)
        plot_path_o = export_plotly_figure_static(fig_o, "orch_symbolic_plot_")
    else:
        fig_o = make_orchestration_symbolic_figure(results_o, title=title_o)
        plot_path_o = new_export_path("orch_symbolic_plot_", ".png")
        fig_o.savefig(plot_path_o, dpi=200)
        plt.close(fig_o)
    csv_path_o = new_export_path("orch_symbolic_", ".csv")
    np.savetxt(
        csv_path_o,
        np.column_stack([np.array(results_o["t"]), np.array(results_o["H_orchestration_symbolic"])]),
        delimiter=",",
        header="t_quarterLength,H_orchestration_symbolic",
        comments="",
    )
    json_path_o = new_export_path("orch_symbolic_data_", ".json")
    write_json_export(json_path_o, build_orchestration_symbolic_export(score_path, params, out))
    return fig_o, summary_o, csv_path_o, plot_path_o, json_path_o


def run_register_app(
    progress=gr.Progress(),
    file_obj=None,
    register_low=None,
    register_high=None,
    time_step=None,
    window_size=None,
    interactive_plot=None,
):
    """Register uniformity U(t): evenness of pitch distribution within [register_low, register_high]."""
    progress_callback = lambda frac, desc: progress(frac, desc=desc) if progress else None
    score_path = validate_uploaded_score(file_obj)
    try:
        params = build_register_params_from_ui(
            register_low=register_low,
            register_high=register_high,
            time_step=time_step,
            window_size=window_size,
        )
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    window_size = float(params["window_size"])
    out = run_register_uniformity_analysis(score_path, params, progress_callback=progress_callback)
    if out.get("error"):
        raise gr.Error(out["error"])
    results_u = out["results"]
    summary_u = out["summary"]
    title_u = register_plot_title(
        register_low=str(params["register_low"]),
        register_high=str(params["register_high"]),
        window_size=window_size,
    )
    if interactive_plot:
        fig_u = make_register_figure_plotly(results_u, title=title_u)
        plot_path_u = export_plotly_figure_static(fig_u, "register_plot_")
    else:
        fig_u = make_register_figure(results_u, title=title_u)
        plot_path_u = new_export_path("register_plot_", ".png")
        fig_u.savefig(plot_path_u, dpi=200)
        plt.close(fig_u)
    csv_path_u = new_export_path("register_", ".csv")
    t_arr = np.array(results_u["t"])
    u_arr = np.array(results_u["U"])
    np.savetxt(csv_path_u, np.column_stack([t_arr, u_arr]), delimiter=",", header="t_quarterLength,U", comments="")
    json_path_u = new_export_path("register_data_", ".json")
    write_json_export(json_path_u, build_register_export(score_path, params, out))
    return fig_u, summary_u, csv_path_u, plot_path_u, json_path_u


def run_both_app(
    file_obj,
    time_step,
    window_size,
    sigma,
    interactive_plot,
    weight_m1=None,
    weight_m2=None,
    weight_m3=None,
    weight_instrument=None,
    weight_register=None,
    family_bonus=None,
    register_ref_semitones=None,
    weight_orch_instr=None,
    weight_orch_fam=None,
    weight_orch_tech=None,
    nf_relief_profile: str = "balanced",
    nf_relief_override: str | None = None,
):
    """Run homogeneity, H_timbral, H_cluster, H_orchestration_symbolic, and H_fusion_acoustic_heuristic."""
    score_path = validate_uploaded_score(file_obj)
    try:
        time_step = _ui_float(time_step, default=0.25, field_name="time step")
        window_size = _ui_float(window_size, default=4.0, field_name="window size")
        sigma = _ui_float(sigma, default=12.0, field_name="sigma")
        if time_step <= 0 or window_size <= 0:
            raise ValueError("Time step and window size must be > 0.")
        if sigma <= 0:
            raise ValueError("Sigma must be > 0.")
        homogeneity_params = build_combined_homogeneity_weight_params(
            weight_m1=weight_m1, weight_m2=weight_m2, weight_m3=weight_m3
        )
        orchestration_params = build_combined_orchestration_weight_params(
            weight_orch_instr=weight_orch_instr,
            weight_orch_fam=weight_orch_fam,
            weight_orch_tech=weight_orch_tech,
        )
        timbral_config = timbral_config_from_optional(
            weight_instrument, weight_register, family_bonus, register_ref_semitones
        )
        nfd = parse_notated_fusion_relief_ui(nf_relief_profile, nf_relief_override)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    timbral_params = {"time_step": time_step, "window_size": window_size, "timbral_config": timbral_config}
    out = run_both_and_combine(
        score_path,
        time_step=time_step,
        window_size=window_size,
        sigma=sigma,
        homogeneity_params=homogeneity_params,
        timbral_params=timbral_params,
        orchestration_params=orchestration_params,
        notated_fusion_params=nfd,
    )
    if out.get("error"):
        raise gr.Error(out["error"])
    out_h = out["out_homogeneity"]
    out_t = out["out_timbral"]
    out_c = out["out_cluster"]
    out_o = out["out_orchestration_symbolic"]
    out_f = out.get("out_fusion_acoustic_heuristic") or {}
    out_nf = out.get("out_notated_fusion_potential") or {}
    res_c = out_c["results"]
    res_o = (out_o or {}).get("results") or {}
    res_nf = (out_nf.get("results") or {}) if isinstance(out_nf, dict) else {}
    res_f = (out_f.get("results") or {}) if isinstance(out_f, dict) else {}
    title_orch = orchestration_symbolic_plot_title(window_size=window_size, time_step=time_step)
    title_nf = f"H_notated_fusion_potential(t) — window={window_size}, step={time_step}"
    title_f = f"H_fusion_acoustic_heuristic(t) — window={window_size}, step={time_step}"
    title_t = timbral_plot_title(window_size=window_size, time_step=time_step)
    if interactive_plot:
        fig_h = make_homogeneity_figure_plotly(
            out_h["plot_results"],
            title=homogeneity_combined_plot_title(window_size=window_size, time_step=time_step),
        )
        fig_c = make_cluster_figure_plotly(res_c, title=cluster_plot_title(window_size=window_size))
        fig_o = make_orchestration_symbolic_figure_plotly(res_o, title=title_orch)
        if res_nf.get("t") and res_nf.get("H_notated_fusion_potential"):
            fig_nf = make_notated_fusion_potential_figure_plotly(res_nf, title=title_nf)
        else:
            fig_nf = make_cluster_figure_plotly(
                {"t": [0.0], "H_cluster": [0.5]},
                title="H_notated_fusion unavailable",
            )
        if res_f.get("t") and res_f.get("H_fusion_acoustic_heuristic"):
            fig_f = make_fusion_acoustic_heuristic_figure_plotly(res_f, title=title_f)
        else:
            fig_f = make_cluster_figure_plotly({"t": [0.0], "H_cluster": [0.5]}, title="H_fusion (unavailable)")
        fig_t = make_timbral_figure_plotly(out_t["results"], title=title_t)
        plot_path_h = export_plotly_figure_static(fig_h, "combined_homogeneity_plot_")
        plot_path_c = export_plotly_figure_static(fig_c, "combined_cluster_plot_")
        plot_path_o = export_plotly_figure_static(fig_o, "combined_orch_symbolic_plot_")
        plot_path_nf = export_plotly_figure_static(fig_nf, "combined_notated_fusion_plot_")
        plot_path_f = export_plotly_figure_static(fig_f, "combined_fusion_plot_")
        plot_path_t = export_plotly_figure_static(fig_t, "combined_timbral_plot_")
    else:
        fig_h = make_homogeneity_figure(
            out_h["plot_results"],
            title=homogeneity_combined_plot_title(window_size=window_size, time_step=time_step),
        )
        fig_c = make_cluster_figure(res_c, title=cluster_plot_title(window_size=window_size))
        fig_o = make_orchestration_symbolic_figure(res_o, title=title_orch)
        if res_nf.get("t") and res_nf.get("H_notated_fusion_potential"):
            fig_nf = make_notated_fusion_potential_figure(res_nf, title=title_nf)
        else:
            fig_nf = make_cluster_figure(
                {"t": [0.0], "H_cluster": [0.5]},
                title="H_notated_fusion unavailable",
            )
        if res_f.get("t") and res_f.get("H_fusion_acoustic_heuristic"):
            fig_f = make_fusion_acoustic_heuristic_figure(res_f, title=title_f)
        else:
            fig_f = make_cluster_figure({"t": [0.0], "H_cluster": [0.5]}, title="H_fusion (unavailable)")
        fig_t = make_timbral_figure(out_t["results"], title=title_t)
        plot_path_h = new_export_path("combined_homogeneity_plot_", ".png")
        fig_h.savefig(plot_path_h, dpi=200)
        plot_path_c = new_export_path("combined_cluster_plot_", ".png")
        fig_c.savefig(plot_path_c, dpi=200)
        plot_path_o = new_export_path("combined_orch_symbolic_plot_", ".png")
        fig_o.savefig(plot_path_o, dpi=200)
        plot_path_nf = new_export_path("combined_notated_fusion_plot_", ".png")
        fig_nf.savefig(plot_path_nf, dpi=200)
        plot_path_f = new_export_path("combined_fusion_plot_", ".png")
        fig_f.savefig(plot_path_f, dpi=200)
        plot_path_t = new_export_path("combined_timbral_plot_", ".png")
        fig_t.savefig(plot_path_t, dpi=200)
        plt.close(fig_h)
        plt.close(fig_c)
        plt.close(fig_o)
        plt.close(fig_nf)
        plt.close(fig_f)
        plt.close(fig_t)
    combined_csv_path = new_export_path("combined_", ".csv")
    Path(combined_csv_path).write_text(out["combined_csv_content"], encoding="utf-8")
    summary_both = build_combined_summary_text(
        out_h_summary=out_h["summary"],
        out_t_summary=out_t["summary"],
        out_c_summary=str(out_c.get("summary") or ""),
        out_o_summary=str(out_o.get("summary") if out_o else ""),
        out_nf_summary=str(out_nf.get("summary") or ""),
        out_f_summary=str(out_f.get("summary") or ""),
    )
    full_h_params = {
        "time_step": time_step,
        "window_size": window_size,
        "sigma": sigma,
        "single_aggregate": False,
        **homogeneity_params,
    }
    json_combined = new_export_path("combined_data_", ".json")
    write_json_export(
        json_combined,
        build_combined_export(score_path, full_h_params, timbral_params, out),
    )
    cof_bundle = cluster_orch_fusion_plot_bundle(out.get("combined") or {})
    title_cof = cluster_orch_fusion_plot_title(window_size=window_size, time_step=time_step)
    if interactive_plot:
        fig_cof = make_cluster_orch_fusion_diagnostics_figure_plotly(cof_bundle, title=title_cof)
        plot_path_cof = export_plotly_figure_static(fig_cof, "cof_diagnostics_plot_")
    else:
        fig_cof = make_cluster_orch_fusion_diagnostics_figure(cof_bundle, title=title_cof)
        plot_path_cof = new_export_path("cof_diagnostics_plot_", ".png")
        fig_cof.savefig(plot_path_cof, dpi=200)
        plt.close(fig_cof)
    cof_rows = out.get("cluster_orch_fusion_diagnostics_rows") or []
    cof_csv_text = out.get("cluster_orch_fusion_diagnostics_csv_content") or ""
    cof_csv_path = new_export_path("cluster_orch_fusion_diagnostics_", ".csv")
    Path(cof_csv_path).write_text(cof_csv_text, encoding="utf-8")
    cof_headers = list(CLUSTER_ORCH_FUSION_DIAGNOSTICS_COLUMNS)
    return (
        fig_h,
        fig_c,
        fig_o,
        fig_nf,
        fig_f,
        fig_t,
        summary_both,
        combined_csv_path,
        json_combined,
        plot_path_h,
        plot_path_c,
        plot_path_o,
        plot_path_nf,
        plot_path_f,
        plot_path_t,
        fig_cof,
        gr.update(value=cof_rows, headers=cof_headers),
        str(cof_csv_path),
        plot_path_cof,
    )
