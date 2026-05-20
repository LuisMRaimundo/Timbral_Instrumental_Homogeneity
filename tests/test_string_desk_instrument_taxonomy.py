"""String-section desk labels (Ruzicka-style) → canonical violin / cello / double bass."""

from __future__ import annotations

import pytest

from homogeneity_analyser.analyzers.hti_taxonomy import macrofamily_from_instrumental_subfamily
from homogeneity_analyser.taxonomy.instrument_taxonomy import (
    FAMILY_STRINGS,
    resolve_instrument_taxonomy,
)


@pytest.mark.parametrize(
    "label",
    (
        "vnl i 5 6",
        "vnl i 7 10",
        "vnl i 11 14",
        "vnl i 1",
        "vnl i 2",
    ),
)
def test_ruzicka_json_normalised_violin_desk_labels_resolve_to_violin(label: str) -> None:
    canon, fam, meta = resolve_instrument_taxonomy(label)
    assert canon == "violin"
    assert fam == FAMILY_STRINGS
    assert macrofamily_from_instrumental_subfamily(fam) == "strings"
    assert meta["raw_part_name"] == label
    assert meta["part_label_original"] == label
    assert meta["desk_group"]
    assert meta["section_label"]


@pytest.mark.parametrize(
    "label, expected_canon",
    (
        ("Vln I: 1", "violin"),
        ("Vln I: 5-6", "violin"),
        ("Vln I: 7-10", "violin"),
        ("Vln I: 11-14", "violin"),
        ("Vln II: 1-4", "violin"),
        ("Vln II: 5-8", "violin"),
        ("Vln II: 9-12", "violin"),
        ("Vc: 1-4", "cello"),
        ("Vc: 5-8", "cello"),
        ("Cb: 1", "double bass"),
        ("Cb: 2", "double bass"),
        ("Cb: 3", "double bass"),
    ),
)
def test_desk_label_colon_hyphen_variants(label: str, expected_canon: str) -> None:
    canon, fam, meta = resolve_instrument_taxonomy(label)
    assert canon == expected_canon
    assert fam == FAMILY_STRINGS
    assert macrofamily_from_instrumental_subfamily(fam) == "strings"
    assert meta["part_label_original"] == label.strip()
    assert meta["desk_group"]
