"""Gradio callback handlers — facade re-exporting split modules."""

from __future__ import annotations

from homogeneity_analyser.ui.callback_helpers import (
    export_plotly_figure_static as _export_plotly_figure_static,
)
from homogeneity_analyser.ui.callback_helpers import (
    timbral_config_from_optional as _timbral_config_from_optional,
)
from homogeneity_analyser.ui.callback_helpers import (
    timbral_parse_error_return as _timbral_parse_error_return,
)
from homogeneity_analyser.ui.callback_helpers import (
    ui_float_gradio as _ui_float_gradio,
)
from homogeneity_analyser.ui.callback_result_formatting import (
    rows_to_dataframe as _rows_to_dataframe,
)
from homogeneity_analyser.ui.callback_result_formatting import (
    write_temp_csv as _write_temp_csv,
)
from homogeneity_analyser.ui.callbacks_hti import run_hti_app
from homogeneity_analyser.ui.callbacks_inspection import run_loaded_xml_inspection
from homogeneity_analyser.ui.callbacks_legacy import (
    run_app,
    run_both_app,
    run_orch_symbolic_app,
    run_register_app,
    run_timbral_app,
)

timbral_config_from_optional = _timbral_config_from_optional

__all__ = [
    "_export_plotly_figure_static",
    "_rows_to_dataframe",
    "_timbral_config_from_optional",
    "_timbral_parse_error_return",
    "_ui_float_gradio",
    "_write_temp_csv",
    "run_app",
    "run_both_app",
    "run_hti_app",
    "run_loaded_xml_inspection",
    "run_orch_symbolic_app",
    "run_register_app",
    "run_timbral_app",
    "timbral_config_from_optional",
]
