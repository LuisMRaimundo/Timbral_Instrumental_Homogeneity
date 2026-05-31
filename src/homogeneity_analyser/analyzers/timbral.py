"""Symbolic score event pipeline and optional **H_timbral** metric (not acoustic timbre).

**H_TI** (`SymbolicTIHomogeneityAnalyzer` in ``hti.py``) and **H_timbral** both inherit
``SymbolicScoreAnalyzer`` (``symbolic_score_analyzer.py``): shared score loading and
``build_symbolic_score_events``. That pipeline is **product infrastructure**, not the deprecated
multimetric package under ``homogeneity_analyser.legacy/``.

The **H_timbral** time series (``analyze_timbral``, pairwise family kernels) is a **separate legacy
metric** — orchestrated from ``services/analysis_service_legacy.py``, not required for ``H_TI_core``.

Each built event includes ``instrument``, ``family``, ``onset`` / ``note_end`` (and legacy
``offset`` / ``end``), ``pitches``, ``technique_state`` (dict), ``technique_state_id`` (full fingerprint),
``technique_uniformity_key`` (instrument-free H_TI bucket), and ``explicit_technique``
(``none`` vs a normalised explicit tail).

:meth:`TimbralHomogeneityAnalyzer.extract_timbral_features` adds overlap-weighted
``timbral_state_distribution``, ``dominant_timbral_state``, and ``timbral_state_concentration``.
:meth:`TimbralHomogeneityAnalyzer.analyze_timbral` returns those three as parallel time series
alongside ``t`` and ``H_timbral`` for audit and JSON export. Pass ``return_components=True`` to also
obtain per-window ``H_timbral_diagnostics`` (same scalar ``H_timbral``; see
:meth:`compute_H_timbral_decomposition`).
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np

from homogeneity_analyser.acoustic_profiles.model_config import (
    build_timbral_window_diagnostics_bundle,
    timbral_float,
)
from homogeneity_analyser.acoustic_profiles.timbral_diag_constants import (
    CROSS_TIMBRAL_SEMANTIC_NAMES,
    GLOBAL_ALWAYS_SEMANTIC_NAMES,
    PAIRWISE_BRANCH_SEMANTIC_NAMES,
    PERCUSSION_REGISTER_BLEND_SEMANTIC_NAMES,
    PERCUSSION_UNPITCHED_REGISTER_PROXY_SEMANTIC_NAMES,
)
from homogeneity_analyser.analyzers.brass_pairwise_timbral import pairwise_brass_homogeneity
from homogeneity_analyser.analyzers.clarinet_pairwise_timbral import pairwise_clarinet_homogeneity
from homogeneity_analyser.analyzers.double_reed_pairwise_timbral import pairwise_double_reed_homogeneity
from homogeneity_analyser.analyzers.flute_pairwise_timbral import pairwise_flute_homogeneity
from homogeneity_analyser.analyzers.percussion_pairwise_timbral import (
    pairwise_percussion_homogeneity,
    unpitched_percussion_register_proxy,
)
from homogeneity_analyser.analyzers.saxophone_pairwise_timbral import pairwise_saxophone_homogeneity
from homogeneity_analyser.analyzers.string_pairwise_timbral import pairwise_string_homogeneity
from homogeneity_analyser.analyzers.symbolic_score_analyzer import SymbolicScoreAnalyzer
from homogeneity_analyser.analyzers.technique_state import timbral_state_concentration_from_distribution
from homogeneity_analyser.analyzers.timbral_window_features import extract_timbral_window_features
from homogeneity_analyser.analyzers.timbre_cross_relations import verified_cross_timbral_boost
from homogeneity_analyser.models.timbral_semantics import (
    TimbralModelMode,
    assert_active_timbral_model_mode,
    timbral_model_metadata_for_diagnostics,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    get_timbral_config,
)


def _numeric_feature_or(features: Mapping[str, Any], key: str, fallback: float) -> float:
    """Return ``features[key]`` as float when it is numeric; otherwise ``fallback``."""
    raw = features.get(key)
    if isinstance(raw, bool):
        return fallback
    if isinstance(raw, int | float):
        return float(raw)
    return fallback


_DEFAULT_WEIGHT_INSTRUMENT = timbral_float("timbral_default_weight_instrument")
_DEFAULT_WEIGHT_REGISTER = timbral_float("timbral_default_weight_register")
_DEFAULT_FAMILY_BONUS = timbral_float("timbral_default_family_bonus")
_DEFAULT_REGISTER_REF_SEMITONES = timbral_float("timbral_default_register_ref_semitones")
# When family-specific pairwises (which already include tessitura/register terms) cover most of
# the overlap mass, lightly down-weight the separate global register span term to avoid
# silently double-counting register spread (notation-only heuristic; see module docstring).
_REGISTER_GLOBAL_DAMPEN_FOR_PAIRWISE_COVERAGE = timbral_float("timbral_register_global_dampen_pairwise_coverage_max")
_TIMBRAL_PERC_REG_PM_TH = timbral_float("timbral_percussion_register_blend_pm_threshold")
_TIMBRAL_PERC_REG_PUN_TH = timbral_float("timbral_percussion_register_blend_pun_threshold")
_TIMBRAL_PERC_REG_BLEND_MULT = timbral_float("timbral_percussion_register_blend_multiplier")
_TIMBRAL_TECH_CONC_OFF = timbral_float("timbral_technique_component_offset")
_TIMBRAL_TECH_CONC_SCL = timbral_float("timbral_technique_component_concentration_scale")


def _semantic_defaults_from_cfg(cfg: dict[str, Any]) -> set[str]:
    """Which ``timbral_default_*`` profile rows materially anchor this run (defaults or explicit matches)."""
    out: set[str] = set()

    def _matches_default(raw: Any, default_val: float, semantic: str) -> None:
        if raw is None or raw == "":
            out.add(semantic)
            return
        try:
            if math.isclose(float(raw), float(default_val), rel_tol=0.0, abs_tol=1e-9):
                out.add(semantic)
        except (TypeError, ValueError):
            pass

    _matches_default(cfg.get("weight_instrument"), _DEFAULT_WEIGHT_INSTRUMENT, "timbral_default_weight_instrument")
    _matches_default(cfg.get("weight_register"), _DEFAULT_WEIGHT_REGISTER, "timbral_default_weight_register")
    _matches_default(cfg.get("family_bonus"), _DEFAULT_FAMILY_BONUS, "timbral_default_family_bonus")
    _matches_default(
        cfg.get("register_ref_semitones"), _DEFAULT_REGISTER_REF_SEMITONES, "timbral_default_register_ref_semitones"
    )
    return out


def _window_diag_semantic_names(
    cfg: dict[str, Any],
    active_pairwise_branches: set[str],
    *,
    register_percussion_blend: bool,
    cross_boost: float,
) -> set[str]:
    used: set[str] = set(GLOBAL_ALWAYS_SEMANTIC_NAMES)
    used |= _semantic_defaults_from_cfg(cfg)
    if register_percussion_blend:
        used |= PERCUSSION_REGISTER_BLEND_SEMANTIC_NAMES
        used |= PERCUSSION_UNPITCHED_REGISTER_PROXY_SEMANTIC_NAMES
    for br in active_pairwise_branches:
        used |= PAIRWISE_BRANCH_SEMANTIC_NAMES.get(br, frozenset())
    if float(cross_boost) > 1e-15:
        used |= CROSS_TIMBRAL_SEMANTIC_NAMES
    return used


def _normalized_instr_register_weights(cfg: dict[str, Any]) -> tuple[float, float]:
    """
    Instrument vs register trade-off weights: coerce to float, clamp negatives to 0,
    normalise to sum 1, fall back to defaults if the sum is zero / non-finite.
    """
    try:
        wi = float(cfg.get("weight_instrument", _DEFAULT_WEIGHT_INSTRUMENT))
    except (TypeError, ValueError):
        wi = _DEFAULT_WEIGHT_INSTRUMENT
    try:
        wr = float(cfg.get("weight_register", _DEFAULT_WEIGHT_REGISTER))
    except (TypeError, ValueError):
        wr = _DEFAULT_WEIGHT_REGISTER
    wi = max(0.0, wi)
    wr = max(0.0, wr)
    s = wi + wr
    if not math.isfinite(s) or s <= 1e-15:
        return _DEFAULT_WEIGHT_INSTRUMENT, _DEFAULT_WEIGHT_REGISTER
    return wi / s, wr / s


def _combine_family_pairwise_homogeneity_detail(
    legacy_instr: float,
    features: dict[str, Any],
    *,
    active_pairwise_branches: set[str] | None = None,
) -> tuple[float, float, float]:
    """
    Same blend as :func:`_combine_family_pairwise_homogeneity`, plus diagnostic scalars.

    Returns ``(h_blended, pairwise_blend_weight, pairwise_branch_mean)`` where
    ``pairwise_blend_weight`` is ``F`` in the docstring (0 when no specialist segments).
    """
    total_m = float(features.get("total_overlap_mass", 0.0) or 0.0)
    segments: list[tuple[float, float]] = []

    def _add(branch: str, mass_key: str, events_key: str, pair_fn: Callable[[list[dict[str, Any]]], float]) -> None:
        m = float(features.get(mass_key) or 0.0)
        ev = features.get(events_key)
        if m <= 0.0 or not isinstance(ev, list) or len(ev) == 0:
            return
        if len(ev) < 2:
            h_k = float(legacy_instr)
        else:
            h_k = float(pair_fn(ev))
            if active_pairwise_branches is not None:
                active_pairwise_branches.add(branch)
        segments.append((m, h_k))

    _add("string", "string_overlap_mass", "string_events", pairwise_string_homogeneity)
    _add("brass", "brass_overlap_mass", "brass_events", pairwise_brass_homogeneity)
    _add("flute", "flute_overlap_mass", "flute_events", pairwise_flute_homogeneity)
    _add("clarinet", "clarinet_overlap_mass", "clarinet_events", pairwise_clarinet_homogeneity)
    _add("double_reed", "double_reed_overlap_mass", "double_reed_events", pairwise_double_reed_homogeneity)
    _add("saxophone", "saxophone_overlap_mass", "saxophone_events", pairwise_saxophone_homogeneity)
    _add("percussion", "percussion_overlap_mass", "percussion_events", pairwise_percussion_homogeneity)

    if not segments:
        return float(legacy_instr), 0.0, float(legacy_instr)
    sum_m = sum(m for m, _ in segments)
    if sum_m <= 1e-15:
        return float(legacy_instr), 0.0, float(legacy_instr)
    h_bar = sum(m * h for m, h in segments) / sum_m
    f_blend = min(1.0, sum_m / max(total_m, 1e-12))
    h_blended = float((1.0 - f_blend) * legacy_instr + f_blend * h_bar)
    return h_blended, float(f_blend), float(h_bar)


def _combine_family_pairwise_homogeneity(legacy_instr: float, features: dict[str, Any]) -> float:
    """
    Mass-weighted, order-independent blend of legacy instrument factor with family pairwise models.

    Each active family branch k with positive overlap mass ``m_k`` contributes ``h_k`` from its
    pairwise homogeneity; the blend is ``(1 - F) * legacy + F * h_bar`` where
    ``F = min(1, sum_k m_k / M_total)`` and ``h_bar = sum_k m_k h_k / sum_k m_k``.  This removes
    dependence on the order in which family refinements were historically chained.

    If a branch has fewer than two sounding events, its pairwise score is vacuous (pairwise
    modules return 1.0 for ``n <= 1``).  Those branches contribute ``legacy_instr`` instead so
    cross-family windows are not spuriously treated as perfectly homogeneous on the instrument
    axis before cross-family affinity and concentration are applied.
    """
    h, _, _ = _combine_family_pairwise_homogeneity_detail(legacy_instr, features, active_pairwise_branches=None)
    return h


def _timbral_overlap_mass_distributions(features: dict[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    """Overlap-quarter mass by canonical instrument and by family (from ``timbral_note_slices``)."""
    inst_m: dict[str, float] = defaultdict(float)
    fam_m: dict[str, float] = defaultdict(float)
    for s in features.get("timbral_note_slices") or []:
        if not isinstance(s, dict):
            continue
        ol = float(s.get("overlap_ql", 0.0) or 0.0)
        inst_m[str(s.get("instrument") or "")] += ol
        fam_m[str(s.get("family") or "")] += ol
    inst_out = {k: float(v) for k, v in inst_m.items() if k}
    fam_out = {k: float(v) for k, v in fam_m.items() if k}
    return inst_out, fam_out


class TimbralHomogeneityAnalyzer(SymbolicScoreAnalyzer):
    """
    Part-name / orchestration homogeneity (H_timbral), not acoustic timbre.

    Uses MusicXML/MIDI **instrument names** (per-note when ``music21`` exposes ``Instrument``
    context on the note, otherwise the part default) and a string taxonomy (family + canonical
    instrument). Same instrument → high score; same family → intermediate; many families → low.

    **Sounding pitch:** note ``pitches`` stored on events and used in all tessitura/register
    logic are **concert MIDI** (``timbral_sounding_pitch.sounding_pitch_ps_list`` per part
    instrument transposition). Other metrics in this project are unchanged.

    **Register span:** ``register_span_pitches`` excludes unpitched percussion placeholder
    staff positions so global span is not driven by arbitrary MIDI for snare/cymbals/etc.;
    see ``docs/H_TIMBRAL_SCORE_REPRESENTATION.md``.

    **Family-specific pairwises** (strings, brass, flutes, clarinets, double reeds, saxophones,
    percussion): each family has a pairwise model (see the ``docs/H_TIMBRAL_*.md`` notes). Their
    contributions are combined in **one overlap-mass–weighted blend** with the legacy instrument
    factor (order-independent; no sequential chaining).

    **Global register span:** a separate notation-span term; when non-percussion specialist
    overlap dominates the window it is **lightly damped** so tessitura already encoded in those
    pairwises is not double-counted. Percussion register uses ``unpitched_percussion_register_proxy``
    where applicable and is excluded from that dampening mass tally.

    **Verified cross-family layer** (bounded additive affinity only): explicit relations in
    ``docs/H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md`` / ``timbre_cross_relations`` — not a general
    cross-timbral matrix. It is clipped with the instrument component so ``H_timbral`` stays in
    ``[0, 1]``. Double-reed oboe↔bassoon macro affinity remains in ``double_reed_pairwise_timbral``.
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
        cfg = self._timbral_config
        w_instr, w_reg = _normalized_instr_register_weights(cfg)
        try:
            family_bonus = float(cfg.get("family_bonus", _DEFAULT_FAMILY_BONUS))
        except (TypeError, ValueError):
            family_bonus = _DEFAULT_FAMILY_BONUS
        family_bonus = max(0.0, min(1.0, family_bonus))

        # Test-only partial instances may omit ``__init__``; default matches production ``legacy``.
        timbral_mode_for_diag: TimbralModelMode = assert_active_timbral_model_mode(
            getattr(self, "_timbral_model_mode", None)
        )

        def _empty_diag(h_val: float) -> dict[str, Any]:
            d: dict[str, Any] = {
                "H_timbral": float(h_val),
                "weight_instrument": float(w_instr),
                "weight_register": float(w_reg),
                "instrument_component": None,
                "instrument_pairwise_component": None,
                "register_component": None,
                "timbral_state_concentration": None,
                "technique_component": None,
                "cross_family_boost": None,
                "legacy_instrument_homogeneity": None,
                "pairwise_blend_weight": None,
                "pairwise_branch_mean": None,
                "family_component": None,
                "n_events": 0,
                "n_notes": 0,
                "n_instruments": 0,
                "n_families": 0,
                "instrument_distribution": {},
                "family_distribution": {},
                "technique_distribution": {},
                "dominant_timbral_state": None,
                "instrument_distribution_concentration": None,
                "family_distribution_concentration": None,
                "technique_only_concentration": None,
                "full_state_concentration": None,
                "legacy_concentration": None,
                "technique_only_distribution": {},
                "technique_state_distribution_full": {},
            }
            d.update(timbral_model_metadata_for_diagnostics(timbral_mode_for_diag))
            d.update(build_timbral_window_diagnostics_bundle(()))
            return d

        if features is None or features["n_notes"] == 0:
            return 0.5, _empty_diag(0.5)

        n_instr = int(features["n_instruments"])
        n_families = int(features["n_families"])
        n_score_events = int(features.get("n_score_events", 0) or 0)
        n_notes = int(features.get("n_notes", 0) or 0)

        if "register_span_pitches" in features:
            reg_arr = features["register_span_pitches"]
            if isinstance(reg_arr, np.ndarray) and reg_arr.size > 0:
                span_semi = float(np.ptp(reg_arr)) if reg_arr.size > 1 else 0.0
            else:
                span_semi = 0.0
        else:
            pitches = features["pitches"]
            span_semi = float(np.ptp(pitches)) if len(pitches) > 1 else 0.0

        try:
            ref_span = float(cfg.get("register_ref_semitones", _DEFAULT_REGISTER_REF_SEMITONES))
        except (TypeError, ValueError):
            ref_span = _DEFAULT_REGISTER_REF_SEMITONES
        if not math.isfinite(ref_span) or ref_span <= 0.0:
            ref_span = _DEFAULT_REGISTER_REF_SEMITONES

        if n_instr == 1:
            legacy_instr = 1.0
        elif n_families == 1:
            legacy_instr = family_bonus
        else:
            legacy_instr = 1.0 / (1.0 + (n_instr - 1))
        family_component: float | None = float(family_bonus) if n_families == 1 and n_instr > 1 else None

        register_component = 1.0 / (1.0 + span_semi / ref_span)

        pm_reg = float(features.get("percussion_overlap_mass", 0.0) or 0.0)
        tot_mass_reg = float(features.get("total_overlap_mass", 0.0) or 0.0)
        pun_reg = float(features.get("percussion_unpitched_overlap_mass", 0.0) or 0.0)
        register_percussion_blend = (
            tot_mass_reg > 1e-9
            and pm_reg / tot_mass_reg >= _TIMBRAL_PERC_REG_PM_TH
            and pun_reg / tot_mass_reg >= _TIMBRAL_PERC_REG_PUN_TH
        )
        if register_percussion_blend:
            pe = features.get("percussion_events") or []
            reg_proxy = unpitched_percussion_register_proxy(pe)
            w_blend = float(
                np.clip(
                    (pun_reg / tot_mass_reg) * (pm_reg / tot_mass_reg) * _TIMBRAL_PERC_REG_BLEND_MULT,
                    0.0,
                    1.0,
                )
            )
            register_component = float((1.0 - w_blend) * register_component + w_blend * reg_proxy)

        specialist_mass_for_register_dampen = sum(
            float(features.get(k, 0.0) or 0.0)
            for k in (
                "string_overlap_mass",
                "brass_overlap_mass",
                "flute_overlap_mass",
                "clarinet_overlap_mass",
                "double_reed_overlap_mass",
                "saxophone_overlap_mass",
            )
        )
        coverage = min(1.0, specialist_mass_for_register_dampen / max(tot_mass_reg, 1e-12))
        register_component *= 1.0 - _REGISTER_GLOBAL_DAMPEN_FOR_PAIRWISE_COVERAGE * coverage

        active_pairwise_branches: set[str] = set()
        instr_pairwise, f_blend, h_bar = _combine_family_pairwise_homogeneity_detail(
            legacy_instr, features, active_pairwise_branches=active_pairwise_branches
        )

        conc_legacy = float(features.get("timbral_state_concentration", 1.0) or 1.0)
        conc_only = float(features.get("technique_only_concentration", conc_legacy) or conc_legacy)
        conc_for_technique_multiplier = conc_legacy if timbral_mode_for_diag == "legacy" else float(conc_only)
        technique_component = float(_TIMBRAL_TECH_CONC_OFF + _TIMBRAL_TECH_CONC_SCL * conc_for_technique_multiplier)
        instr_after_tech = float(np.clip(instr_pairwise * technique_component, 0.0, 1.0))

        slices = features.get("timbral_note_slices")
        cross_boost = verified_cross_timbral_boost(
            slices if isinstance(slices, list) else None,
            float(features.get("total_overlap_mass", 0.0) or 0.0),
        )
        instr_final = float(np.clip(instr_after_tech + cross_boost, 0.0, 1.0))

        h = w_instr * instr_final + w_reg * register_component
        if not math.isfinite(h):
            return 0.5, _empty_diag(0.5)
        h_out = float(max(0.0, min(1.0, h)))

        inst_dist, fam_dist = _timbral_overlap_mass_distributions(features)
        tech_dist = {str(k): float(v) for k, v in (features.get("timbral_state_distribution") or {}).items()}
        dom = features.get("dominant_timbral_state")
        dom_s = str(dom) if dom is not None else None

        diag: dict[str, Any] = {
            "H_timbral": h_out,
            "weight_instrument": float(w_instr),
            "weight_register": float(w_reg),
            "instrument_component": instr_final,
            "instrument_pairwise_component": float(instr_pairwise),
            "register_component": float(register_component),
            "timbral_state_concentration": float(conc_legacy),
            "technique_component": float(technique_component),
            "cross_family_boost": float(cross_boost),
            "legacy_instrument_homogeneity": float(legacy_instr),
            "pairwise_blend_weight": float(f_blend),
            "pairwise_branch_mean": float(h_bar),
            "family_component": family_component,
            "n_events": n_score_events,
            "n_notes": n_notes,
            "n_instruments": n_instr,
            "n_families": n_families,
            "instrument_distribution": inst_dist,
            "family_distribution": fam_dist,
            "technique_distribution": tech_dist,
            "dominant_timbral_state": dom_s,
            "instrument_distribution_concentration": float(
                _numeric_feature_or(
                    features,
                    "instrument_distribution_concentration",
                    timbral_state_concentration_from_distribution({str(k): float(v) for k, v in inst_dist.items()}),
                )
            ),
            "family_distribution_concentration": float(
                _numeric_feature_or(
                    features,
                    "family_distribution_concentration",
                    timbral_state_concentration_from_distribution({str(k): float(v) for k, v in fam_dist.items()}),
                )
            ),
            "technique_only_concentration": float(
                _numeric_feature_or(features, "technique_only_concentration", float(conc_only))
            ),
            "full_state_concentration": float(
                _numeric_feature_or(features, "full_state_concentration", float(conc_legacy))
            ),
            "legacy_concentration": float(conc_legacy),
            "technique_only_distribution": dict(features.get("technique_only_distribution") or {}),
            "technique_state_distribution_full": dict(features.get("technique_state_distribution_full") or {}),
        }
        diag.update(timbral_model_metadata_for_diagnostics(timbral_mode_for_diag))
        diag.update(
            build_timbral_window_diagnostics_bundle(
                _window_diag_semantic_names(
                    cfg,
                    active_pairwise_branches,
                    register_percussion_blend=register_percussion_blend,
                    cross_boost=float(cross_boost),
                )
            )
        )
        return h_out, diag

    def compute_H_timbral(self, features: dict | None) -> float:
        h, _diag = self.compute_H_timbral_decomposition(features)
        return h

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
