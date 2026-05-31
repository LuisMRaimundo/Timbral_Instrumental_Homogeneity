"""Gradio Blocks layout and application entrypoint — symbolic H_TI(t) only."""

from __future__ import annotations

from typing import cast

import gradio as gr

from homogeneity_analyser.analyzers.harmonic_pitch import HARMONIC_PITCH_POLICIES
from homogeneity_analyser.analyzers.pitch_interpretation import PITCH_INTERPRETATION_MODES
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS, DEFAULT_REGISTER_REF_PROFILE
from homogeneity_analyser.ui.callbacks import run_hti_app, run_loaded_xml_inspection
from homogeneity_analyser.ui.components import INTRO_MARKDOWN, METRICS_EXPLAINER
from homogeneity_analyser.utils.output_paths import cleanup_stale_exports


def build_demo() -> gr.Blocks:
    """Single-tab Gradio UI: H_TI(t) plus optional symbolic inspection."""
    demo = gr.Blocks(title="Orchomogeneity Analyser")
    with demo:
        gr.Markdown("# Orchomogeneity Analyser")
        gr.Markdown(
            "Score-derived symbolic timbral–instrumental homogeneity **H_TI** from MusicXML/MXL/MIDI "
            "(**symbolic notation only** — not audio analysis)."
        )
        gr.Markdown(
            "**Score-derived H_TI_core(t)** with **notated dynamic conditioning**. "
            "**MusicXML / MIDI only** — **no audio analysis**, no waveform or FFT on recordings, no SPL."
        )
        gr.Markdown("### H_TI_core(t)")
        gr.Markdown(INTRO_MARKDOWN)
        file_shared = gr.File(
            label="Upload score (MusicXML / MXL or MIDI)",
        )
        gr.Markdown(METRICS_EXPLAINER)
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Accordion("Window settings", open=True):
                    window_mode_in = gr.Dropdown(
                        choices=["manual", "auto_by_excerpt_duration", "auto_by_target_windows"],
                        value=str(DEFAULT_HTI_PARAMS.get("window_mode") or "manual"),
                        label="window_mode",
                        info="Manual keeps your time step and window size. Auto modes scale to excerpt length.",
                    )
                    edge_policy_in = gr.Dropdown(
                        choices=[
                            "include_partial_windows",
                            "drop_partial_windows",
                            "mark_partial_windows",
                        ],
                        value=str(DEFAULT_HTI_PARAMS.get("edge_policy") or "mark_partial_windows"),
                        label="edge_policy",
                        info="How windows that extend past the score end are handled in exports.",
                    )
                    gr.Markdown(
                        "Adaptive windows improve proportional comparison across excerpts but may reduce "
                        "strict comparability of absolute time-scale results. "
                        "**Always report the effective window and step values.**"
                    )
                    with gr.Group() as manual_window_grp:
                        time_step_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["time_step"]),
                            label="Time step (quarterLength)",
                            info="Sampling interval along the score timeline (manual mode).",
                        )
                        window_size_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["window_size"]),
                            label="Window size (quarterLength)",
                            info="Sliding window length for overlap mass (manual mode).",
                        )
                    with gr.Group(visible=False) as auto_clamps_grp:
                        min_window_size_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["min_window_size"]),
                            label="min_window_size (adaptive clamps)",
                        )
                        max_window_size_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["max_window_size"]),
                            label="max_window_size (adaptive clamps)",
                        )
                        min_time_step_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["min_time_step"]),
                            label="min_time_step (adaptive clamps)",
                        )
                        max_time_step_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["max_time_step"]),
                            label="max_time_step (adaptive clamps)",
                        )
                    with gr.Group(visible=False) as auto_duration_grp:
                        window_ratio_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["window_ratio"]),
                            label="window_ratio",
                            info="Nominal window length as a fraction of excerpt duration.",
                        )
                        step_ratio_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["step_ratio"]),
                            label="step_ratio",
                            info="Nominal time step as a fraction of excerpt duration.",
                        )
                    with gr.Group(visible=False) as auto_target_grp:
                        target_window_count_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["target_window_count"]),
                            label="target_window_count",
                            info="Approximate number of steps along the excerpt (auto by target windows).",
                        )
                        window_to_step_ratio_in = gr.Number(
                            value=cast(float, DEFAULT_HTI_PARAMS["window_to_step_ratio"]),
                            label="window_to_step_ratio",
                            info="Effective window size divided by effective time step.",
                        )

                def _hti_window_visibility(mode: str | None):
                    m = str(mode or "manual").strip()
                    is_manual = m == "manual"
                    is_dur = m == "auto_by_excerpt_duration"
                    is_tgt = m == "auto_by_target_windows"
                    return (
                        gr.update(visible=is_manual),
                        gr.update(visible=not is_manual),
                        gr.update(visible=is_dur),
                        gr.update(visible=is_tgt),
                    )

                window_mode_in.change(
                    _hti_window_visibility,
                    inputs=window_mode_in,
                    outputs=[manual_window_grp, auto_clamps_grp, auto_duration_grp, auto_target_grp],
                )
                register_profile_in = gr.Dropdown(
                    choices=["strict", "balanced", "permissive"],
                    value=str(DEFAULT_REGISTER_REF_PROFILE),
                    label="Register reference profile (semitones)",
                    info="strict=3, balanced=7, permissive=12 for span denominator in register proximity.",
                )
                register_ref_override_in = gr.Number(
                    value=None,
                    label="Manual register ref. override (semitones, optional)",
                    placeholder="e.g. 9 — leave empty to use profile",
                    info="When set, overrides the profile numeric ref.",
                )
                pitch_interpretation_in = gr.Dropdown(
                    choices=list(PITCH_INTERPRETATION_MODES),
                    value=str(DEFAULT_HTI_PARAMS["pitch_interpretation_mode"]),
                    label="Pitch interpretation mode",
                    info=(
                        "musicxml_sounding: full MusicXML transposition (default). "
                        "xml_pitch_as_real: concert pitches in XML; no transpose. "
                        "ignore_octave_transpositions_only: chromatic transpose only (octave shifts dropped). "
                        "xml_pitch_as_real_with_octave_transposers: real pitch for Bb/F instruments, "
                        "but still −12 for double bass / contrabassoon written one octave high."
                    ),
                )
                harmonic_pitch_policy_in = gr.Dropdown(
                    choices=list(HARMONIC_PITCH_POLICIES),
                    value=str(DEFAULT_HTI_PARAMS["harmonic_pitch_policy"]),
                    label="Harmonic pitch policy (strings / MusicXML harmonics)",
                    info=(
                        "conservative: explicit sounding pitch only; diamond noteheads stay unresolved. "
                        "infer_common_artificial: infer sounding pitch when artificial harmonic + two encoded "
                        "pitches allow a recognised touching interval. "
                        "written_as_sounding: treat diamond notehead pitch as sounding (exporter-specific)."
                    ),
                )
                gr.Markdown(
                    "**Optional component weights** (non-negative; renormalised per window when a layer is omitted):"
                )
                w_instr_in = gr.Number(
                    value=None,
                    label="Instrument uniformity weight (default 0.40)",
                    placeholder="0.40",
                )
                w_fam_in = gr.Number(
                    value=None,
                    label="Family uniformity weight (default 0.25)",
                    placeholder="0.25",
                )
                w_tech_in = gr.Number(
                    value=None,
                    label="Technique-state uniformity weight (default 0.15)",
                    placeholder="0.15",
                )
                w_reg_in = gr.Number(
                    value=None,
                    label="Register proximity weight (default 0.20)",
                    placeholder="0.20",
                )
                same_subfamily_relief_in = gr.Dropdown(
                    choices=[0.0, 0.5, 0.75],
                    value=cast(float, DEFAULT_HTI_PARAMS["same_subfamily_relief_factor"]),
                    label="Same-subfamily relief (interpretive H_TI only)",
                    info=(
                        "0 = strict canonical instruments (default). 0.5 / 0.75 blend toward instrumental "
                        "subfamily uniformity for **H_TI_subfamily_relieved** and CSV/JSON diagnostics only; "
                        "**H_TI_core** stays strict."
                    ),
                )
                gr.Markdown(
                    "**Optional symbolic timbral-affinity relief** — literature-governed pairwise rules "
                    "(taxonomy / organology / technique tags). **Not** measured acoustic fusion. "
                    "**H_TI_core** remains the strict reference."
                )
                timbral_affinity_profile_in = gr.Dropdown(
                    choices=["strict", "conservative", "moderate", "exploratory"],
                    value=str(DEFAULT_HTI_PARAMS["timbral_affinity_profile"]),
                    label="Timbral affinity profile",
                    info="Gates which symbolic similarity tiers apply (conservative recommended when relief > 0).",
                )
                timbral_affinity_relief_in = gr.Dropdown(
                    choices=[0.0, 0.35, 0.5, 0.75],
                    value=cast(float, DEFAULT_HTI_PARAMS["timbral_affinity_relief_factor"]),
                    label="Timbral affinity relief factor",
                    info="Blends strict instrument uniformity with timbral_affinity_uniformity for **H_TI_affinity_literature_relieved**.",
                )
                dynamic_affinity_enabled_in = gr.Checkbox(
                    value=bool(DEFAULT_HTI_PARAMS["dynamic_affinity_enabled"]),
                    label="Dynamic affinity qualifiers (interpretive)",
                    info="Adds timbral_affinity_dynamic_factor / H_TI_affinity_dynamic_conditioned; does not rescale H_TI_core.",
                )
                export_affinity_pairs_in = gr.Checkbox(
                    value=False,
                    label="Export pairwise affinity table (JSON + optional CSV sidecar)",
                    info="Adds event-pair rows to JSON and writes hti_affinity_pairs_*.csv next to other exports.",
                )
                with gr.Accordion(
                    "Optional symbolic interval-class / blend-potential diagnostics",
                    open=False,
                ):
                    gr.Markdown(
                        "Separate from **timbral-affinity relief** (above) and from **H_TA_acoustic_proxy** (below). "
                        "**Register compactness** remains inside **H_TI_core**. "
                        "Interval-class keys (e.g. **seconds_sevenths**) are **mod‑12 equivalence buckets** — "
                        "they do not assert that literal sevenths appear in the score. "
                        "Use **literal_interval_semitone_pair_mass** in exports for absolute semitone distances."
                    )
                    include_symbolic_blend_in = gr.Checkbox(
                        value=bool(DEFAULT_HTI_PARAMS.get("include_symbolic_blend_potential", False)),
                        label="Include optional symbolic interval-class / blend-potential diagnostics",
                        info=(
                            "Adds interval_class_profile (stable keys), interval_class_profile_display, "
                            "literal_interval_semitone_pair_mass, chromatic_mod12_pair_mass, symbolic_blend_potential, etc. "
                            "Does not modify H_TI_core; not the acoustic proxy; not audio/SPL/perceptual validation."
                        ),
                    )
                with gr.Accordion(
                    "Acoustic-aligned symbolic timbral-affinity proxy (optional secondary diagnostic)",
                    open=False,
                ):
                    gr.Markdown(
                        "**Score-derived** symbolic / acoustic-organology proxy (**H_TA_acoustic_proxy**). "
                        "**No audio**, **no FFT/SPL**, **not perceptually validated**. "
                        "For relative analytical comparison and sensitivity testing; **H_TI_core** stays strict."
                    )
                    include_acoustic_proxy_in = gr.Checkbox(
                        value=bool(DEFAULT_HTI_PARAMS.get("include_acoustic_proxy", False)),
                        label="Compute H_TA_acoustic_proxy / timbral_acoustic_affinity",
                    )
                    acoustic_proxy_profile_in = gr.Dropdown(
                        choices=["strict", "conservative", "moderate", "exploratory"],
                        value=str(DEFAULT_HTI_PARAMS["acoustic_proxy_profile"]),
                        label="Acoustic proxy profile",
                    )
                    acoustic_proxy_pairwise_export_in = gr.Checkbox(
                        value=bool(DEFAULT_HTI_PARAMS.get("acoustic_proxy_pairwise_export", False)),
                        label="Export timbral acoustic pairwise rows (JSON sidecar)",
                    )
                interactive_in = gr.Checkbox(value=True, label="Interactive plot (zoom/pan)")
                run_btn = gr.Button("Run analysis", variant="primary")
            with gr.Column(scale=2):
                plot_out = gr.Plot(label="H_TI_core(t) (= H_TI export)")
                summary_out = gr.Textbox(label="Summary", lines=12)
                csv_out = gr.File(label="Download CSV")
                plot_file_out = gr.File(label="Download plot (PNG or HTML)")
                json_out = gr.File(label="Download JSON")
        with gr.Accordion("Symbolic inspection (Loaded XML inspection)", open=False):
            gr.Markdown(
                "The **Symbolic inspection** report shows what the parser actually found in the uploaded score. "
                "It is intended to verify instrument mapping, sounding pitch, dynamics, techniques, articulations, "
                "effects, and vertical sonorities before interpreting **H_TI**. "
                "This is a **parser audit**, not a homogeneity metric. "
                "Same symbolic pipeline as **H_TI**; tables refresh automatically when the upload changes."
            )
            audit_notice_md = gr.Markdown(
                "Upload a score above to populate inspection tables. MusicXML / MXL is recommended."
            )
            gr.Markdown("#### Instrument inventory")
            audit_inv_df = gr.Dataframe(label="Instrument inventory", interactive=False, wrap=True)
            audit_inv_csv = gr.File(label="instrument_inventory.csv")
            gr.Markdown("#### Event audit")
            audit_ev_df = gr.Dataframe(label="Event audit", interactive=False, wrap=True)
            audit_ev_csv = gr.File(label="event_audit.csv")
            gr.Markdown("#### Vertical sonorities")
            audit_ver_df = gr.Dataframe(label="Vertical sonorities", interactive=False, wrap=True)
            audit_ver_csv = gr.File(label="vertical_sonorities.csv")

        run_btn.click(
            fn=run_hti_app,
            inputs=[
                file_shared,
                window_mode_in,
                edge_policy_in,
                time_step_in,
                window_size_in,
                window_ratio_in,
                step_ratio_in,
                min_window_size_in,
                max_window_size_in,
                min_time_step_in,
                max_time_step_in,
                target_window_count_in,
                window_to_step_ratio_in,
                register_profile_in,
                register_ref_override_in,
                pitch_interpretation_in,
                harmonic_pitch_policy_in,
                w_instr_in,
                w_fam_in,
                w_tech_in,
                w_reg_in,
                same_subfamily_relief_in,
                timbral_affinity_profile_in,
                timbral_affinity_relief_in,
                dynamic_affinity_enabled_in,
                export_affinity_pairs_in,
                include_symbolic_blend_in,
                include_acoustic_proxy_in,
                acoustic_proxy_profile_in,
                acoustic_proxy_pairwise_export_in,
                interactive_in,
            ],
            outputs=[plot_out, summary_out, csv_out, plot_file_out, json_out],
        )
        _audit_inputs = [file_shared, pitch_interpretation_in, harmonic_pitch_policy_in]
        _audit_outputs = [
            audit_notice_md,
            audit_inv_df,
            audit_inv_csv,
            audit_ev_df,
            audit_ev_csv,
            audit_ver_df,
            audit_ver_csv,
        ]
        file_shared.change(fn=run_loaded_xml_inspection, inputs=_audit_inputs, outputs=_audit_outputs)
        pitch_interpretation_in.change(fn=run_loaded_xml_inspection, inputs=_audit_inputs, outputs=_audit_outputs)
        harmonic_pitch_policy_in.change(fn=run_loaded_xml_inspection, inputs=_audit_inputs, outputs=_audit_outputs)
    return demo


def main() -> None:
    from homogeneity_analyser.utils.output_paths import gradio_launch_kwargs

    cleanup_stale_exports()
    build_demo().launch(**gradio_launch_kwargs(inbrowser=True))


if __name__ == "__main__":
    main()
