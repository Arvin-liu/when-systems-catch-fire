#!/usr/bin/env python3
"""Render a bounded Driver Console snapshot from a JSON source bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.driver_console import build_driver_snapshot, render_driver_console


def main() -> int:
    parser = argparse.ArgumentParser(prog="driver-console")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--json", action="store_true", dest="json_mode")
    args = parser.parse_args()
    snapshot = build_driver_snapshot(json.loads(args.input.read_text(encoding="utf-8")))
    if args.json_mode:
        print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
    else:
        print(render_driver_console(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
