"""
Pitch-dependent **spectral roughness proxy** for ``H_fusion_acoustic_heuristic``.

This is an explicit v1 engineering surrogate: harmonic trains are enumerated from MIDI f0,
amplitudes follow a simple power-law rolloff controlled by the instrument's ``spectral_slope``
proxy, and close non-coincident partial pairs accumulate a penalty. It is **not** a full
psychoacoustic dissonance model (no critical bands, no roughness calibration to listening tests).

The weighting template and harmonic count are **project-specific** constants documented here;
they are not inferred from user audio.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

# Declared provenance for the mathematical template (not a literature page number).
SPECTRAL_PROXY_FORMULA_SOURCE_KEY = "project_specific"

# MIDI A4 reference for Hz conversion.
_A4_HZ = 440.0
_A4_MIDI = 69.0


def midi_to_hz(midi: float) -> float:
    """Convert MIDI pitch space (float) to fundamental frequency in Hz."""
    return float(_A4_HZ * (2.0 ** ((float(midi) - _A4_MIDI) / 12.0)))


def harmonic_frequencies(f0_hz: float, n_harmonics: int) -> np.ndarray:
    """Return frequencies ``[f0, 2f0, …, n f0]`` (length ``n_harmonics``)."""
    n = max(1, int(n_harmonics))
    k = np.arange(1, n + 1, dtype=float)
    return float(f0_hz) * k


def harmonic_amplitudes(
    n_harmonics: int,
    spectral_slope: float | None,
    *,
    neutral_slope: float = -0.45,
) -> np.ndarray:
    """
    Simple **power-law** harmonic weights ``a_k ∝ k^{slope}`` with ``slope <= 0``.

    ``spectral_slope`` comes from the fusion feature vector (dB-like proxy stored as a
    negative scalar). When missing, ``neutral_slope`` is used and callers should record
    a confidence penalty separately.
    """
    n = max(1, int(n_harmonics))
    s = float(spectral_slope) if spectral_slope is not None else float(neutral_slope)
    s = min(-0.05, s)  # avoid division blow-up at k=0; slopes are expected negative
    k = np.arange(1, n + 1, dtype=float)
    raw = np.power(k, s)
    tot = float(np.sum(raw))
    if tot <= 1e-15 or not math.isfinite(tot):
        return np.ones(n, dtype=float) / n
    return raw / tot


def pairwise_partial_roughness_proxy(
    freqs_a: np.ndarray,
    amps_a: np.ndarray,
    freqs_b: np.ndarray,
    amps_b: np.ndarray,
    *,
    relative_bandwidth: float = 0.02,
) -> float:
    """
    Sum over partial pairs of ``a_i a_j max(0, 1 - Δf / (w·min(f_i,f_j)))`` when partials are near.

    ``relative_bandwidth`` ``w`` sets how close partials must be (relative to the lower frequency)
    to count as interacting. This is a **deliberately simplified** stand-in for roughness-like
    interaction density, not a calibrated sensory model.
    """
    if freqs_a.size == 0 or freqs_b.size == 0:
        return 0.0
    w = max(1e-6, float(relative_bandwidth))
    penalty = 0.0
    for fa, aa in zip(freqs_a.tolist(), amps_a.tolist(), strict=False):
        for fb, ab in zip(freqs_b.tolist(), amps_b.tolist(), strict=False):
            if fa <= 0.0 or fb <= 0.0:
                continue
            denom = w * min(fa, fb)
            delta = abs(fa - fb)
            if delta >= denom:
                continue
            penalty += float(aa) * float(ab) * (1.0 - delta / denom)
    return float(penalty)


def window_spectral_roughness_proxy(
    slices: Sequence[dict[str, Any]],
    resolved_rows: Sequence[dict[str, Any]],
    *,
    n_harmonics: int = 12,
    relative_bandwidth: float = 0.02,
) -> float:
    """
    Aggregate roughness-like proxy for all unordered sounding-note pairs in ``slices``.

    Each slice must provide ``pitch`` (MIDI float) and ``overlap_ql``. Spectral slope is taken
    from ``resolved_rows[i]['vector']['spectral_slope']`` when present.
    """
    n = min(len(slices), len(resolved_rows))
    if n < 2:
        return 0.0
    masses = [max(0.0, float(slices[i].get("overlap_ql", 0.0) or 0.0)) for i in range(n)]
    rough_terms: list[float] = []
    banks: list[tuple[np.ndarray, np.ndarray]] = []
    for i in range(n):
        si = slices[i]
        ri = resolved_rows[i]
        midi_i = float(si.get("pitch", 0.0) or 0.0)
        slope_i = (ri.get("vector") or {}).get("spectral_slope")
        f0_i = midi_to_hz(midi_i)
        hzi = harmonic_frequencies(f0_i, n_harmonics)
        ai = harmonic_amplitudes(n_harmonics, float(slope_i) if slope_i is not None else None)
        banks.append((hzi, ai))
    for i in range(n):
        hzi, ai = banks[i]
        for j in range(i + 1, n):
            hzj, aj = banks[j]
            r = pairwise_partial_roughness_proxy(hzi, ai, hzj, aj, relative_bandwidth=relative_bandwidth)
            rough_terms.append(r * masses[i] * masses[j])
    if not rough_terms:
        return 0.0
    mass_sq = sum(m * m for m in masses) or 1.0
    return float(sum(rough_terms) / mass_sq)


def spectral_proxy_model_note() -> dict[str, Any]:
    """Static metadata bundle for exports/diagnostics."""
    return {
        "spectral_proxy_formula_source_key": SPECTRAL_PROXY_FORMULA_SOURCE_KEY,
        "harmonic_enumeration": "integer multiples 1..N of f0 from MIDI",
        "amplitude_law": "normalized power law k**spectral_slope with floor on slope",
        "interaction": "pairwise partial penalty for relative frequency spacing < relative_bandwidth",
        "not_audio_analysis": True,
    }
