"""
MusicXML fixture corpus: end-to-end via ``parse_score`` (production loader) and
``TimbralHomogeneityAnalyzer``. See ``tests/fixtures/musicxml/README.md`` for exporter limits.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from music21 import stream

from homogeneity_analyser.analyzers.parsing_bridge import parse_score
from homogeneity_analyser.analyzers.timbral import TimbralHomogeneityAnalyzer
from homogeneity_analyser.services.analysis_service import run_timbral_analysis

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "musicxml"


def _require_fixture(name: str) -> Path:
    p = FIXTURE_DIR / name
    if not p.is_file():
        pytest.skip(f"Missing fixture {p}")
    return p


def _event_technique_ids(score_path: str) -> list[str]:
    an = TimbralHomogeneityAnalyzer(score_path, time_step=1.0)
    return [str(e["technique_state_id"]) for e in an._events]


def _union_timbral_state_keys(score_path: str, *, time_step: float = 0.5, window_size: float = 3.0) -> set[str]:
    an = TimbralHomogeneityAnalyzer(score_path, time_step=time_step)
    r = an.analyze_timbral(window_size)
    keys: set[str] = set()
    for d in r["timbral_state_distribution"]:
        if isinstance(d, dict):
            keys |= set(d.keys())
    return keys


@pytest.mark.parametrize(
    "filename,expected_substrings",
    [
        (
            "corpus_horn_techniques.musicxml",
            ("horn|open", "horn|stopped", "horn|cuivre"),
        ),
        (
            "corpus_strings_techniques.musicxml",
            ("violin|pizz", "sul_pont", "violin|arco|muted", "violin|arco"),
        ),
        (
            "corpus_flute_techniques.musicxml",
            ("flute|air_sound", "flute|jet_whistle"),
        ),
        (
            "corpus_clarinet_sax_techniques.musicxml",
            ("clarinet|slap", "clarinet|multiphonic", "bisbigliando"),
        ),
    ],
)
def test_parse_fixture_timbral_events_contain_technique_ids(filename, expected_substrings):
    p = _require_fixture(filename)
    score = parse_score(str(p))
    assert isinstance(score, stream.Score)
    assert score.parts, f"{filename}: expected at least one part after parse"
    joined = "|".join(_event_technique_ids(str(p)))
    for needle in expected_substrings:
        assert needle in joined, f"{filename}: missing {needle!r} in {joined!r}"


def test_horn_editorial_words_fixture_matches_plain_sequence():
    """Typical ``words`` layout attributes should not change parsed technique ids."""
    p0 = _require_fixture("corpus_horn_techniques.musicxml")
    p1 = _require_fixture("corpus_horn_words_realistic.musicxml")
    assert _event_technique_ids(str(p0)) == _event_technique_ids(str(p1))


def test_timbral_state_distribution_union_covers_event_states():
    p = _require_fixture("corpus_horn_techniques.musicxml")
    parse_score(str(p))
    keys = _union_timbral_state_keys(str(p))
    for k in ("horn|open", "horn|stopped", "horn|cuivre"):
        assert k in keys, f"missing distribution key {k!r} in {sorted(keys)!r}"


def test_run_timbral_analysis_service_on_horn_fixture():
    """Service layer uses the same ``parse_score`` path as the analyzers."""
    p = _require_fixture("corpus_horn_techniques.musicxml")
    out = run_timbral_analysis(str(p), {"time_step": 0.5, "window_size": 3.0, "timbral_config": None})
    assert not out.get("error"), out.get("error")
    dists = out["results"]["timbral_state_distribution"]
    assert any(isinstance(d, dict) and "horn|stopped" in d for d in dists)


def test_percussion_fixture_directions_in_ids_and_distribution():
    p = _require_fixture("corpus_percussion_techniques.musicxml")
    parse_score(str(p))
    ids = _event_technique_ids(str(p))
    assert len(ids) == 4
    assert "suspended cymbal|let_ring" in ids[0]
    assert any("damped" in x for x in ids)
    assert any("soft_mallet" in x for x in ids)
    joined_dist = "|".join(sorted(_union_timbral_state_keys(str(p))))
    assert "let_ring" in joined_dist and "damped" in joined_dist
