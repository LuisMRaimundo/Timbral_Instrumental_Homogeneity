"""Tests for brass pairwise H_timbral refinement (symbolic)."""

from __future__ import annotations

from music21 import articulations, expressions, note

from homogeneity_analyser.analyzers.brass_pairwise_timbral import (
    brass_register_similarity,
    brass_section_similarity,
    brass_technique_similarity,
    pairwise_brass_homogeneity,
)
from homogeneity_analyser.analyzers.brass_technique import (
    BRASS_HARMON,
    BRASS_OPEN,
    BRASS_STOPPED,
    BRASS_STRAIGHT,
    brass_technique_from_note,
)
from homogeneity_analyser.taxonomy.instrument_taxonomy import FAMILY_BRASS


def _be(inst: str, pitch: float, tech: str = BRASS_OPEN, w: float = 1.0) -> dict:
    return {"instrument": inst, "pitch": pitch, "technique": tech, "overlap_ql": w}


def test_trombone_bass_trombone_vs_trumpet_trombone():
    a = pairwise_brass_homogeneity([_be("trombone", 55), _be("bass trombone", 50)])
    b = pairwise_brass_homogeneity([_be("trumpet", 62), _be("trombone", 55)])
    assert a > b


def test_bass_trombone_tuba_vs_trumpet_tuba():
    a = pairwise_brass_homogeneity([_be("bass trombone", 48), _be("tuba", 36)])
    b = pairwise_brass_homogeneity([_be("trumpet", 70), _be("tuba", 36)])
    assert a > b


def test_trumpet_horn_vs_trumpet_tuba():
    a = pairwise_brass_homogeneity([_be("trumpet", 65), _be("horn", 60)])
    b = pairwise_brass_homogeneity([_be("trumpet", 65), _be("tuba", 40)])
    assert a > b


def test_trumpet_open_straight_vs_open_harmon():
    oo = pairwise_brass_homogeneity([_be("trumpet", 65, BRASS_OPEN), _be("trumpet", 65, BRASS_OPEN)])
    os = pairwise_brass_homogeneity([_be("trumpet", 65, BRASS_OPEN), _be("trumpet", 65, BRASS_STRAIGHT)])
    oh = pairwise_brass_homogeneity([_be("trumpet", 65, BRASS_OPEN), _be("trumpet", 65, BRASS_HARMON)])
    assert oo > os > oh


def test_horn_open_vs_stopped():
    oo = pairwise_brass_homogeneity([_be("horn", 60, BRASS_OPEN), _be("horn", 62, BRASS_OPEN)])
    ost = pairwise_brass_homogeneity([_be("horn", 60, BRASS_OPEN), _be("horn", 62, BRASS_STOPPED)])
    assert oo - ost > 0.35


def test_trumpet_same_tessitura_adjacent_distant():
    same = brass_register_similarity("trumpet", 68.0, "trumpet", 69.0)
    adj = brass_register_similarity("trumpet", 68.0, "trumpet", 74.0)
    far = brass_register_similarity("trumpet", 56.0, "trumpet", 84.0)
    assert same >= adj >= far


def test_trombone_same_vs_distant_tessitura():
    same = brass_register_similarity("trombone", 55.0, "trombone", 56.0)
    far = brass_register_similarity("trombone", 38.0, "trombone", 70.0)
    assert same > far


def test_three_trumpets_vs_trumpets_horns_tuba():
    t3 = pairwise_brass_homogeneity([_be("trumpet", 65), _be("trumpet", 66), _be("trumpet", 64)])
    tht = pairwise_brass_homogeneity([_be("trumpet", 65), _be("horn", 60), _be("tuba", 36)])
    assert t3 > tht


def test_trombones_plus_bass_trombone_vs_trumpet_tuba():
    low = pairwise_brass_homogeneity([_be("trombone", 52), _be("bass trombone", 48), _be("trombone", 53)])
    ht = pairwise_brass_homogeneity([_be("trumpet", 72), _be("tuba", 34)])
    assert low > ht


def test_brass_technique_stopped_articulation():
    # music21 `Stopped` here is a **symbolic** articulation on the note; meaning is conventionally horn
    # stopped / hand-stopping in orchestral brass, but not guaranteed without part/instrument context.
    n = note.Note("G4")
    n.articulations = [articulations.Stopped()]
    assert brass_technique_from_note(n, family=FAMILY_BRASS) == BRASS_STOPPED


def test_brass_technique_harmon_text():
    n = note.Note("C5")
    n.expressions.append(expressions.TextExpression("Harmon mute"))
    assert brass_technique_from_note(n, family=FAMILY_BRASS) == BRASS_HARMON


def test_brass_technique_non_brass_returns_open():
    n = note.Note("D5")
    n.expressions.append(expressions.TextExpression("Harmon mute"))
    assert brass_technique_from_note(n, family="strings") == BRASS_OPEN


def test_section_table_ordering_magnitudes():
    assert brass_section_similarity("trombone", "bass trombone") > brass_section_similarity("trumpet", "trombone")
    assert brass_section_similarity("bass trombone", "tuba") > brass_section_similarity("trumpet", "tuba")
    assert brass_section_similarity("trumpet", "horn") > brass_section_similarity("trumpet", "tuba")


def test_technique_symmetric():
    a = brass_technique_similarity(BRASS_OPEN, BRASS_STRAIGHT)
    b = brass_technique_similarity(BRASS_STRAIGHT, BRASS_OPEN)
    assert a == b


def test_open_harmon_strong_penalty():
    assert brass_technique_similarity(BRASS_OPEN, BRASS_HARMON) < 0.2
