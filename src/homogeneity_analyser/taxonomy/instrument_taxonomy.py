"""
Instrument taxonomy for **part-name / orchestration** homogeneity (not acoustic timbre).

Maps score part or instrument names (MusicXML, music21) to a canonical instrument id and
a coarse family. Used so H_timbral can reward same-instrument and same-family layouts.

**Source of truth:** ``_CANONICAL_INSTRUMENTS`` maps each canonical instrument to ``family`` and
``aliases``. ``_INSTRUMENT_MAP`` is derived at import (flattened aliases) for collision checks and
legacy introspection.

**Ambiguous conventions (orchestral defaults, not universal):**
- Bare ``bass`` → double bass (string section). Use ``bass voice`` for vocal bass.
- Bare ``alto`` / ``tenor`` / ``baritone`` → voice roles, not sax/flute/baritone horn without extra words.
- ``cb`` / ``cb.`` → double bass in this project (string context); ``cbcl`` is contrabass clarinet.
- ``cornetto`` is treated as modern brass cornet (common PT/IT naming). Historical ``cornett`` stays separate.
- Short abbreviations (e.g. ``fl``, ``cl``, ``bd``) only match in **score-like** short phrases (see
  ``_SHORT_ALIAS_MAX_TOKENS`` and token boundaries) so prose such as "random text with cl inside" does not match.
"""

import re
import unicodedata
from typing import Any, Final, TypedDict

# Family identifiers (same family = higher homogeneity than cross-family)
FAMILY_STRINGS = "strings"
FAMILY_FLUTES = "flutes"
FAMILY_RECORDERS = "recorders"
FAMILY_OBOES = "oboes"
FAMILY_CLARINETS = "clarinets"
FAMILY_BASSOONS = "bassoons"
FAMILY_SAXOPHONES = "saxophones"
FAMILY_BRASS = "brass"
FAMILY_KEYBOARD = "keyboard"
FAMILY_PERCUSSION = "percussion"
FAMILY_VOICE = "voice"
FAMILY_OTHER = "other"


class _CanonInstrMeta(TypedDict):
    family: str
    aliases: tuple[str, ...]


_CANONICAL_INSTRUMENTS: dict[str, _CanonInstrMeta] = {
    "cello": {"family": FAMILY_STRINGS, "aliases": ("violoncello", "violoncelo", "violoncélo", "cello", "vc.", "vlc.")},
    "double bass": {
        "family": FAMILY_STRINGS,
        "aliases": ("double bass", "contrabass", "cb.", "cb", "db.", "contrabaixo", "bass"),
    },
    "guitar": {
        "family": FAMILY_STRINGS,
        "aliases": ("acoustic guitar", "electric guitar", "classical guitar", "guitar", "guitarra"),
    },
    "bass guitar": {"family": FAMILY_STRINGS, "aliases": ("bass guitar",)},
    "violin": {
        "family": FAMILY_STRINGS,
        "aliases": (
            "violin",
            "vln.",
            "vn.",
            "vl.",
            "violino",
            "violino i",
            "violino ii",
            "first violins",
            "second violins",
        ),
    },
    "viola": {"family": FAMILY_STRINGS, "aliases": ("viola", "vla.", "va.", "viola de arco")},
    "harp": {"family": FAMILY_STRINGS, "aliases": ("harp", "hp.", "harpa")},
    "lute": {"family": FAMILY_STRINGS, "aliases": ("lute",)},
    "theorbo": {"family": FAMILY_STRINGS, "aliases": ("theorbo",)},
    "mandolin": {"family": FAMILY_STRINGS, "aliases": ("mandolin",)},
    "mandola": {"family": FAMILY_STRINGS, "aliases": ("mandola",)},
    "banjo": {"family": FAMILY_STRINGS, "aliases": ("banjo",)},
    "ukulele": {"family": FAMILY_STRINGS, "aliases": ("ukulele",)},
    "zither": {"family": FAMILY_STRINGS, "aliases": ("zither",)},
    "dulcimer": {"family": FAMILY_STRINGS, "aliases": ("dulcimer",)},
    "viola da gamba": {"family": FAMILY_STRINGS, "aliases": ("viola da gamba",)},
    "viol": {"family": FAMILY_STRINGS, "aliases": ("viol",)},
    "baryton": {"family": FAMILY_STRINGS, "aliases": ("baryton",)},
    "cittern": {"family": FAMILY_STRINGS, "aliases": ("cittern",)},
    "vihuela": {"family": FAMILY_STRINGS, "aliases": ("vihuela",)},
    "sitar": {"family": FAMILY_STRINGS, "aliases": ("sitar",)},
    "koto": {"family": FAMILY_STRINGS, "aliases": ("koto",)},
    "shamisen": {"family": FAMILY_STRINGS, "aliases": ("shamisen",)},
    "erhu": {"family": FAMILY_STRINGS, "aliases": ("erhu",)},
    "guzheng": {"family": FAMILY_STRINGS, "aliases": ("guzheng",)},
    "pipa": {"family": FAMILY_STRINGS, "aliases": ("pipa",)},
    "alto flute": {"family": FAMILY_FLUTES, "aliases": ("alto flute", "flauta alto", "flauta em sol")},
    "bass flute": {"family": FAMILY_FLUTES, "aliases": ("bass flute", "flauta baixo")},
    "flute": {"family": FAMILY_FLUTES, "aliases": ("flute", "traverso", "fl.", "fl", "flauta", "flauta transversal")},
    "piccolo": {"family": FAMILY_FLUTES, "aliases": ("piccolo", "picc.", "picc", "flautim", "ottavino")},
    "fife": {"family": FAMILY_FLUTES, "aliases": ("fife",)},
    "pan flute": {"family": FAMILY_FLUTES, "aliases": ("pan flute", "pan pipes")},
    "shakuhachi": {"family": FAMILY_FLUTES, "aliases": ("shakuhachi",)},
    "dizi": {"family": FAMILY_FLUTES, "aliases": ("dizi",)},
    "bansuri": {"family": FAMILY_FLUTES, "aliases": ("bansuri",)},
    "tin whistle": {"family": FAMILY_FLUTES, "aliases": ("tin whistle",)},
    "ocarina": {"family": FAMILY_FLUTES, "aliases": ("ocarina",)},
    "sopranino recorder": {"family": FAMILY_RECORDERS, "aliases": ("sopranino recorder",)},
    "soprano recorder": {"family": FAMILY_RECORDERS, "aliases": ("soprano recorder",)},
    "alto recorder": {"family": FAMILY_RECORDERS, "aliases": ("alto recorder",)},
    "tenor recorder": {"family": FAMILY_RECORDERS, "aliases": ("tenor recorder",)},
    "bass recorder": {"family": FAMILY_RECORDERS, "aliases": ("bass recorder",)},
    "recorder": {"family": FAMILY_RECORDERS, "aliases": ("recorder", "blockflöte", "block flute")},
    "oboe d'amore": {
        "family": FAMILY_OBOES,
        "aliases": ("oboe d'amore", "oboé d'amore", "oboe de amor", "oboe d amore", "oboe damore"),
    },
    "oboe da caccia": {"family": FAMILY_OBOES, "aliases": ("oboe da caccia",)},
    "cor anglais": {
        "family": FAMILY_OBOES,
        "aliases": ("cor anglais", "english horn", "cor inglês", "cor ingles", "corno inglese"),
    },
    "heckelphone": {"family": FAMILY_OBOES, "aliases": ("heckelphone", "heckelfone")},
    "bass oboe": {"family": FAMILY_OBOES, "aliases": ("bass oboe",)},
    "oboe": {"family": FAMILY_OBOES, "aliases": ("oboe", "ob.", "ob", "oboé")},
    "musette": {"family": FAMILY_OBOES, "aliases": ("musette",)},
    "shawm": {"family": FAMILY_OBOES, "aliases": ("shawm",)},
    "duduk": {"family": FAMILY_OBOES, "aliases": ("duduk",)},
    "suona": {"family": FAMILY_OBOES, "aliases": ("suona",)},
    "contrabass clarinet": {
        "family": FAMILY_CLARINETS,
        "aliases": ("contrabass clarinet", "cbcl", "clarinete contrabaixo"),
    },
    "bass clarinet": {"family": FAMILY_CLARINETS, "aliases": ("bass clarinet", "bass cl.", "bcl", "clarinete baixo")},
    "alto clarinet": {"family": FAMILY_CLARINETS, "aliases": ("alto clarinet",)},
    "e flat clarinet": {
        "family": FAMILY_CLARINETS,
        "aliases": (
            "clarinet in e flat",
            "clarinet in eb",
            "e flat clarinet",
            "eb clarinet",
            "cl in eb",
            "clarinete em mi bemol",
            "requinta",
        ),
    },
    "b flat clarinet": {
        "family": FAMILY_CLARINETS,
        "aliases": (
            "clarinet in b flat",
            "clarinet in bb",
            "b flat clarinet",
            "bb clarinet",
            "cl in bb",
            "clarinete em si bemol",
            "clarinete em sib",
        ),
    },
    "a clarinet": {
        "family": FAMILY_CLARINETS,
        "aliases": ("clarinet in a", "a clarinet", "cl in a", "clarinete em lá", "clarinete em la"),
    },
    "c clarinet": {"family": FAMILY_CLARINETS, "aliases": ("clarinet in c", "c clarinet")},
    "clarinet": {"family": FAMILY_CLARINETS, "aliases": ("soprano clarinet", "clarinet", "clarinete", "cl.", "cl")},
    "basset clarinet": {"family": FAMILY_CLARINETS, "aliases": ("basset clarinet",)},
    "basset horn": {"family": FAMILY_CLARINETS, "aliases": ("basset horn",)},
    "contrabassoon": {
        "family": FAMILY_BASSOONS,
        "aliases": (
            "contrabassoon",
            "contrabassoon in f",
            "cfg.",
            "cbn",
            "contrafagote",
            "contra fagote",
            "contra fagotto",
            "contrafagotto",
        ),
    },
    "bassoon": {
        "family": FAMILY_BASSOONS,
        "aliases": ("bassoon", "fagott", "bn.", "bsn.", "fg.", "fg", "fag.", "fagote"),
    },
    "dulcian": {"family": FAMILY_BASSOONS, "aliases": ("dulcian", "dulciana")},
    "racket": {"family": FAMILY_BASSOONS, "aliases": ("racket",)},
    "crumhorn": {"family": FAMILY_BASSOONS, "aliases": ("crumhorn",)},
    "sopranino saxophone": {"family": FAMILY_SAXOPHONES, "aliases": ("sopranino saxophone",)},
    "soprano saxophone": {"family": FAMILY_SAXOPHONES, "aliases": ("soprano saxophone",)},
    "alto saxophone": {"family": FAMILY_SAXOPHONES, "aliases": ("alto saxophone", "alto sax", "saxofone alto")},
    "tenor saxophone": {"family": FAMILY_SAXOPHONES, "aliases": ("tenor saxophone", "tenor sax", "saxofone tenor")},
    "baritone saxophone": {
        "family": FAMILY_SAXOPHONES,
        "aliases": ("baritone saxophone", "baritone sax", "saxofone baritono"),
    },
    "bass saxophone": {"family": FAMILY_SAXOPHONES, "aliases": ("bass saxophone",)},
    "saxophone": {"family": FAMILY_SAXOPHONES, "aliases": ("saxophone", "sax")},
    "contrabass trombone": {"family": FAMILY_BRASS, "aliases": ("contrabass trombone", "trombone contrabaixo")},
    "bass trombone": {"family": FAMILY_BRASS, "aliases": ("bass trombone", "trombone baixo")},
    "alto trombone": {"family": FAMILY_BRASS, "aliases": ("alto trombone", "trombone alto")},
    "trombone": {
        "family": FAMILY_BRASS,
        "aliases": ("tenor trombone", "soprano trombone", "sackbut", "trombone", "trb.", "tbn."),
    },
    "tuba": {"family": FAMILY_BRASS, "aliases": ("bass tuba", "tuba", "tba.")},
    "euphonium": {
        "family": FAMILY_BRASS,
        "aliases": ("baritone horn", "euphonium", "eufónio", "eufonio", "bombardino"),
    },
    "horn": {"family": FAMILY_BRASS, "aliases": ("french horn", "horn", "hn.", "hn", "trompa", "trompa em fa")},
    "wagner tuba": {"family": FAMILY_BRASS, "aliases": ("wagner tuba", "tuba wagneriana")},
    "natural horn": {
        "family": FAMILY_BRASS,
        "aliases": ("cor de chasse", "hunting horn", "natural horn", "trompa natural"),
    },
    "trumpet": {
        "family": FAMILY_BRASS,
        "aliases": ("natural trumpet", "trumpet", "tpt.", "trp.", "tr.", "tr", "trompete", "trompete em do"),
    },
    "bass trumpet": {"family": FAMILY_BRASS, "aliases": ("bass trumpet", "trompete baixo")},
    "serpent": {"family": FAMILY_BRASS, "aliases": ("serpent",)},
    "cornett": {"family": FAMILY_BRASS, "aliases": ("cornett",)},
    "mellophone": {"family": FAMILY_BRASS, "aliases": ("mellophone",)},
    "sousaphone": {"family": FAMILY_BRASS, "aliases": ("sousaphone",)},
    "cornet": {"family": FAMILY_BRASS, "aliases": ("cornet", "cornetto", "corneta", "cornetim")},
    "flugelhorn": {"family": FAMILY_BRASS, "aliases": ("flugelhorn", "fliscorne")},
    "cimbasso": {"family": FAMILY_BRASS, "aliases": ("cimbasso",)},
    "ophicleide": {"family": FAMILY_BRASS, "aliases": ("ophicleide",)},
    "bugle": {"family": FAMILY_BRASS, "aliases": ("bugle",)},
    "alphorn": {"family": FAMILY_BRASS, "aliases": ("alphorn",)},
    "didgeridoo": {"family": FAMILY_BRASS, "aliases": ("didgeridoo",)},
    "piano": {
        "family": FAMILY_KEYBOARD,
        "aliases": ("grand piano", "upright piano", "electric piano", "piano", "pf.", "pno."),
    },
    "fortepiano": {"family": FAMILY_KEYBOARD, "aliases": ("fortepiano",)},
    "organ": {"family": FAMILY_KEYBOARD, "aliases": ("organ", "pipe organ", "org.", "órgão", "orgao")},
    "harpsichord": {"family": FAMILY_KEYBOARD, "aliases": ("harpsichord", "cravo")},
    "clavichord": {"family": FAMILY_KEYBOARD, "aliases": ("clavichord",)},
    "celesta": {"family": FAMILY_KEYBOARD, "aliases": ("celesta", "celeste", "cel.")},
    "accordion": {"family": FAMILY_KEYBOARD, "aliases": ("accordion", "acordeão")},
    "harmonium": {"family": FAMILY_KEYBOARD, "aliases": ("harmonium",)},
    "bandoneon": {"family": FAMILY_KEYBOARD, "aliases": ("bandoneon",)},
    "concertina": {"family": FAMILY_KEYBOARD, "aliases": ("concertina",)},
    "harmonica": {"family": FAMILY_KEYBOARD, "aliases": ("harmonica",)},
    "synthesizer": {"family": FAMILY_KEYBOARD, "aliases": ("synthesizer", "synth", "sintetizador", "synth.")},
    "clavinet": {"family": FAMILY_KEYBOARD, "aliases": ("clavinet",)},
    "virginal": {"family": FAMILY_KEYBOARD, "aliases": ("virginal",)},
    "spinet": {"family": FAMILY_KEYBOARD, "aliases": ("spinet",)},
    "tubular bells": {"family": FAMILY_PERCUSSION, "aliases": ("tubular bells", "chimes")},
    "steelpan": {"family": FAMILY_PERCUSSION, "aliases": ("steelpan", "steel drum")},
    "glockenspiel": {"family": FAMILY_PERCUSSION, "aliases": ("glockenspiel", "orchestral bells", "glock.")},
    "vibraphone": {"family": FAMILY_PERCUSSION, "aliases": ("vibraphone", "vibes", "vib.", "vibrafone")},
    "xylophone": {"family": FAMILY_PERCUSSION, "aliases": ("xylophone", "xyl.", "xilofone")},
    "marimba": {"family": FAMILY_PERCUSSION, "aliases": ("marimba",)},
    "crotales": {"family": FAMILY_PERCUSSION, "aliases": ("crotales",)},
    "timpani": {"family": FAMILY_PERCUSSION, "aliases": ("timpani", "kettledrum", "timp.", "tímpanos", "timpanos")},
    "snare drum": {"family": FAMILY_PERCUSSION, "aliases": ("snare drum", "sd", "caixa clara", "tarola")},
    "bass drum": {"family": FAMILY_PERCUSSION, "aliases": ("bass drum", "bd", "bombo")},
    "tom-tom": {"family": FAMILY_PERCUSSION, "aliases": ("tom-tom", "tom tom")},
    "tambourine": {"family": FAMILY_PERCUSSION, "aliases": ("tambourine",)},
    "triangle": {"family": FAMILY_PERCUSSION, "aliases": ("triangle", "tgl", "triângulo")},
    "cymbal": {"family": FAMILY_PERCUSSION, "aliases": ("cymbal", "cymbals", "pratos")},
    "gong": {"family": FAMILY_PERCUSSION, "aliases": ("gong",)},
    "tam-tam": {"family": FAMILY_PERCUSSION, "aliases": ("tam-tam", "tamtam")},
    "castanets": {"family": FAMILY_PERCUSSION, "aliases": ("castanets",)},
    "claves": {"family": FAMILY_PERCUSSION, "aliases": ("claves",)},
    "cowbell": {"family": FAMILY_PERCUSSION, "aliases": ("cowbell",)},
    "wood block": {"family": FAMILY_PERCUSSION, "aliases": ("wood block",)},
    "temple block": {"family": FAMILY_PERCUSSION, "aliases": ("temple block",)},
    "bongos": {"family": FAMILY_PERCUSSION, "aliases": ("bongos", "bongo")},
    "congas": {"family": FAMILY_PERCUSSION, "aliases": ("congas", "conga")},
    "djembe": {"family": FAMILY_PERCUSSION, "aliases": ("djembe",)},
    "tabla": {"family": FAMILY_PERCUSSION, "aliases": ("tabla",)},
    "cajón": {"family": FAMILY_PERCUSSION, "aliases": ("cajón", "cajon")},
    "rototom": {"family": FAMILY_PERCUSSION, "aliases": ("rototom",)},
    "wind chimes": {"family": FAMILY_PERCUSSION, "aliases": ("wind chimes",)},
    "percussion": {
        "family": FAMILY_PERCUSSION,
        "aliases": ("percussion", "drums", "drum set", "drum kit", "perc.", "percussão", "percussao"),
    },
    "suspended cymbal": {"family": FAMILY_PERCUSSION, "aliases": ("suspended cymbal", "prato suspenso")},
    "piccolo trumpet": {"family": FAMILY_BRASS, "aliases": ("piccolo trumpet", "trompete piccolo")},
    "mezzo-soprano": {"family": FAMILY_VOICE, "aliases": ("mezzo-soprano", "mezzo soprano")},
    "countertenor": {"family": FAMILY_VOICE, "aliases": ("countertenor",)},
    "contralto": {"family": FAMILY_VOICE, "aliases": ("contralto",)},
    "bass": {"family": FAMILY_VOICE, "aliases": ("bass voice",)},
    "soprano": {"family": FAMILY_VOICE, "aliases": ("soprano",)},
    "alto": {"family": FAMILY_VOICE, "aliases": ("alto",)},
    "tenor": {"family": FAMILY_VOICE, "aliases": ("tenor",)},
    "baritone": {"family": FAMILY_VOICE, "aliases": ("baritone",)},
    "voice": {"family": FAMILY_VOICE, "aliases": ("voice", "vocals")},
    "choir": {"family": FAMILY_VOICE, "aliases": ("choir", "chorus")},
}


def _flatten_canonical_instruments() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for canonical, meta in _CANONICAL_INSTRUMENTS.items():
        fam = meta["family"]
        raw_aliases = meta["aliases"]
        # Single-element tuples must be written as ("x",) in source; ("x") is a str, so guard here.
        if isinstance(raw_aliases, str):
            alias_iter: tuple[str, ...] = (raw_aliases,)
        else:
            alias_iter = tuple(str(a) for a in raw_aliases)
        for alias in alias_iter:
            rows.append((alias, fam, canonical))
    return rows


_INSTRUMENT_MAP: list[tuple[str, str, str]] = _flatten_canonical_instruments()

_SHORT_TOKEN_MAX_LEN: Final[int] = 3
# Short abbreviations (length <= _SHORT_TOKEN_MAX_LEN, no spaces in key) only match when the
# normalised part name is a short score-style phrase (few tokens), avoiding mid-sentence false positives.
_SHORT_ALIAS_MAX_TOKENS: Final[int] = 4


def _normalize(name: str) -> str:
    """Normalise a raw part name for alias lookup (lowercase, accents, flats, hyphens, etc.)."""
    if not name or not isinstance(name, str):
        return ""
    t = unicodedata.normalize("NFD", str(name))
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.lower().strip()
    for ch in ("\u2018", "\u2019", "\u02bc", "\u02b9"):
        t = t.replace(ch, "'")
    t = t.replace("♭", "b").replace("♯", "#")
    # Written-out flat names (EN/PT) → tokens used in alias keys (bb / eb).
    t = re.sub(r"\be\s*flat\b", "eb", t, flags=re.I)
    t = re.sub(r"\bb\s*flat\b", "bb", t, flags=re.I)
    t = re.sub(r"\bmi\s+be+mol\b", "eb", t, flags=re.I)
    t = re.sub(r"\bsi\s+be+mol\b", "bb", t, flags=re.I)
    t = re.sub(r"\bmib\b", "eb", t, flags=re.I)
    t = re.sub(r"\bsib\b", "bb", t, flags=re.I)
    # Oboe d'amore spellings (curly quotes already folded to ').
    t = re.sub(r"\bd\s*'\s*amore\b", "d'amore", t)
    t = re.sub(r"\bd\s+amore\b", "d'amore", t)
    t = re.sub(r"\boboe\s+damore\b", "oboe d'amore", t)
    t = re.sub(r"\bdamore\b", "d'amore", t)
    t = re.sub(r"\s*[\(\[].*?[\)\]]", "", t)
    t = t.replace("-", " ")
    t = re.sub(r"\.\s+", " ", t)
    t = re.sub(r"(?<=\S)\.(?=\s|$)", " ", t)
    t = re.sub(r"[^\w\s']+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# Orchestral string-section / desk labels (Ruzicka-style part names) → canonical strings.
_ORCH_DESK_LINE = re.compile(
    r"^("
    r"double\s+bass|contrabass\b|cb\.?|cb\b|"
    r"violoncello|cello|vc\.?|"
    r"viola|vla\.?|va\.?|va\b|"
    r"violino|violin|vnl|vln|vn\b"
    r")"
    r"(?:\s+(?P<roman>i{1,3}|iv|[1-4]))?"
    r"\s+(?P<d1>\d+)(?:\s+(?P<d2>\d+))?\s*$",
    re.IGNORECASE | re.VERBOSE,
)


def match_string_section_desk_label(raw_name: str | None) -> tuple[str, str, str, str] | None:
    """
    If ``raw_name`` is a string-desk / section label (e.g. ``vnl i 5 6``, ``Vln I: 7-10``),
    return ``(canonical_instrument, family, section_label, desk_group)``.

    Normalisation follows ``_normalize`` so colons, hyphens, and punctuation fold consistently.
    """
    if not raw_name or not str(raw_name).strip():
        return None
    orig = str(raw_name).strip()
    n = _normalize(orig)
    m = _ORCH_DESK_LINE.match(n)
    if not m:
        return None
    inst_tok = m.group(1).lower().strip()
    roman = (m.group("roman") or "").strip()
    d1, d2 = m.group("d1"), m.group("d2")
    desk_group = f"{d1}-{d2}" if d2 else str(d1)
    sec_bits = [inst_tok]
    if roman:
        sec_bits.append(roman)
    section_label = " ".join(sec_bits)

    if re.match(r"(double\s+bass|contrabass|cb)", inst_tok):
        return "double bass", FAMILY_STRINGS, section_label, desk_group
    if re.match(r"(violoncello|cello|vc)", inst_tok):
        return "cello", FAMILY_STRINGS, section_label, desk_group
    if re.match(r"(viola|vla|va)", inst_tok):
        return "viola", FAMILY_STRINGS, section_label, desk_group
    if re.match(r"(violino|violin|vnl|vln|vn)", inst_tok):
        return "violin", FAMILY_STRINGS, section_label, desk_group
    return None


def orchestration_label_fields(raw_name: str | None) -> dict[str, str]:
    """Stable orchestration columns for audit rows (empty strings when not a desk label)."""
    orig = (raw_name or "").strip()
    base = {"part_label_original": orig, "raw_part_name": orig, "section_label": "", "desk_group": ""}
    hit = match_string_section_desk_label(raw_name)
    if hit is None:
        return base
    _c, _f, sec, desk = hit
    return {"part_label_original": orig, "raw_part_name": orig, "section_label": sec, "desk_group": desk}


def _is_word_char(c: str) -> bool:
    return c.isalnum() or c in "'’"


def _short_alias_matches(n: str, key: str) -> bool:
    if len(key) > _SHORT_TOKEN_MAX_LEN or " " in key:
        return False
    if n == key:
        return True
    if len(n.split()) > _SHORT_ALIAS_MAX_TOKENS:
        return False
    for m in re.finditer(re.escape(key), n):
        lo, hi = m.span()
        if (lo == 0 or not _is_word_char(n[lo - 1])) and (hi == len(n) or not _is_word_char(n[hi])):
            return True
    return False


def _alias_matches(n: str, key: str) -> bool:
    if not key:
        return False
    if n == key:
        return True
    if len(key) <= _SHORT_TOKEN_MAX_LEN and " " not in key:
        return _short_alias_matches(n, key)
    pos = 0
    while True:
        j = n.find(key, pos)
        if j < 0:
            return False
        lo, hi = j, j + len(key)
        left_ok = lo == 0 or not _is_word_char(n[lo - 1])
        right_ok = hi == len(n) or not _is_word_char(n[hi])
        if left_ok and right_ok:
            return True
        pos = j + 1


def _build_sorted_lookup() -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str, str, str]]]:
    seen: dict[str, tuple[str, str]] = {}
    collisions: list[tuple[str, str, str, str, str]] = []
    for raw_key, family, canonical in _INSTRUMENT_MAP:
        key = _normalize(raw_key)
        if not key:
            continue
        prev = seen.get(key)
        if prev is not None:
            if prev != (family, canonical):
                collisions.append((key, prev[0], prev[1], family, canonical))
            continue
        seen[key] = (family, canonical)
    rows = [(k, fam, inst) for k, (fam, inst) in seen.items()]
    rows.sort(key=lambda r: (-len(r[0]), r[0]))
    return rows, collisions


_ALIAS_COLLISIONS_LOG: list[tuple[str, str, str, str, str]] = []
_sorted_keys, _collisions = _build_sorted_lookup()
_ALIAS_COLLISIONS_LOG[:] = _collisions


def get_alias_collision_log() -> list[tuple[str, str, str, str, str]]:
    """Return alias normalisation collisions (key, fam_a, inst_a, fam_b, inst_b) from last build."""
    return list(_ALIAS_COLLISIONS_LOG)


def resolve_instrument_taxonomy(raw_name: str | None) -> tuple[str, str, dict[str, str]]:
    """
    Resolve ``(canonical_instrument, family, orchestration_label_fields)``.

    ``orchestration_label_fields`` always contains ``part_label_original``, ``raw_part_name``,
    ``section_label``, and ``desk_group`` (last two empty when the name is not a string-desk label).
    """
    orig = (raw_name or "").strip()
    empty_meta = {"part_label_original": orig, "raw_part_name": orig, "section_label": "", "desk_group": ""}
    if raw_name is None:
        return (
            "unknown",
            FAMILY_OTHER,
            {"part_label_original": "", "raw_part_name": "", "section_label": "", "desk_group": ""},
        )
    desk = match_string_section_desk_label(raw_name)
    if desk is not None:
        canon, fam, sec, dg = desk
        return canon, fam, {"part_label_original": orig, "raw_part_name": orig, "section_label": sec, "desk_group": dg}
    n = _normalize(raw_name)
    if not n:
        return "unknown", FAMILY_OTHER, empty_meta
    for key, family, canonical in _sorted_keys:
        if _alias_matches(n, key):
            return canonical, family, empty_meta
    return n or "unknown", FAMILY_OTHER, empty_meta


def get_instrument_and_family(raw_name: str | None) -> tuple[str, str]:
    """
    Return (canonical_instrument, family) for a given instrument name from the score.
    If unknown, returns (normalized name, FAMILY_OTHER).
    """
    canon, fam, _meta = resolve_instrument_taxonomy(raw_name)
    return canon, fam


def same_family_bonus() -> float:
    """Homogeneity weight when all instruments are in the same family (but not same instrument). User tuneable."""
    return _timbral_config_copy()["family_bonus"]


def register_span_semitones_for_bonus() -> float:
    """Reference span in semitones for register bonus (e.g. minor 3rd = 3)."""
    return _timbral_config_copy()["register_ref_semitones"]


_DEFAULT_TIMBRAL_CONFIG = {
    "weight_instrument": 0.65,
    "weight_register": 0.35,
    "family_bonus": 0.65,
    "register_ref_semitones": 3.0,
}
_timbral_config: dict[str, Any] = dict(_DEFAULT_TIMBRAL_CONFIG)


def _timbral_config_copy() -> dict[str, Any]:
    return dict(_timbral_config)


def get_timbral_config() -> dict[str, Any]:
    """Return a copy of the current timbral config."""
    return _timbral_config_copy()


def set_timbral_config(overrides: dict[str, Any]) -> None:
    """Update timbral config with given keys."""
    for k, v in overrides.items():
        if k in _DEFAULT_TIMBRAL_CONFIG:
            val = float(v)
            if k == "family_bonus":
                val = max(0.0, min(1.0, val))
            _timbral_config[k] = val
