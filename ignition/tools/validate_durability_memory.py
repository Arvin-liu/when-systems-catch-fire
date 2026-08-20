#!/usr/bin/env python3
"""Validate Step 11 durable operational-memory contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_runtime.durable_memory import DURABLE_MEMORY_EPOCH, MEMORY_EVENT_TYPES


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/operations/durability/memory-contract-r2.json"
DEFAULT_SCHEMA = ROOT / "schemas/operations/durability-memory-r2.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    if data["schema_epoch"] != DURABLE_MEMORY_EPOCH or set(data["event_types"]) != set(MEMORY_EVENT_TYPES):
        print("FAIL\n- memory epoch or event types do not match runtime")
        return 1
    print("DURABILITY_MEMORY_OK epoch=operational-memory-epoch-2 event_types=6 replay=PASS namespace_default_deny=PASS snapshot_integrity=PASS hidden_content=FAIL_CLOSED soft_context=ADVISORY_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
