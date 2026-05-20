"""Summary text and combined export assembly."""

from __future__ import annotations

import csv
import io
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from homogeneity_analyser.services.param_validation import safe_nan_summary


def _fmt_stat(v: float | None, *, prec: int = 4) -> str:
    return "n/a" if v is None else f"{v:.{prec}f}"


def format_homogeneity_summary(
    results: dict[str, Any],
    analyzer: Any,
    change_times: list[float],
    sensitivity: list[tuple[float, float, float, float]],
    params: dict[str, Any],
) -> str:
    H = np.array(results["H"], dtype=float)
    hs = safe_nan_summary(H)
    w1 = params.get("weight_m1", 1.0 / 3.0)
    w2 = params.get("weight_m2", 1.0 / 3.0)
    w3 = params.get("weight_m3", 1.0 / 3.0)
    lines = [
        "H(t) = weighted geometric mean of m1 (intra), m2 (inter Wasserstein), m3 (multi-scale); "
        f"weights m1:m2:m3 = {w1:.3f}:{w2:.3f}:{w3:.3f} (normalized).",
        f"Windows: {len(H)}",
        f"Score duration (quarterLength): {analyzer.end_time:.3f}",
        f"H min: {_fmt_stat(hs['min'])}",
        f"H mean: {_fmt_stat(hs['mean'])}",
        f"H max: {_fmt_stat(hs['max'])}",
        f"Pitch space: {params.get('pitch_space', 'absolute')}",
        f"Pitch bin step: {params.get('pitch_bin_step', 1.0)}",
        f"Silence intra value: {params.get('silence_intra_value', 0.5):.2f}",
        f"Silence transition value: {params.get('silence_transition_value', 0.5):.2f}",
        f"Allow partial scales: {params.get('allow_partial_scales', True)}",
        f"Change points: {len(change_times)}",
        f"Change times: {', '.join(f'{t:.2f}' for t in change_times) if change_times else 'none'}",
    ]
    if sensitivity:
        lines.append("Sensitivity (window size → corr/mean/std):")
        for ws, corr, mean, std in sensitivity:
            lines.append(f"  {ws:.2f} → r={corr:.3f}, mean={mean:.3f}, std={std:.3f}")
    else:
        lines.append("Sensitivity: n/a (single aggregate mode)")
    return "\n".join(lines)


def build_combined_csv(
    t_h: np.ndarray,
    H: np.ndarray,
    H_timbral_aligned: np.ndarray,
    rh: dict[str, Any],
    *,
    dominant_timbral_aligned: list[Any] | None = None,
    H_cluster_aligned: np.ndarray | None = None,
    H_orchestration_symbolic_aligned: np.ndarray | None = None,
    H_notated_fusion_potential_aligned: np.ndarray | None = None,
    H_notated_fusion_potential_dynamic_aligned: np.ndarray | None = None,
) -> str:
    """Build combined CSV text aligned to homogeneity time grid.

    When ``dominant_timbral_aligned`` is provided with one entry per ``t_h`` row, appends
    ``dominant_timbral_state`` (RFC-4180 quoted where needed).

    When ``H_cluster_aligned`` is provided with length matching ``t_h``, appends ``H_cluster``
    (instrument-independent vertical pitch-cluster compactness).

    When ``H_orchestration_symbolic_aligned`` is provided with matching length, appends
    ``H_orchestration_symbolic`` (Herfindahl-only symbolic orchestration uniformity).

    When ``H_notated_fusion_potential_aligned`` is provided with matching length, appends
    ``H_notated_fusion_potential`` (notation-derived fusion-potential proxy).

    When ``H_notated_fusion_potential_dynamic_aligned`` is provided with matching length, appends
    ``H_notated_fusion_potential_dynamic`` (base scalar × dynamic coherence ** weight_dynamic).
    """
    has_m = "m1" in rh and len(rh.get("m1", [])) == len(t_h)
    dom_opt = dominant_timbral_aligned
    if dom_opt is not None and len(dom_opt) == len(t_h):
        has_dom = True
        dom_rows: list[Any] = dom_opt
    else:
        has_dom = False
        dom_rows = []
    hc = np.asarray(H_cluster_aligned, dtype=float).ravel() if H_cluster_aligned is not None else None
    has_cluster = hc is not None and hc.size == len(t_h)
    ho = (
        np.asarray(H_orchestration_symbolic_aligned, dtype=float).ravel()
        if H_orchestration_symbolic_aligned is not None
        else None
    )
    has_orch = ho is not None and ho.size == len(t_h)
    hn = (
        np.asarray(H_notated_fusion_potential_aligned, dtype=float).ravel()
        if H_notated_fusion_potential_aligned is not None
        else None
    )
    has_nf = hn is not None and hn.size == len(t_h)
    hnd = (
        np.asarray(H_notated_fusion_potential_dynamic_aligned, dtype=float).ravel()
        if H_notated_fusion_potential_dynamic_aligned is not None
        else None
    )
    has_nfd = hnd is not None and hnd.size == len(t_h)
    # Narrow optional arrays for indexing inside CSV loops (mypy + numpy stubs).
    hc_ix = cast(NDArray[np.floating[Any]], hc) if has_cluster else None
    ho_ix = cast(NDArray[np.floating[Any]], ho) if has_orch else None
    hn_ix = cast(NDArray[np.floating[Any]], hn) if has_nf else None
    hnd_ix = cast(NDArray[np.floating[Any]], hnd) if has_nfd else None
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    if has_m:
        header = ["t_quarterLength", "H", "m1", "m2", "m3", "H_timbral"]
        if has_cluster:
            header.append("H_cluster")
        if has_orch:
            header.append("H_orchestration_symbolic")
        if has_nf:
            header.append("H_notated_fusion_potential")
        if has_nfd:
            header.append("H_notated_fusion_potential_dynamic")
        if has_dom:
            header.append("dominant_timbral_state")
        w.writerow(header)
        m1a, m2a, m3a = rh["m1"], rh["m2"], rh["m3"]
        for i in range(len(t_h)):
            row = [
                float(t_h[i]),
                float(H[i]),
                m1a[i],
                m2a[i],
                m3a[i],
                float(H_timbral_aligned[i]),
            ]
            if has_cluster and hc_ix is not None:
                row.append(float(hc_ix[i]))
            if has_orch and ho_ix is not None:
                row.append(float(ho_ix[i]))
            if has_nf and hn_ix is not None:
                row.append(float(hn_ix[i]))
            if has_nfd and hnd_ix is not None:
                row.append(float(hnd_ix[i]))
            if has_dom:
                row.append(dom_rows[i])
            w.writerow(row)
    else:
        header = ["t_quarterLength", "H", "H_timbral"]
        if has_cluster:
            header.append("H_cluster")
        if has_orch:
            header.append("H_orchestration_symbolic")
        if has_nf:
            header.append("H_notated_fusion_potential")
        if has_nfd:
            header.append("H_notated_fusion_potential_dynamic")
        if has_dom:
            header.append("dominant_timbral_state")
        w.writerow(header)
        for i in range(len(t_h)):
            row = [float(t_h[i]), float(H[i]), float(H_timbral_aligned[i])]
            if has_cluster and hc_ix is not None:
                row.append(float(hc_ix[i]))
            if has_orch and ho_ix is not None:
                row.append(float(ho_ix[i]))
            if has_nf and hn_ix is not None:
                row.append(float(hn_ix[i]))
            if has_nfd and hnd_ix is not None:
                row.append(float(hnd_ix[i]))
            if has_dom:
                row.append(dom_rows[i])
            w.writerow(row)
    return buf.getvalue()


# Per-window table for UI + standalone CSV: cluster vs symbolic orch vs fusion vs legacy timbral.
CLUSTER_ORCH_FUSION_DIAGNOSTICS_COLUMNS: tuple[str, ...] = (
    "t_quarterLength",
    "H_cluster",
    "H_orchestration_symbolic",
    "H_notated_fusion_potential",
    "H_notated_fusion_potential_dynamic",
    "H_fusion_acoustic_heuristic",
    "legacy_H_timbral",
    "confidence_score",
    "confidence_label",
    "dominant_timbral_state",
    "main_penalty_reason",
)


def build_cluster_orch_fusion_diagnostics_rows(
    t_h: np.ndarray,
    H_cluster: np.ndarray,
    H_orchestration_symbolic: np.ndarray,
    H_notated_fusion_potential: np.ndarray,
    H_notated_fusion_potential_dynamic: np.ndarray,
    H_fusion_acoustic_heuristic: np.ndarray,
    legacy_H_timbral: np.ndarray,
    confidence_score: list[float | None],
    confidence_label: list[Any],
    dominant_timbral_state: list[Any],
    main_penalty_reason: list[Any],
) -> list[dict[str, Any]]:
    """One dict per window; values are JSON-/CSV-friendly (no numpy scalars)."""
    tt = np.asarray(t_h, dtype=float).ravel()
    hc = np.asarray(H_cluster, dtype=float).ravel()
    ho = np.asarray(H_orchestration_symbolic, dtype=float).ravel()
    hn = np.asarray(H_notated_fusion_potential, dtype=float).ravel()
    hnd = np.asarray(H_notated_fusion_potential_dynamic, dtype=float).ravel()
    hf = np.asarray(H_fusion_acoustic_heuristic, dtype=float).ravel()
    hl = np.asarray(legacy_H_timbral, dtype=float).ravel()
    n = int(tt.size)
    rows: list[dict[str, Any]] = []

    def _conf(v: float | None) -> float | None:
        if v is None:
            return None
        fv = float(v)
        if np.isnan(fv) or np.isinf(fv):
            return None
        return fv

    for i in range(n):
        rows.append(
            {
                "t_quarterLength": float(tt[i]),
                "H_cluster": float(hc[i]) if i < hc.size else float("nan"),
                "H_orchestration_symbolic": float(ho[i]) if i < ho.size else float("nan"),
                "H_notated_fusion_potential": float(hn[i]) if i < hn.size else float("nan"),
                "H_notated_fusion_potential_dynamic": float(hnd[i]) if i < hnd.size else float("nan"),
                "H_fusion_acoustic_heuristic": float(hf[i]) if i < hf.size else float("nan"),
                "legacy_H_timbral": float(hl[i]) if i < hl.size else float("nan"),
                "confidence_score": _conf(confidence_score[i] if i < len(confidence_score) else None),
                "confidence_label": confidence_label[i] if i < len(confidence_label) else None,
                "dominant_timbral_state": dominant_timbral_state[i] if i < len(dominant_timbral_state) else None,
                "main_penalty_reason": main_penalty_reason[i] if i < len(main_penalty_reason) else None,
            }
        )
    return rows


def build_cluster_orch_fusion_diagnostics_csv(rows: list[dict[str, Any]]) -> str:
    """RFC-4180 CSV text for :data:`CLUSTER_ORCH_FUSION_DIAGNOSTICS_COLUMNS`."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(list(CLUSTER_ORCH_FUSION_DIAGNOSTICS_COLUMNS))
    for r in rows:
        line: list[Any] = []
        for c in CLUSTER_ORCH_FUSION_DIAGNOSTICS_COLUMNS:
            v = r.get(c, "")
            if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
                line.append("")
            else:
                line.append(v)
        w.writerow(line)
    return buf.getvalue()
