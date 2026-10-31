#!/usr/bin/env python3
"""Emit a bounded, offline, proposal-only Goal intake preflight receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
IGNITION_ROOT = HERE.parents[1]
sys.path.insert(0, str(IGNITION_ROOT))

from research_os_v1.g1_goal_intake.preflight import evaluate_request  # noqa: E402


TOOL_ID = "research.preflight_g1_goal_intake"
TOOL_VERSION = "0.1.0"
MAX_INPUT_BYTES = 1_000_000
CLAIM_CEILING = (
    "Offline structural preflight of caller-supplied, untrusted Goal proposal bytes only. "
    "No owner identity, trust root, live Current state, canonical Goal activation, completion, "
    "approval receipt, dispatch, truth, or scientific validity is established."
)


def build_receipt(raw_request: bytes) -> dict[str, object]:
    """Project one exact request byte string and bind this wrapper source."""

    report = evaluate_request(raw_request)
    return {
        "schema": "ignition.toolbox.g1_goal_intake.receipt.v1",
        "tool_id": TOOL_ID,
        "tool_version": TOOL_VERSION,
        "wrapper_source_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
        "preflight_report": report,
        "claim_ceiling": CLAIM_CEILING,
        "execution_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", required=True, help="read one bounded UTF-8 JSON request from stdin")
    parser.parse_args(argv)
    raw_request = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    try:
        receipt = build_receipt(raw_request)
    except (OSError, TypeError, ValueError, KeyError, RecursionError) as exc:
        print("G1_GOAL_INTAKE_PREFLIGHT_UNAVAILABLE: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
    # A zero exit means a report was emitted. The machine report carries the
    # preflight status; no status can authorize a Goal or a dispatch.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
