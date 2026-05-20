"""
Symbolic percussion ontology for **H_timbral** (notation only).

Maps each canonical taxonomy instrument to macro-class, material, pitch role, and coarse
acoustic proxies (resonance / noise / size bin). Not acoustic measurement.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PercussionMacroClass(str, Enum):
    TUNED_MEMBRANOPHONE = "tuned_membranophone"
    UNTUNED_MEMBRANOPHONE = "untuned_membranophone"
    WOODEN_BAR_IDIOPHONE = "wooden_bar_idiophone"
    METALLIC_PITCHED_IDIOPHONE = "metallic_pitched_idiophone"
    PLATE_SHELL_METAL = "plate_shell_metal"
    SMALL_HIGH_METAL = "small_high_metal"
    MISC_SMALL_IDIOPHONE = "misc_small_idiophone"
    GENERIC = "generic"


class PitchStatus(str, Enum):
    PITCHED = "pitched"
    QUASI_PITCHED = "quasi_pitched"
    UNPITCHED = "unpitched"


@dataclass(frozen=True)
class PercussionMeta:
    macro: PercussionMacroClass
    material: str  # membrane | wood | metal | mixed
    pitch_status: PitchStatus
    resonance: int  # 0 short, 1 medium, 2 long
    noise: int  # 0 low, 1 medium, 2 high
    size_bin: int  # 1–5 spectral/size proxy for unpitched pairing
    tessitura_lo: float | None  # MIDI concert, pitched / quasi only
    tessitura_hi: float | None


def _m(
    macro: PercussionMacroClass,
    material: str,
    ps: PitchStatus,
    res: int,
    noise: int,
    size: int,
    lo: float | None = None,
    hi: float | None = None,
) -> PercussionMeta:
    return PercussionMeta(macro, material, ps, res, noise, size, lo, hi)


# Canonical instrument strings must match ``instrument_taxonomy`` outputs.
PERCUSSION_ONTOLOGY: dict[str, PercussionMeta] = {
    "timpani": _m(
        PercussionMacroClass.TUNED_MEMBRANOPHONE,
        "membrane",
        PitchStatus.PITCHED,
        2,
        1,
        4,
        40.0,
        68.0,
    ),
    "snare drum": _m(
        PercussionMacroClass.UNTUNED_MEMBRANOPHONE,
        "membrane",
        PitchStatus.UNPITCHED,
        1,
        2,
        3,
    ),
    "bass drum": _m(
        PercussionMacroClass.UNTUNED_MEMBRANOPHONE,
        "membrane",
        PitchStatus.UNPITCHED,
        2,
        1,
        5,
    ),
    "tom-tom": _m(
        PercussionMacroClass.UNTUNED_MEMBRANOPHONE,
        "membrane",
        PitchStatus.UNPITCHED,
        1,
        2,
        3,
    ),
    "xylophone": _m(
        PercussionMacroClass.WOODEN_BAR_IDIOPHONE,
        "wood",
        PitchStatus.PITCHED,
        1,
        1,
        2,
        52.0,
        96.0,
    ),
    "marimba": _m(
        PercussionMacroClass.WOODEN_BAR_IDIOPHONE,
        "wood",
        PitchStatus.PITCHED,
        2,
        0,
        3,
        45.0,
        96.0,
    ),
    "glockenspiel": _m(
        PercussionMacroClass.METALLIC_PITCHED_IDIOPHONE,
        "metal",
        PitchStatus.PITCHED,
        0,
        1,
        2,
        65.0,
        108.0,
    ),
    "crotales": _m(
        PercussionMacroClass.METALLIC_PITCHED_IDIOPHONE,
        "metal",
        PitchStatus.PITCHED,
        0,
        1,
        1,
        76.0,
        108.0,
    ),
    "vibraphone": _m(
        PercussionMacroClass.METALLIC_PITCHED_IDIOPHONE,
        "metal",
        PitchStatus.PITCHED,
        2,
        0,
        3,
        50.0,
        92.0,
    ),
    "tubular bells": _m(
        PercussionMacroClass.METALLIC_PITCHED_IDIOPHONE,
        "metal",
        PitchStatus.QUASI_PITCHED,
        2,
        1,
        4,
        48.0,
        96.0,
    ),
    "steelpan": _m(
        PercussionMacroClass.METALLIC_PITCHED_IDIOPHONE,
        "metal",
        PitchStatus.PITCHED,
        1,
        1,
        3,
        50.0,
        95.0,
    ),
    "cymbal": _m(
        PercussionMacroClass.PLATE_SHELL_METAL,
        "metal",
        PitchStatus.UNPITCHED,
        2,
        2,
        4,
    ),
    "gong": _m(
        PercussionMacroClass.PLATE_SHELL_METAL,
        "metal",
        PitchStatus.QUASI_PITCHED,
        2,
        1,
        5,
        30.0,
        75.0,
    ),
    "tam-tam": _m(
        PercussionMacroClass.PLATE_SHELL_METAL,
        "metal",
        PitchStatus.UNPITCHED,
        2,
        1,
        5,
    ),
    "triangle": _m(
        PercussionMacroClass.SMALL_HIGH_METAL,
        "metal",
        PitchStatus.UNPITCHED,
        0,
        2,
        1,
    ),
    "tambourine": _m(
        PercussionMacroClass.MISC_SMALL_IDIOPHONE,
        "mixed",
        PitchStatus.UNPITCHED,
        1,
        2,
        2,
    ),
    "castanets": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "wood", PitchStatus.UNPITCHED, 0, 2, 1),
    "claves": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "wood", PitchStatus.UNPITCHED, 0, 1, 1),
    "cowbell": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "metal", PitchStatus.QUASI_PITCHED, 0, 2, 2, 55.0, 85.0),
    "wood block": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "wood", PitchStatus.UNPITCHED, 0, 1, 2),
    "temple block": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "wood", PitchStatus.UNPITCHED, 0, 1, 2),
    "bongos": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "membrane", PitchStatus.UNPITCHED, 1, 2, 2),
    "congas": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "membrane", PitchStatus.UNPITCHED, 1, 2, 3),
    "djembe": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "membrane", PitchStatus.UNPITCHED, 1, 2, 3),
    "tabla": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "membrane", PitchStatus.UNPITCHED, 1, 2, 2),
    "cajón": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "mixed", PitchStatus.UNPITCHED, 1, 2, 3),
    "rototom": _m(PercussionMacroClass.UNTUNED_MEMBRANOPHONE, "membrane", PitchStatus.UNPITCHED, 1, 2, 3),
    "wind chimes": _m(PercussionMacroClass.MISC_SMALL_IDIOPHONE, "metal", PitchStatus.PITCHED, 2, 1, 1, 72.0, 100.0),
    "percussion": _m(PercussionMacroClass.GENERIC, "mixed", PitchStatus.UNPITCHED, 1, 1, 3),
}


def get_percussion_meta(canonical_instrument: str) -> PercussionMeta:
    return PERCUSSION_ONTOLOGY.get(
        canonical_instrument,
        PercussionMeta(
            PercussionMacroClass.GENERIC,
            "mixed",
            PitchStatus.UNPITCHED,
            1,
            1,
            3,
            None,
            None,
        ),
    )
