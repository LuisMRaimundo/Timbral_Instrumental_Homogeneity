"""
Persistent **timbral technique state** for H_timbral (symbolic MusicXML / music21 only).

Tracks directions **in chronological order** (via ``iter_timbral_elements`` + ``TechniqueStateContext``)
until cancelled (pizz./arco, sul pont./ord., bouché/open, con sord./senza sord., cuivré, etc.),
then merges note-local articulations. Same-measure text is **not** merged onto earlier notes
when using ``notation_text_context_for_note(..., measure_text="none")`` in timbral; family
keyword helpers default to ``measure_text="prior"`` (strictly earlier offsets in the measure).

This module does **not** interpret PDF or bitmap graphics; only semantic objects and text
that music21 exposes after MusicXML import.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_OBOES,
    FAMILY_PERCUSSION,
    FAMILY_SAXOPHONES,
    FAMILY_STRINGS,
)

# Tokens from ``music21.dynamics.Dynamic`` / MusicXML ``<dynamics>`` (longest-first match).
_STANDARD_DYNAMIC_MARKS: tuple[str, ...] = (
    "pppp",
    "ppp",
    "pp",
    "mpp",
    "mp",
    "mf",
    "mfp",
    "nf",
    "f",
    "ff",
    "fff",
    "ffff",
    "fp",
    "sf",
    "sfp",
    "sfz",
    "sffz",
    "fz",
    "rf",
    "sp",
    "sfzp",
    "n",
    "p",
)


def parse_standard_dynamic_mark(blob: str) -> str | None:
    """
    If ``blob`` is (after normalisation) a single standard dynamic token, return that token.

    This is **notation-symbolic** (score marking), not measured SPL. Returns ``None`` for non-dynamic text.
    """
    b = normalize_technique_text(blob or "")
    if not b:
        return None
    for tok in _STANDARD_DYNAMIC_MARKS:
        if b == tok:
            return tok
    return None


def normalize_technique_text(s: str) -> str:
    """Lowercase, strip accents, collapse space, normalise apostrophes / hyphens / periods."""
    if not s:
        return ""
    t = unicodedata.normalize("NFD", s)
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.lower()
    t = re.sub(r"['\u2019]", "'", t)
    t = t.replace("-", " ")
    t = re.sub(r"\.(?=\s|$)|(?<=\s)\.", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


@dataclass(frozen=True)
class TechniqueState:
    family: str
    instrument: str
    primary: str = "ordinary"
    mute: str = "none"
    contact_point: str = "ordinary"
    excitation: str = "ordinary"
    articulation_effect: str = "none"
    resonance: str = "ordinary"
    noise_component: str = "ordinary"
    pressure: str = "ordinary"
    beater: str = "ordinary"
    stroke: str = "ordinary"
    special: tuple[str, ...] = ()


def technique_state_to_dict(st: TechniqueState) -> dict[str, Any]:
    """JSON-serialisable dict for exports / audit."""
    return {
        "family": st.family,
        "instrument": st.instrument,
        "primary": st.primary,
        "mute": st.mute,
        "contact_point": st.contact_point,
        "excitation": st.excitation,
        "articulation_effect": st.articulation_effect,
        "resonance": st.resonance,
        "noise_component": st.noise_component,
        "pressure": st.pressure,
        "beater": st.beater,
        "stroke": st.stroke,
        "special": list(st.special),
    }


def technique_state_from_dict(d: dict[str, Any]) -> TechniqueState:
    sp = d.get("special") or ()
    if isinstance(sp, list):
        sp = tuple(sp)
    return TechniqueState(
        family=str(d["family"]),
        instrument=str(d["instrument"]),
        primary=str(d.get("primary", "ordinary")),
        mute=str(d.get("mute", "none")),
        contact_point=str(d.get("contact_point", "ordinary")),
        excitation=str(d.get("excitation", "ordinary")),
        articulation_effect=str(d.get("articulation_effect", "none")),
        resonance=str(d.get("resonance", "ordinary")),
        noise_component=str(d.get("noise_component", "ordinary")),
        pressure=str(d.get("pressure", "ordinary")),
        beater=str(d.get("beater", "ordinary")),
        stroke=str(d.get("stroke", "ordinary")),
        special=tuple(sp),
    )


def _is_bowed_string(inst: str) -> bool:
    return inst in frozenset({"violin", "viola", "cello", "double bass"})


def technique_state_id(instrument: str, family: str, state: TechniqueState) -> str:
    """
    Stable coarse id for overlap-weighted distributions, e.g. ``horn|open``, ``horn|stopped``,
    ``violin|arco|sul_pont``, ``trumpet|harmon_mute|stem_out``, ``suspended cymbal|let_ring``.
    """
    parts: list[str] = [instrument]
    if family == FAMILY_BRASS:
        prim = state.primary
        if prim not in ("open", "ordinary", ""):
            parts.append(prim)
        if state.mute != "none":
            m = state.mute
            if m == "harmon_stem_in":
                parts.extend(["harmon_mute", "stem_in"])
            elif m == "harmon_stem_out":
                parts.extend(["harmon_mute", "stem_out"])
            else:
                parts.append(m)
        if prim in ("open", "ordinary", "") and len(parts) == 1:
            parts.append("open")
        if state.articulation_effect != "none":
            parts.append(state.articulation_effect)
        parts.extend(state.special)
        return "|".join(parts)

    if family == FAMILY_STRINGS and _is_bowed_string(instrument):
        parts.append(state.excitation if state.excitation not in ("ordinary", "") else "arco")
        if state.mute != "none":
            parts.append(state.mute)
        if state.contact_point not in ("ordinary", ""):
            parts.append(state.contact_point)
        if state.articulation_effect == "tremolo" or state.excitation == "tremolo":
            parts.append("tremolo")
        hd = harmonic_dim(state)
        if hd != "none":
            parts.append(hd)
        pd = pressure_dim(state)
        if pd != "ordinary":
            parts.append(pd)
        parts.extend(state.special)
        return "|".join(parts)

    # Winds / percussion / other
    if family == FAMILY_PERCUSSION:
        if state.resonance not in ("ordinary", "open", ""):
            parts.append(state.resonance)
        if state.beater not in ("ordinary", ""):
            parts.append(state.beater)
        if state.stroke not in ("ordinary", ""):
            parts.append(state.stroke)
        if state.articulation_effect != "none":
            parts.append(state.articulation_effect)
        parts.extend(state.special)
        return "|".join(parts)

    lane = state.primary if state.primary not in ("ordinary", "") else state.excitation
    if lane not in ("ordinary", "ordinario", ""):
        parts.append(lane)
    if state.articulation_effect != "none":
        parts.append(state.articulation_effect)
    parts.extend(state.special)
    return "|".join(parts)


# Instrument-free bucket for H_TI ``technique_uniformity`` when nothing is explicitly marked.
ORDINARY_DEFAULT_UNIFORMITY_KEY = "ordinary_default"

# Normalise technique tails for uniformity keys / audit (instrument-free).
_UNIFORMITY_TAIL_ALIASES: dict[str, str] = {
    "sul_pont": "sul_ponticello",
    "molto_sul_pont": "sul_ponticello",
    "sul_tasto": "sul_tasto",
    "molto_sul_tasto": "sul_tasto",
    "pizz": "pizzicato",
    "snap_pizz": "pizzicato",
}


def technique_state_default_like(state: TechniqueState) -> bool:
    """True when merged technique is generic / unmarked (no explicit special technique)."""
    pr = str(state.primary or "")
    if pr not in ("ordinary", "open", "", "ordinario", "unknown"):
        return False
    if str(state.mute or "none") not in ("none",):
        return False
    if str(state.contact_point or "ordinary") not in ("ordinary", ""):
        return False
    if str(state.excitation or "ordinary") not in ("ordinary", "arco", ""):
        return False
    if str(state.articulation_effect or "none") not in ("none",):
        return False
    sp = state.special
    return not (isinstance(sp, list | tuple) and len(sp) > 0)


def has_special_explicit_technique(instrument: str, family: str, state: TechniqueState) -> bool:
    """
    True only for **contrasting** playing techniques (how they play), not default
    brass **open**, **arco**, **ordinario**, etc., so ``technique_uniformity`` does not
    duplicate instrument identity.
    """
    inst = str(instrument or "").strip()
    fam = str(family or "")
    if fam == FAMILY_BRASS:
        pr = str(state.primary or "")
        if pr in ("stopped", "cuivre", "half_stopped"):
            return True
        if state.mute != "none":
            return True
        if str(state.articulation_effect or "none") not in ("none",):
            return True
        sp = state.special
        return bool(isinstance(sp, list | tuple) and len(sp) > 0)
    if fam == FAMILY_STRINGS and _is_bowed_string(inst):
        if not technique_state_default_like(state):
            return True
        ex = str(state.excitation or "")
        if ex in ("pizz", "snap_pizz", "col_legno", "tremolo"):
            return True
        cp = str(state.contact_point or "")
        if cp not in ("ordinary", ""):
            return True
        if harmonic_dim(state) != "none":
            return True
        return str(state.articulation_effect or "none") == "tremolo"
    if fam in (FAMILY_FLUTES, FAMILY_CLARINETS, FAMILY_OBOES, FAMILY_BASSOONS, FAMILY_SAXOPHONES):
        pr = str(state.primary or "")
        if pr not in ("ordinary", "ordinario", "open", "", "unknown", "naturale", "normal"):
            return True
        if str(state.articulation_effect or "none") not in ("none",):
            return True
        sp = state.special
        return bool(isinstance(sp, list | tuple) and len(sp) > 0)
    if fam == FAMILY_PERCUSSION:
        if str(state.resonance or "ordinary") not in ("ordinary", "open", ""):
            return True
        if str(state.beater or "ordinary") not in ("ordinary", ""):
            return True
        if str(state.stroke or "ordinary") not in ("ordinary", ""):
            return True
        if str(state.articulation_effect or "none") not in ("none",):
            return True
        sp = state.special
        return bool(isinstance(sp, list | tuple) and len(sp) > 0)
    return bool(not technique_state_default_like(state))


# Backwards-compatible name for callers outside this module.
has_explicit_notated_technique = has_special_explicit_technique


def technique_tail_from_fingerprint(full_id: str) -> str:
    """Drop leading ``instrument`` segment from a composite ``technique_state_id``."""
    parts = [p.strip() for p in (full_id or "").split("|") if p.strip()]
    if len(parts) <= 1:
        return ""
    return "|".join(parts[1:])


def _canonical_uniformity_slug(tail_underscore: str) -> str:
    """Map internal tail tokens to stable user-facing uniformity labels."""
    if not tail_underscore:
        return ORDINARY_DEFAULT_UNIFORMITY_KEY
    parts = [p for p in tail_underscore.split("_") if p]
    out: list[str] = []
    for p in parts:
        out.append(_UNIFORMITY_TAIL_ALIASES.get(p, p))
    joined = "_".join(out)
    if joined in ("con_sord", "con_sordino"):
        return "con_sordino"
    if joined in ("senza_sord", "senza_sordino"):
        return "senza_sordino"
    return joined


def compute_technique_uniformity_key(instrument: str, family: str, state: TechniqueState) -> str:
    """Stable instrument-free key used for ``technique_uniformity`` / audit (never prefixes instrument)."""
    inst = str(instrument or "").strip()
    fam = str(family or "")
    full = technique_state_id(inst, fam, state)
    if not has_special_explicit_technique(inst, fam, state):
        return ORDINARY_DEFAULT_UNIFORMITY_KEY
    tail = technique_tail_from_fingerprint(full)
    if not tail:
        return ORDINARY_DEFAULT_UNIFORMITY_KEY
    raw = tail.replace("|", "_")
    return _canonical_uniformity_slug(raw)


def explicit_technique_audit_label(instrument: str, family: str, state: TechniqueState) -> str:
    """Human-facing explicit technique token, or ``none`` when only defaults apply."""
    inst = str(instrument or "").strip()
    fam = str(family or "")
    if not has_special_explicit_technique(inst, fam, state):
        return "none"
    return compute_technique_uniformity_key(inst, fam, state)


def explicit_technique_detected(instrument: str, family: str, state: TechniqueState) -> bool:
    return bool(has_special_explicit_technique(instrument, family, state))


def compute_technique_uniformity_key_from_event(ev: dict[str, Any]) -> str:
    """Resolve uniformity key from a timbral event dict (prefers precomputed fields)."""
    z = str(ev.get("technique_uniformity_key") or "").strip()
    if z:
        return z
    inst = str(ev.get("instrument") or ev.get("canonical_instrument") or "unknown")
    fam = str(ev.get("family") or ev.get("instrumental_subfamily") or "unknown")
    raw = ev.get("technique_state")
    if isinstance(raw, dict) and raw:
        try:
            st = technique_state_from_dict(raw)
            return compute_technique_uniformity_key(inst, fam, st)
        except (KeyError, TypeError, ValueError):
            pass
    tid = str(ev.get("technique_state_id") or "").strip()
    if not tid:
        return ""
    if "|" in tid:
        parts = [p.strip() for p in tid.split("|") if p.strip()]
        tail = "|".join(parts[1:]) if len(parts) > 1 else ""
        if tail in ("arco", "open"):
            return ORDINARY_DEFAULT_UNIFORMITY_KEY
        return _canonical_uniformity_slug(tail.replace("|", "_")) if tail else ORDINARY_DEFAULT_UNIFORMITY_KEY
    # Single-segment fingerprint (e.g. ``clarinet`` with no technique tail) must not
    # become a false technique key duplicating the instrument name.
    return ORDINARY_DEFAULT_UNIFORMITY_KEY


def event_has_special_explicit_technique(ev: dict[str, Any]) -> bool:
    raw = ev.get("technique_state")
    inst = str(ev.get("instrument") or ev.get("canonical_instrument") or "unknown")
    fam = str(ev.get("family") or ev.get("instrumental_subfamily") or "unknown")
    if isinstance(raw, dict) and raw:
        try:
            st = technique_state_from_dict(raw)
            return has_special_explicit_technique(inst, fam, st)
        except (KeyError, TypeError, ValueError):
            pass
    tid = str(ev.get("technique_state_id") or "").strip()
    if "|" in tid:
        parts = [p.strip() for p in tid.split("|") if p.strip()]
        tail = "|".join(parts[1:]) if len(parts) > 1 else ""
        if tail == "arco":
            return False
        if tail == "open":
            return False
        return bool(tail)
    return False


def event_has_explicit_notated_technique(ev: dict[str, Any]) -> bool:
    """Backwards-compatible alias for H_TI window logic."""
    return event_has_special_explicit_technique(ev)


def event_explicit_technique_detected(ev: dict[str, Any]) -> bool:
    return event_has_special_explicit_technique(ev)


def harmonic_dim(state: TechniqueState) -> str:
    for s in state.special:
        if s.startswith("harmonic:"):
            return s.split(":", 1)[-1]
    return "none"


def pressure_dim(state: TechniqueState) -> str:
    p = getattr(state, "pressure", "ordinary") or "ordinary"
    if p not in ("ordinary", ""):
        return p
    for s in state.special:
        if s.startswith("pressure:"):
            return s.split(":", 1)[-1]
    return "ordinary"


@dataclass
class TechniqueStateContext:
    """Mutable per-part playing state while scanning a part in chronological order."""

    family: str
    instrument: str
    brass_primary: str = "open"
    brass_mute: str = "none"
    brass_articulation: str = "none"
    str_excitation: str = "arco"
    str_contact: str = "ordinary"
    str_mute: str = "none"
    str_harmonic: str = "none"
    str_pressure: str = "ordinary"
    str_tremolo: bool = False
    wind_lane: str = "ordinario"
    perc_beater: str = "ordinary"
    perc_resonance: str = "open"
    perc_stroke: str = "ordinary"
    # Notated dynamics / hairpins (symbolic; not SPL). Persist across technique text within a part.
    dynamic_mark: str = ""
    hairpin: str = "none"  # none | crescendo | diminuendo

    def to_state(self) -> TechniqueState:
        inst = self.instrument
        fam = self.family
        spec: list[str] = []
        if self.str_harmonic != "none":
            spec.append(f"harmonic:{self.str_harmonic}")
        if fam == FAMILY_BRASS:
            prim = self.brass_primary
            mute = self.brass_mute
            art = self.brass_articulation
            return TechniqueState(
                family=fam,
                instrument=inst,
                primary=prim,
                mute=mute,
                contact_point="ordinary",
                excitation="ordinary",
                articulation_effect=art,
                resonance="ordinary",
                noise_component="ordinary",
                pressure="ordinary",
                beater="ordinary",
                stroke="ordinary",
                special=tuple(spec),
            )

        if fam == FAMILY_STRINGS and _is_bowed_string(inst):
            exc = self.str_excitation
            art = "tremolo" if self.str_tremolo else "none"
            return TechniqueState(
                family=fam,
                instrument=inst,
                primary="ordinary",
                mute=self.str_mute,
                contact_point=self.str_contact,
                excitation=exc,
                articulation_effect=art,
                resonance="ordinary",
                noise_component="ordinary",
                pressure=self.str_pressure,
                beater="ordinary",
                stroke="ordinary",
                special=tuple(spec),
            )

        if fam == FAMILY_PERCUSSION:
            return TechniqueState(
                family=fam,
                instrument=inst,
                primary="ordinary",
                mute="none",
                contact_point="ordinary",
                excitation="ordinary",
                articulation_effect="none",
                resonance=self.perc_resonance,
                noise_component="ordinary",
                pressure="ordinary",
                beater=self.perc_beater,
                stroke=self.perc_stroke,
                special=tuple(spec),
            )

        return TechniqueState(
            family=fam,
            instrument=inst,
            primary=self.wind_lane,
            mute="none",
            contact_point="ordinary",
            excitation="ordinary",
            articulation_effect="none",
            resonance="ordinary",
            noise_component="ordinary",
            pressure="ordinary",
            beater="ordinary",
            stroke="ordinary",
            special=tuple(spec),
        )


def _apply_brass_direction(blob: str, ctx: TechniqueStateContext) -> None:
    b = normalize_technique_text(blob)
    if not b:
        return
    if re.search(
        r"\bsenza\s+sord\b|\bsenza\s+sord\.\b|\bsenza\s+sordino\b|\bsenza\s+sordina\b"
        r"|\bwithout\s+mute\b|\bmute\s+off\b",
        b,
    ):
        ctx.brass_mute = "none"
        return
    if re.search(r"cuivres\s+bouch|sons\s+bouch|sons\s+bouchés|sons\s+bouches", b):
        ctx.brass_primary = "stopped"
        return
    if re.search(
        r"\bcuivr(e|é)s?\b|très\s+cuivr|tres\s+cuivr|\bbrassy\b|\bbrassily\b|\bmetallic\b"
        r"|\bmetallico\b|\bmétal\b|\bschmetternd\b|bells?\s+up|bell\s+up|pavillons?\s+en\s+l\s*air"
        r"|pavillon\s+en\s+l\s*air|pavillons?\s+en\s+haut|campana\s+in\s+aria",
        b,
    ):
        ctx.brass_primary = "cuivre"
        return
    if re.fullmatch(r"\s*\+\s*", b):
        ctx.brass_primary = "stopped"
        return
    if re.search(
        r"\bstopped\b|\bstopped\s+horn\b|\bstop\b|hand[\s-]stopped|hand\s+stopped\s+horn"
        r"|\bclosed\s+horn\b|\bclosed\b"
        r"|\bbouch(é|e|és|ees)\b|\bbouche\b|\bsons?\s+bouch(é|e)s?\b|\bcuivres\s+bouch(é|e)s?\b"
        r"|\bgestopft\b|\bgestopf\b|\bgest\.\b|\bchius[oaie]\b|\btappat[oaie]\b|\btappe\b",
        b,
    ):
        ctx.brass_primary = "stopped"
        return
    if re.search(
        r"\bhalf\s+stopped\b|\bhalf\s+muted\b|half\s+mute|half\s+closed|half\s+bouch",
        b,
    ):
        ctx.brass_primary = "half_stopped"
        return
    if re.search(
        r"\bopen\b|\bopen\s+horn\b|\bopen\s+circle\b|\bouvert\b|\baperto\b|\boffen\b"
        r"|\bsenza\s+mano\b|\bnon\s+bouch(é|e)\b|\bord\b|\bord\.\b|\bordinario\b|\bnormale\b"
        r"|\bnatural\b",
        b,
    ):
        ctx.brass_primary = "open"
        return
    if re.search(r"flutter|frullato|flz\.?|flatter|flatterzunge", b):
        ctx.brass_articulation = "flutter"
        return
    if re.search(
        r"\bgrowl\b|\bshake\b|lip\s+trill|half\s+valve|valve\s+tremolo|\bglissando\b|\bgliss\b"
        r"|\bfall\b|\bdoit\b|\brip\b|\bsmear\b|breath\s+attack|air\s+tone",
        b,
    ):
        if "growl" in b:
            ctx.brass_articulation = "growl"
        elif re.search(r"\bshake\b", b):
            ctx.brass_articulation = "shake"
        elif "lip trill" in b:
            ctx.brass_articulation = "lip_trill"
        elif "half valve" in b:
            ctx.brass_articulation = "half_valve"
        elif "valve tremolo" in b:
            ctx.brass_articulation = "valve_tremolo"
        elif "gliss" in b:
            ctx.brass_articulation = "glissando"
        elif re.search(r"\bfall\b", b):
            ctx.brass_articulation = "fall"
        elif "doit" in b:
            ctx.brass_articulation = "doit"
        elif re.search(r"\brip\b", b):
            ctx.brass_articulation = "rip"
        elif "smear" in b:
            ctx.brass_articulation = "smear"
        elif "breath attack" in b:
            ctx.brass_articulation = "breath_attack"
        else:
            ctx.brass_articulation = "air_tone"
        return
    if re.search(r"straight\s+mute|\bst\.?\s*mute\b|\bsourdine\s+s(e|è)che\b|\bsourdine\s+droite\b", b):
        ctx.brass_mute = "straight_mute"
        ctx.brass_primary = "open"
        return
    if re.search(r"\bcup\s+mute\b|\bcup\b(?!\s+tone)", b) or re.search(r"sourdine\s+bol|sourdine\s+cup", b):
        ctx.brass_mute = "cup_mute"
        ctx.brass_primary = "open"
        return
    if re.search(r"harmon|wa[\s-]*wa[\s-]*mute|wah[\s-]*wah[\s-]*mute", b):
        ctx.brass_mute = "harmon_mute"
        if re.search(r"stem\s*in|stem\s+in", b):
            ctx.brass_mute = "harmon_stem_in"
        elif re.search(r"stem\s*out|stem\s+out", b):
            ctx.brass_mute = "harmon_stem_out"
        ctx.brass_primary = "open"
        return
    if "practice" in b and "mute" in b:
        ctx.brass_mute = "practice_mute"
        ctx.brass_primary = "open"
        return
    if re.search(
        r"\bcon\s+sord\b|\bcon\s+sord\.\b|\bcon\s+sordino\b|\bcon\s+sordina\b|\bsordino\b|\bsordina\b"
        r"|\bsord\.\b|\bmuted\b|\bmute\b|\bmit\s+d(a|ä)mpfer\b|\bavec\s+sourdine\b|\bsourdine\b",
        b,
    ):
        ctx.brass_mute = "muted_generic"
        return
    if "bucket" in b:
        ctx.brass_mute = "bucket_mute"
        ctx.brass_primary = "open"
        return
    if re.search(r"plunger|derby|\bhat\b", b) or re.search(r"\bwah\b(?!\s*tone)", b):
        ctx.brass_mute = "plunger"
        ctx.brass_primary = "open"
        return


def _apply_string_direction(blob: str, ctx: TechniqueStateContext) -> None:
    b = normalize_technique_text(blob)
    if not b:
        return
    if re.search(
        r"\bsenza\s+sord\b|\bsenza\s+sord\.\b|\bsenza\s+sordino\b|\bwithout\s+mute\b|\bmute\s+off\b"
        r"|\bsans\s+sourdine\b|\bohne\s+d(a|ä)mpfer\b",
        b,
    ):
        ctx.str_mute = "none"
        return
    if re.search(
        r"\bcon\s+sord\b|\bcon\s+sord\.\b|\bcon\s+sordino\b|\bsordino\b|\bavec\s+sourdine\b|\bsourdine\b"
        r"|\bmit\s+d(a|ä)mpfer\b|\bmuted\b|\bmute\b",
        b,
    ):
        ctx.str_mute = "muted"
        return
    if re.search(
        r"\bsnap\s+pizz|snap\s+pizzicato|bart(ó|o)k\s+pizz|pizz\s*bart|à\s+la\s+bart|a\s+la\s+bart",
        b,
    ):
        ctx.str_excitation = "snap_pizz"
        return
    if re.search(r"\bpizz(icato)?\b|\bpizz\.\b", b):
        ctx.str_excitation = "pizz"
        return
    if re.search(r"\barco\b|\bmodo\s+ordinario\b|\bnat\.\b", b):
        ctx.str_excitation = "arco"
        ctx.str_tremolo = False
        return
    if re.search(r"molto\s+sul\s+pont|molto\s+sul\s+ponticello|m\.s\.p\.|extreme\s+sul\s+pont", b):
        ctx.str_contact = "molto_sul_pont"
        return
    if re.search(
        r"sul\s+pont|sul\s+ponticello|s\.p\.|s\.pont|\bs\s*pont\b|ponticello|au\s+chevalet|pr(è|e)s\s+du\s+chevalet"
        r"|near\s+bridge|at\s+bridge|sul\s+ponte",
        b,
    ):
        ctx.str_contact = "sul_pont"
        return
    # Before generic ``flautando`` / sul tasto: ``molto flautando`` is pressure/colour, not contact point.
    if re.search(r"molto\s+flautando", b):
        ctx.str_pressure = "molto_flautando"
        return
    if re.search(r"molto\s+sul\s+tasto|flautando|sulla\s+tastiera|sur\s+la\s+touche|over\s+fingerboard", b):
        ctx.str_contact = "molto_sul_tasto"
        return
    if re.search(r"sul\s+tasto|s\.t\.|on\s+fingerboard", b):
        ctx.str_contact = "sul_tasto"
        return
    if re.search(
        r"\bcol\s+legno\s+battuto|\blegno\s+battuto\b|\bcol\s+legno\s+tratto|\blegno\s+tratto\b",
        b,
    ):
        if "tratto" in b or re.search(r"col\s+legno\s+tratto|legno\s+tratto", b):
            ctx.str_excitation = "col_legno_tratto"
        else:
            ctx.str_excitation = "col_legno_battuto"
        return
    if re.search(r"\bcol\s+legno\b", b):
        ctx.str_excitation = "col_legno_battuto"
        return
    if re.search(r"\btremolo\b|\btrem\.\b|^\s*trem\s*$", b):
        ctx.str_tremolo = True
        return
    if re.search(
        r"\bharmonic\b|\bharmonics\b|\bharm\b|\bflageolet\b|\barmonici\b|\barmonico\b|sons\s+harmoniques"
        r"|natural\s+harmonic|artificial\s+harmonic",
        b,
    ):
        if "artificial" in b:
            ctx.str_harmonic = "artificial_harmonic"
        elif "natural" in b:
            ctx.str_harmonic = "natural_harmonic"
        else:
            ctx.str_harmonic = "harmonic_generic"
        return
    if re.search(r"overpressure|scratch\s+tone", b):
        ctx.str_pressure = "overpressure" if "overpressure" in b else "scratch_tone"
        return
    if re.search(r"\bsul\s+g\b|\bsul\s+d\b|\bsul\s+a\b|\bsul\s+e\b", b):
        ctx.str_excitation = b.replace(" ", "_").replace(".", "")
        return
    if re.search(r"behind\s+bridge|on\s+bridge|sub\s+ponticello", b):
        ctx.str_contact = "behind_bridge" if "behind" in b else "on_bridge" if "on bridge" in b else "sub_ponticello"
        return
    if re.search(
        r"\bord\.|\bord\b|\bordinario\b|\bnormale\b|\bnat\.\b|\bnatural\b(?!\s+harmonic)|modo\s+ordinario",
        b,
    ):
        ctx.str_contact = "ordinary"
        ctx.str_pressure = "ordinary"
        ctx.str_tremolo = False
        ctx.str_excitation = "arco"
        ctx.str_harmonic = "none"
        return


def _apply_wind_direction(blob: str, ctx: TechniqueStateContext) -> None:
    b = normalize_technique_text(blob)
    if not b:
        return
    if re.fullmatch(r"a\s*2", b) or b == "a2":
        return
    if re.search(r"bisbigliando|timbral\s+trill|colour\s+trill|color\s+trill", b):
        ctx.wind_lane = "bisbigliando"
        return
    if re.search(r"tongue\s+ram", b):
        ctx.wind_lane = "tongue_ram"
        return
    if re.search(r"jet\s*whistle", b):
        ctx.wind_lane = "jet_whistle"
        return
    if re.search(r"whistle\s*tone|whistle\s+tones|^\s*whistle\s*$", b):
        ctx.wind_lane = "whistle_tone"
        return
    if re.search(
        r"\bharmonic\b|\bharmonics\b|\bharm\b|\bflageolet\b|natural\s+harmonic|artificial\s+harmonic",
        b,
    ):
        ctx.wind_lane = "harmonic"
        return
    if re.search(r"flutter\s+tongue|flutter|flz\.?|flatterzunge|flatter|frullato|tremolo\s+tongue", b):
        ctx.wind_lane = "flutter"
        return
    if re.search(r"slap\s*tong|slap[\s-]tongue|schlagzunge|slap\s*tonguing", b):
        ctx.wind_lane = "slap"
        return
    if re.search(r"\bslap\b", b):
        ctx.wind_lane = "slap"
        return
    if re.search(r"key\s*click|key\s*clicks|key\s*slap|cliquetis|\bcles\b", b):
        ctx.wind_lane = "key_click"
        return
    if re.search(r"multiphonic|multiphonics|multi\s+phonic|split\s+tone|double\s+tone", b):
        ctx.wind_lane = "multiphonic"
        return
    if re.fullmatch(r"air", b) or re.search(
        r"\bair\s+sound\b|\baeolian\s+sound\b|\baeolian\b|souffl|breath\s+tone|breathy|airy",
        b,
    ):
        ctx.wind_lane = "air_sound"
        return
    if re.search(
        r"growl|subtone|overblown|sing(ing)?\s+and\s+play|singing\s+while\s+playing|voice\s+and\s+instrument",
        b,
    ):
        ctx.wind_lane = "growl" if "growl" in b else "subtone" if "subtone" in b else "singing_and_playing"
        return
    if re.search(r"senza\s+vibrato|non\s+vibrato|senza\s+vib|non\s+vib|ohne\s+vibr", b):
        ctx.wind_lane = "ordinario"
        return
    if re.search(r"\bvibrato\b", b):
        ctx.wind_lane = "vibrato"
        return
    if re.search(
        r"\bordinary\b|\bordinario\b|\bord\.|\bord\b|\bnormale\b|\bnatural\b(?!\s+harmonic)|modo\s+ordinario",
        b,
    ):
        ctx.wind_lane = "ordinario"
        return


def _apply_percussion_direction(blob: str, ctx: TechniqueStateContext) -> None:
    b = normalize_technique_text(blob)
    if not b:
        return
    if re.search(r"hard\s+mallet", b):
        ctx.perc_beater = "hard_mallet"
        return
    if re.search(r"yarn\s+mallet", b):
        ctx.perc_beater = "yarn_mallet"
        return
    if re.search(r"felt\s+mallet", b):
        ctx.perc_beater = "felt_mallet"
        return
    if re.search(r"soft\s+mallet", b):
        ctx.perc_beater = "soft_mallet"
        return
    if re.search(r"rubber\s+mallet", b):
        ctx.perc_beater = "rubber_mallet"
        return
    if re.search(r"wood\s+stick", b):
        ctx.perc_beater = "wood_stick"
        return
    if re.search(r"metal\s+stick", b):
        ctx.perc_beater = "metal_stick"
        return
    if re.search(r"wire\s+brushes|\bbrushes\b", b):
        ctx.perc_beater = "brushes"
        return
    if re.search(r"\bhands\b", b):
        ctx.perc_beater = "hands"
        return
    if re.search(r"\bfingers\b", b):
        ctx.perc_beater = "fingers"
        return
    if re.search(r"superball", b):
        ctx.perc_beater = "superball"
        return
    if re.search(r"\bbow(ed)?\b|\barco\b", b):
        ctx.perc_beater = "bow"
        ctx.perc_stroke = "bowed"
        return
    if re.search(r"let\s+ring|laissez\s+vibrer|\bl\.v\.\b", b):
        ctx.perc_resonance = "let_ring"
        return
    if re.search(r"\bopen\b", b) and not re.search(r"open\s+roll", b):
        ctx.perc_resonance = "open"
        return
    if re.search(r"\bchoke\b", b) and not re.search(r"\bdamp|etouff|secco", b):
        ctx.perc_resonance = "choke"
        return
    if re.search(r"\bdamp|etouff|secco", b):
        ctx.perc_resonance = "damped"
        return
    if re.search(r"\broll\b|\btremolo\b", b):
        ctx.perc_stroke = "roll"
        return
    if re.search(r"rimshot", b):
        ctx.perc_stroke = "rimshot"
        return
    if re.search(r"\brim\b", b):
        ctx.perc_stroke = "rim"
        return
    if re.search(r"edge|center|centre", b):
        ctx.perc_stroke = "edge" if "edge" in b else "center"
        return
    if re.search(r"scrape", b):
        ctx.perc_stroke = "scrape"
        return


def apply_persistent_text(blob: str, ctx: TechniqueStateContext) -> None:
    """Update mutable context from a free-text direction (already from TextExpression etc.)."""
    dm = parse_standard_dynamic_mark(blob)
    if dm is not None:
        ctx.dynamic_mark = dm
    fam = ctx.family
    if fam == FAMILY_BRASS:
        _apply_brass_direction(blob, ctx)
    elif fam == FAMILY_STRINGS and _is_bowed_string(ctx.instrument):
        _apply_string_direction(blob, ctx)
    elif fam in (FAMILY_FLUTES, FAMILY_CLARINETS, FAMILY_OBOES, FAMILY_BASSOONS, FAMILY_SAXOPHONES):
        _apply_wind_direction(blob, ctx)
    elif fam == FAMILY_PERCUSSION:
        _apply_percussion_direction(blob, ctx)


def direction_element_text(el: Any) -> str:
    from music21 import dynamics, expressions

    parts: list[str] = []
    if isinstance(el, expressions.TextExpression | expressions.RehearsalMark):
        c = getattr(el, "content", None)
        if c:
            parts.append(str(c))
    elif isinstance(el, dynamics.Dynamic):
        v = getattr(el, "value", None)
        if v is not None:
            parts.append(str(v))
    return " ".join(parts)


def _timbral_direction_sort_priority(el: Any) -> int:
    """Lower sorts earlier at the same offset: ``Dynamic`` before hairpins before free text."""
    from music21 import dynamics, expressions

    if isinstance(el, dynamics.Dynamic):
        return 0
    if isinstance(el, dynamics.Crescendo | dynamics.Diminuendo):
        return 1
    if isinstance(el, expressions.TextExpression | expressions.RehearsalMark):
        return 2
    return 3


def iter_timbral_elements(part: Any) -> Iterable[tuple[float, int, str, Any]]:
    """
    Yield (global_offset, sort_priority, kind, element) in score order.

    kind is ``direction`` (TextExpression, RehearsalMark, Dynamic) or ``note`` (Note, Chord).
    Directions at the same offset sort before notes so they apply to following simultaneous notes.
    """
    from music21 import chord, dynamics, expressions
    from music21 import note as m21note

    items: list[tuple[float, int, str, Any]] = []
    for el in part.flatten():
        try:
            o = float(el.offset)
        except (TypeError, ValueError, AttributeError):
            continue
        if isinstance(el, m21note.Note | m21note.Unpitched | chord.Chord):
            items.append((o, 10, "note", el))
        elif isinstance(el, dynamics.Crescendo | dynamics.Diminuendo):
            items.append((o, _timbral_direction_sort_priority(el), "direction", el))
        elif isinstance(el, expressions.TextExpression | expressions.RehearsalMark | dynamics.Dynamic):
            txt = direction_element_text(el)
            if txt.strip():
                items.append((o, _timbral_direction_sort_priority(el), "direction", el))
    items.sort(key=lambda t: (t[0], t[1], id(t[3])))
    yield from items


def merge_note_technique_state(
    ctx: TechniqueStateContext,
    n: Any,
    *,
    instrument: str,
    family: str,
) -> TechniqueState:
    """
    Merge note-local articulations / expressions into ``ctx`` (mutated in place).

    Callers should pass a **copy** of the timeline context plus any note-only text already
    applied via :func:`apply_persistent_text`.
    """
    ctx.family = family
    ctx.instrument = instrument

    from music21 import articulations, expressions

    if family == FAMILY_BRASS:
        for a in getattr(n, "articulations", None) or []:
            if isinstance(a, articulations.Stopped):
                ctx.brass_primary = "stopped"
        for ex in getattr(n, "expressions", None) or []:
            if isinstance(ex, expressions.Tremolo):
                ctx.brass_articulation = "flutter"

    if family == FAMILY_STRINGS and _is_bowed_string(instrument):
        for a in getattr(n, "articulations", None) or []:
            if isinstance(
                a,
                articulations.Pizzicato
                | articulations.NailPizzicato
                | articulations.SnapPizzicato
                | articulations.FrettedPluck,
            ):
                ctx.str_excitation = "snap_pizz" if isinstance(a, articulations.SnapPizzicato) else "pizz"
            if isinstance(a, articulations.StringHarmonic | articulations.Harmonic):
                ctx.str_harmonic = "natural_harmonic"
            if isinstance(a, articulations.Stopped):
                ctx.str_mute = "muted"
        for ex in getattr(n, "expressions", None) or []:
            if isinstance(ex, expressions.Tremolo):
                ctx.str_tremolo = True
        nh = getattr(getattr(n, "notehead", None), "name", None) or getattr(n, "notehead", None)
        if nh in ("diamond", "Diamond") and ctx.str_harmonic == "none":
            ctx.str_harmonic = "harmonic_generic"

    if family in (FAMILY_FLUTES, FAMILY_CLARINETS, FAMILY_OBOES, FAMILY_BASSOONS, FAMILY_SAXOPHONES):
        for a in getattr(n, "articulations", None) or []:
            if isinstance(a, articulations.Harmonic):
                ctx.wind_lane = "harmonic"

    return ctx.to_state()


def technique_state_similarity(a: TechniqueState, b: TechniqueState) -> float:
    """Heuristic 0..1 similarity between two states (same family assumed for tuning)."""
    if a.family != b.family:
        return 0.55
    if a.family == FAMILY_STRINGS and _is_bowed_string(a.instrument) and _is_bowed_string(b.instrument):
        return _string_state_similarity(a, b)
    if a.family == FAMILY_BRASS:
        return _brass_state_similarity(a, b)
    if a.family in (FAMILY_FLUTES, FAMILY_CLARINETS, FAMILY_OBOES, FAMILY_BASSOONS, FAMILY_SAXOPHONES):
        return 0.85 if a.primary == b.primary else 0.35 if {a.primary, b.primary} <= {"ordinario", "unknown"} else 0.45
    if a.family == FAMILY_PERCUSSION:
        same = (
            a.resonance == b.resonance
            and a.beater == b.beater
            and a.stroke == b.stroke
            and a.articulation_effect == b.articulation_effect
        )
        return 0.7 if same else 0.4
    return 0.75 if a.primary == b.primary else 0.5


def timbral_event_technique_pair_similarity(
    ei: dict[str, Any],
    ej: dict[str, Any],
    *,
    matrix_similarity: Callable[[str, str], float],
    technique_key: str = "technique",
) -> float:
    """
    Pairwise technique factor for H_timbral: prefer full :class:`TechniqueState` similarity
    when both events carry ``technique_state`` dicts; otherwise fall back to the discrete
    matrix similarity on string ``technique`` labels.
    """
    raw_i = ei.get("technique_state")
    raw_j = ej.get("technique_state")
    if isinstance(raw_i, dict) and isinstance(raw_j, dict):
        try:
            st_i = technique_state_from_dict(raw_i)
            st_j = technique_state_from_dict(raw_j)
            return float(technique_state_similarity(st_i, st_j))
        except (KeyError, TypeError, ValueError):
            pass
    return float(matrix_similarity(str(ei.get(technique_key, "")), str(ej.get(technique_key, ""))))


def _string_state_similarity(a: TechniqueState, b: TechniqueState) -> float:
    def sim(x: str, y: str, same: float = 1.0, diff: float = 0.12) -> float:
        if x == y:
            return same
        if x in ("ordinary", "arco", "none", "") or y in ("ordinary", "arco", "none", ""):
            return 0.55
        return diff

    ea, eb = a.excitation, b.excitation
    if ea == eb:
        s_e = 1.0
    elif {ea, eb} == {"pizz", "arco"} or ("pizz" in {ea, eb} and "arco" in {ea, eb}):
        s_e = 0.12
    else:
        s_e = 0.55
    s_c = (
        1.0
        if a.contact_point == b.contact_point
        else (
            0.35
            if {a.contact_point, b.contact_point} <= {"sul_pont", "sul_tasto", "molto_sul_pont", "molto_sul_tasto"}
            else 0.72
        )
    )
    s_m = sim(a.mute, b.mute, 1.0, 0.25)
    h1, h2 = harmonic_dim(a), harmonic_dim(b)
    s_h = 1.0 if h1 == h2 else 0.5
    p1, p2 = pressure_dim(a), pressure_dim(b)
    s_p = 1.0 if p1 == p2 else 0.65
    trem_a = a.articulation_effect == "tremolo" or a.excitation == "tremolo"
    trem_b = b.articulation_effect == "tremolo" or b.excitation == "tremolo"
    s_t = 1.0 if trem_a == trem_b else 0.82
    return float(max(0.0, min(1.0, s_e * s_c * s_m * s_h * s_p * s_t)))


def _brass_state_similarity(a: TechniqueState, b: TechniqueState) -> float:
    from homogeneity_analyser.analyzers.brass_pairwise_timbral import brass_technique_similarity
    from homogeneity_analyser.analyzers.brass_technique import brass_matrix_key_from_technique_state

    ka = brass_matrix_key_from_technique_state(a)
    kb = brass_matrix_key_from_technique_state(b)
    base = brass_technique_similarity(ka, kb)
    if a.articulation_effect == b.articulation_effect:
        flutter_adj = 1.0
    elif a.articulation_effect == "flutter" or b.articulation_effect == "flutter":
        flutter_adj = 0.88
    else:
        flutter_adj = 1.0
    return float(max(0.0, min(1.0, base * flutter_adj)))


def timbral_state_concentration_from_distribution(dist: dict[str, float]) -> float:
    """Herfindahl-style concentration: sum p^2 in [0,1]; 1.0 = single state."""
    tot = sum(dist.values())
    if tot <= 1e-12:
        return 1.0
    s = sum((v / tot) ** 2 for v in dist.values())
    return float(max(0.0, min(1.0, s)))


def dominant_timbral_state(dist: dict[str, float]) -> str | None:
    if not dist:
        return None
    tot = sum(dist.values())
    if tot <= 1e-12:
        return None
    return max(dist.items(), key=lambda kv: kv[1])[0]


def legacy_string_technique_from_state(st: TechniqueState) -> str:
    """Map multi-state strings to the coarse labels used by legacy docs / matrices."""
    from homogeneity_analyser.analyzers.string_technique import (
        TECH_ARCO,
        TECH_HARMONIC,
        TECH_MUTED,
        TECH_PIZZ,
        TECH_SUL_PONT,
        TECH_SUL_TASTO,
        TECH_TREMOLO,
        TECH_UNKNOWN,
    )

    if st.excitation in ("pizz", "snap_pizz"):
        return TECH_PIZZ
    if st.articulation_effect == "tremolo" or st.excitation == "tremolo":
        return TECH_TREMOLO
    if st.contact_point in ("sul_pont", "molto_sul_pont"):
        return TECH_SUL_PONT
    if st.contact_point in ("sul_tasto", "molto_sul_tasto", "flautando"):
        return TECH_SUL_TASTO
    if harmonic_dim(st) != "none":
        return TECH_HARMONIC
    if st.mute == "muted":
        return TECH_MUTED
    if st.excitation == "arco":
        return TECH_ARCO
    return TECH_UNKNOWN
