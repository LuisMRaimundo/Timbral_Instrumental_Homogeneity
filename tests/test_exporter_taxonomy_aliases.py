"""Exporter-style part-name aliases (Finale / Sibelius / Dorico patterns)."""

from __future__ import annotations

import pytest

from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_BRASS,
    FAMILY_PERCUSSION,
    FAMILY_STRINGS,
    resolve_instrument_taxonomy,
)


@pytest.mark.parametrize(
    "label, expected_canon, expected_family",
    (
        ("Violins I", "violin", FAMILY_STRINGS),
        ("Violin 2", "violin", FAMILY_STRINGS),
        ("Horn in F", "horn", FAMILY_BRASS),
        ("Trumpet in B-flat", "trumpet", FAMILY_BRASS),
        ("Kettle Drums", "timpani", FAMILY_PERCUSSION),
    ),
)
def test_common_exporter_part_names(label: str, expected_canon: str, expected_family: str) -> None:
    canon, fam, _meta = resolve_instrument_taxonomy(label)
    assert canon == expected_canon
    assert fam == expected_family
