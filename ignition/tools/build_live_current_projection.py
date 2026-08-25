#!/usr/bin/env python3
"""Build/check the deterministic Current live-attempt projection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from agent_federation.live_current_projection import build_live_current_projection, validate_projection


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DEFAULT_LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
DEFAULT_OUTPUT_PATH = ROOT / "data/operations/iterations/139/live-current-projection-r1.json"


def render(projection: dict) -> bytes:
    return (json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def check(ledger_path: Path, output_path: Path) -> list[str]:
    expected = render(build_live_current_projection(ledger_path))
    if not output_path.is_file():
        return [f"missing projection: {output_path}"]
    try:
        validate_projection(json.loads(output_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        return [f"projection unreadable: {exc}"]
    return [] if output_path.read_bytes() == expected else [f"stale projection: {output_path}"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("choose exactly one of --write or --check")
    if args.write:
        projection = build_live_current_projection(args.ledger)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(render(projection))
        print(f"LIVE_CURRENT_PROJECTION_WRITTEN path={args.output} digest={projection['projection_digest']}")
        return 0
    errors = check(args.ledger, args.output)
    if errors:
        print("LIVE_CURRENT_PROJECTION_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    projection = json.loads(args.output.read_text(encoding="utf-8"))
    print(
        f"LIVE_CURRENT_PROJECTION_OK attempts={projection['counts']['total_attempts']} "
        f"unreconciled={projection['counts']['unreconciled_count']} "
        f"incomplete={projection['counts']['observation_incomplete_count']} "
        f"digest={projection['projection_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
