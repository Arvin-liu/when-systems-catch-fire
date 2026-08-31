#!/usr/bin/env python3
"""Validate the immutable Task149 Step02 upstream observations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
ARTIFACT_PATH = ROOT / "data/operations/iterations/149/step02-upstream-freeze.json"
SCHEMA_PATH = ROOT / "schemas/operations/task149-step02-upstream-freeze-r0.schema.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(document: dict[str, Any] | None = None) -> list[str]:
    document = document if document is not None else load_json(ARTIFACT_PATH)
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(document)]
    upstreams = {entry.get("provider_candidate_id"): entry for entry in document.get("upstreams", [])}
    if upstreams.get("archify", {}).get("observed_main_sha") != "2bfb47132c057195d8dddb3e25ae966dd7c7a72e":
        errors.append("Archify must remain pinned to the freshly observed main SHA")
    if upstreams.get("agent-reach", {}).get("observed_main_sha") != "06c202b03400a7d31886bf4399213706da1a0324":
        errors.append("Agent Reach must remain pinned to the freshly observed main SHA")
    if upstreams.get("archify", {}).get("starting_clue_matches_observed") is not False:
        errors.append("Archify clue drift must remain visible")
    if upstreams.get("agent-reach", {}).get("starting_clue_matches_observed") is not True:
        errors.append("Agent Reach clue equality must remain recorded")
    if document.get("fresh_fetch_policy", {}).get("source_copied_into_ignition") is not False:
        errors.append("upstream source must not be copied into Ignition")
    if document.get("fresh_fetch_policy", {}).get("system_install_performed") is not False:
        errors.append("Step02 must not perform system installation")
    if upstreams.get("agent-reach", {}).get("health", {}).get("pinned_source_status") != "BLOCKED_DEPENDENCY":
        errors.append("Agent Reach pinned-source dependency blocker must remain explicit")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("TASK149_STEP02_UPSTREAM_FREEZE_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("TASK149_STEP02_UPSTREAM_FREEZE_OK archify=2bfb4713 agent_reach=06c202b0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
