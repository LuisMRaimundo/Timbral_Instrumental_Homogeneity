"""Tests for orchestration, register, and combined legacy UI helpers."""

from __future__ import annotations

import pytest

from homogeneity_analyser.ui.legacy_multimetric_ui_params import (
    build_combined_summary_text,
    build_orchestration_symbolic_params_from_ui,
    build_register_params_from_ui,
    cluster_orch_fusion_plot_bundle,
    parse_notated_fusion_relief_ui,
    register_plot_title,
)


def test_orchestration_params_weights() -> None:
    p = build_orchestration_symbolic_params_from_ui()
    assert p["weight_orchestration_instrument"] == pytest.approx(0.45)


def test_register_requires_limits() -> None:
    with pytest.raises(ValueError, match="lower register"):
        build_register_params_from_ui(register_low="", register_high="E7")


def test_register_plot_title() -> None:
    t = register_plot_title(register_low="A1", register_high="E7", window_size=4.0)
    assert "[A1, E7]" in t


def test_notated_fusion_relief_override() -> None:
    nfd = parse_notated_fusion_relief_ui("balanced", "0.5")
    assert nfd["same_family_relief_override"] == pytest.approx(0.5)


def test_combined_summary_includes_schema_note() -> None:
    s = build_combined_summary_text(
        out_h_summary="H",
        out_t_summary="T",
        out_c_summary="C",
        out_o_summary="O",
        out_nf_summary="N",
        out_f_summary="F",
    )
    assert "schema_version" in s
    assert "1.8" in s


def test_cluster_orch_fusion_bundle_legacy_alias() -> None:
    b = cluster_orch_fusion_plot_bundle({"t": [0.0], "H_timbral": [0.3], "H_cluster": [0.4]})
    assert b["legacy_H_timbral"] == [0.3]
