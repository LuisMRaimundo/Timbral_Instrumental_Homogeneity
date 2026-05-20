from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import gradio as gr

import homogeneity_analyser.ui.gradio_app as gradio_app
from homogeneity_analyser.ui import callbacks as cb
from homogeneity_analyser.ui.gradio_app import build_demo, main


class _CM:
    """No-op context manager (Tabs, Row, Column, …)."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeBlocks(_CM):
    def __init__(self, **kwargs):
        self.title = kwargs.get("title")


def _cm_factory(*_a, **_k):
    return _CM()


def _make_fake_gr():
    """Minimal gr facade so build_demo() runs without constructing real Blocks."""
    clicks: list[dict] = []

    def _button(*_a, **_k):
        b = _CM()

        def click(*, fn=None, inputs=None, outputs=None, **_kwargs):
            clicks.append(
                {
                    "fn": getattr(fn, "__name__", str(fn)),
                    "n_inputs": len(inputs or []),
                    "n_outputs": len(outputs or []),
                    "trigger": "click",
                }
            )

        b.click = click  # type: ignore[attr-defined]
        return b

    def _len_io(x: object) -> int:
        if x is None:
            return 0
        if isinstance(x, list | tuple):
            return len(x)
        return 1

    def _file(*_a, **_k):
        f = _CM()

        def change(fn=None, inputs=None, outputs=None, **_kwargs):
            clicks.append(
                {
                    "fn": getattr(fn, "__name__", str(fn)),
                    "n_inputs": _len_io(inputs),
                    "n_outputs": _len_io(outputs),
                    "trigger": "change",
                }
            )

        f.change = change  # type: ignore[attr-defined]
        return f

    def _dropdown(*_a, **_k):
        d = _CM()

        def change(fn=None, inputs=None, outputs=None, **_kwargs):
            clicks.append(
                {
                    "fn": getattr(fn, "__name__", str(fn)),
                    "n_inputs": _len_io(inputs),
                    "n_outputs": _len_io(outputs),
                    "trigger": "change",
                }
            )

        d.change = change  # type: ignore[attr-defined]
        return d

    return SimpleNamespace(
        Blocks=_FakeBlocks,
        Markdown=_cm_factory,
        File=_file,
        Dataframe=_cm_factory,
        Tabs=_cm_factory,
        TabItem=_cm_factory,
        Accordion=_cm_factory,
        Row=_cm_factory,
        Column=_cm_factory,
        Group=_cm_factory,
        Number=_cm_factory,
        Radio=_cm_factory,
        Slider=_cm_factory,
        Checkbox=_cm_factory,
        Dropdown=_dropdown,
        Button=_button,
        Plot=_cm_factory,
        Textbox=_cm_factory,
    ), clicks


def test_build_demo_monkeypatched_gr_records_two_handlers():
    fake_gr, clicks = _make_fake_gr()
    with patch.object(gradio_app, "gr", fake_gr):
        demo = gradio_app.build_demo()
    assert isinstance(demo, _FakeBlocks)
    assert len(clicks) == 5
    assert [c["fn"] for c in clicks] == [
        "_hti_window_visibility",
        "run_hti_app",
        "run_loaded_xml_inspection",
        "run_loaded_xml_inspection",
        "run_loaded_xml_inspection",
    ]
    assert clicks[0]["n_inputs"] == 1
    assert clicks[0]["n_outputs"] == 4
    assert clicks[0]["trigger"] == "change"
    assert clicks[1]["n_inputs"] == 31
    assert clicks[1]["n_outputs"] == 5
    assert clicks[1]["trigger"] == "click"
    assert clicks[2]["n_inputs"] == 3
    assert clicks[2]["n_outputs"] == 7
    assert clicks[2]["trigger"] == "change"
    assert clicks[3]["n_inputs"] == 3
    assert clicks[3]["n_outputs"] == 7
    assert clicks[3]["trigger"] == "change"
    assert clicks[4]["n_inputs"] == 3
    assert clicks[4]["n_outputs"] == 7
    assert clicks[4]["trigger"] == "change"


def test_build_demo_real_blocks_fn_graph():
    demo = build_demo()
    assert isinstance(demo, gr.Blocks)
    assert len(demo.fns) == 5
    bf0 = demo.fns[0]
    assert bf0.fn.__name__ == "_hti_window_visibility"
    assert len(bf0.inputs) == 1
    assert len(bf0.outputs) == 4
    assert bf0.targets and bf0.targets[0][1] == "change"
    expected = [
        (cb.run_hti_app, 31, 5, "click"),
        (cb.run_loaded_xml_inspection, 3, 7, "change"),
        (cb.run_loaded_xml_inspection, 3, 7, "change"),
        (cb.run_loaded_xml_inspection, 3, 7, "change"),
    ]
    for idx, (want_fn, want_in, want_out, want_trigger) in enumerate(expected, start=1):
        bf = demo.fns[idx]
        assert bf.fn is want_fn
        assert len(bf.inputs) == want_in
        assert len(bf.outputs) == want_out
        assert bf.targets and bf.targets[0][1] == want_trigger

    shared = demo.fns[1].inputs[0]
    assert demo.fns[2].inputs[0] is shared
    assert demo.fns[3].inputs[0] is shared
    assert demo.fns[4].inputs[0] is shared


def test_main_calls_cleanup_build_launch():
    mock_demo = MagicMock()
    with (
        patch.object(gradio_app, "build_demo", return_value=mock_demo),
        patch.object(gradio_app, "cleanup_stale_exports") as clean,
    ):
        main()
    clean.assert_called_once()
    mock_demo.launch.assert_called_once()
