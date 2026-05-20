"""Validate ``source_registry.json`` shape, uniqueness, and release-safety rules."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path, PureWindowsPath
from typing import Any

PAGE_REQUIRED_SENTINEL = "PAGE_REQUIRED_DO_NOT_RELEASE"

EVIDENCE_TYPES = frozenset(
    {
        "measured_acoustic_data",
        "theoretical_acoustics",
        "musical_instrument_acoustics",
        "orchestration_performance_acoustics",
        "psychoacoustics",
        "signal_analysis",
        "instrument_classification",
        "spectral_features",
        "project_specific",
    }
)

RELIABILITY_LEVELS = frozenset({"high", "medium", "low"})


class SourceRegistryValidationError(ValueError):
    """Raised when the acoustic source registry fails validation."""


def get_acoustic_model_governed_source_keys() -> frozenset[str]:
    """
    Source keys whose ``pages_consulted`` must not be ``PAGE_REQUIRED_DO_NOT_RELEASE`` in release mode.

    Empty until a future acoustic/fusion config module binds literature to parameters.
    """
    return frozenset()


def count_words(s: str) -> int:
    """Whitespace-delimited word count for quote compliance."""
    return len([w for w in s.replace("\u2019", "'").split() if w])


def _flatten_string_values(obj: Any) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _flatten_string_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _flatten_string_values(v)


def _pdf_marker_present(entries: list[dict[str, Any]]) -> bool:
    return any("%pdf" in s.lower() for s in _flatten_string_values(entries))


def _local_private_filename_ok(value: str, evidence_type: str) -> bool:
    if evidence_type == "project_specific":
        return value == "" or _local_private_filename_ok(value, "musical_instrument_acoustics")
    if value.strip() == "":
        return False
    if Path(value).name != value:
        return False
    if ".." in value or value.startswith(("/", "\\")):
        return False
    pwin = PureWindowsPath(value)
    return not pwin.drive


def validate_source_registry(
    entries: list[dict[str, Any]],
    *,
    release_mode: bool = False,
    governed_source_keys: frozenset[str] | None = None,
) -> None:
    """
    Validate registry records.

    When ``release_mode`` is True, every ``source_key`` listed in ``governed_source_keys``
    (or in :func:`get_acoustic_model_governed_source_keys` when ``governed_source_keys`` is
    ``None``) must not use ``PAGE_REQUIRED_DO_NOT_RELEASE`` for ``pages_consulted``.
    """
    keys = [e.get("source_key") for e in entries]
    if any(not isinstance(k, str) or not k.strip() for k in keys):
        raise SourceRegistryValidationError("Every entry needs a non-empty string source_key.")
    if len(keys) != len(set(keys)):
        raise SourceRegistryValidationError("source_key values must be unique.")

    if _pdf_marker_present(entries):
        raise SourceRegistryValidationError("Registry must not embed PDF marker literals.")

    governed = governed_source_keys if governed_source_keys is not None else get_acoustic_model_governed_source_keys()
    by_key = {e["source_key"]: e for e in entries}

    for e in entries:
        sk = e["source_key"]
        et = e.get("evidence_type")
        if et not in EVIDENCE_TYPES:
            raise SourceRegistryValidationError(f"{sk}: invalid evidence_type {et!r}.")
        rl = e.get("reliability_level")
        if rl not in RELIABILITY_LEVELS:
            raise SourceRegistryValidationError(f"{sk}: invalid reliability_level {rl!r}.")

        for field in ("authors", "title", "publication_or_book", "used_for", "notes"):
            val = e.get(field)
            if not isinstance(val, str) or not val.strip():
                raise SourceRegistryValidationError(f"{sk}: missing or empty {field}.")

        year = e.get("year")
        if year is not None and not isinstance(year, int):
            raise SourceRegistryValidationError(f"{sk}: year must be int or null.")
        if year is None and "year not verified" not in e["notes"].lower() and et != "project_specific":
            raise SourceRegistryValidationError(
                f"{sk}: null year requires 'Year not verified' in notes (or evidence_type project_specific)."
            )

        pc = e.get("pages_consulted")
        if et != "project_specific":
            if not isinstance(pc, str) or not pc.strip():
                raise SourceRegistryValidationError(f"{sk}: pages_consulted required for non-project_specific sources.")
        else:
            if not isinstance(pc, str) or not pc.strip():
                raise SourceRegistryValidationError(f"{sk}: pages_consulted required.")

        lpf = e.get("local_private_filename")
        if not isinstance(lpf, str):
            raise SourceRegistryValidationError(f"{sk}: local_private_filename must be a string.")
        if not _local_private_filename_ok(lpf, et):
            raise SourceRegistryValidationError(
                f"{sk}: local_private_filename must be a basename only (or empty for project_specific)."
            )

        sq = e.get("short_quote_optional")
        if sq is not None:
            if not isinstance(sq, str):
                raise SourceRegistryValidationError(f"{sk}: short_quote_optional must be string or null.")
            if count_words(sq) > 25:
                raise SourceRegistryValidationError(f"{sk}: short_quote_optional exceeds 25 words.")

        if e.get("no_long_quotes") is not True:
            raise SourceRegistryValidationError(f"{sk}: no_long_quotes must be true.")

        if release_mode and sk in governed and pc == PAGE_REQUIRED_SENTINEL:
            raise SourceRegistryValidationError(
                f"{sk}: pages_consulted is {PAGE_REQUIRED_SENTINEL!r} but this key is release-governed."
            )

    if release_mode and governed_source_keys is None:
        # When caller passes explicit governed set, only that set is checked above.
        # Additionally enforce module-default governed keys if any are configured later.
        for gk in get_acoustic_model_governed_source_keys():
            if gk not in by_key:
                raise SourceRegistryValidationError(f"Governed source_key {gk!r} missing from registry.")
            if by_key[gk].get("pages_consulted") == PAGE_REQUIRED_SENTINEL:
                raise SourceRegistryValidationError(
                    f"{gk}: pages_consulted is {PAGE_REQUIRED_SENTINEL!r} but this key is release-governed."
                )


def validate_default_registry_file(
    *,
    release_mode: bool = False,
    governed_source_keys: frozenset[str] | None = None,
    path: Path | None = None,
) -> None:
    """Load the packaged JSON and validate."""
    from homogeneity_analyser.acoustic_profiles.source_registry import load_source_registry

    validate_source_registry(
        load_source_registry(path),
        release_mode=release_mode,
        governed_source_keys=governed_source_keys,
    )
