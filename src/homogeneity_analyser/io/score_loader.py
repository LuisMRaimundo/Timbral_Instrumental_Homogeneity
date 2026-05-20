"""music21 score loading with pre-validation."""

from __future__ import annotations

import os

import music21 as m21

from homogeneity_analyser.io.score_validation import validate_score_path

_MUSICXML_EXTENSIONS = frozenset({".xml", ".musicxml", ".mxl"})


def parse_score(score_path: str):
    """
    Parse score from path. Force MusicXML for .xml/.musicxml/.mxl so Sibelius and Dorico
    exports are read correctly. Validates path and MXL zip safety first.
    """
    validate_score_path(score_path)
    ext = os.path.splitext(score_path)[1].lower()
    if ext in _MUSICXML_EXTENSIONS:
        return m21.converter.parse(score_path, format="musicxml")
    return m21.converter.parse(score_path)
