# H_TIMBRAL design corpus — index

Nine internal Markdown files document **timbral-affinity rule design** by instrument family. They are **maintainer reference**, not end-user product docs. The primary metric remains **H_TI** (`H_TI_core` + standard weights); these notes explain how family-specific timbral states were derived.

Files stay in `docs/` for version control but are listed in `mkdocs.yml` `exclude_docs` so they do not inflate the default site search index. This index is the entry point.

## Files

| Document | Focus |
|----------|--------|
| [H_TIMBRAL_SCORE_REPRESENTATION.md](H_TIMBRAL_SCORE_REPRESENTATION.md) | Score event fields used by timbral rules |
| [H_TIMBRAL_STRINGS.md](H_TIMBRAL_STRINGS.md) | Bowed strings |
| [H_TIMBRAL_BRASS.md](H_TIMBRAL_BRASS.md) | Brass |
| [H_TIMBRAL_WOODWINDS — flutes](H_TIMBRAL_FLUTES.md) | Flutes |
| [H_TIMBRAL_CLARINETS.md](H_TIMBRAL_CLARINETS.md) | Clarinets |
| [H_TIMBRAL_DOUBLE_REEDS.md](H_TIMBRAL_DOUBLE_REEDS.md) | Double reeds |
| [H_TIMBRAL_SAXOPHONES.md](H_TIMBRAL_SAXOPHONES.md) | Saxophones |
| [H_TIMBRAL_PERCUSSION.md](H_TIMBRAL_PERCUSSION.md) | Percussion / unpitched handling |
| [H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md](H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md) | Cross-family verified relations |

## Related product docs

- [Timbral affinity literature audit](TIMBRAL_AFFINITY_LITERATURE_AUDIT.md) — bibliography and verification status
- [Metric code map](METRIC_CODE_MAP.md) — `timbral_affinity.py`, `technique_state.py` entry points
- [Product scope](PRODUCT_SCOPE.md) — Tier 1 vs optional vs legacy

## Implementation map

Rule execution lives in `src/homogeneity_analyser/analyzers/timbral_affinity.py` and supporting taxonomy modules. The H_TIMBRAL corpus does **not** duplicate runtime code; it records design rationale and literature links.
