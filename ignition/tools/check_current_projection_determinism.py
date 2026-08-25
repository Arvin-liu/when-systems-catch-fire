#!/usr/bin/env python3
"""Check Current Facts, Snapshot and Surface Compiler outputs twice in memory.

Unlike the historical Task134 receipt writer, this Task135 preflight check never
rewrites a projection while checking it.  It compares two fresh derivations and
then compares the derivation with the committed bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from tools import build_current_snapshot as snapshot
    from tools import current_surface_compiler as compiler
    from tools import generate_current_facts as facts
except ModuleNotFoundError:
    import build_current_snapshot as snapshot
    import current_surface_compiler as compiler
    import generate_current_facts as facts


SURFACE_CONTRACT = ROOT / "data/operations/current-surface-block-contract-r1.json"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def derive() -> dict[str, bytes]:
    contract = facts.load_json(facts.CONTRACT_PATH)
    projection = facts.build_projection(contract)
    current_snapshot = snapshot.build_snapshot()
    surface_contract = compiler.load_json(SURFACE_CONTRACT)
    outputs = {
        facts.relative(facts.FACTS_PATH): facts.render_json(projection),
        facts.relative(facts.FACTS_MARKDOWN_PATH): facts.render_markdown(projection),
        snapshot.relative(snapshot.SNAPSHOT_PATH): snapshot.render(current_snapshot),
    }
    for surface in surface_contract["surfaces"]:
        path = REPO_ROOT / surface["path"]
        outputs[surface["path"]] = compiler.compile_surface(
            path.read_text(encoding="utf-8"), surface, current_snapshot
        ).encode("utf-8")
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    first = derive()
    second = derive()
    errors: list[str] = []
    if first != second:
        errors.append("two in-memory derivations differ")
    for relative, expected in first.items():
        path = REPO_ROOT / relative
        if not path.is_file() or path.read_bytes() != expected:
            errors.append(f"stale or missing Current projection: {relative}")
    if errors:
        print("CURRENT_PROJECTION_DETERMINISM_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"CURRENT_PROJECTION_DETERMINISM_OK passes=2 outputs={len(first)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
