"""Legacy **H_timbral** analyzer facade (score events via ``SymbolicScoreAnalyzer``).

Window features: ``timbral_window_features.py``. Metric + diagnostics: ``timbral_window_metric.py``.
Symbolic score → events: ``symbolic_score_analyzer.py`` / ``symbolic_event_pipeline.py``.
"""

from __future__ import annotations

from typing import Any

from homogeneity_analyser.analyzers.symbolic_score_analyzer import SymbolicScoreAnalyzer
from homogeneity_analyser.analyzers.timbral_window_features import extract_timbral_window_features
from homogeneity_analyser.analyzers.timbral_window_metric import (
    _combine_family_pairwise_homogeneity,
    _normalized_instr_register_weights,
    compute_timbral_window_decomposition,
    compute_timbral_window_metric,
)
from homogeneity_analyser.models.timbral_semantics import (
    TimbralModelMode,
    assert_active_timbral_model_mode,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import get_timbral_config

__all__ = [
    "TimbralHomogeneityAnalyzer",
    "_combine_family_pairwise_homogeneity",
    "_normalized_instr_register_weights",
]


class TimbralHomogeneityAnalyzer(SymbolicScoreAnalyzer):
    """
    Part-name / orchestration homogeneity (H_timbral), not acoustic timbre.

    Uses MusicXML/MIDI **instrument names** (per-note when ``music21`` exposes ``Instrument``
    context on the note, otherwise the part default) and a string taxonomy (family + canonical
    instrument). Same instrument → high score; same family → intermediate; many families → low.

    Implementation modules: ``timbral_window_features`` (per-window dict),
    ``timbral_window_metric`` (scalar + diagnostics). See ``docs/H_TIMBRAL_*.md``.
    """

    def __init__(
        self,
        score_path: str | None = None,
        time_step: float = 0.25,
        timbral_config: dict | None = None,
        *,
        timbral_model_mode: str | None = None,
        music21_score: Any | None = None,
        pitch_interpretation_mode: str | None = None,
        harmonic_pitch_policy: str | None = None,
    ):
        super().__init__(
            score_path=score_path,
            time_step=time_step,
            music21_score=music21_score,
            pitch_interpretation_mode=pitch_interpretation_mode,
            harmonic_pitch_policy=harmonic_pitch_policy,
        )
        tc = dict(timbral_config) if timbral_config else {}
        nested_mode = tc.pop("timbral_model_mode", None)
        arg_mode = timbral_model_mode
        if arg_mode is not None and not str(arg_mode).strip():
            arg_mode = None
        if arg_mode is not None:
            if nested_mode is not None and str(nested_mode).strip() != "" and str(arg_mode) != str(nested_mode):
                raise ValueError("Conflicting timbral_model_mode between argument and timbral_config.")
            resolved_mode: str | None = str(arg_mode)
        else:
            resolved_mode = str(nested_mode) if nested_mode is not None else None
        self._timbral_model_mode: TimbralModelMode = assert_active_timbral_model_mode(resolved_mode)
        cfg = get_timbral_config()
        if tc:
            cfg = {**cfg, **{k: v for k, v in tc.items() if k in cfg}}
        self._timbral_config = cfg

    def extract_timbral_features(self, window_center: float, window_size: float) -> dict | None:
        return extract_timbral_window_features(
            self._events,
            window_center,
            window_size,
            is_event_active_in_window=self._active_in_window,
        )

    def compute_H_timbral_decomposition(self, features: dict | None) -> tuple[float, dict[str, Any]]:
        """
        Return ``(H_timbral, diagnostics)`` using the same formula as :meth:`compute_H_timbral`.

        ``diagnostics`` is JSON-friendly (floats, ints, strings, dicts of floats, or ``null``).
        """
        return compute_timbral_window_decomposition(
            features,
            timbral_config=self._timbral_config,
            timbral_model_mode=getattr(self, "_timbral_model_mode", None),
        )

    def compute_H_timbral(self, features: dict | None) -> float:
        return compute_timbral_window_metric(
            features,
            timbral_config=self._timbral_config,
            timbral_model_mode=getattr(self, "_timbral_model_mode", None),
        )

    def analyze_timbral(self, window_size: float, progress_callback=None, *, return_components: bool = False):
        results: dict[str, list] = {
            "t": [],
            "H_timbral": [],
            "timbral_state_distribution": [],
            "dominant_timbral_state": [],
            "timbral_state_concentration": [],
        }
        if return_components:
            results["H_timbral_diagnostics"] = []
        n = len(self.time_axis)
        for i, t in enumerate(self.time_axis):
            feats = self.extract_timbral_features(float(t), window_size)
            h, diag = self.compute_H_timbral_decomposition(feats)
            results["t"].append(float(t))
            results["H_timbral"].append(h)
            if return_components:
                results["H_timbral_diagnostics"].append(diag)
            if feats is not None:
                results["timbral_state_distribution"].append(dict(feats.get("timbral_state_distribution") or {}))
                results["dominant_timbral_state"].append(feats.get("dominant_timbral_state"))
                results["timbral_state_concentration"].append(float(feats.get("timbral_state_concentration") or 1.0))
            else:
                results["timbral_state_distribution"].append({})
                results["dominant_timbral_state"].append(None)
                results["timbral_state_concentration"].append(1.0)
            if progress_callback and n > 0:
                progress_callback((i + 1) / n, "Timbral H_timbral(t)")
        return results
