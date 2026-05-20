"""
Symbolic string-harmonic pitch roles and optional artificial-harmonic sounding inference.

Uses only MusicXML / music21 structures (no PDF/audio). Ambiguous harmonic noteheads
(diamond, square) on bowed orchestral strings are treated as candidates only when
MusicXML does not assign base/touching/sounding roles.

Interval table source metadata: see ``HARMONIC_INTERVAL_TABLE_SOURCE`` and
``docs/STRING_HARMONIC_INTERVAL_REFERENCE.md``.
"""

from __future__ import annotations

import math
from typing import Any

from homogeneity_analyser.analyzers.pitch_interpretation import (
    interpret_pitch_tone,
    normalize_pitch_interpretation_mode,
)
from homogeneity_analyser.analyzers.string_pairwise_timbral import is_bowed_orchestral_string

HARMONIC_PITCH_POLICY_CONSERVATIVE = "conservative"
HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL = "infer_common_artificial"
HARMONIC_PITCH_POLICY_WRITTEN_AS_SOUNDING = "written_as_sounding"

HARMONIC_PITCH_POLICIES: tuple[str, ...] = (
    HARMONIC_PITCH_POLICY_CONSERVATIVE,
    HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL,
    HARMONIC_PITCH_POLICY_WRITTEN_AS_SOUNDING,
)

# Practical chart reference (not peer-reviewed organology); see docs.
HARMONIC_INTERVAL_TABLE_SOURCE: dict[str, str] = {
    "source_name": "Violin Harmonics — arranged by Agatha Mallett",
    "local_file": "violin_harmonics_chart.pdf",
    "local_reference_page": "1",
    "source_status": "practical notation chart, not peer-reviewed theoretical source",
    "release_status": "usable as practical reference; cite stronger organological sources where possible",
    "evidence_type": "string_harmonic_notation_reference",
    "scope": (
        "bowed string artificial harmonics (violin chart; same interval rows applied to viola, cello, double bass)"
    ),
}

ARTIFICIAL_STRING_HARMONIC_INTERVALS: dict[str, dict[str, Any]] = {
    "octave": {
        "touching_interval_semitones": 12,
        "sounding_interval_above_base": 12,
        "harmonic_division": 2,
        "description": ("touching pitch an octave above stopped/base pitch; sounds one octave above the base"),
        "confidence": "high",
        "intonation_note": "perfect",
    },
    "perfect_fifth": {
        "touching_interval_semitones": 7,
        "sounding_interval_above_base": 19,
        "harmonic_division": 3,
        "description": (
            "touching pitch a perfect fifth above stopped/base pitch; sounds one octave plus a perfect fifth "
            "above the base"
        ),
        "confidence": "high",
        "intonation_note": "slightly imperfect / just-harmonic relation",
    },
    "perfect_fourth": {
        "touching_interval_semitones": 5,
        "sounding_interval_above_base": 24,
        "harmonic_division": 4,
        "description": ("touching pitch a perfect fourth above stopped/base pitch; sounds two octaves above the base"),
        "confidence": "high",
        "intonation_note": "perfect",
    },
    "major_third": {
        "touching_interval_semitones": 4,
        "sounding_interval_above_base": 28,
        "harmonic_division": 5,
        "description": (
            "touching pitch a major third above stopped/base pitch; sounds approximately two octaves plus a "
            "major third above the base"
        ),
        "confidence": "moderate",
        "warning": "tempered approximation; harmonic 5 is not exactly equal-tempered",
        "intonation_note": "partial series vs 12-TET",
    },
    "minor_third": {
        "touching_interval_semitones": 3,
        "sounding_interval_above_base": 31,
        "harmonic_division": 6,
        "description": (
            "touching pitch a minor third above stopped/base pitch; sounds approximately two octaves plus a "
            "perfect fifth above the base"
        ),
        "confidence": "moderate",
        "warning": "tempered approximation; harmonic 6 is not exactly equal-tempered",
        "intonation_note": "partial series vs 12-TET",
    },
}

# Descending touching-interval order: unambiguous at tolerance 0.25; prefer first exact best_delta.
_ARTIFICIAL_RULE_MATCH_ORDER: tuple[str, ...] = (
    "octave",
    "perfect_fifth",
    "perfect_fourth",
    "major_third",
    "minor_third",
)

INTERVAL_MATCH_TOLERANCE_SEMITONES = 0.25

_DIAMOND_NOTEHEAD_WARNING = (
    "Diamond notehead on bowed string detected, but MusicXML does not specify whether this is sounding, base, "
    "or touching pitch."
)
_NON_STRING_DIAMOND_WARNING = "Diamond notehead ignored as harmonic outside bowed strings."


def normalize_harmonic_pitch_policy(mode: str | None) -> str:
    s = str(mode or "").strip().lower()
    if s in HARMONIC_PITCH_POLICIES:
        return s
    return HARMONIC_PITCH_POLICY_CONSERVATIVE


def _empty_harmonic_fields() -> dict[str, Any]:
    return {
        "harmonic_state": "none",
        "harmonic_type": "none",
        "harmonic_pitch_role": "none",
        "harmonic_detection_source": "none",
        "harmonic_base_pitch": "",
        "harmonic_base_midi": "",
        "harmonic_touching_pitch": "",
        "harmonic_touching_midi": "",
        "harmonic_touching_interval_semitones": "",
        "harmonic_interval_rule_id": "",
        "harmonic_sounding_pitch": "",
        "harmonic_sounding_midi": "",
        "harmonic_sounding_status": "unavailable",
        "harmonic_pitch_policy": "",
        "harmonic_warning": "",
    }


def _pitch_name_from_ps(ps: float) -> str:
    from music21 import pitch as m21pitch

    try:
        return m21pitch.Pitch(ps=float(ps)).nameWithOctave
    except (AttributeError, TypeError, ValueError):
        return ""


def _string_harmonics(note: Any) -> list[Any]:
    from music21 import articulations

    out: list[Any] = []
    for a in getattr(note, "articulations", None) or []:
        if isinstance(a, articulations.StringHarmonic):
            out.append(a)
    return out


def _bowed_string_ambiguous_harmonic_notehead(note: Any) -> bool:
    """Diamond / square noteheads often mark touching nodes; not used on winds here."""
    nh = getattr(note, "notehead", None)
    if nh is None:
        return False
    s = str(nh).strip().lower()
    return s in ("diamond", "square")


def _warning_for_artificial_rule_row(row: dict[str, Any]) -> str:
    parts: list[str] = []
    w = str(row.get("warning") or "").strip()
    if w:
        parts.append(w)
    into = str(row.get("intonation_note") or "").strip()
    if into and into.lower() not in ("perfect",):
        parts.append(f"intonation_note={into}")
    conf = str(row.get("confidence") or "").strip()
    if conf == "moderate":
        parts.append(f"rule_confidence={conf}")
    return "; ".join(parts)


def match_artificial_harmonic_interval(
    base_midi: float,
    touching_midi: float,
) -> tuple[float | None, str, str, str, float | None]:
    """
    Match ``touching_midi - base_midi`` against ``ARTIFICIAL_STRING_HARMONIC_INTERVALS``.

    Returns
    -------
    sounding_written_ps, harmonic_sounding_status, harmonic_warning, rule_id, touching_interval_semitones
    """
    iv = float(touching_midi) - float(base_midi)
    tol = float(INTERVAL_MATCH_TOLERANCE_SEMITONES)
    best_rule: str | None = None
    best_delta = float("inf")
    for rid in _ARTIFICIAL_RULE_MATCH_ORDER:
        row = ARTIFICIAL_STRING_HARMONIC_INTERVALS.get(rid) or {}
        target = float(row.get("touching_interval_semitones", float("nan")))
        if not math.isfinite(target):
            continue
        d = abs(iv - target)
        if d <= tol and d < best_delta:
            best_delta = d
            best_rule = rid
    if best_rule is None:
        return (
            None,
            "unresolved",
            "Touching-to-base interval not recognised for artificial harmonic inference.",
            "",
            round(iv, 4) if math.isfinite(iv) else None,
        )
    row = ARTIFICIAL_STRING_HARMONIC_INTERVALS[best_rule]
    snd = float(base_midi) + float(row["sounding_interval_above_base"])
    warn = _warning_for_artificial_rule_row(row)
    return float(snd), "inferred_common_artificial", warn, best_rule, round(iv, 4)


def infer_artificial_sounding_written_midi(base_midi: float, touching_midi: float) -> tuple[float | None, str, str]:
    """
    Return (sounding_written_ps, harmonic_sounding_status, harmonic_warning).

    ``sounding_written_ps`` is in staff notated MIDI space (same frame as ``effective_written_midi``).
    """
    sw, st, warn, _rid, _iv = match_artificial_harmonic_interval(base_midi, touching_midi)
    return sw, st, warn


def sounding_midi_from_baked_written_ps(
    written_ps: float,
    trans: Any,
    *,
    mode: str,
    canonical_instrument: str | None,
) -> float:
    """Apply the same pitch_interpretation_mode / transposition rules to a baked written MIDI value."""
    from music21 import pitch as mp

    p0 = mp.Pitch()
    p0.ps = float(written_ps)
    m = interpret_pitch_tone(
        p0, trans, mode=normalize_pitch_interpretation_mode(mode), canonical_instrument=canonical_instrument
    )
    return float(m["effective_sounding_midi"])


def _merge_string_harmonic_bundle(
    *,
    htype: str,
    hstate: str,
    role: str,
    source: str,
    base_ps: float | None,
    touch_ps: float | None,
    sound_ps: float | None,
    status: str,
    warning: str,
    apply_sounding_ps: float | None,
    touching_interval_semitones: float | None = None,
    interval_rule_id: str = "",
    harmonic_pitch_policy: str = "",
) -> dict[str, Any]:
    out = _empty_harmonic_fields()
    out["harmonic_type"] = htype
    out["harmonic_state"] = hstate
    out["harmonic_pitch_role"] = role
    out["harmonic_detection_source"] = source
    if touching_interval_semitones is not None and math.isfinite(float(touching_interval_semitones)):
        out["harmonic_touching_interval_semitones"] = round(float(touching_interval_semitones), 4)
    out["harmonic_interval_rule_id"] = str(interval_rule_id or "")
    out["harmonic_pitch_policy"] = str(harmonic_pitch_policy or "")
    if base_ps is not None and math.isfinite(float(base_ps)):
        out["harmonic_base_midi"] = round(float(base_ps), 4)
        out["harmonic_base_pitch"] = _pitch_name_from_ps(float(base_ps))
    if touch_ps is not None and math.isfinite(float(touch_ps)):
        out["harmonic_touching_midi"] = round(float(touch_ps), 4)
        out["harmonic_touching_pitch"] = _pitch_name_from_ps(float(touch_ps))
    if sound_ps is not None and math.isfinite(float(sound_ps)):
        out["harmonic_sounding_midi"] = round(float(sound_ps), 4)
        out["harmonic_sounding_pitch"] = _pitch_name_from_ps(float(sound_ps))
    out["harmonic_sounding_status"] = status
    out["harmonic_warning"] = warning
    # Register / H_TI: only explicit MusicXML sounding or table-matched artificial inference may override MIDI.
    if (
        apply_sounding_ps is not None
        and math.isfinite(float(apply_sounding_ps))
        and status in ("explicit", "inferred_common_artificial")
    ):
        out["_apply_effective_sounding_midi"] = float(apply_sounding_ps)
    return out


def _try_chord_two_pitch_artificial(
    note: Any,
    metas: list[dict[str, Any]],
    canon: str,
    policy: str,
    trans: Any,
    mode: str,
) -> dict[str, Any] | None:
    """
    If a 2-pitch Chord on a bowed string has explicit artificial harmonic markup (music21
    ``StringHarmonic``) without a resolved per-pitch ``pitchType``, infer sounding from the
    two encoded written pitches (lower MIDI as base, higher as touching), then try the
    reverse order if the first attempt fails.
    """
    from music21 import chord as m21chord

    if policy != HARMONIC_PITCH_POLICY_INFER_COMMON_ARTIFICIAL:
        return None
    if not is_bowed_orchestral_string(str(canon)):
        return None
    if not isinstance(note, m21chord.Chord) or len(metas) != 2:
        return None
    harms = _string_harmonics(note)
    if not harms:
        return None
    if not any(getattr(h, "harmonicType", None) == "artificial" for h in harms):
        return None
    # If any articulation already pins sounding, do not second-guess here.
    if any(getattr(h, "pitchType", None) == "sounding" for h in harms):
        return None

    w0 = float(metas[0].get("effective_written_midi") or 0.0)
    w1 = float(metas[1].get("effective_written_midi") or 0.0)
    if not (math.isfinite(w0) and math.isfinite(w1)):
        return None

    def _attempt(base_m: float, touch_m: float) -> dict[str, Any] | None:
        sw, st, warn, rid, tiv = match_artificial_harmonic_interval(base_m, touch_m)
        if sw is None or st != "inferred_common_artificial":
            return None
        eff_snd = sounding_midi_from_baked_written_ps(float(sw), trans, mode=mode, canonical_instrument=canon)
        return {
            "sounding_written_ps": float(sw),
            "effective_sounding_midi": float(eff_snd),
            "base_midi": float(base_m),
            "touch_midi": float(touch_m),
            "status": st,
            "warning": warn,
            "rule_id": rid,
            "touching_interval_semitones": tiv,
        }

    lo, hi = (w0, w1) if w0 <= w1 else (w1, w0)
    got = _attempt(lo, hi)
    if got is None:
        got = _attempt(hi, lo)
    return got


def finalize_harmonic_pitches_for_note(
    note: Any,
    part: Any,
    mode: str,
    trans_resolver: Any,
    canonical_instrument: str | None,
    harmonic_pitch_policy: str | None,
    pits: list[float],
    metas: list[dict[str, Any]],
) -> None:
    """Mutates ``metas`` and ``pits`` in place."""
    if not metas:
        return
    policy = normalize_harmonic_pitch_policy(harmonic_pitch_policy)
    canon = str(canonical_instrument or "").strip().lower()
    trans = trans_resolver(note, part)
    mode_n = normalize_pitch_interpretation_mode(mode)

    chord_bundle = _try_chord_two_pitch_artificial(note, metas, canon, policy, trans, mode_n)
    if chord_bundle is not None:
        sw = float(chord_bundle["sounding_written_ps"])
        eff_s = float(chord_bundle["effective_sounding_midi"])
        warn = str(chord_bundle.get("warning") or "")
        base_m = float(chord_bundle["base_midi"])
        touch_m = float(chord_bundle["touch_midi"])
        rid = str(chord_bundle.get("rule_id") or "")
        tiv = chord_bundle.get("touching_interval_semitones")
        tiv_f = float(tiv) if tiv is not None and math.isfinite(float(tiv)) else None
        for i, m in enumerate(metas):
            role = "base" if abs(float(m.get("effective_written_midi") or 0.0) - base_m) < 1e-3 else "touching"
            hb = _merge_string_harmonic_bundle(
                htype="artificial",
                hstate="artificial",
                role=role,
                source="music21_string_harmonic",
                base_ps=base_m,
                touch_ps=touch_m,
                sound_ps=sw,
                status="inferred_common_artificial",
                warning=warn,
                apply_sounding_ps=eff_s,
                touching_interval_semitones=tiv_f,
                interval_rule_id=rid,
                harmonic_pitch_policy=policy,
            )
            m.update(hb)
            m["effective_sounding_midi"] = float(eff_s)
            pits[i] = float(eff_s)
            m.pop("_apply_effective_sounding_midi", None)
        return

    for i, m in enumerate(metas):
        hb = _harmonic_bundle_for_tone(
            note=note,
            tone_index=i,
            trans=trans,
            mode=mode_n,
            canon=canon,
            policy=policy,
            base_meta=m,
        )
        m.update(hb)
        app = hb.get("_apply_effective_sounding_midi")
        if app is not None and math.isfinite(float(app)):
            m["effective_sounding_midi"] = float(app)
            pits[i] = float(app)
        m.pop("_apply_effective_sounding_midi", None)


def _harmonic_bundle_for_tone(
    *,
    note: Any,
    tone_index: int,
    trans: Any,
    mode: str,
    canon: str,
    policy: str,
    base_meta: dict[str, Any],
) -> dict[str, Any]:
    _ = tone_index
    eff_w = float(base_meta.get("effective_written_midi") or float("nan"))
    if not math.isfinite(eff_w):
        return _empty_harmonic_fields()

    nh_harm_vis = _bowed_string_ambiguous_harmonic_notehead(note)
    harms = _string_harmonics(note)

    # --- Explicit MusicXML / music21 StringHarmonic ---
    if harms:
        # Prefer the first harmonic articulation (exporters rarely attach multiples).
        h0 = harms[0]
        htype = str(getattr(h0, "harmonicType", None) or "unknown")
        ptype = getattr(h0, "pitchType", None)
        src = "explicit_musicxml_harmonic"
        if htype == "natural":
            if ptype == "sounding":
                snd = sounding_midi_from_baked_written_ps(eff_w, trans, mode=mode, canonical_instrument=canon)
                return _merge_string_harmonic_bundle(
                    htype="natural",
                    hstate="natural",
                    role="sounding",
                    source=src,
                    base_ps=None,
                    touch_ps=None,
                    sound_ps=eff_w,
                    status="explicit",
                    warning="",
                    apply_sounding_ps=snd,
                    harmonic_pitch_policy=policy,
                )
            # Natural harmonic without explicit sounding pitch: do not infer node from notation alone.
            return _merge_string_harmonic_bundle(
                htype="natural",
                hstate="harmonic_candidate",
                role="unresolved",
                source=src,
                base_ps=None,
                touch_ps=None,
                sound_ps=None,
                status="unresolved",
                warning=(
                    "Natural harmonic without explicit sounding pitch in MusicXML; notated pitch not used as node; "
                    "sounding not computed without string/node/fingering data."
                ),
                apply_sounding_ps=None,
                harmonic_pitch_policy=policy,
            )

        if htype == "artificial":
            if ptype == "sounding":
                snd = sounding_midi_from_baked_written_ps(eff_w, trans, mode=mode, canonical_instrument=canon)
                return _merge_string_harmonic_bundle(
                    htype="artificial",
                    hstate="artificial",
                    role="sounding",
                    source=src,
                    base_ps=None,
                    touch_ps=None,
                    sound_ps=eff_w,
                    status="explicit",
                    warning="",
                    apply_sounding_ps=snd,
                    harmonic_pitch_policy=policy,
                )
            if ptype == "base":
                return _merge_string_harmonic_bundle(
                    htype="artificial",
                    hstate="artificial",
                    role="base",
                    source=src,
                    base_ps=eff_w,
                    touch_ps=None,
                    sound_ps=None,
                    status="unresolved",
                    warning="Artificial harmonic base pitch without touching pitch; cannot infer sounding pitch.",
                    apply_sounding_ps=None,
                    harmonic_pitch_policy=policy,
                )
            if ptype == "touching":
                return _merge_string_harmonic_bundle(
                    htype="artificial",
                    hstate="artificial",
                    role="touching",
                    source=src,
                    base_ps=None,
                    touch_ps=eff_w,
                    sound_ps=None,
                    status="unresolved",
                    warning="Artificial harmonic touching pitch without paired base pitch on this note/chord.",
                    apply_sounding_ps=None,
                    harmonic_pitch_policy=policy,
                )
            # artificial, pitchType None — chord inference handled earlier; single note: unresolved
            return _merge_string_harmonic_bundle(
                htype="artificial",
                hstate="artificial",
                role="unresolved",
                source="music21_string_harmonic",
                base_ps=None,
                touch_ps=None,
                sound_ps=None,
                status="unresolved",
                warning="Artificial harmonic without base/touching/sounding pitch role in MusicXML.",
                apply_sounding_ps=None,
                harmonic_pitch_policy=policy,
            )

    # --- Diamond / square notehead (string-only candidate; no XML harmonic roles) ---
    if nh_harm_vis:
        if is_bowed_orchestral_string(canon):
            if policy == HARMONIC_PITCH_POLICY_WRITTEN_AS_SOUNDING:
                snd = sounding_midi_from_baked_written_ps(eff_w, trans, mode=mode, canonical_instrument=canon)
                return _merge_string_harmonic_bundle(
                    htype="unknown",
                    hstate="harmonic_candidate",
                    role="sounding",
                    source="inferred_diamond_notehead",
                    base_ps=None,
                    touch_ps=None,
                    sound_ps=eff_w,
                    status="written_as_sounding_policy",
                    warning=(
                        "written_as_sounding policy: treating notated diamond pitch as sounding pitch "
                        "(verify exporter behaviour; risky for editions that encode touching pitch)."
                    ),
                    apply_sounding_ps=None,
                    harmonic_pitch_policy=policy,
                )
            return _merge_string_harmonic_bundle(
                htype="unknown",
                hstate="harmonic_candidate",
                role="unresolved",
                source="inferred_diamond_notehead",
                base_ps=None,
                touch_ps=None,
                sound_ps=None,
                status="unresolved",
                warning=_DIAMOND_NOTEHEAD_WARNING,
                apply_sounding_ps=None,
                harmonic_pitch_policy=policy,
            )
        # Non-string diamond/square: never treat as harmonic pitch candidate
        return _merge_string_harmonic_bundle(
            htype="none",
            hstate="none",
            role="none",
            source="none",
            base_ps=None,
            touch_ps=None,
            sound_ps=None,
            status="unavailable",
            warning=_NON_STRING_DIAMOND_WARNING if nh_harm_vis else "",
            apply_sounding_ps=None,
            harmonic_pitch_policy=policy,
        )

    return _empty_harmonic_fields()
