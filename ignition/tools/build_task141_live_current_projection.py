#!/usr/bin/env python3
"""Materialize the Task141 canonical R3 live Current projection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_federation.live_current_projection import LIVE_CURRENT_PROJECTION_SCHEMA, build_live_current_projection, validate_projection


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
RECONCILIATION = ROOT / "data/operations/iterations/140/live-reconciliation-events-r1.jsonl"
OBSERVATION = ROOT / "data/operations/iterations/140/live-observation-events-r1.jsonl"
INFERENCE = ROOT / "data/operations/iterations/141/live-inference-observation-events-r1.jsonl"
RECONCILIATION_REF = Path("ignition/data/operations/iterations/140/live-reconciliation-events-r1.jsonl")
OBSERVATION_REF = Path("ignition/data/operations/iterations/140/live-observation-events-r1.jsonl")
INFERENCE_REF = Path("ignition/data/operations/iterations/141/live-inference-observation-events-r1.jsonl")
OUTPUT = ROOT / "data/operations/iterations/141/live-current-projection-r3.json"


def render(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build() -> dict:
    projection = build_live_current_projection(
        LEDGER,
        source_path="ignition/data/operations/iterations/139/live-attempt-ledger.jsonl",
        projection_schema=LIVE_CURRENT_PROJECTION_SCHEMA,
        reconciliation_events_path=RECONCILIATION_REF,
        observation_events_path=OBSERVATION_REF,
        inference_observation_events_path=INFERENCE_REF,
    )
    return validate_projection(projection)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.write:
        parser.error("--write is required")
    projection = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(render(projection))
    print(f"TASK141_R3_PROJECTION_WRITTEN digest={projection['projection_digest']} attempts={projection['counts']['total_attempts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
