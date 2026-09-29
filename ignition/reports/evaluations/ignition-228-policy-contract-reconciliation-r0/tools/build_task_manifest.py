#!/usr/bin/env python3
"""Write SHA256SUMS for every Task228 subtree file except the manifest itself."""
from __future__ import annotations

import hashlib
from pathlib import Path

TASK228 = Path(__file__).resolve().parents[1]
MANIFEST = TASK228 / "SHA256SUMS"


def main() -> None:
    rows = []
    for path in sorted(TASK228.rglob("*")):
        if not path.is_file() or path == MANIFEST or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(TASK228).as_posix()
        rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    MANIFEST.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"TASK228_MANIFEST_ENTRIES={len(rows)}")


if __name__ == "__main__":
    main()
