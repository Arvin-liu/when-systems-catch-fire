#!/usr/bin/env python3
"""Create a review packet whose exposure and challenge labels are anonymized."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data/epistemic-governance/challenge-fixtures-r0.json"
OUT = ROOT / "data/epistemic-governance/blind-evaluation-packet-r0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_packet(fixtures: dict) -> dict:
    exposures = sorted({item["exposure_arm"] for item in fixtures["fixtures"]})
    challenges = sorted({item["challenge_arm"] for item in fixtures["fixtures"]})
    cases = sorted({item["case_id"] for item in fixtures["fixtures"]})
    exposure_codes = {value: f"EXP-{chr(65 + index)}" for index, value in enumerate(exposures)}
    challenge_codes = {value: f"CHAL-{index}" for index, value in enumerate(challenges)}
    case_codes = {value: f"CASE-{index + 1:03d}" for index, value in enumerate(cases)}
    units = []
    for item in fixtures["fixtures"]:
        units.append({
            "review_unit_id": f"UNIT-{len(units) + 1:03d}",
            "exposure_code": exposure_codes[item["exposure_arm"]],
            "challenge_code": challenge_codes[item["challenge_arm"]],
            "case_code": case_codes[item["case_id"]],
            "evidence_packet": item["evidence_packet"],
            "task_prompt": item["task_prompt"],
            "challenge_prompt": item["challenge_prompt"],
            "response_required": True,
            "model_output": None,
        })
    return {
        "schema_version": "blind-evaluation-packet-r0",
        "packet_id": "ESI-BLIND-R0",
        "reviewer_instruction": "Use exposure_code, challenge_code and case_code only; do not infer the original exposure label from this packet.",
        "units": units,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    packet = build_packet(load(FIXTURES))
    expected = (json.dumps(packet, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        if not args.output.is_file() or args.output.read_bytes() != expected:
            print("FAIL: blind packet is stale or missing")
            return 1
        print(f"BLIND_PACKET_DERIVED_OK units={len(packet['units'])} original_labels=HIDDEN")
        return 0
    if not args.write:
        print(json.dumps(packet, ensure_ascii=False, indent=2))
        return 0
    args.output.write_bytes(expected)
    print(f"BLIND_PACKET_WRITTEN units={len(packet['units'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
