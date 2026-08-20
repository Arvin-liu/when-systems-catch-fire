#!/usr/bin/env python3
"""Fail-closed validator for advisory soft-governance durability semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_runtime.soft_governance_durability import validate_soft_state


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/soft-governance-durability-r1.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    errors = validate_soft_state(json.loads(args.data.read_text(encoding="utf-8")))
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("DURABILITY_SOFT_GOVERNANCE_OK status=ADVISORY_ONLY hard_effects=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
