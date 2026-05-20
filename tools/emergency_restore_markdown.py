"""
Emergency restore of Markdown files damaged by formula-flattening.

Sources (in priority order):
  - Homogeneity_analyser - Backup/  (older but structurally valid snapshots)
  - Repository _from_tr_*.md transcript snapshots
  - TECHNICAL_MANUAL.md: merge Cursor/read-style head (optional), _appendix_d_extract.md, tail from ## 19) on disk

Run from project root:
  python tools/emergency_restore_markdown.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    bak = root.parent / "Homogeneity_analyser - Backup"
    if not bak.is_dir():
        print("ERROR: backup folder not found:", bak, file=sys.stderr)
        return 2

    copies: list[tuple[Path, Path, str]] = [
        (bak / "docs" / "METRIC_CODE_MAP.md", root / "docs" / "METRIC_CODE_MAP.md", "Homogeneity_analyser - Backup/docs/METRIC_CODE_MAP.md"),
        (bak / "docs" / "ARCHITECTURE.md", root / "docs" / "ARCHITECTURE.md", "Homogeneity_analyser - Backup/docs/ARCHITECTURE.md"),
        (root / "_from_tr_SCIENTIFIC_TECHNICAL_AUDIT.md", root / "docs" / "SCIENTIFIC_TECHNICAL_AUDIT.md", "_from_tr_SCIENTIFIC_TECHNICAL_AUDIT.md"),
        (root / "_from_tr_STRING_HARMONIC_INTERVAL_REFERENCE.md", root / "docs" / "STRING_HARMONIC_INTERVAL_REFERENCE.md", "_from_tr_STRING_HARMONIC_INTERVAL_REFERENCE.md"),
        (root / "_from_tr_TIMBRAL_AFFINITY_LITERATURE_AUDIT.md", root / "docs" / "TIMBRAL_AFFINITY_LITERATURE_AUDIT.md", "_from_tr_TIMBRAL_AFFINITY_LITERATURE_AUDIT.md"),
        (root / "_from_transcript_README.md", root / "README.md", "_from_transcript_README.md"),
        # HOMOGENEITY master: transcript snapshot matches Cursor agent Write payload (no separate backup on disk)
        (root / "docs" / "_from_transcript_MASTER.md", root / "docs" / "HOMOGENEITY_ANALYSER_MASTER_DOCUMENT.md", "docs/_from_transcript_MASTER.md"),
    ]

    for src, dst, label in copies:
        if not src.is_file():
            print("SKIP missing source:", label)
            continue
        shutil.copy2(src, dst)
        print("RESTORED", dst.relative_to(root), "<-", label)

    # README: keep H_TI schema note aligned with code (surgical text replace, not formula conversion)
    readme = root / "README.md"
    if readme.is_file():
        t = readme.read_text(encoding="utf-8", errors="replace")
        old = "- **JSON** — `schema_version` **2.2**, `time_series`, nested `dynamic_conditioning`, `warnings`."
        new = "- **JSON** — `schema_version` **2.7**, `time_series`, nested `dynamic_conditioning`, `warnings`."
        if old in t:
            readme.write_text(t.replace(old, new, 1), encoding="utf-8", newline="\n")
            print("PATCH README.md: H_TI JSON schema_version 2.2 -> 2.7 (transcript line)")

    # QUICK_REFERENCE: prefer backup (valid Markdown) if present
    qb = bak / "QUICK_REFERENCE.md"
    qdst = root / "QUICK_REFERENCE.md"
    if qb.is_file():
        shutil.copy2(qb, qdst)
        print("RESTORED", qdst.relative_to(root), "<-", "Homogeneity_analyser - Backup/QUICK_REFERENCE.md")

    # TECHNICAL_MANUAL: merge known-good repo transcript narrative + preserved appendix + preserved §19 tail from disk
    narrative_path = root / "docs" / "_from_transcript_NARRATIVE.md"
    appendix_path = root / "_appendix_d_extract.md"
    tech_dst = root / "TECHNICAL_MANUAL.md"
    if narrative_path.is_file() and appendix_path.is_file() and tech_dst.is_file():
        narrative = narrative_path.read_text(encoding="utf-8", errors="replace")
        appendix = appendix_path.read_text(encoding="utf-8", errors="replace")
        corrupt = tech_dst.read_text(encoding="utf-8", errors="replace")
        j = corrupt.find("## 19) Bibliography")
        if j == -1:
            print("ERROR: cannot find ## 19) Bibliography in TECHNICAL_MANUAL.md", file=sys.stderr)
            return 3
        tail = corrupt[j:].lstrip("\n")
        out = narrative.rstrip() + "\n\n" + appendix.rstrip() + "\n\n" + tail.rstrip() + "\n"
        tech_dst.write_text(out, encoding="utf-8", newline="\n")
        print(
            "RESTORED TECHNICAL_MANUAL.md <- docs/_from_transcript_NARRATIVE.md + "
            "_appendix_d_extract.md + on-disk tail from ## 19) Bibliography"
        )
    else:
        print("NOTE: TECHNICAL_MANUAL.md not merged (missing narrative or appendix extract).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
