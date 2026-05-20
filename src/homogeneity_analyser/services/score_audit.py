"""
Symbolic score audit tables for debugging MusicXML import (independent of H / U / H_timbral).

Produces JSON/CSV-serialisable dict rows only; no metric formulas.
"""

from __future__ import annotations

import csv
import io
import json
import math
from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Any

from homogeneity_analyser.analyzers.hti import compute_register_compactness_fields
from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.analyzers.percussion_ontology import get_percussion_meta
from homogeneity_analyser.analyzers.percussion_pairwise_timbral import is_percussion_family
from homogeneity_analyser.analyzers.technique_state import (
    compute_technique_uniformity_key_from_event,
    parse_standard_dynamic_mark,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_OTHER, resolve_instrument_taxonomy

__all__ = [
    "SCORE_AUDIT_EVENT_COLUMNS",
    "SCORE_AUDIT_HARMONIC_PITCH_COLUMNS",
    "SCORE_AUDIT_INVENTORY_COLUMNS",
    "SCORE_AUDIT_VERTICAL_COLUMNS",
    "audit_rows_to_csv_string",
    "build_symbolic_inspection_tables",
    "build_vertical_sonority_audit",
    "extract_instrument_inventory",
    "extract_score_event_audit",
    "note_symbolic_audit_surface",
]


def _raw_instrument_name_from_m21(ins: Any) -> str:
    if ins is None:
        return ""
    try:
        best = getattr(ins, "bestName", None)
        nm = best() if callable(best) else getattr(ins, "instrumentName", "")
        name = str(nm or "").strip()
        if name:
            return name
    except (AttributeError, TypeError, ValueError):
        pass
    return ""


def _part_instrument_fallback(part: Any) -> tuple[str, str]:
    try:
        instrs = part.getInstruments()
        if instrs:
            i0 = instrs[0]
            best = getattr(i0, "bestName", None)
            nm = best() if callable(best) else getattr(i0, "instrumentName", "")
            name = str(nm or "").strip()
            if name:
                return name, "part_context"
    except (AttributeError, TypeError, ValueError, IndexError):
        pass
    raw = getattr(part, "partName", None) or getattr(part, "id", None) or "unknown"
    if raw == "unknown":
        return "unknown", "unknown"
    return str(raw), "part_name_fallback"


def _transposition_str(ins: Any) -> str | None:
    if ins is None:
        return None
    t = getattr(ins, "transposition", None)
    if t is None:
        return None
    try:
        s = str(t)
        return s if s.strip() else None
    except (AttributeError, TypeError, ValueError):
        return None


def _part_default_instrument(part: Any) -> Any:
    try:
        return part.getInstrument(returnDefault=True)
    except (AttributeError, TypeError, ValueError):
        return None


def _instrument_class_str(ins: Any) -> str:
    if ins is None:
        return ""
    try:
        return str(ins.__class__.__name__)
    except (AttributeError, TypeError, ValueError):
        return ""


def _measure_number_and_beat(n: Any) -> tuple[int | None, float | None]:
    from music21 import stream

    try:
        meas = n.getContextByClass(stream.Measure)
    except (AttributeError, TypeError, ValueError):
        return None, None
    if meas is None:
        return None, None
    try:
        mn = int(meas.measureNumber) if meas.measureNumber is not None else None
    except (TypeError, ValueError):
        mn = None
    try:
        b = float(n.beat) if getattr(n, "beat", None) is not None else None
    except (TypeError, ValueError):
        b = None
    return mn, b


def _text_directions_raw_for_note(n: Any) -> str:
    """
    Words / directions that may affect interpretation: note-local + strictly earlier in-measure
    text (same policy as ``notation_context`` ``prior`` but preserving original casing).
    """
    from music21 import dynamics, expressions, stream

    parts: list[str] = []
    for ly in getattr(n, "lyrics", None) or []:
        t = getattr(ly, "text", None) or str(ly)
        if t and str(t).strip():
            parts.append(str(t).strip())
    for ex in getattr(n, "expressions", None) or []:
        c = getattr(ex, "content", None)
        if c and str(c).strip():
            parts.append(str(c).strip())
    try:
        meas = n.getContextByClass(stream.Measure)
    except (AttributeError, TypeError, ValueError):
        meas = None
    if meas is None or not isinstance(meas, stream.Measure):
        return " | ".join(parts) if parts else ""
    try:
        n_off = float(n.getOffsetBySite(meas))
    except (AttributeError, TypeError, ValueError):
        return " | ".join(parts) if parts else ""
    try:
        for tex in meas.recurse().getElementsByClass(expressions.TextExpression):
            c = getattr(tex, "content", None)
            if not c:
                continue
            try:
                eo = float(tex.getOffsetBySite(meas))
            except (AttributeError, TypeError, ValueError):
                continue
            if eo <= n_off:
                parts.append(str(c).strip())
        for rm in meas.recurse().getElementsByClass(expressions.RehearsalMark):
            c = getattr(rm, "content", None)
            if not c:
                continue
            try:
                eo = float(rm.getOffsetBySite(meas))
            except (AttributeError, TypeError, ValueError):
                continue
            if eo <= n_off:
                parts.append(str(c).strip())
        for dyn in meas.recurse().getElementsByClass(dynamics.Dynamic):
            v = getattr(dyn, "value", None)
            if v is None or not str(v).strip():
                continue
            try:
                eo = float(dyn.getOffsetBySite(meas))
            except (AttributeError, TypeError, ValueError):
                continue
            if eo <= n_off:
                parts.append(str(v).strip())
    except (AttributeError, TypeError, ValueError):
        pass
    return " | ".join(parts) if parts else ""


def _articulation_names(n: Any) -> str:
    arts = getattr(n, "articulations", None) or []
    names = [type(a).__name__ for a in arts]
    return ", ".join(names) if names else ""


def _expression_labels(n: Any) -> str:
    from music21 import dynamics

    exs = getattr(n, "expressions", None) or []
    out: list[str] = []
    for ex in exs:
        if isinstance(ex, dynamics.Dynamic):
            v = getattr(ex, "value", None)
            if v is not None:
                out.append(f"Dynamic({v})")
            continue
        c = getattr(ex, "content", None)
        if c:
            out.append(f"{type(ex).__name__}({c})")
        else:
            out.append(type(ex).__name__)
    return ", ".join(out) if out else ""


def _technical_notations_raw(n: Any) -> str:
    """Articulations + expression types + string technicals if present (music21 surface)."""
    chunks: list[str] = []
    a = _articulation_names(n)
    if a:
        chunks.append(f"articulations={a}")
    e = _expression_labels(n)
    if e:
        chunks.append(f"expressions={e}")
    tech = getattr(n, "technical", None)
    if tech:
        try:
            chunks.append(f"technical={tech!s}")
        except Exception:
            chunks.append("technical=(unprintable)")
    return " | ".join(chunks)


def _notehead_type_str(n: Any) -> str:
    nh = getattr(n, "notehead", None)
    if nh is None:
        return ""
    return str(nh)


def note_symbolic_audit_surface(n: Any) -> dict[str, Any]:
    """
    Note-local symbolic strings for Gradio inspection (merged into timbral score events).

    Keys are prefixed with ``audit_`` so they sit alongside core event fields without clashes.
    """
    measure, beat = _measure_number_and_beat(n)
    return {
        "audit_measure": measure,
        "audit_beat": beat,
        "audit_articulation_marks": _articulation_names(n),
        "audit_expression_text": _expression_labels(n),
        "audit_direction_text": _text_directions_raw_for_note(n),
        "audit_technical_marks": _technical_notations_raw(n),
        "audit_dynamic_note_surface": _dynamic_for_note(n),
        "audit_notehead_type": _notehead_type_str(n),
    }


def _dynamic_for_note(n: Any) -> str:
    from music21 import dynamics, stream

    found: list[str] = []
    for ex in getattr(n, "expressions", None) or []:
        if isinstance(ex, dynamics.Dynamic):
            v = getattr(ex, "value", None)
            if v is not None and str(v).strip():
                found.append(str(v).strip())
    try:
        meas = n.getContextByClass(stream.Measure)
    except (AttributeError, TypeError, ValueError):
        meas = None
    if meas is not None and isinstance(meas, stream.Measure):
        try:
            n_off = float(n.getOffsetBySite(meas))
        except (AttributeError, TypeError, ValueError):
            n_off = None
        if n_off is not None:
            try:
                for dyn in meas.recurse().getElementsByClass(dynamics.Dynamic):
                    v = getattr(dyn, "value", None)
                    if v is None or not str(v).strip():
                        continue
                    try:
                        eo = float(dyn.getOffsetBySite(meas))
                    except (AttributeError, TypeError, ValueError):
                        continue
                    if eo <= n_off:
                        found.append(str(v).strip())
            except (AttributeError, TypeError, ValueError):
                pass
    if not found:
        return ""
    return ", ".join(found)


def _pitch_name_for_ps(ps: float) -> str:
    from music21 import pitch as m21pitch

    try:
        return m21pitch.Pitch(ps=float(ps)).nameWithOctave
    except (AttributeError, TypeError, ValueError):
        return ""


def _cell_json(v: Any) -> Any:
    if v is None or isinstance(v, bool | int | str):
        return v
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return ""
        return v
    if isinstance(v, dict | list):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def audit_rows_to_csv_string(
    rows: Iterable[dict[str, Any]],
    *,
    fieldnames: Sequence[str] | None = None,
) -> str:
    rows = list(rows)
    fn: list[str] = list(fieldnames) if fieldnames is not None else (list(rows[0].keys()) if rows else [])
    if not fn:
        return ""
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=fn, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell_json(r.get(k)) for k in fn})
    return buf.getvalue()


def _resolve_active_dynamic(carried_dynamic: str, note_surface: str) -> str:
    t = parse_standard_dynamic_mark(str(carried_dynamic or "").strip())
    if t:
        return t
    for piece in str(note_surface or "").replace("|", ",").split(","):
        t2 = parse_standard_dynamic_mark(piece.strip())
        if t2:
            return t2
    return "unknown"


def _technique_state_summary(ts: dict[str, Any], ts_id: str) -> str:
    if ts_id:
        return str(ts_id)
    parts: list[str] = []
    for key in (
        "primary",
        "mute",
        "contact_point",
        "excitation",
        "articulation_effect",
        "resonance",
        "beater",
        "stroke",
    ):
        v = ts.get(key)
        if v is not None and str(v) not in ("", "none", "ordinary", "ordinario", "open"):
            parts.append(f"{key}={v}")
    sp = ts.get("special") or ()
    if isinstance(sp, list | tuple) and sp:
        parts.append("special=" + ",".join(map(str, sp)))
    return "|".join(parts) if parts else "unknown"


def _technique_breakout(ts: dict[str, Any]) -> dict[str, Any]:
    mute = str(ts.get("mute") or "none")
    exc = str(ts.get("excitation") or "")
    cp = str(ts.get("contact_point") or "")
    prim = str(ts.get("primary") or "")
    art_eff = str(ts.get("articulation_effect") or "none")
    spec = ts.get("special") or ()
    spec_l = list(spec) if isinstance(spec, list | tuple) else []
    spec_s = ",".join(str(x) for x in spec_l)
    sul_pont = ""
    if "sul_pont" in cp.lower() or "sul pont" in cp.lower():
        sul_pont = cp
    sul_tasto = ""
    if "sul tasto" in cp.lower() or "sul_tasto" in cp.lower():
        sul_tasto = cp
    technique_harmonic_marker = "none"
    for s in spec_l:
        if str(s).startswith("harmonic:"):
            technique_harmonic_marker = str(s)
    trem = ""
    if art_eff == "tremolo" or exc == "tremolo" or any("tremolo" in str(s).lower() for s in spec_l):
        trem = "yes" if art_eff == "tremolo" else str(art_eff or exc or "yes")
    stopped_open = ""
    if prim in ("stopped", "open", "cuivre", "half_stopped"):
        stopped_open = prim
    vib = "yes" if prim == "vibrato" else ""
    other = ", ".join(x for x in (spec_s, art_eff if art_eff not in ("none", "") else "") if x)
    return {
        "mute_state": mute,
        "sordino_state": mute if mute not in ("none",) else "none",
        "pizz_arco_state": exc or "unknown",
        "sul_ponticello_state": sul_pont or "none",
        "sul_tasto_state": sul_tasto or "none",
        "technique_harmonic_marker": technique_harmonic_marker,
        "tremolo_state": trem or "none",
        "stopped_open_cuivre_state": stopped_open or "none",
        "vibrato_state": vib or "none",
        "other_effects": other or "none",
    }


def _flatten_timbral_events_from_analyzer(analyzer: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ev in analyzer.score_events:
        inst = str(ev.get("instrument") or "unknown")
        fam = str(ev.get("family") or "unknown")
        macro = macrofamily_from_instrumental_subfamily(fam)
        ts_dict = ev.get("technique_state") if isinstance(ev.get("technique_state"), dict) else {}
        ts_id = str(ev.get("technique_state_id") or "")
        tb = _technique_breakout(ts_dict)
        carried = str(ev.get("dynamic_mark") or "")
        note_surf = str(ev.get("audit_dynamic_note_surface") or "")
        dyn_display = carried if carried.strip() else (note_surf if note_surf.strip() else "unknown")
        active_dyn = _resolve_active_dynamic(carried, note_surf)
        hp = str(ev.get("hairpin") or "none")
        cresc = hp == "crescendo"
        dim = hp == "diminuendo"
        part_ix = int(ev.get("part_index", 0))
        part_id = str(ev.get("part_id") or "")
        part_name = str(ev.get("part_name") or "")
        off = float(ev.get("offset", 0.0))
        dur = float(ev.get("duration_ql", 0.0) or 0.0)
        meas = ev.get("audit_measure")
        inst_src = str(ev.get("instrument_source") or "")
        pits: list[float] = [float(x) for x in (ev.get("pitches") or [])]
        written_ps: list[float] = [float(x) for x in (ev.get("written_pitches_ps") or [])]
        pmeta_list: list[dict[str, Any]] = list(ev.get("pitch_tone_metadata") or [])
        is_unp = bool(ev.get("is_unpitched"))
        chord_id = f"ch_{part_ix}_{round(off, 6)}"
        parser_parts: list[str] = []
        if inst_src == "unknown":
            parser_parts.append("unknown_or_ambiguous_instrument_mapping")
        if pits and written_ps and len(pits) != len(written_ps):
            parser_parts.append("written_sounding_pitch_cardinality_mismatch")
        parser_warning = "; ".join(parser_parts)

        hpolicy_ev = str(ev.get("harmonic_pitch_policy") or "").strip()

        tu_k = str(ev.get("technique_uniformity_key") or "").strip()
        if not tu_k:
            tu_k = compute_technique_uniformity_key_from_event(ev)
        exp_te = str(ev.get("explicit_technique") or "none").strip() or "none"
        exp_det = bool(ev.get("explicit_technique_detected", False))

        def _row_common(
            chord_tone_index: int,
            is_chord_tone: bool,
            *,
            _meas: Any = meas,
            _off: float = off,
            _dur: float = dur,
            _part_ix: int = part_ix,
            _part_id: str = part_id,
            _part_name: str = part_name,
            _inst: str = inst,
            _fam: str = fam,
            _macro: str = macro,
            _chord_id: str = chord_id,
            _is_unp: bool = is_unp,
            _dyn_display: str = dyn_display,
            _active_dyn: str = active_dyn,
            _cresc: bool = cresc,
            _dim: bool = dim,
            _exp_te: str = exp_te,
            _exp_det: bool = exp_det,
            _tu_k: str = tu_k,
            _ts_id: str = ts_id,
            _ts_dict: dict[str, Any] = ts_dict,
            _parser_warning: str = parser_warning,
            _tb: dict[str, Any] = tb,
            _ev: dict[str, Any] = ev,
        ) -> dict[str, Any]:
            return {
                "measure": _meas,
                "offset_quarterLength": round(_off, 6),
                "duration_quarterLength": _dur,
                "part_index": _part_ix,
                "part_id": _part_id,
                "part_name": _part_name,
                "raw_part_name": str(_ev.get("raw_part_name") or ""),
                "section_label": str(_ev.get("section_label") or ""),
                "desk_group": str(_ev.get("desk_group") or ""),
                "part_label_original": str(_ev.get("part_label_original") or ""),
                "canonical_instrument": _inst,
                "instrumental_subfamily": _fam,
                "macrofamily": _macro,
                "chord_id": _chord_id,
                "chord_tone_index": chord_tone_index,
                "is_chord_tone": is_chord_tone,
                "is_unpitched": _is_unp,
                "dynamic_mark": _dyn_display,
                "active_dynamic": _active_dyn,
                "crescendo_active": _cresc,
                "diminuendo_active": _dim,
                "explicit_technique": _exp_te,
                "explicit_technique_detected": _exp_det,
                "technique_uniformity_key": _tu_k,
                "technique_state_id": _ts_id,
                "technique_state_summary": _technique_state_summary(_ts_dict, _ts_id),
                "articulation_marks": str(_ev.get("audit_articulation_marks") or ""),
                "technical_marks": str(_ev.get("audit_technical_marks") or ""),
                "expression_text": str(_ev.get("audit_expression_text") or ""),
                "direction_text": str(_ev.get("audit_direction_text") or ""),
                "notehead_type": str(_ev.get("audit_notehead_type") or ""),
                "parser_warning": _parser_warning,
                **_tb,
            }

        if is_unp or not pits:
            rows.append(
                {
                    **_row_common(0, False),
                    "written_pitch": str(ev.get("unpitched_display") or "unpitched"),
                    "written_midi": "unknown",
                    "sounding_pitch": "unknown",
                    "sounding_midi": "unknown",
                    "octave": "unknown",
                    "raw_xml_alter": "",
                    "accidental_text": "",
                    "microtonal_accidental_detected": False,
                    "effective_alter": "",
                    "raw_written_pitch": "",
                    "raw_written_midi": "",
                    "effective_written_midi": "",
                    "effective_sounding_midi": "",
                    "chromatic_transpose_detected": "",
                    "octave_transpose_detected": "",
                    "chromatic_transpose_applied": "",
                    "octave_transpose_applied": "",
                    "total_transpose_applied": "",
                    "transpose_applied": "",
                    "pitch_interpretation_mode": "",
                    "microtonal_accidental_status": "",
                    "explicit_technique": "none",
                    "explicit_technique_detected": False,
                    "technique_uniformity_key": "",
                    **_harmonic_pitch_cells({}, hpolicy_ev),
                }
            )
            continue

        n_tones = len(pits)
        for idx, ps in enumerate(pits):
            wps = written_ps[idx] if idx < len(written_ps) else None
            pm = pmeta_list[idx] if idx < len(pmeta_list) else {}
            eff_w = float(pm["effective_written_midi"]) if pm else (float(wps) if wps is not None else float("nan"))
            eff_s = float(pm["effective_sounding_midi"]) if pm else float(ps)
            written_name = _pitch_name_for_ps(eff_w) if math.isfinite(eff_w) else "unknown"
            sounding_name = _pitch_name_for_ps(eff_s)
            written_midi: Any = round(eff_w, 4) if math.isfinite(eff_w) else "unknown"
            sounding_midi = round(eff_s, 4)
            oct_val: Any = "unknown"
            if math.isfinite(eff_w):
                try:
                    from music21 import pitch as m21pitch

                    _p_w = m21pitch.Pitch(ps=float(eff_w))
                    _oct_w = _p_w.octave
                    oct_val = int(_oct_w) if _oct_w is not None else "unknown"
                except (AttributeError, TypeError, ValueError):
                    oct_val = "unknown"
            rows.append(
                {
                    **_row_common(idx, n_tones > 1),
                    "written_pitch": written_name,
                    "written_midi": written_midi,
                    "sounding_pitch": sounding_name,
                    "sounding_midi": sounding_midi,
                    "octave": oct_val,
                    "raw_xml_alter": pm.get("raw_xml_alter", ""),
                    "accidental_text": str(pm.get("accidental_text") or ""),
                    "microtonal_accidental_detected": bool(pm.get("microtonal_accidental_detected", False)),
                    "effective_alter": pm.get("effective_alter", ""),
                    "raw_written_pitch": str(pm.get("raw_written_pitch") or ""),
                    "raw_written_midi": pm.get("raw_written_midi", ""),
                    "effective_written_midi": round(eff_w, 4) if math.isfinite(eff_w) else "",
                    "effective_sounding_midi": round(eff_s, 4),
                    "chromatic_transpose_detected": pm.get("chromatic_transpose_detected", ""),
                    "octave_transpose_detected": pm.get("octave_transpose_detected", ""),
                    "chromatic_transpose_applied": pm.get("chromatic_transpose_applied", ""),
                    "octave_transpose_applied": pm.get("octave_transpose_applied", ""),
                    "total_transpose_applied": pm.get("total_transpose_applied", ""),
                    "transpose_applied": pm.get("transpose_applied", ""),
                    "pitch_interpretation_mode": str(pm.get("pitch_interpretation_mode") or ""),
                    "microtonal_accidental_status": str(pm.get("microtonal_accidental_status") or ""),
                    **_harmonic_pitch_cells(pm if isinstance(pm, dict) else {}, hpolicy_ev),
                }
            )

    rows.sort(
        key=lambda r: (
            float(r["offset_quarterLength"]),
            int(r["part_index"]),
            int(r["chord_tone_index"]) if isinstance(r["chord_tone_index"], int) else 0,
            str(r.get("sounding_midi")),
        )
    )
    return rows


SCORE_AUDIT_HARMONIC_PITCH_COLUMNS: tuple[str, ...] = (
    "harmonic_state",
    "harmonic_type",
    "harmonic_pitch_role",
    "harmonic_detection_source",
    "harmonic_base_pitch",
    "harmonic_base_midi",
    "harmonic_touching_pitch",
    "harmonic_touching_midi",
    "harmonic_touching_interval_semitones",
    "harmonic_interval_rule_id",
    "harmonic_sounding_pitch",
    "harmonic_sounding_midi",
    "harmonic_sounding_status",
    "harmonic_pitch_policy",
    "harmonic_warning",
)


def _harmonic_pitch_cells(pm: dict[str, Any], fallback_harmonic_pitch_policy: str = "") -> dict[str, Any]:
    out = {k: pm.get(k, "") for k in SCORE_AUDIT_HARMONIC_PITCH_COLUMNS}
    if not str(out.get("harmonic_pitch_policy") or "").strip():
        out["harmonic_pitch_policy"] = str(fallback_harmonic_pitch_policy or "")
    return out


def build_symbolic_inspection_tables(
    score: Any,
    *,
    pitch_interpretation_mode: str | None = None,
    harmonic_pitch_policy: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Single parse: inventory + flattened event audit + vertical sonorities."""
    from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer

    analyzer = TimbralHomogeneityAnalyzer(
        music21_score=score,
        time_step=0.25,
        timbral_model_mode="legacy",
        pitch_interpretation_mode=pitch_interpretation_mode,
        harmonic_pitch_policy=harmonic_pitch_policy,
    )
    events = _flatten_timbral_events_from_analyzer(analyzer)
    inv = _build_instrument_inventory_rows(score, events)
    vert = build_vertical_sonority_audit(events)
    return inv, events, vert


def extract_instrument_inventory(score: Any) -> list[dict[str, Any]]:
    return build_symbolic_inspection_tables(score)[0]


def extract_score_event_audit(score: Any) -> list[dict[str, Any]]:
    return build_symbolic_inspection_tables(score)[1]


def _build_instrument_inventory_rows(score: Any, event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_part: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in event_rows:
        by_part[int(r.get("part_index", 0))].append(r)

    out: list[dict[str, Any]] = []
    for part_index, part in enumerate(score.parts):
        part_id = str(getattr(part, "id", "") or "")
        part_name = str(getattr(part, "partName", "") or "")
        ins0 = _part_default_instrument(part)
        raw_name = _raw_instrument_name_from_m21(ins0)
        instrument_class = _instrument_class_str(ins0)
        raw_for_tax = raw_name or part_name or ""
        canon, subfam, inv_orch = resolve_instrument_taxonomy(str(raw_for_tax) if raw_for_tax else None)
        macro = macrofamily_from_instrumental_subfamily(subfam)
        transposition = _transposition_str(ins0) or ""
        is_perc = is_percussion_family(subfam)
        pmeta = get_percussion_meta(canon) if is_perc else None
        perc_pitch_status = str(pmeta.pitch_status.value) if pmeta is not None else ""
        pitched_events = 0
        unpitched_events = 0
        for er in by_part.get(part_index, []):
            if er.get("is_unpitched") or str(er.get("sounding_midi")) == "unknown":
                unpitched_events += 1
            else:
                pitched_events += 1
        evs = by_part.get(part_index, [])
        n_events = len(evs)
        dyn_marks = {
            str(r.get("active_dynamic")) for r in evs if str(r.get("active_dynamic") or "") not in ("", "unknown")
        }
        tech_marks = {str(r.get("explicit_technique")) for r in evs if bool(r.get("explicit_technique_detected"))}
        art_marks = sum(1 for r in evs if str(r.get("articulation_marks") or "").strip())
        eff_marks = sum(1 for r in evs if str(r.get("other_effects") or "") not in ("", "none"))
        warnings: list[str] = []
        unresolved = ""
        if any(str(r.get("parser_warning")) for r in evs):
            warnings.append("see_event_rows_parser_warning")
        if canon == "unknown" and subfam == FAMILY_OTHER and not raw_for_tax.strip():
            unresolved = "no_instrument_name"
        elif subfam == FAMILY_OTHER and raw_for_tax.strip():
            unresolved = "taxonomy_other_bucket"
        pitched_or_unpitched = "mixed"
        if pitched_events and not unpitched_events:
            pitched_or_unpitched = "pitched"
        elif unpitched_events and not pitched_events:
            pitched_or_unpitched = "unpitched"
        elif not pitched_events and not unpitched_events:
            pitched_or_unpitched = "none"

        out.append(
            {
                "part_index": part_index,
                "part_id": part_id,
                "part_name": part_name,
                "raw_part_name": inv_orch["raw_part_name"],
                "section_label": inv_orch["section_label"],
                "desk_group": inv_orch["desk_group"],
                "part_label_original": inv_orch["part_label_original"],
                "staff_name": part_name,
                "raw_instrument_name": raw_name,
                "music21_instrument_class": instrument_class,
                "canonical_instrument": canon,
                "instrumental_subfamily": subfam,
                "macrofamily": macro,
                "transposition": transposition,
                "sounding_pitch_policy": "concert_via_instrument_transposition",
                "is_percussion": is_perc,
                "percussion_pitch_status": perc_pitch_status,
                "pitched_or_unpitched": pitched_or_unpitched,
                "number_of_events": n_events,
                "number_of_pitched_events": pitched_events,
                "number_of_unpitched_events": unpitched_events,
                "dynamic_marks_found": len(dyn_marks),
                "technique_marks_found": len(tech_marks),
                "articulation_marks_found": art_marks,
                "effect_marks_found": eff_marks,
                "warnings": "; ".join(warnings),
                "unresolved_or_ambiguous_mapping": unresolved,
            }
        )
    return out


_REGISTER_REF_VERTICAL = 7.0


def _format_audit_midi_cell(m: float) -> str:
    """Integer string for 12-TET semitones; fractional when microtonal."""
    ir = round(m)
    if abs(float(m) - float(ir)) < 1e-4:
        return str(ir)
    return str(round(float(m), 4))


def build_vertical_sonority_audit(event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group flattened pitch rows by rounded score offset (quarterLength)."""
    groups: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for r in event_rows:
        key = round(float(r.get("offset_quarterLength", 0.0)), 6)
        groups[key].append(r)

    out: list[dict[str, Any]] = []
    for t_key in sorted(groups.keys()):
        g = groups[t_key]
        pitched = [r for r in g if not r.get("is_unpitched") and str(r.get("sounding_midi")) != "unknown"]
        smidi_vals: list[float] = []
        for r in pitched:
            evs = r.get("effective_sounding_midi")
            if evs is not None and evs != "":
                try:
                    smidi_vals.append(float(evs))
                    continue
                except (TypeError, ValueError):
                    pass
            try:
                smidi_vals.append(float(r["sounding_midi"]))
            except (TypeError, ValueError):
                continue
        measure_nums: list[int | float] = []
        for r in g:
            mnum = r.get("measure")
            if isinstance(mnum, bool):
                continue
            if isinstance(mnum, int | float):
                measure_nums.append(mnum)
        measure_val = min(measure_nums) if measure_nums else None

        names_sorted = sorted({str(r.get("part_name") or "") for r in g if str(r.get("part_name") or "")})
        inst_sorted = sorted({str(r.get("canonical_instrument") or "") for r in g})
        sub_sorted = sorted({str(r.get("instrumental_subfamily") or "") for r in g})
        macro_sorted = sorted({str(r.get("macrofamily") or "") for r in g})
        written_pitches = [str(r.get("written_pitch") or "") for r in g]
        sounding_pitches = [str(r.get("sounding_pitch") or "") for r in g]
        sounding_midi_strs = [str(r.get("sounding_midi")) for r in g]

        n_pitched = len(pitched)
        n_unpitched = len(g) - n_pitched
        vert_card = len({round(x, 4) for x in smidi_vals}) if smidi_vals else 0
        reg_span = float("nan")
        reg_span_prox = float("nan")
        pair_prox = float("nan")
        reg_compact = float("nan")
        if len(smidi_vals) >= 1:
            arr = smidi_vals
            lowest_m = min(arr)
            highest_m = max(arr)
            reg_span = float(highest_m - lowest_m)
            occ = [(float(m), 1.0) for m in smidi_vals]
            reg_bundle = compute_register_compactness_fields(occ, _REGISTER_REF_VERTICAL)
            reg_span_prox = float(reg_bundle.get("register_span_proximity", float("nan")))
            pair_prox = float(reg_bundle.get("pairwise_interval_proximity", float("nan")))
            reg_compact = float(reg_bundle.get("register_compactness", float("nan")))

        dyn_hist: dict[str, int] = defaultdict(int)
        for r in g:
            d = str(r.get("active_dynamic") or "unknown")
            dyn_hist[d] += 1
        dom_dyn = max(dyn_hist.items(), key=lambda kv: kv[1])[0] if dyn_hist else "unknown"

        def _row_uniformity_key(r: dict[str, Any]) -> str:
            tu = str(r.get("technique_uniformity_key") or "").strip()
            if tu:
                return tu
            return compute_technique_uniformity_key_from_event(
                {
                    "technique_uniformity_key": "",
                    "technique_state": r.get("technique_state"),
                    "technique_state_id": str(r.get("technique_state_id") or ""),
                    "instrument": str(r.get("canonical_instrument") or ""),
                    "family": str(r.get("instrumental_subfamily") or ""),
                }
            )

        tech_states = sorted({_row_uniformity_key(r) for r in g if _row_uniformity_key(r)})
        any_det_g = any(bool(r.get("explicit_technique_detected")) for r in g)
        if not any_det_g:
            vert_tech_cov = "ordinary_default_uniform"
        elif len(tech_states) <= 1:
            vert_tech_cov = "explicit_uniform"
        else:
            vert_tech_cov = "explicit_mixed"
        arts = ", ".join(
            sorted({str(r.get("articulation_marks") or "") for r in g if str(r.get("articulation_marks") or "")})
        )
        effects = ", ".join(
            sorted(
                {str(r.get("other_effects") or "") for r in g if str(r.get("other_effects") or "") not in ("", "none")}
            )
        )
        warn_g = "; ".join(
            sorted({str(r.get("parser_warning") or "") for r in g if str(r.get("parser_warning") or "")})
        )
        harm_bits: list[str] = []
        harm_unres = 0
        for r in g:
            st = str(r.get("harmonic_sounding_status") or "").strip()
            if st == "unresolved":
                harm_unres += 1
            hs = str(r.get("harmonic_state") or "").strip()
            if hs and hs != "none":
                harm_bits.append(f"{hs}:{st or 'n/a'}")
        for r in g:
            hw = str(r.get("harmonic_warning") or "").strip()
            if hw:
                harm_bits.append(f"warn:{hw[:80]}")
        harmonic_summary = "; ".join(sorted(set(harm_bits)))[:800]

        rounded = [round(x, 4) for x in smidi_vals]
        dup = len(rounded) - len(set(rounded)) if rounded else 0
        midi_sorted = sorted(smidi_vals)
        midi_set_sorted = sorted(set(rounded))

        out.append(
            {
                "measure": measure_val,
                "offset_quarterLength": t_key,
                "active_part_names": ", ".join(names_sorted),
                "active_canonical_instruments": ", ".join(inst_sorted),
                "active_instrumental_subfamilies": ", ".join(sub_sorted),
                "active_macrofamilies": ", ".join(macro_sorted),
                "written_pitches": ", ".join(written_pitches),
                "sounding_pitches": ", ".join(sounding_pitches),
                "sounding_midi_values": ", ".join(_format_audit_midi_cell(x) for x in smidi_vals)
                if smidi_vals
                else ", ".join(sounding_midi_strs),
                "number_of_active_events": len(g),
                "number_of_active_pitched_events": n_pitched,
                "number_of_active_unpitched_events": n_unpitched,
                "vertical_pitch_cardinality": vert_card,
                "register_span_semitones": reg_span,
                "register_span_proximity": reg_span_prox,
                "pairwise_interval_proximity": pair_prox,
                "register_compactness": reg_compact,
                "active_dynamic_distribution": json.dumps(dict(dyn_hist), ensure_ascii=False),
                "dominant_dynamic": dom_dyn,
                "active_technique_states": ", ".join(tech_states),
                "technique_coverage_status": vert_tech_cov,
                "articulation_summary": arts,
                "effect_summary": effects,
                "warnings": warn_g,
                "harmonic_summary": harmonic_summary,
                "harmonic_unresolved_count": harm_unres,
                "n_unique_sounding_midis": len(midi_set_sorted),
                "midi_multiset": ", ".join(_format_audit_midi_cell(m) for m in midi_sorted),
                "midi_set": ", ".join(_format_audit_midi_cell(m) for m in midi_set_sorted),
                "duplicate_pitch_count": dup,
            }
        )
    return out


# Stable column order for CSV exports and empty Gradio tables.
SCORE_AUDIT_INVENTORY_COLUMNS: tuple[str, ...] = (
    "part_index",
    "part_id",
    "part_name",
    "raw_part_name",
    "section_label",
    "desk_group",
    "part_label_original",
    "staff_name",
    "raw_instrument_name",
    "music21_instrument_class",
    "canonical_instrument",
    "instrumental_subfamily",
    "macrofamily",
    "transposition",
    "sounding_pitch_policy",
    "is_percussion",
    "percussion_pitch_status",
    "pitched_or_unpitched",
    "number_of_events",
    "number_of_pitched_events",
    "number_of_unpitched_events",
    "dynamic_marks_found",
    "technique_marks_found",
    "articulation_marks_found",
    "effect_marks_found",
    "warnings",
    "unresolved_or_ambiguous_mapping",
)
SCORE_AUDIT_EVENT_COLUMNS: tuple[str, ...] = (
    "measure",
    "offset_quarterLength",
    "duration_quarterLength",
    "part_index",
    "part_id",
    "part_name",
    "raw_part_name",
    "section_label",
    "desk_group",
    "part_label_original",
    "canonical_instrument",
    "instrumental_subfamily",
    "macrofamily",
    "written_pitch",
    "written_midi",
    "sounding_pitch",
    "sounding_midi",
    "octave",
    "raw_xml_alter",
    "accidental_text",
    "microtonal_accidental_detected",
    "effective_alter",
    "raw_written_pitch",
    "raw_written_midi",
    "effective_written_midi",
    "effective_sounding_midi",
    "chromatic_transpose_detected",
    "octave_transpose_detected",
    "chromatic_transpose_applied",
    "octave_transpose_applied",
    "total_transpose_applied",
    "transpose_applied",
    "pitch_interpretation_mode",
    "microtonal_accidental_status",
    "chord_id",
    "chord_tone_index",
    "is_chord_tone",
    "is_unpitched",
    "dynamic_mark",
    "active_dynamic",
    "crescendo_active",
    "diminuendo_active",
    "explicit_technique",
    "explicit_technique_detected",
    "technique_uniformity_key",
    "technique_state_id",
    "technique_state_summary",
    "articulation_marks",
    "technical_marks",
    "expression_text",
    "direction_text",
    "notehead_type",
    *SCORE_AUDIT_HARMONIC_PITCH_COLUMNS,
    "mute_state",
    "sordino_state",
    "pizz_arco_state",
    "sul_ponticello_state",
    "sul_tasto_state",
    "technique_harmonic_marker",
    "tremolo_state",
    "stopped_open_cuivre_state",
    "vibrato_state",
    "other_effects",
    "parser_warning",
)
SCORE_AUDIT_VERTICAL_COLUMNS: tuple[str, ...] = (
    "measure",
    "offset_quarterLength",
    "active_part_names",
    "active_canonical_instruments",
    "active_instrumental_subfamilies",
    "active_macrofamilies",
    "written_pitches",
    "sounding_pitches",
    "sounding_midi_values",
    "number_of_active_events",
    "number_of_active_pitched_events",
    "number_of_active_unpitched_events",
    "vertical_pitch_cardinality",
    "register_span_semitones",
    "register_span_proximity",
    "pairwise_interval_proximity",
    "register_compactness",
    "active_dynamic_distribution",
    "dominant_dynamic",
    "active_technique_states",
    "technique_coverage_status",
    "articulation_summary",
    "effect_summary",
    "warnings",
    "harmonic_summary",
    "harmonic_unresolved_count",
    "n_unique_sounding_midis",
    "midi_multiset",
    "midi_set",
    "duplicate_pitch_count",
)
