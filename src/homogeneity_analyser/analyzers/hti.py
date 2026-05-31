"""
Symbolic Timbral–Instrumental Homogeneity H_TI(t) — orchestration entry point.

Score-derived only (MusicXML / MIDI). This module wires the symbolic pipeline (``timbral.py``)
to per-window features (``hti_window_features.py``), **H_TI_core** (``hti_active_weights.py``),
and time-series export (``hti_analyze_series.py`` / ``hti_export_rows.py``).

See ``docs/HTI_SYMBOLIC_PIPELINE.md`` for stage → module map.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.hti_active_weights import (
    DEFAULT_W_FAM as _DEFAULT_W_FAM,
)
from homogeneity_analyser.analyzers.hti_active_weights import (
    DEFAULT_W_INSTR as _DEFAULT_W_INSTR,
)
from homogeneity_analyser.analyzers.hti_active_weights import (
    DEFAULT_W_REG as _DEFAULT_W_REG,
)
from homogeneity_analyser.analyzers.hti_active_weights import (
    DEFAULT_W_TECH as _DEFAULT_W_TECH,
)
from homogeneity_analyser.analyzers.hti_active_weights import (
    compute_hti_active_components,
)
from homogeneity_analyser.analyzers.hti_adaptive_windows import HTI_EDGE_MARK, hti_window_row_geometry
from homogeneity_analyser.analyzers.hti_analyze_series import (
    HTI_ANALYZE_SERIES_KEYS,
    append_hti_analyze_window_row,
    enrich_hti_window_optional_layers,
)
from homogeneity_analyser.analyzers.hti_comparability import classify_hti_comparability_class
from homogeneity_analyser.analyzers.hti_concentration import herfindahl_from_masses as _herfindahl_from_masses
from homogeneity_analyser.analyzers.hti_export_rows import (  # noqa: F401 — public re-exports
    HTI_CSV_COLUMNS,
    HTI_EXPORT_TIME_SERIES_KEYS,
    hti_csv_row_dict,
)
from homogeneity_analyser.analyzers.hti_register_compactness import compute_register_compactness_fields
from homogeneity_analyser.analyzers.hti_score_lookup import measure_number_at_ql
from homogeneity_analyser.analyzers.hti_window_features import extract_hti_window_features
from homogeneity_analyser.analyzers.hti_window_overlap import event_overlap_ql
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer

TECHNIQUE_MODEL_VERSION = "technique_state_id_v3_dynamic_conditioning"


class SymbolicTIHomogeneityAnalyzer(TimbralHomogeneityAnalyzer):
    """
    H_TI(t): overlap-mass Herfindahl on instrument / instrumental subfamily (taxonomy family) /
    technique_uniformity_key (instrument-free), plus register proximity; separate macrofamily Herfindahl diagnostic;
    written-dynamic interpretive layer (ordinal, not SPL).
    """

    def __init__(
        self,
        score_path: str | None = None,
        time_step: float = 0.25,
        *,
        hti_weights: dict[str, float] | None = None,
        register_ref_semitones: float | None = None,
        music21_score: Any | None = None,
        pitch_interpretation_mode: str | None = None,
        same_subfamily_relief_factor: float = 0.0,
        timbral_affinity_relief_factor: float = 0.0,
        timbral_affinity_profile: str = "conservative",
        dynamic_affinity_enabled: bool = True,
        harmonic_pitch_policy: str | None = None,
        include_symbolic_blend_potential: bool = False,
        include_acoustic_proxy: bool = False,
        acoustic_proxy_profile: str = "conservative",
        acoustic_proxy_pairwise_export: bool = False,
        acoustic_proxy_kernel_weights: dict[str, float] | None = None,
        acoustic_proxy_include_interval_class: bool = False,
        acoustic_proxy_min_evidence_policy: str = "omit_missing_components",
    ):
        super().__init__(
            score_path=score_path,
            time_step=time_step,
            timbral_config=None,
            timbral_model_mode="legacy",
            music21_score=music21_score,
            pitch_interpretation_mode=pitch_interpretation_mode,
            harmonic_pitch_policy=harmonic_pitch_policy,
        )
        self._hti_weights = dict(hti_weights) if hti_weights else {}
        self._register_ref_semitones = float(register_ref_semitones) if register_ref_semitones is not None else 7.0
        sfr = float(same_subfamily_relief_factor)
        self.same_subfamily_relief_factor = float(np.clip(sfr, 0.0, 1.0)) if math.isfinite(sfr) else 0.0
        tar = float(timbral_affinity_relief_factor)
        self.timbral_affinity_relief_factor = float(np.clip(tar, 0.0, 1.0)) if math.isfinite(tar) else 0.0
        self.timbral_affinity_profile = str(timbral_affinity_profile or "conservative").strip().lower()
        self.dynamic_affinity_enabled = bool(dynamic_affinity_enabled)
        self.include_symbolic_blend_potential = bool(include_symbolic_blend_potential)
        self.include_acoustic_proxy = bool(include_acoustic_proxy)
        self.acoustic_proxy_profile = str(acoustic_proxy_profile or "conservative").strip().lower()
        self.acoustic_proxy_pairwise_export = bool(acoustic_proxy_pairwise_export)
        self.acoustic_proxy_kernel_weights = (
            dict(acoustic_proxy_kernel_weights) if acoustic_proxy_kernel_weights else None
        )
        self.acoustic_proxy_include_interval_class = bool(acoustic_proxy_include_interval_class)
        self.acoustic_proxy_min_evidence_policy = str(
            acoustic_proxy_min_evidence_policy or "omit_missing_components"
        ).strip()

    def _event_overlap_ql(self, e: dict[str, Any], t_start: float, t_end: float) -> float:
        return event_overlap_ql(e, t_start, t_end)

    def extract_hti_window(self, window_center: float, window_size: float) -> dict[str, Any] | None:
        return extract_hti_window_features(
            self._events,
            window_center=window_center,
            window_size=window_size,
            register_ref_semitones=self._register_ref_semitones,
            is_event_active_in_window=self._active_in_window,
        )

    def compute_H_TI(
        self,
        feats: dict[str, Any] | None,
        *,
        w_instr: float = _DEFAULT_W_INSTR,
        w_fam: float = _DEFAULT_W_FAM,
        w_tech: float = _DEFAULT_W_TECH,
        w_reg: float = _DEFAULT_W_REG,
        instrument_uniformity_component: float | None = None,
    ) -> tuple[float, dict[str, Any], dict[str, float]]:
        h, _comp, renorm, diag = compute_hti_active_components(
            feats,
            w_instr=w_instr,
            w_fam=w_fam,
            w_tech=w_tech,
            w_reg=w_reg,
            instrument_uniformity_component=instrument_uniformity_component,
        )
        return h, diag, renorm

    def analyze_hti(
        self,
        window_size: float,
        *,
        time_centers: list[float] | None = None,
        excerpt_start_ql: float = 0.0,
        excerpt_end_ql: float | None = None,
        edge_policy: str | None = None,
        w_instr: float = _DEFAULT_W_INSTR,
        w_fam: float = _DEFAULT_W_FAM,
        w_tech: float = _DEFAULT_W_TECH,
        w_reg: float = _DEFAULT_W_REG,
        progress_callback: Callable[[float, str], None] | None = None,
        collect_affinity_pairs: bool = False,
    ) -> dict[str, list[Any]]:
        series_keys = HTI_ANALYZE_SERIES_KEYS
        results: dict[str, list[Any]] = {k: [] for k in series_keys}
        pair_accum: list[dict[str, Any]] = []
        acoustic_pair_accum: list[dict[str, Any]] = []
        ee = float(excerpt_end_ql) if excerpt_end_ql is not None else float(self.end_time)
        ep = str(edge_policy or HTI_EDGE_MARK)
        centers: list[float] = list(time_centers) if time_centers is not None else [float(x) for x in self.time_axis]
        n = len(centers)
        mode_label = str(getattr(self, "_pitch_interpretation_mode", "musicxml_sounding"))
        r_relief = float(np.clip(float(getattr(self, "same_subfamily_relief_factor", 0.0)), 0.0, 1.0))
        for i, t in enumerate(centers):
            geom = hti_window_row_geometry(float(t), float(window_size), float(excerpt_start_ql), ee, ep)
            mnum = measure_number_at_ql(self.score, float(t))
            feats = self.extract_hti_window(float(t), window_size)
            ieff = float("nan")
            h_relaxed = float("nan")
            if feats is None:
                h_strict, _diag, aw = self.compute_H_TI(
                    None,
                    w_instr=w_instr,
                    w_fam=w_fam,
                    w_tech=w_tech,
                    w_reg=w_reg,
                )
            else:
                iu0 = float(feats["instrument_uniformity"])
                isu0 = float(feats["instrumental_subfamily_uniformity"])
                ieff = (1.0 - r_relief) * iu0 + r_relief * isu0
                h_strict, _diag, aw = self.compute_H_TI(
                    feats,
                    w_instr=w_instr,
                    w_fam=w_fam,
                    w_tech=w_tech,
                    w_reg=w_reg,
                )
                h_relaxed, _, _ = self.compute_H_TI(
                    feats,
                    w_instr=w_instr,
                    w_fam=w_fam,
                    w_tech=w_tech,
                    w_reg=w_reg,
                    instrument_uniformity_component=float(ieff),
                )
            h = h_strict
            aff_full: dict[str, Any] = {}
            acoustic_full: dict[str, Any] = {}
            contrib: list[tuple[dict[str, Any], float]] = []
            if feats is not None:
                aff_full, acoustic_full, contrib, lbl_r = enrich_hti_window_optional_layers(
                    self,
                    feats,
                    h_strict=float(h_strict),
                    h_relaxed=float(h_relaxed),
                    ieff=float(ieff),
                    w_instr=w_instr,
                    w_fam=w_fam,
                    w_tech=w_tech,
                    w_reg=w_reg,
                    collect_affinity_pairs=collect_affinity_pairs,
                    t=float(t),
                    mnum=mnum,
                    pair_accum=pair_accum,
                    acoustic_pair_accum=acoustic_pair_accum,
                )
            else:
                lbl_r = "insufficient_dynamic_evidence"
            cmp_class = classify_hti_comparability_class(feats=feats, active_weights=aw)
            append_hti_analyze_window_row(
                results,
                series_keys,
                self,
                feats=feats,
                t=float(t),
                geom=geom,
                mnum=mnum,
                mode_label=mode_label,
                h=h,
                h_strict=float(h_strict),
                h_relaxed=float(h_relaxed),
                ieff=float(ieff),
                r_relief=r_relief,
                aff_full=aff_full,
                acoustic_full=acoustic_full,
                contrib=contrib,
                lbl_r=lbl_r,
                aw=aw,
                cmp_class=cmp_class,
            )
            if progress_callback and n > 0:
                progress_callback((i + 1) / n, "Symbolic timbral–instrumental H_TI(t)")
        if collect_affinity_pairs:
            results["affinity_pair_rows"] = pair_accum
        if acoustic_pair_accum:
            results["timbral_acoustic_pairwise_rows"] = acoustic_pair_accum
        return results
