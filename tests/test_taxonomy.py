"""
Unit tests for instrument taxonomy.

Assumption tags (non-obvious rows are mostly **ambiguous but intentionally accepted** orchestration
spellings, or **confirmed musical convention** where PT/EN abbreviations are standard; the alias table
itself is **project-specific convention** (``_CANONICAL_INSTRUMENTS`` in ``instrument_taxonomy.py``).
``test_alias_collision_log_empty`` encodes **project-specific convention** (no undocumented collisions).
See ``test_audit_rigorous_timbral`` for the full legend.

**Project-specific:** bare ``bass`` → double bass (``test_bare_bass_maps_to_double_bass_orchestral_convention``);
choral bass should use ``bass voice`` etc. Bare ``alto`` / ``tenor`` / ``baritone`` as voice roles are
asserted in ``test_audit_rigorous_timbral.test_ambiguous_voice_labels_not_mapped_to_winds``.
"""

from __future__ import annotations

import pytest

import unittest


from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BASSOONS,
    FAMILY_BRASS,
    FAMILY_CLARINETS,
    FAMILY_FLUTES,
    FAMILY_KEYBOARD,
    FAMILY_OBOES,
    FAMILY_OTHER,
    FAMILY_PERCUSSION,
    FAMILY_RECORDERS,
    FAMILY_SAXOPHONES,
    FAMILY_STRINGS,
    FAMILY_VOICE,
    _normalize,
    get_alias_collision_log,
    get_instrument_and_family,
    get_timbral_config,
    set_timbral_config,
)


class TestGetInstrumentAndFamily(unittest.TestCase):
    def test_known_instruments(self):
        self.assertEqual(get_instrument_and_family("Violin 1"), ("violin", FAMILY_STRINGS))
        self.assertEqual(get_instrument_and_family("Bass Trombone"), ("bass trombone", FAMILY_BRASS))
        self.assertEqual(get_instrument_and_family("Bass Clarinet"), ("bass clarinet", FAMILY_CLARINETS))
        self.assertEqual(get_instrument_and_family("A Clarinet"), ("a clarinet", FAMILY_CLARINETS))
        self.assertEqual(get_instrument_and_family("Bb Clarinet"), ("b flat clarinet", FAMILY_CLARINETS))
        self.assertEqual(get_instrument_and_family("Eb Clarinet"), ("e flat clarinet", FAMILY_CLARINETS))
        self.assertEqual(get_instrument_and_family("C Clarinet"), ("c clarinet", FAMILY_CLARINETS))
        self.assertEqual(get_instrument_and_family("Basset Clarinet"), ("basset clarinet", FAMILY_CLARINETS))
        self.assertEqual(get_instrument_and_family("Flute"), ("flute", FAMILY_FLUTES))
        self.assertEqual(get_instrument_and_family("Alto Saxophone"), ("alto saxophone", FAMILY_SAXOPHONES))
        self.assertEqual(get_instrument_and_family("Natural Horn"), ("natural horn", FAMILY_BRASS))
        self.assertEqual(get_instrument_and_family("Cor de chasse"), ("natural horn", FAMILY_BRASS))
        self.assertEqual(get_instrument_and_family("Bass Trumpet"), ("bass trumpet", FAMILY_BRASS))
        self.assertEqual(get_instrument_and_family("Recorder"), ("recorder", FAMILY_RECORDERS))
        self.assertEqual(get_instrument_and_family("Soprano"), ("soprano", FAMILY_VOICE))

    def test_longest_match_first(self):
        self.assertEqual(get_instrument_and_family("Bass Clarinet"), ("bass clarinet", FAMILY_CLARINETS))
        self.assertEqual(get_instrument_and_family("Contrabass Clarinet"), ("contrabass clarinet", FAMILY_CLARINETS))

    def test_unknown_returns_normalized_and_other(self):
        inst, fam = get_instrument_and_family("Some Weird Instrument 99")
        self.assertEqual(fam, FAMILY_OTHER)
        self.assertIn("weird", inst.lower() or "unknown")

    def test_empty_or_none(self):
        self.assertEqual(get_instrument_and_family(""), ("unknown", FAMILY_OTHER))
        self.assertEqual(get_instrument_and_family(None), ("unknown", FAMILY_OTHER))

    def test_no_false_positive_cl_in_classical(self):
        inst, fam = get_instrument_and_family("classical guitar")
        self.assertEqual(inst, "guitar")
        self.assertEqual(fam, FAMILY_STRINGS)

    def test_bare_bass_maps_to_double_bass_orchestral_convention(self):
        # Project-specific convention (not universal): a lone part name "bass" is mapped to orchestral
        # double bass. Choral or vocal bass lines should use labels like "bass voice"; we do not infer
        # score genre beyond the raw instrument string.
        self.assertEqual(get_instrument_and_family("bass"), ("double bass", FAMILY_STRINGS))

    def test_alias_collision_log_empty(self):
        self.assertEqual(get_alias_collision_log(), [])


# Each row: mostly **confirmed musical convention** (standard aliases);
# a few **ambiguous but intentionally accepted** (e.g. cor anglais spellings).
@pytest.mark.parametrize(
    "raw,expected_canonical,expected_family",
    [
        ("fl.", "flute", FAMILY_FLUTES),
        ("flauta", "flute", FAMILY_FLUTES),
        ("flauta transversal", "flute", FAMILY_FLUTES),
        ("picc.", "piccolo", FAMILY_FLUTES),
        ("flautim", "piccolo", FAMILY_FLUTES),
        ("ob.", "oboe", FAMILY_OBOES),
        ("oboé", "oboe", FAMILY_OBOES),
        ("cor inglês", "cor anglais", FAMILY_OBOES),
        ("english horn", "cor anglais", FAMILY_OBOES),
        ("cl.", "clarinet", FAMILY_CLARINETS),
        ("cl in bb", "b flat clarinet", FAMILY_CLARINETS),
        ("clarinete em si bemol", "b flat clarinet", FAMILY_CLARINETS),
        ("clarinete em lá", "a clarinet", FAMILY_CLARINETS),
        ("requinta", "e flat clarinet", FAMILY_CLARINETS),
        ("bass cl.", "bass clarinet", FAMILY_CLARINETS),
        ("clarinete baixo", "bass clarinet", FAMILY_CLARINETS),
        ("fg.", "bassoon", FAMILY_BASSOONS),
        ("fag.", "bassoon", FAMILY_BASSOONS),
        ("fagote", "bassoon", FAMILY_BASSOONS),
        ("cfg.", "contrabassoon", FAMILY_BASSOONS),
        ("contrafagote", "contrabassoon", FAMILY_BASSOONS),
        ("hn.", "horn", FAMILY_BRASS),
        ("trompa", "horn", FAMILY_BRASS),
        ("tpt.", "trumpet", FAMILY_BRASS),
        ("trompete", "trumpet", FAMILY_BRASS),
        ("trb.", "trombone", FAMILY_BRASS),
        ("trombone baixo", "bass trombone", FAMILY_BRASS),
        ("tba.", "tuba", FAMILY_BRASS),
        ("eufónio", "euphonium", FAMILY_BRASS),
        ("bombardino", "euphonium", FAMILY_BRASS),
        ("vln.", "violin", FAMILY_STRINGS),
        ("violino", "violin", FAMILY_STRINGS),
        ("vla.", "viola", FAMILY_STRINGS),
        ("vc.", "cello", FAMILY_STRINGS),
        ("violoncelo", "cello", FAMILY_STRINGS),
        ("cb.", "double bass", FAMILY_STRINGS),
        ("contrabaixo", "double bass", FAMILY_STRINGS),
        ("hp.", "harp", FAMILY_STRINGS),
        ("pf.", "piano", FAMILY_KEYBOARD),
        ("pno.", "piano", FAMILY_KEYBOARD),
        ("cel.", "celesta", FAMILY_KEYBOARD),
        ("cravo", "harpsichord", FAMILY_KEYBOARD),
        ("org.", "organ", FAMILY_KEYBOARD),
        ("órgão", "organ", FAMILY_KEYBOARD),
        ("timp.", "timpani", FAMILY_PERCUSSION),
        ("tímpanos", "timpani", FAMILY_PERCUSSION),
        ("bd", "bass drum", FAMILY_PERCUSSION),
        ("bombo", "bass drum", FAMILY_PERCUSSION),
        ("sd", "snare drum", FAMILY_PERCUSSION),
        ("caixa clara", "snare drum", FAMILY_PERCUSSION),
        ("tgl", "triangle", FAMILY_PERCUSSION),
        ("triângulo", "triangle", FAMILY_PERCUSSION),
        ("tam-tam", "tam-tam", FAMILY_PERCUSSION),
        ("tam tam", "tam-tam", FAMILY_PERCUSSION),
        ("glock.", "glockenspiel", FAMILY_PERCUSSION),
        ("xilofone", "xylophone", FAMILY_PERCUSSION),
        ("vibrafone", "vibraphone", FAMILY_PERCUSSION),
        ("pratos", "cymbal", FAMILY_PERCUSSION),
        ("prato suspenso", "suspended cymbal", FAMILY_PERCUSSION),
        ("Clarinet in Bb", "b flat clarinet", FAMILY_CLARINETS),
        ("Cl. in B♭", "b flat clarinet", FAMILY_CLARINETS),
        ("Flauta 1", "flute", FAMILY_FLUTES),
        ("Violino II", "violin", FAMILY_STRINGS),
        ("alto flute", "alto flute", FAMILY_FLUTES),
        ("saxofone barítono", "baritone saxophone", FAMILY_SAXOPHONES),
        ("cor anglais", "cor anglais", FAMILY_OBOES),
    ],
)
def test_acceptance_and_score_style_aliases(raw, expected_canonical, expected_family):
    inst, fam = get_instrument_and_family(raw)
    assert inst == expected_canonical
    assert fam == expected_family


@pytest.mark.parametrize(
    "raw,expected_norm",
    [
        ("violoncélo", "violoncelo"),
        ("tímpanos", "timpanos"),
        ("oboé", "oboe"),
        ("Oboe d amore", "oboe d'amore"),
        ("oboe damore", "oboe d'amore"),
        ("tam-tam", "tam tam"),
        ("mezzo-soprano", "mezzo soprano"),
        ("Clarinet in B flat", "clarinet in bb"),
        ("clarinet in E flat", "clarinet in eb"),
        ("clarinete em mi bemol", "clarinete em eb"),
        ("si bemol", "bb"),
        ("sib", "bb"),
        ("mib", "eb"),
    ],
)
def test_instrument_normalize_contract(raw, expected_norm):
    """**Project-specific convention:** ``_normalize`` contract for taxonomy lookup keys."""
    assert _normalize(raw) == expected_norm


@pytest.mark.parametrize(
    "prose_fragment",
    [
        "random text with cl inside",
        "traces",
        "band",
        "correlation",
        "five token phrase with cl here",
    ],
)
def test_long_prose_does_not_match_short_score_abbreviations(prose_fragment):
    """
    **Project-specific convention:** short abbreviations (``cl``, ``tr``, ``bd``, …) must not fire inside
    long free-text phrases; see ``_SHORT_ALIAS_MAX_TOKENS`` in ``instrument_taxonomy.py``.
    """
    inst, fam = get_instrument_and_family(prose_fragment)
    assert fam == FAMILY_OTHER
    assert inst == _normalize(prose_fragment)


@pytest.mark.parametrize(
    "raw,expected_canonical,expected_family",
    [
        ("cl in bb", "b flat clarinet", FAMILY_CLARINETS),
        ("bd", "bass drum", FAMILY_PERCUSSION),
        ("Clarinet in E flat", "e flat clarinet", FAMILY_CLARINETS),
        ("Oboe d\u2019amore", "oboe d'amore", FAMILY_OBOES),
    ],
)
def test_short_alias_and_flat_spellings_still_resolve(raw, expected_canonical, expected_family):
    """**Confirmed musical convention** (standard part abbreviations / pitch wording)."""
    inst, fam = get_instrument_and_family(raw)
    assert inst == expected_canonical
    assert fam == expected_family


class TestTimbralConfig(unittest.TestCase):
    def test_get_returns_copy(self):
        c = get_timbral_config()
        self.assertIn("weight_instrument", c)
        self.assertIn("family_bonus", c)
        c["weight_instrument"] = 999
        c2 = get_timbral_config()
        self.assertNotEqual(c2["weight_instrument"], 999)

    def test_set_timbral_config(self):
        set_timbral_config({"family_bonus": 0.7})
        c = get_timbral_config()
        self.assertEqual(c["family_bonus"], 0.7)
        set_timbral_config({"family_bonus": 0.65})
