"""
Symbolic Timbral–Instrumental Homogeneity H_TI(t).

Score-derived only (MusicXML / MIDI): canonical instrument, instrumental subfamily (taxonomy
``family``), macrofamily, technique_uniformity_key, written dynamics (ordinal, not SPL), and
sounding-pitch **register compactness** (span + pairwise intervals). Not audio analysis.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable
from typing import Any

import numpy as np

from homogeneity_analyser.analyzers.dominant_distribution import dominant_with_ties
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
from homogeneity_analyser.analyzers.hti_dynamics import aggregate_notated_dynamics_for_window
from homogeneity_analyser.analyzers.hti_export_rows import (  # noqa: F401 — public re-exports
    HTI_CSV_COLUMNS,
    HTI_EXPORT_TIME_SERIES_KEYS,
    hti_csv_row_dict,
)
from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.analyzers.hti_technique_coverage import resolve_technique_uniformity_and_coverage
from homogeneity_analyser.analyzers.percussion_ontology import PitchStatus, get_percussion_meta
from homogeneity_analyser.analyzers.percussion_pairwise_timbral import is_percussion_family
from homogeneity_analyser.analyzers.technique_state import compute_technique_uniformity_key_from_event
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer

_EPS = 1e-12


TECHNIQUE_MODEL_VERSION = "technique_state_id_v3_dynamic_conditioning"


def compute_register_compactness_fields(
    pitch_occurrences: list[tuple[float, float]],
    register_ref_semitones: float,
) -> dict[str, Any]:
    """
    Register **compactness** diagnostics from pitched MIDI/ps occurrences.

    Each entry is ``(midi_pitch, overlap_mass)`` for one chord tone / sounding pitch
    (same overlap mass as the parent event for each listed pitch). Unpitched percussion
    must be excluded **before** calling.

    Returns ``register_span_proximity`` (outer span only), overlap-weighted mean
    ``pairwise_interval_proximity`` over unordered pairs, ``register_compactness`` as
    ``sqrt(max(ε, span) * max(ε, pairwise))``, and ``register_proximity`` equal to
    ``register_compactness`` (the value that enters **H_TI_core**'s weighted geometric mean).

    Explicit aliases (same numerics; **not** interval-class fusion): ``register_span_factor``
    equals ``register_span_proximity``; ``register_pair_distance_factor`` equals
    ``pairwise_interval_proximity`` (semitone-distance / ref attenuation only).
    """
    ref = float(register_ref_semitones)
    if not math.isfinite(ref) or ref <= 0.0:
        ref = 7.0
    if not pitch_occurrences:
        nan = float("nan")
        return {
            "register_span_semitones": nan,
            "register_span_proximity": nan,
            "register_span_factor": nan,
            "pairwise_interval_proximity": nan,
            "register_pair_distance_factor": nan,
            "pairwise_interval_coverage_status": "unpitched_only",
            "register_compactness": nan,
            "register_proximity": nan,
            "register_coverage_status": "unpitched_only",
        }

    mids = [float(p) for p, _w in pitch_occurrences]
    arr = np.asarray(mids, dtype=float)
    span_semi = float(np.ptp(arr)) if arr.size > 1 else 0.0
    register_span_proximity = 1.0 / (1.0 + span_semi / ref)

    n = len(pitch_occurrences)
    if n < 2:
        pairwise_interval_proximity = 1.0
        pairwise_interval_coverage_status = "insufficient_pairs"
    else:
        num = 0.0
        den = 0.0
        for i in range(n):
            pi, wi = float(pitch_occurrences[i][0]), float(pitch_occurrences[i][1])
            wi = max(0.0, wi)
            for j in range(i + 1, n):
                pj, wj = float(pitch_occurrences[j][0]), float(pitch_occurrences[j][1])
                wj = max(0.0, wj)
                d = abs(pi - pj)
                prox = 1.0 / (1.0 + d / ref)
                wij = wi * wj
                num += wij * prox
                den += wij
        pairwise_interval_proximity = float(num / den) if den > 1e-15 else 1.0
        pairwise_interval_coverage_status = "sufficient_pairs"

    rp_span = max(float(register_span_proximity), _EPS)
    rp_pair = max(float(pairwise_interval_proximity), _EPS)
    register_compactness = float(np.clip(math.sqrt(rp_span * rp_pair), 0.0, 1.0))
    rsp = float(register_span_proximity)
    pip = float(pairwise_interval_proximity)
    return {
        "register_span_semitones": span_semi,
        "register_span_proximity": rsp,
        "register_span_factor": rsp,
        "pairwise_interval_proximity": pip,
        "register_pair_distance_factor": pip,
        "pairwise_interval_coverage_status": pairwise_interval_coverage_status,
        "register_compactness": register_compactness,
        "register_proximity": register_compactness,
        "register_coverage_status": "pitched",
    }


def _measure_number_at_ql(score: Any, t: float) -> int | None:
    try:
        from music21 import stream as m21stream

        for part in score.parts:
            for m in part.getElementsByClass(m21stream.Measure):
                off = float(m.offset)
                dur = float(m.duration.quarterLength) if m.duration is not None else 0.0
                if off <= t < off + dur + 1e-9:
                    mn = getattr(m, "measureNumber", None)
                    if mn is not None and int(mn) not in (0,):
                        return int(mn)
        return None
    except (AttributeError, TypeError, ValueError):
        return None


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
        o = float(e["offset"])
        end = float(e["end"])
        return max(0.0, min(end, t_end) - max(o, t_start))

    def extract_hti_window(self, window_center: float, window_size: float) -> dict[str, Any] | None:
        t_start = window_center - window_size / 2.0
        t_end = window_center + window_size / 2.0
        active = [e for e in self._events if self._active_in_window(e, t_start, t_end)]
        if not active:
            return None

        contrib: list[tuple[dict[str, Any], float]] = []
        for e in active:
            ol = self._event_overlap_ql(e, t_start, t_end)
            if ol > 0.0:
                contrib.append((e, float(ol)))

        if not contrib:
            return None

        inst_mass: dict[str, float] = defaultdict(float)
        fam_mass: dict[str, float] = defaultdict(float)
        macro_mass: dict[str, float] = defaultdict(float)
        tech_mass: dict[str, float] = defaultdict(float)
        register_span_pitches: list[float] = []
        pitch_occurrences: list[tuple[float, float]] = []

        for e, ol in contrib:
            inst = str(e.get("instrument") or "unknown")
            fam = str(e.get("family") or "unknown")
            inst_mass[inst] += ol
            fam_mass[fam] += ol
            macro_mass[macrofamily_from_instrumental_subfamily(fam)] += ol
            tuk = compute_technique_uniformity_key_from_event(e)
            if tuk:
                tech_mass[tuk] += ol
            inst_e = inst
            ol_f = float(ol)
            for p in e.get("pitches") or []:
                try:
                    pf = float(p)
                except (TypeError, ValueError):
                    continue
                skip_reg = is_percussion_family(fam) and (
                    get_percussion_meta(inst_e).pitch_status == PitchStatus.UNPITCHED
                )
                if not skip_reg:
                    register_span_pitches.append(pf)
                    pitch_occurrences.append((pf, ol_f))

        tot_inst = float(sum(inst_mass.values()))
        if tot_inst <= 1e-15:
            return None

        instrument_uniformity = _herfindahl_from_masses(dict(inst_mass))
        instrumental_subfamily_uniformity = _herfindahl_from_masses(dict(fam_mass))
        macrofamily_uniformity = _herfindahl_from_masses(dict(macro_mass))

        technique_uniformity, technique_coverage_status = resolve_technique_uniformity_and_coverage(
            dict(tech_mass), contrib
        )

        ref = self._register_ref_semitones
        if not math.isfinite(ref) or ref <= 0.0:
            ref = 7.0
        reg_bundle = compute_register_compactness_fields(pitch_occurrences, ref)
        span_semi = float(reg_bundle["register_span_semitones"])
        register_span_proximity = float(reg_bundle["register_span_proximity"])
        register_span_factor = float(reg_bundle.get("register_span_factor", register_span_proximity))
        pairwise_interval_proximity = float(reg_bundle["pairwise_interval_proximity"])
        register_pair_distance_factor = float(
            reg_bundle.get("register_pair_distance_factor", pairwise_interval_proximity)
        )
        pairwise_interval_coverage_status = str(reg_bundle["pairwise_interval_coverage_status"])
        register_compactness = float(reg_bundle["register_compactness"])
        register_proximity = float(reg_bundle["register_proximity"])
        register_coverage_status = str(reg_bundle["register_coverage_status"])

        inst_share = {k: float(v) / tot_inst for k, v in inst_mass.items()}
        fam_tot = float(sum(fam_mass.values())) or 1.0
        fam_share = {k: float(v) / fam_tot for k, v in fam_mass.items()}
        macro_tot = float(sum(macro_mass.values())) or 1.0
        macro_share = {k: float(v) / macro_tot for k, v in macro_mass.items()}
        tech_tot = float(sum(tech_mass.values())) or 1.0
        tech_share = {k: float(v) / tech_tot for k, v in tech_mass.items()} if tech_mass else {}

        d_inst = dominant_with_ties(dict(inst_share))
        d_fam = dominant_with_ties(dict(fam_share))
        d_macro = dominant_with_ties(dict(macro_share))
        d_tech = dominant_with_ties(dict(tech_share)) if tech_share else dominant_with_ties({})
        dom_inst = str(d_inst["dominant_primary"] or "")
        dom_fam = str(d_fam["dominant_primary"] or "")
        dom_macro = str(d_macro["dominant_primary"] or "")
        dom_ts = d_tech["dominant_primary"]

        ev_only = [e for e, _ol in contrib]
        dyn = aggregate_notated_dynamics_for_window(ev_only, self._event_overlap_ql, t_start, t_end)

        feats: dict[str, Any] = {
            "instrument_uniformity": instrument_uniformity,
            "instrumental_subfamily_uniformity": instrumental_subfamily_uniformity,
            "family_uniformity": instrumental_subfamily_uniformity,
            "macrofamily_uniformity": macrofamily_uniformity,
            "technique_uniformity": technique_uniformity,
            "register_proximity": register_proximity,
            "register_compactness": register_compactness,
            "register_span_proximity": register_span_proximity,
            "register_span_factor": register_span_factor,
            "pairwise_interval_proximity": pairwise_interval_proximity,
            "register_pair_distance_factor": register_pair_distance_factor,
            "pairwise_interval_coverage_status": pairwise_interval_coverage_status,
            "register_span_semitones": span_semi,
            "register_coverage_status": register_coverage_status,
            "technique_coverage_status": technique_coverage_status,
            "n_instruments": len(inst_mass),
            "n_families": len(fam_mass),
            "n_macrofamilies": len(macro_mass),
            "dominant_instrument": dom_inst,
            "dominant_instruments": list(d_inst["dominant_all"]),
            "dominant_instrument_tie": bool(d_inst["tie"]),
            "dominant_instrument_share": d_inst["max_share"],
            "dominant_instrument_margin": d_inst["margin_to_second"],
            "dominant_instrumental_subfamily": dom_fam,
            "dominant_macrofamily": dom_macro,
            "dominant_macrofamilies": list(d_macro["dominant_all"]),
            "dominant_macrofamily_tie": bool(d_macro["tie"]),
            "dominant_macrofamily_share": d_macro["max_share"],
            "dominant_macrofamily_margin": d_macro["margin_to_second"],
            "dominant_family": dom_fam,
            "dominant_families": list(d_fam["dominant_all"]),
            "dominant_family_tie": bool(d_fam["tie"]),
            "dominant_family_share": d_fam["max_share"],
            "dominant_family_margin": d_fam["margin_to_second"],
            "dominant_timbral_state": dom_ts,
            "dominant_timbral_states": list(d_tech["dominant_all"]),
            "dominant_timbral_state_tie": bool(d_tech["tie"]),
            "dominant_timbral_state_share": d_tech["max_share"],
            "dominant_timbral_state_margin": d_tech["margin_to_second"],
            "instrument_distribution": dict(inst_share),
            "instrumental_subfamily_distribution": dict(fam_share),
            "family_distribution": dict(fam_share),
            "macrofamily_distribution": dict(macro_share),
            "technique_state_distribution": dict(tech_share),
            **dyn,
            "__contrib__": contrib,
            "__inst_mass__": dict(inst_mass),
            "__fam_mass__": dict(fam_mass),
            "__macro_mass__": dict(macro_mass),
            "__register_pitches__": list(register_span_pitches),
            "__span_semi__": float(span_semi) if math.isfinite(float(span_semi)) else float("nan"),
        }
        return feats

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
            mnum = _measure_number_at_ql(self.score, float(t))
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
                aff_full = {}
                acoustic_full = {}
                contrib = []
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
