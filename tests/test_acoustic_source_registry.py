"""Acoustic literature registry: load, shape, and validation rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from homogeneity_analyser.acoustic_profiles.source_registry import REGISTRY_JSON_PATH, load_source_registry
from homogeneity_analyser.acoustic_profiles.source_validation import (
    PAGE_REQUIRED_SENTINEL,
    SourceRegistryValidationError,
    count_words,
    validate_default_registry_file,
    validate_source_registry,
)

MINIMUM_REQUIRED_SOURCE_KEYS = (
    "sivian_dunn_white_1931_absolute_amplitudes_spectra",
    "physical_correlates_brass_instrument_tones_pending",
    "campbell_gilbert_myers_2021_science_of_brass_instruments",
    "meyer_acoustics_performance_of_music",
    "fletcher_rossing_1998_physics_of_musical_instruments",
    "rossing_2010_science_of_string_instruments",
    "rossing_et_al_science_of_sound_pearson",
    "benade_1976_fundamentals_musical_acoustics",
)


def test_load_default_registry() -> None:
    reg = load_source_registry()
    assert isinstance(reg, list) and len(reg) >= len(MINIMUM_REQUIRED_SOURCE_KEYS)


def test_minimum_source_keys_present() -> None:
    keys = {e["source_key"] for e in load_source_registry()}
    for k in MINIMUM_REQUIRED_SOURCE_KEYS:
        assert k in keys


def test_source_keys_unique() -> None:
    reg = load_source_registry()
    keys = [e["source_key"] for e in reg]
    assert len(keys) == len(set(keys))


def test_packaged_json_validates() -> None:
    validate_default_registry_file()


def test_no_quote_exceeds_25_words() -> None:
    for e in load_source_registry():
        q = e.get("short_quote_optional")
        if q:
            assert count_words(q) <= 25


def test_no_absolute_local_private_filename() -> None:
    bad_samples = (
        "/tmp/x.pdf",
        "C:\\secret\\x.pdf",
        "\\\\server\\share\\x.pdf",
        "subdir\\x.pdf",
        "../x.pdf",
    )
    for bad in bad_samples:
        entry = {
            "source_key": "k",
            "authors": "A",
            "year": 2000,
            "title": "T",
            "publication_or_book": "P",
            "publisher": None,
            "edition": None,
            "volume": None,
            "issue": None,
            "article_pages": None,
            "doi_or_url": None,
            "local_private_filename": bad,
            "pages_consulted": "1-2",
            "evidence_type": "theoretical_acoustics",
            "reliability_level": "low",
            "used_for": "u",
            "notes": "n",
            "short_quote_optional": None,
            "no_long_quotes": True,
        }
        with pytest.raises(SourceRegistryValidationError):
            validate_source_registry([entry])


def test_non_project_sources_have_pages_consulted() -> None:
    for e in load_source_registry():
        if e.get("evidence_type") == "project_specific":
            continue
        pc = e.get("pages_consulted")
        assert isinstance(pc, str) and pc.strip()


def test_release_mode_fails_when_governed_source_needs_pages(tmp_path: Path) -> None:
    reg_path = tmp_path / "reg.json"
    payload = [
        {
            "source_key": "governed_test_source",
            "authors": "Test",
            "year": 2000,
            "title": "Title",
            "publication_or_book": "Journal",
            "publisher": None,
            "edition": None,
            "volume": None,
            "issue": None,
            "article_pages": None,
            "doi_or_url": None,
            "local_private_filename": "x.pdf",
            "pages_consulted": PAGE_REQUIRED_SENTINEL,
            "evidence_type": "psychoacoustics",
            "reliability_level": "low",
            "used_for": "fusion",
            "notes": "Year not verified optional not used",
            "short_quote_optional": None,
            "no_long_quotes": True,
        }
    ]
    reg_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SourceRegistryValidationError):
        validate_default_registry_file(
            release_mode=True,
            governed_source_keys=frozenset({"governed_test_source"}),
            path=reg_path,
        )


def test_release_mode_passes_for_governed_source_with_real_pages(tmp_path: Path) -> None:
    reg_path = tmp_path / "reg.json"
    payload = [
        {
            "source_key": "governed_ok",
            "authors": "Test",
            "year": 2000,
            "title": "Title",
            "publication_or_book": "Journal",
            "publisher": None,
            "edition": None,
            "volume": None,
            "issue": None,
            "article_pages": "10-20",
            "doi_or_url": None,
            "local_private_filename": "doc.pdf",
            "pages_consulted": "10-20 (verified on copy)",
            "evidence_type": "psychoacoustics",
            "reliability_level": "low",
            "used_for": "fusion",
            "notes": "n",
            "short_quote_optional": None,
            "no_long_quotes": True,
        }
    ]
    reg_path.write_text(json.dumps(payload), encoding="utf-8")
    validate_default_registry_file(release_mode=True, governed_source_keys=frozenset({"governed_ok"}), path=reg_path)


def test_short_quote_word_limit_enforced() -> None:
    long_q = "word " * 26
    assert count_words(long_q) == 26
    entry = {
        "source_key": "qtest",
        "authors": "A",
        "year": 2000,
        "title": "T",
        "publication_or_book": "P",
        "publisher": None,
        "edition": None,
        "volume": None,
        "issue": None,
        "article_pages": None,
        "doi_or_url": None,
        "local_private_filename": "a.pdf",
        "pages_consulted": "1",
        "evidence_type": "project_specific",
        "reliability_level": "low",
        "used_for": "u",
        "notes": "n",
        "short_quote_optional": long_q.strip(),
        "no_long_quotes": True,
    }
    with pytest.raises(SourceRegistryValidationError):
        validate_source_registry([entry])


def test_registry_json_path_exists_in_repo() -> None:
    assert REGISTRY_JSON_PATH.is_file()
