"""
Symbolic percussion playing / mallet / damping states for **H_timbral** (notation only).

Single primary label per note; ``unknown`` pairs moderately with common defaults.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from homogeneity_analyser.analyzers.notation_context import notation_text_context_for_note
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_PERCUSSION

if TYPE_CHECKING:
    from music21.note import GeneralNote

PERC_ORDINARIO = "ordinario"
PERC_MALLET_HARD = "mallet_hard"
PERC_MALLET_SOFT = "mallet_soft"
PERC_MALLET_FELT = "mallet_felt"
PERC_MALLET_YARN = "mallet_yarn"
PERC_STICKS = "sticks"
PERC_BRUSHES = "brushes"
PERC_SNARE_ON = "snare_on"
PERC_SNARE_OFF = "snare_off"
PERC_DAMPED = "damped"
PERC_OPEN = "open"
PERC_ROLLED = "rolled"
PERC_BOWED = "bowed"
PERC_VIB_PEDAL = "vibraphone_pedal"
PERC_VIB_NO_PEDAL = "vibraphone_no_pedal"
PERC_CYM_SUSPENDED = "cymbal_suspended"
PERC_CYM_CRASH = "cymbal_crash"
PERC_RIM = "rim_stroke"
PERC_UNKNOWN = "unknown"


def percussion_technique_from_note(n: GeneralNote, *, family: str) -> str:
    if family != FAMILY_PERCUSSION:
        return PERC_ORDINARIO

    blob = notation_text_context_for_note(n)

    if re.search(r"\bbowed\b|archet|arco", blob):
        return PERC_BOWED
    if re.search(r"\broll|tr\s*~|tremolo|trem\.", blob):
        return PERC_ROLLED
    if re.search(r"pedal\s*down|ped\s*dn|with\s*pedal|motor\s*on", blob):
        return PERC_VIB_PEDAL
    if re.search(r"pedal\s*up|senza\s*pedal|no\s*pedal|motor\s*off", blob):
        return PERC_VIB_NO_PEDAL
    if re.search(r"snare\s*off|snares\s*off| ohne schnarr", blob):
        return PERC_SNARE_OFF
    if re.search(r"snare\s*on|snares\s*on|mit schnarr", blob):
        return PERC_SNARE_ON
    if re.search(r"damp|choked|stopped|staccato\s*secco|secco", blob):
        return PERC_DAMPED
    if re.search(r"let\s*ring|open\s*sound|senza\s*sord", blob):
        return PERC_OPEN
    if re.search(r"suspended|hang|let\s*vibrate", blob):
        return PERC_CYM_SUSPENDED
    if re.search(r"crash|accent\s*cym", blob):
        return PERC_CYM_CRASH
    if re.search(r"\brim\b|rimshot|stick\s*on\s*rim", blob):
        return PERC_RIM
    if re.search(r"yarn|cord\s*mallet", blob):
        return PERC_MALLET_YARN
    if re.search(r"felt\s*mallet|felt\s*beater", blob):
        return PERC_MALLET_FELT
    if re.search(r"soft\s*mallet|rubber\s*mallet|marimba\s*mallet", blob):
        return PERC_MALLET_SOFT
    if re.search(r"hard\s*mallet|plastic\s*mallet|xylophone\s*mallet", blob):
        return PERC_MALLET_HARD
    if re.search(r"\bbrushes\b", blob):
        return PERC_BRUSHES
    if re.search(r"\bsticks\b|drumsticks|beater", blob):
        return PERC_STICKS
    if re.search(r"normale|natural|ord\.|ordinario", blob):
        return PERC_ORDINARIO

    return PERC_UNKNOWN
