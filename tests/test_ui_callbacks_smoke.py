"""

Smoke tests for ``ui/callbacks.py`` (Gradio boundary; no server launched).



Pure parameter/result logic is tested in ``test_*_ui_params.py`` modules.

"""



from __future__ import annotations

import pytest

from pathlib import Path
from unittest.mock import MagicMock

import gradio as gr

import homogeneity_analyser.ui.callbacks as cb
import homogeneity_analyser.ui.callbacks_hti as cb_hti
import homogeneity_analyser.ui.callbacks_legacy as cb_legacy
from homogeneity_analyser.ui.timbral_ui_params import timbral_config_from_optional


def test_callbacks_entry_points_exist() -> None:

    for name in (

        "run_hti_app",

        "run_app",

        "run_timbral_app",

        "run_orch_symbolic_app",

        "run_register_app",

        "run_both_app",

        "run_loaded_xml_inspection",

    ):

        assert hasattr(cb, name)

        assert callable(getattr(cb, name))





def test_timbral_config_shim_on_callbacks_module() -> None:
    assert cb._timbral_config_from_optional is timbral_config_from_optional
    assert cb._timbral_config_from_optional is cb.timbral_config_from_optional





def test_run_hti_app_missing_upload_raises() -> None:

    with pytest.raises(gr.Error):

        cb.run_hti_app(file_obj=None)





@pytest.mark.skipif(

    not (Path(__file__).resolve().parent / "fixtures" / "musicxml" / "golden_two_violins_unison_c5.musicxml").is_file(),

    reason="golden fixture missing",

)

def test_run_hti_app_golden_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:

    fixture = Path(__file__).resolve().parent / "fixtures" / "musicxml" / "golden_two_violins_unison_c5.musicxml"

    monkeypatch.setattr(cb_hti, "validate_uploaded_score", lambda _f: str(fixture))

    monkeypatch.setattr(cb_hti, "new_export_path", lambda stem, ext: str(tmp_path / f"{stem}out{ext}"))

    monkeypatch.setattr(cb_hti.plt, "close", lambda *_a, **_k: None)

    fig_mock = MagicMock()

    fig_mock.savefig = MagicMock()

    monkeypatch.setattr(cb_hti, "make_hti_figure", lambda *_a, **_k: fig_mock)

    out = cb.run_hti_app(progress=MagicMock(), file_obj=str(fixture), interactive_plot=False)

    assert len(out) == 5





def test_run_app_mocked_homogeneity(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:

    score = tmp_path / "s.musicxml"

    score.write_text(

        '<?xml version="1.0"?><score-partwise version="3.1"><part-list>'

        '<score-part id="P1"><part-name>X</part-name></score-part></part-list>'

        "<part id=\"P1\"><measure><note><rest/><duration>4</duration></note></measure></part>"

        "</score-partwise>",

        encoding="utf-8",

    )

    monkeypatch.setattr(cb_legacy, "validate_uploaded_score", lambda _f: str(score))

    monkeypatch.setattr(

        cb_legacy,

        "run_homogeneity_analysis",

        lambda *_a, **_k: {

            "results": {"t": [0.0], "H": [0.5]},

            "plot_results": {"t": [0.0], "H": [0.5]},

            "summary": "ok",

        },

    )

    monkeypatch.setattr(cb_legacy, "make_homogeneity_figure", lambda *_a, **_k: MagicMock())

    monkeypatch.setattr(cb_legacy, "make_gauge_placeholder", lambda: MagicMock())

    monkeypatch.setattr(cb_legacy, "new_export_path", lambda stem, ext: str(tmp_path / f"{stem}x{ext}"))

    monkeypatch.setattr(cb_legacy.plt, "close", lambda *_a, **_k: None)

    monkeypatch.setattr(cb_legacy, "build_homogeneity_export", lambda *_a, **_k: {})

    monkeypatch.setattr(cb_legacy, "write_json_export", lambda *_a, **_k: None)

    out = cb.run_app(file_obj=str(score), interactive_plot=False, single_aggregate=False)

    assert len(out) == 6





def test_run_timbral_parse_error_returns_seven_tuple() -> None:

    out = cb._timbral_parse_error_return(False, "bad")

    assert len(out) == 7





def test_run_register_missing_limits_raises() -> None:

    with pytest.raises(gr.Error):

        cb.run_register_app(file_obj="x", register_low="", register_high="E7")

