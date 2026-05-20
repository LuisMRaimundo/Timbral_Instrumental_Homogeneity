"""One-off splitter: analysis_service.py -> legacy + hti modules. Run from repo root."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVC = ROOT / "src" / "homogeneity_analyser" / "services"
src = (SVC / "analysis_service.py").read_text(encoding="utf-8")
lines = src.splitlines(keepends=True)
hti_start = next(
    i for i, line in enumerate(lines) if line.startswith("def _acoustic_proxy_kernel_weights_from_params")
)
legacy_lines = lines[:hti_start]
hti_lines = lines[hti_start:]

legacy_doc = (
    '"""\n'
    "Legacy multimetric orchestration (H(t), H_timbral metric, H_cluster, fusion, U(t), combined JSON 1.8).\n\n"
    "Uses the same symbolic score pipeline as H_TI (``analyzers/timbral.py`` — event/taxonomy base class),\n"
    "but runs **separate metrics** from ``homogeneity_analyser.legacy``. "
    "Not required for ``run_symbolic_ti_homogeneity_analysis``.\n\n"
    "Import via ``homogeneity_analyser.services.analysis_service`` (facade) for backward compatibility.\n"
    '"""\n\n'
)
hti_doc = (
    '"""\n'
    "H_TI product orchestration — ``run_symbolic_ti_homogeneity_analysis`` only.\n\n"
    "Built on ``SymbolicTIHomogeneityAnalyzer`` (extends the symbolic event pipeline in ``timbral.py``).\n"
    "Taxonomy, families, and register compactness logic live in ``analyzers/hti.py`` and helpers.\n\n"
    "Import via ``homogeneity_analyser.services.analysis_service`` (facade) for backward compatibility.\n"
    '"""\n\n'
)
legacy_body = "".join(legacy_lines)
if legacy_body.startswith('"""'):
    end = legacy_body.index('"""', 3) + 3
    legacy_body = legacy_doc + legacy_body[end:].lstrip("\n")

hti_imports = """from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.hti import SymbolicTIHomogeneityAnalyzer
from homogeneity_analyser.analyzers.hti_adaptive_windows import (
    HTI_WINDOW_MODE_MANUAL,
    build_hti_window_centers,
    resolve_hti_windowing,
)
from homogeneity_analyser.io.score_validation import ScoreValidationError
from homogeneity_analyser.services.constants import DEFAULT_HTI_PARAMS, resolve_register_ref_semitones
from homogeneity_analyser.services.param_validation import (
    AnalysisParameterError,
    safe_nan_summary,
    validate_hti_params,
)

"""
hti_body = hti_doc + hti_imports + "".join(hti_lines)

(SVC / "analysis_service_legacy.py").write_text(legacy_body, encoding="utf-8")
(SVC / "analysis_service_hti.py").write_text(hti_body, encoding="utf-8")
print("legacy lines:", len(legacy_body.splitlines()))
print("hti lines:", len(hti_body.splitlines()))
