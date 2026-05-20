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
from homogeneity_analyser.analyzers.hti_concentration import finite_share_float as _finite_share_float
from homogeneity_analyser.analyzers.hti_concentration import herfindahl_from_masses as _herfindahl_from_masses
from homogeneity_analyser.analyzers.hti_dynamic_conditioning import (
    attach_dynamic_conditioning_for_window,
    pick_dynamic_interpretation_label_subfamily_relieved,
)
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
from homogeneity_analyser.analyzers.symbolic_blend_layers import (
    HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS,
    HTI_SYMBOLIC_BLEND_SERIES_KEYS,
    append_hti_symbolic_blend_series_row,
    compute_attack_compatibility_factor,
    compute_pairwise_interval_blend_factor,
    compute_symbolic_blend_bundle_for_window,
)
from homogeneity_analyser.analyzers.technique_state import compute_technique_uniformity_key_from_event
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.analyzers.timbral_acoustic_proxy import (
    HTI_ACOUSTIC_PROXY_SERIES_KEYS,
    acoustic_proxy_series_value,
    append_hti_acoustic_proxy_series_row,
    compute_H_TA_acoustic_contextual,
    compute_timbral_acoustic_affinity,
    disabled_acoustic_proxy_bundle,
    insufficient_window_acoustic_proxy_bundle,
)
from homogeneity_analyser.analyzers.timbral_affinity import (
    compute_timbral_affinity_bundle_for_window,
    finalize_timbral_affinity_dynamic,
)

_EPS = 1e-12


def _hti_pitch_occurrences_for_symbolic_layers(
    contrib: list[tuple[dict[str, Any], float]],
) -> list[tuple[float, float]]:
    """Pitched (midi, overlap_mass) pairs for optional interval-class diagnostics (mirrors register logic)."""
    pitch_occurrences: list[tuple[float, float]] = []
    for e, ol in contrib:
        fam = str(e.get("family") or "")
        inst_e = str(e.get("instrument") or "")
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
                pitch_occurrences.append((pf, ol_f))
    return pitch_occurrences


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
        series_keys = (
            "t",
            "window_start",
            "window_end",
            "edge_window",
            "window_coverage_ratio",
            "effective_window_overlap_duration",
            "measure",
            "pitch_interpretation_mode",
            "H_TI",
            "H_TI_core",
            "H_TI_strict",
            "H_TI_subfamily_relieved",
            "same_subfamily_relief_factor",
            "instrument_effective_uniformity",
            "instrument_uniformity",
            "instrumental_subfamily_uniformity",
            "macrofamily_uniformity",
            "family_uniformity",
            "technique_uniformity",
            "register_proximity",
            "register_compactness",
            "register_span_proximity",
            "register_span_factor",
            "pairwise_interval_proximity",
            "register_pair_distance_factor",
            "pairwise_interval_coverage_status",
            "n_instruments",
            "n_families",
            "n_macrofamilies",
            "register_span_semitones",
            "dominant_instrument",
            "dominant_instruments",
            "dominant_instrument_tie",
            "dominant_instrument_share",
            "dominant_instrument_margin",
            "dominant_instrumental_subfamily",
            "dominant_macrofamily",
            "dominant_macrofamilies",
            "dominant_macrofamily_tie",
            "dominant_macrofamily_share",
            "dominant_macrofamily_margin",
            "dominant_family",
            "dominant_families",
            "dominant_family_tie",
            "dominant_family_share",
            "dominant_family_margin",
            "dominant_timbral_state",
            "dominant_timbral_states",
            "dominant_timbral_state_tie",
            "dominant_timbral_state_share",
            "dominant_timbral_state_margin",
            "technique_state_distribution",
            "instrument_distribution",
            "family_distribution",
            "macrofamily_distribution",
            "technique_coverage_status",
            "register_coverage_status",
            "active_weights",
            "notated_dynamic_level_distribution",
            "notated_dynamic_coherence",
            "dominant_dynamic",
            "dominant_dynamics",
            "dominant_dynamic_tie",
            "dominant_dynamic_share",
            "dominant_dynamic_margin",
            "dynamic_intensity_ordinal",
            "dynamic_softness",
            "dynamic_coverage_status",
            "crescendo_active",
            "diminuendo_active",
            "dynamic_divergence_detected",
            "soft_blend_potential",
            "intra_family_convergence_potential",
            "transparent_blend_potential",
            "bright_salience_risk",
            "projection_divergence_risk",
            "masked_tonal_mass_risk",
            "same_family_mixed_instrument_mass",
            "family_heterogeneity",
            "masking_context_weight",
            "family_specific_projection_weight",
            "dynamic_interpretation_label",
            "dynamic_interpretation_label_subfamily_relieved",
            "dynamic_evidence_status",
            "H_TI_affinity_literature_relieved",
            "timbral_affinity_uniformity",
            "instrument_affinity_effective_uniformity",
            "timbral_affinity_profile",
            "timbral_affinity_relief_factor",
            "timbral_affinity_dynamic_factor",
            "timbral_affinity_dynamic_status",
            "affinity_dynamic_interpretation_label",
            "H_TI_affinity_dynamic_conditioned",
            "timbral_affinity_evidence_status",
            "timbral_affinity_rule_summary",
            "timbral_affinity_literature_sources",
            "literature_affinity_unverified_rule_blocked",
            *HTI_SYMBOLIC_BLEND_SERIES_KEYS,
            *HTI_ACOUSTIC_PROXY_SERIES_KEYS,
        )
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
            if feats is not None:
                contrib_pre = list(feats.get("__contrib__", []))
                aff_base = compute_timbral_affinity_bundle_for_window(
                    contrib_pre,
                    feats,
                    profile=str(getattr(self, "timbral_affinity_profile", "conservative")),
                    relief_factor=float(getattr(self, "timbral_affinity_relief_factor", 0.0)),
                    instrument_uniformity=float(feats["instrument_uniformity"]),
                    compute_h_ti=self.compute_H_TI,
                    feats_for_h_ti=feats,
                    w_instr=w_instr,
                    w_fam=w_fam,
                    w_tech=w_tech,
                    w_reg=w_reg,
                    collect_pairs=collect_affinity_pairs,
                )
                contrib = list(feats.pop("__contrib__", []))
                inst_mass = dict(feats.pop("__inst_mass__", {}))
                fam_mass = dict(feats.pop("__fam_mass__", {}))
                macro_mass = dict(feats.pop("__macro_mass__", {}))
                reg_pitches = list(feats.pop("__register_pitches__", []))
                span_semi_priv = feats.pop("__span_semi__", float("nan"))
                span_semi_use = float(span_semi_priv) if isinstance(span_semi_priv, int | float) else float("nan")
                attach_dynamic_conditioning_for_window(
                    feats,
                    float(h_strict),
                    contrib,
                    inst_mass,
                    fam_mass,
                    macro_mass,
                    reg_pitches,
                    span_semi_use,
                )
                aff_full = finalize_timbral_affinity_dynamic(
                    aff_base,
                    feats,
                    dynamic_affinity_enabled=bool(getattr(self, "dynamic_affinity_enabled", True)),
                )
                if bool(getattr(self, "include_acoustic_proxy", False)):
                    acoustic_full = compute_timbral_acoustic_affinity(
                        contrib_pre,
                        feats,
                        profile=str(getattr(self, "acoustic_proxy_profile", "conservative")),
                        kernel_weights=getattr(self, "acoustic_proxy_kernel_weights", None),
                        include_interval_class=bool(
                            getattr(self, "acoustic_proxy_include_interval_class", False)
                        ),
                        collect_pairs=bool(getattr(self, "acoustic_proxy_pairwise_export", False))
                        or collect_affinity_pairs,
                        min_evidence_policy=str(
                            getattr(self, "acoustic_proxy_min_evidence_policy", "omit_missing_components")
                        ),
                    )
                    h_ctx = compute_H_TA_acoustic_contextual(acoustic_full, feats)
                    acoustic_full["H_TA_acoustic_contextual"] = h_ctx
                prs = aff_full.pop("_pair_rows", [])
                if collect_affinity_pairs:
                    mstr = int(mnum) if mnum is not None else ""
                    for pr in prs:
                        pair_accum.append({**pr, "t_quarterLength": float(t), "measure": mstr})
                if acoustic_full:
                    aprs = acoustic_full.pop("_pair_rows", [])
                    if bool(getattr(self, "acoustic_proxy_pairwise_export", False)) or collect_affinity_pairs:
                        mstr_a = int(mnum) if mnum is not None else ""
                        for pr in aprs:
                            acoustic_pair_accum.append(
                                {**pr, "t_quarterLength": float(t), "measure": mstr_a}
                            )
                lbl_r = pick_dynamic_interpretation_label_subfamily_relieved(
                    feats, float(h_relaxed), float(ieff), contrib=contrib
                )
            else:
                lbl_r = "insufficient_dynamic_evidence"
            results["t"].append(float(t))
            results["window_start"].append(geom["window_start"])
            results["window_end"].append(geom["window_end"])
            results["edge_window"].append(bool(geom["edge_window"]))
            results["window_coverage_ratio"].append(float(geom["window_coverage_ratio"]))
            results["effective_window_overlap_duration"].append(float(geom["effective_window_overlap_duration"]))
            results["measure"].append(int(mnum) if mnum is not None else "")
            results["pitch_interpretation_mode"].append(mode_label)
            results["H_TI"].append(h)
            nanf = float("nan")
            if feats is None:
                results["H_TI_core"].append(float("nan"))
                for k in series_keys:
                    if k in (
                        "t",
                        "window_start",
                        "window_end",
                        "edge_window",
                        "window_coverage_ratio",
                        "effective_window_overlap_duration",
                        "measure",
                        "pitch_interpretation_mode",
                        "H_TI",
                        "H_TI_core",
                    ):
                        continue
                    if k in (
                        "crescendo_active",
                        "diminuendo_active",
                        "dynamic_divergence_detected",
                    ):
                        results[k].append(False)
                    elif k == "dynamic_interpretation_label":
                        results[k].append("insufficient_dynamic_evidence")
                    elif k == "dynamic_interpretation_label_subfamily_relieved":
                        results[k].append(lbl_r)
                    elif k == "same_subfamily_relief_factor":
                        results[k].append(float(r_relief))
                    elif k == "timbral_affinity_profile":
                        results[k].append(str(getattr(self, "timbral_affinity_profile", "conservative")))
                    elif k == "timbral_affinity_relief_factor":
                        results[k].append(float(getattr(self, "timbral_affinity_relief_factor", 0.0)))
                    elif k in ("timbral_affinity_rule_summary", "timbral_affinity_literature_sources"):
                        results[k].append("")
                    elif k == "timbral_affinity_dynamic_status" or k == "timbral_affinity_evidence_status":
                        results[k].append("insufficient")
                    elif k == "affinity_dynamic_interpretation_label":
                        results[k].append("insufficient_dynamic_evidence_for_affinity_qualifier")
                    elif k == "literature_affinity_unverified_rule_blocked":
                        results[k].append(False)
                    elif k in HTI_SYMBOLIC_BLEND_CSV_JSON_DICT_KEYS:
                        results[k].append({})
                    elif k in HTI_ACOUSTIC_PROXY_SERIES_KEYS:
                        results[k].append(
                            acoustic_proxy_series_value(
                                k,
                                insufficient_window_acoustic_proxy_bundle(),
                                nan_value=nanf,
                            )
                        )
                    elif k in HTI_SYMBOLIC_BLEND_SERIES_KEYS:
                        if k == "interval_class_evidence_status":
                            results[k].append("")
                        else:
                            results[k].append(nanf)
                    elif k == "dynamic_evidence_status":
                        results[k].append("insufficient")
                    elif k == "dynamic_coverage_status":
                        results[k].append("unavailable")
                    elif k.endswith("_distribution") or k == "notated_dynamic_level_distribution":
                        results[k].append({})
                    elif (
                        k == "technique_coverage_status"
                        or k == "register_coverage_status"
                        or k == "pairwise_interval_coverage_status"
                    ):
                        results[k].append("none")
                    elif k == "active_weights":
                        results[k].append(aw)
                    elif k == "dominant_timbral_state" or k == "dominant_dynamic":
                        results[k].append(None)
                    elif k in (
                        "dominant_instruments",
                        "dominant_macrofamilies",
                        "dominant_families",
                        "dominant_timbral_states",
                        "dominant_dynamics",
                    ):
                        results[k].append([])
                    elif k in (
                        "dominant_instrument_tie",
                        "dominant_macrofamily_tie",
                        "dominant_family_tie",
                        "dominant_timbral_state_tie",
                        "dominant_dynamic_tie",
                    ):
                        results[k].append(False)
                    elif k in (
                        "dominant_instrument_share",
                        "dominant_instrument_margin",
                        "dominant_macrofamily_share",
                        "dominant_macrofamily_margin",
                        "dominant_family_share",
                        "dominant_family_margin",
                        "dominant_timbral_state_share",
                        "dominant_timbral_state_margin",
                        "dominant_dynamic_share",
                        "dominant_dynamic_margin",
                    ):
                        results[k].append(nanf)
                    else:
                        results[k].append(
                            nanf
                            if k
                            not in (
                                "dominant_instrument",
                                "dominant_family",
                                "dominant_instrumental_subfamily",
                                "dominant_macrofamily",
                            )
                            else ""
                        )
            else:
                results["H_TI_core"].append(float(feats["H_TI_core"]))
                results["H_TI_strict"].append(float(h_strict))
                results["H_TI_subfamily_relieved"].append(float(h_relaxed))
                results["same_subfamily_relief_factor"].append(float(r_relief))
                results["instrument_effective_uniformity"].append(float(ieff))
                results["instrument_uniformity"].append(float(feats["instrument_uniformity"]))
                results["instrumental_subfamily_uniformity"].append(float(feats["instrumental_subfamily_uniformity"]))
                results["macrofamily_uniformity"].append(float(feats["macrofamily_uniformity"]))
                results["family_uniformity"].append(float(feats["family_uniformity"]))
                tu = feats["technique_uniformity"]
                results["technique_uniformity"].append(float(tu) if math.isfinite(float(tu)) else float("nan"))
                rp = feats["register_proximity"]
                results["register_proximity"].append(float(rp) if math.isfinite(float(rp)) else float("nan"))
                rc = feats["register_compactness"]
                results["register_compactness"].append(float(rc) if math.isfinite(float(rc)) else float("nan"))
                rsp = feats["register_span_proximity"]
                results["register_span_proximity"].append(float(rsp) if math.isfinite(float(rsp)) else float("nan"))
                rsf = feats.get("register_span_factor", rsp)
                results["register_span_factor"].append(float(rsf) if math.isfinite(float(rsf)) else float("nan"))
                pip = feats["pairwise_interval_proximity"]
                results["pairwise_interval_proximity"].append(float(pip) if math.isfinite(float(pip)) else float("nan"))
                rpdf = feats.get("register_pair_distance_factor", pip)
                results["register_pair_distance_factor"].append(
                    float(rpdf) if math.isfinite(float(rpdf)) else float("nan")
                )
                results["pairwise_interval_coverage_status"].append(str(feats["pairwise_interval_coverage_status"]))
                results["n_instruments"].append(int(feats["n_instruments"]))
                results["n_families"].append(int(feats["n_families"]))
                results["n_macrofamilies"].append(int(feats["n_macrofamilies"]))
                rs = feats["register_span_semitones"]
                results["register_span_semitones"].append(float(rs) if math.isfinite(float(rs)) else float("nan"))
                results["dominant_instrument"].append(str(feats["dominant_instrument"]))
                results["dominant_instruments"].append(list(feats["dominant_instruments"]))
                results["dominant_instrument_tie"].append(bool(feats["dominant_instrument_tie"]))
                results["dominant_instrument_share"].append(_finite_share_float(feats["dominant_instrument_share"]))
                results["dominant_instrument_margin"].append(_finite_share_float(feats["dominant_instrument_margin"]))
                results["dominant_instrumental_subfamily"].append(str(feats["dominant_instrumental_subfamily"]))
                results["dominant_macrofamily"].append(str(feats["dominant_macrofamily"]))
                results["dominant_macrofamilies"].append(list(feats["dominant_macrofamilies"]))
                results["dominant_macrofamily_tie"].append(bool(feats["dominant_macrofamily_tie"]))
                results["dominant_macrofamily_share"].append(_finite_share_float(feats["dominant_macrofamily_share"]))
                results["dominant_macrofamily_margin"].append(_finite_share_float(feats["dominant_macrofamily_margin"]))
                results["dominant_family"].append(str(feats["dominant_family"]))
                results["dominant_families"].append(list(feats["dominant_families"]))
                results["dominant_family_tie"].append(bool(feats["dominant_family_tie"]))
                results["dominant_family_share"].append(_finite_share_float(feats["dominant_family_share"]))
                results["dominant_family_margin"].append(_finite_share_float(feats["dominant_family_margin"]))
                results["dominant_timbral_state"].append(feats.get("dominant_timbral_state"))
                results["dominant_timbral_states"].append(list(feats["dominant_timbral_states"]))
                results["dominant_timbral_state_tie"].append(bool(feats["dominant_timbral_state_tie"]))
                results["dominant_timbral_state_share"].append(
                    _finite_share_float(feats["dominant_timbral_state_share"])
                )
                results["dominant_timbral_state_margin"].append(
                    _finite_share_float(feats["dominant_timbral_state_margin"])
                )
                results["technique_state_distribution"].append(dict(feats["technique_state_distribution"]))
                results["instrument_distribution"].append(dict(feats["instrument_distribution"]))
                results["family_distribution"].append(dict(feats["family_distribution"]))
                results["macrofamily_distribution"].append(dict(feats["macrofamily_distribution"]))
                results["technique_coverage_status"].append(str(feats["technique_coverage_status"]))
                results["register_coverage_status"].append(str(feats["register_coverage_status"]))
                results["active_weights"].append(aw)
                results["notated_dynamic_level_distribution"].append(dict(feats["notated_dynamic_level_distribution"]))
                results["notated_dynamic_coherence"].append(float(feats["notated_dynamic_coherence"]))
                results["dominant_dynamic"].append(feats.get("dominant_dynamic"))
                results["dominant_dynamics"].append(list(feats.get("dominant_dynamics") or []))
                results["dominant_dynamic_tie"].append(bool(feats.get("dominant_dynamic_tie", False)))
                results["dominant_dynamic_share"].append(_finite_share_float(feats.get("dominant_dynamic_share")))
                results["dominant_dynamic_margin"].append(_finite_share_float(feats.get("dominant_dynamic_margin")))
                results["dynamic_intensity_ordinal"].append(float(feats["dynamic_intensity_ordinal"]))
                results["dynamic_softness"].append(float(feats["dynamic_softness"]))
                results["dynamic_coverage_status"].append(str(feats["dynamic_coverage_status"]))
                results["crescendo_active"].append(bool(feats["crescendo_active"]))
                results["diminuendo_active"].append(bool(feats["diminuendo_active"]))
                results["dynamic_divergence_detected"].append(bool(feats["dynamic_divergence_detected"]))
                results["soft_blend_potential"].append(float(feats["soft_blend_potential"]))
                results["intra_family_convergence_potential"].append(float(feats["intra_family_convergence_potential"]))
                results["transparent_blend_potential"].append(float(feats["transparent_blend_potential"]))
                results["bright_salience_risk"].append(float(feats["bright_salience_risk"]))
                results["projection_divergence_risk"].append(float(feats["projection_divergence_risk"]))
                results["masked_tonal_mass_risk"].append(float(feats["masked_tonal_mass_risk"]))
                results["same_family_mixed_instrument_mass"].append(float(feats["same_family_mixed_instrument_mass"]))
                results["family_heterogeneity"].append(float(feats["family_heterogeneity"]))
                results["masking_context_weight"].append(float(feats["masking_context_weight"]))
                results["family_specific_projection_weight"].append(float(feats["family_specific_projection_weight"]))
                results["dynamic_interpretation_label"].append(str(feats["dynamic_interpretation_label"]))
                results["dynamic_interpretation_label_subfamily_relieved"].append(str(lbl_r))
                nanx = float("nan")
                results["H_TI_affinity_literature_relieved"].append(
                    float(aff_full["H_TI_affinity_literature_relieved"])
                    if aff_full and math.isfinite(float(aff_full.get("H_TI_affinity_literature_relieved", nanx)))
                    else nanx
                )
                results["timbral_affinity_uniformity"].append(
                    float(aff_full["timbral_affinity_uniformity"])
                    if aff_full and math.isfinite(float(aff_full.get("timbral_affinity_uniformity", nanx)))
                    else nanx
                )
                results["instrument_affinity_effective_uniformity"].append(
                    float(aff_full["instrument_affinity_effective_uniformity"])
                    if aff_full and math.isfinite(float(aff_full.get("instrument_affinity_effective_uniformity", nanx)))
                    else nanx
                )
                results["timbral_affinity_profile"].append(str(aff_full.get("timbral_affinity_profile", "")))
                results["timbral_affinity_relief_factor"].append(
                    float(
                        aff_full.get(
                            "timbral_affinity_relief_factor", getattr(self, "timbral_affinity_relief_factor", 0.0)
                        )
                    )
                )
                results["timbral_affinity_dynamic_factor"].append(
                    float(aff_full["timbral_affinity_dynamic_factor"])
                    if aff_full and math.isfinite(float(aff_full.get("timbral_affinity_dynamic_factor", nanx)))
                    else nanx
                )
                results["timbral_affinity_dynamic_status"].append(
                    str(aff_full.get("timbral_affinity_dynamic_status", ""))
                )
                results["affinity_dynamic_interpretation_label"].append(
                    str(aff_full.get("affinity_dynamic_interpretation_label", ""))
                )
                results["H_TI_affinity_dynamic_conditioned"].append(
                    float(aff_full["H_TI_affinity_dynamic_conditioned"])
                    if aff_full and math.isfinite(float(aff_full.get("H_TI_affinity_dynamic_conditioned", nanx)))
                    else nanx
                )
                results["timbral_affinity_evidence_status"].append(
                    str(aff_full.get("timbral_affinity_evidence_status", ""))
                )
                results["timbral_affinity_rule_summary"].append(str(aff_full.get("timbral_affinity_rule_summary", "")))
                results["timbral_affinity_literature_sources"].append(
                    str(aff_full.get("timbral_affinity_literature_sources", ""))
                )
                results["literature_affinity_unverified_rule_blocked"].append(
                    bool(aff_full.get("literature_affinity_unverified_rule_blocked", False)) if aff_full else False
                )
                if getattr(self, "include_symbolic_blend_potential", False) and contrib:
                    po_sym = _hti_pitch_occurrences_for_symbolic_layers(contrib)
                    ivb = compute_pairwise_interval_blend_factor(po_sym)
                    atk = compute_attack_compatibility_factor(contrib)
                    tau_u = float(aff_full.get("timbral_affinity_uniformity", nanx))
                    if not math.isfinite(tau_u):
                        tau_u = float("nan")
                    sympk = compute_symbolic_blend_bundle_for_window(
                        feats,
                        contrib,
                        po_sym,
                        h_ti_core=float(feats["H_TI_core"]),
                        timbral_affinity_uniformity=tau_u,
                    )
                    append_hti_symbolic_blend_series_row(
                        results,
                        enabled=True,
                        ivb=ivb,
                        atk=atk,
                        sympk=sympk,
                        nan_value=nanx,
                    )
                else:
                    append_hti_symbolic_blend_series_row(
                        results,
                        enabled=False,
                        ivb=None,
                        atk=None,
                        sympk=None,
                        nan_value=nanx,
                    )
                if bool(getattr(self, "include_acoustic_proxy", False)) and acoustic_full:
                    acb = acoustic_full
                else:
                    acb = disabled_acoustic_proxy_bundle()
                append_hti_acoustic_proxy_series_row(results, acb, nan_value=nanx)
                results["dynamic_evidence_status"].append(str(feats["dynamic_evidence_status"]))
            if progress_callback and n > 0:
                progress_callback((i + 1) / n, "Symbolic timbral–instrumental H_TI(t)")
        if collect_affinity_pairs:
            results["affinity_pair_rows"] = pair_accum
        if acoustic_pair_accum:
            results["timbral_acoustic_pairwise_rows"] = acoustic_pair_accum
        return results
