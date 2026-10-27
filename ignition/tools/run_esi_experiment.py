#!/usr/bin/env python3
"""Provider-neutral ESI runner: ingest normalized outputs, never invent live calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.score_esi_response import BENCHMARK, RUBRIC, score_records


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "data/epistemic-governance/experiment-protocol-r0.json"
PACKET = ROOT / "data/epistemic-governance/blind-evaluation-packet-r0.json"
ANNOTATION_SCHEMA = ROOT / "schemas/epistemic-governance/blind-annotation-schema-r0.schema.json"
PROTOCOL_SCHEMA = ROOT / "schemas/epistemic-governance/experiment-protocol-r0.schema.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_records(path: Path) -> list[dict]:
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = load(path)
    return payload if isinstance(payload, list) else payload.get("responses", [])


def validate_protocol(protocol: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(protocol)]
    if "E3_ORIGINAL_STRUCTURE" not in protocol.get("exposure_arms", []) or "C6_DELAYED_TRANSFER" not in protocol.get("challenge_arms", []):
        errors.append("protocol omits required original-structure or delayed-transfer arm")
    return sorted(set(errors))


def validate_response_record(record: dict, annotation_schema: dict) -> list[str]:
    return sorted(error.message for error in Draft202012Validator(annotation_schema).iter_errors(record))


def run(responses: list[dict] | None = None, provider: str = "none") -> dict:
    protocol = load(PROTOCOL)
    protocol_errors = validate_protocol(protocol, load(PROTOCOL_SCHEMA))
    if protocol_errors:
        raise ValueError("protocol invalid: " + "; ".join(protocol_errors))
    if responses is None:
        return {
            "schema_version": "esi-experiment-run-r0",
            "protocol_id": protocol["protocol_id"],
            "run_status": "READY_NOT_RUN",
            "execution_mode": "NO_LIVE_PROVIDER",
            "provider": provider,
            "live_model_status": "READY_NOT_RUN",
            "reason": "No safe explicit provider adapter or normalized response file was supplied.",
            "response_count": 0,
            "scores": [],
            "claim_ceiling": "Protocol readiness only; no ESI effect or live model behavior is established."
        }
    annotation_schema = load(ANNOTATION_SCHEMA)
    invalid = [(index, errors) for index, response in enumerate(responses) if (errors := validate_response_record(response, annotation_schema))]
    if invalid:
        raise ValueError("invalid normalized response records: " + json.dumps(invalid, ensure_ascii=False))
    benchmark = load(BENCHMARK)
    cases_by_code = {f"CASE-{index + 1:03d}": case for index, case in enumerate(sorted(benchmark["cases"], key=lambda item: item["case_id"]))}
    for response in responses:
        if response.get("case_code") not in cases_by_code:
            raise ValueError(f"unknown blind case code: {response.get('case_code')}")
        if any(key in response for key in ("exposure_arm", "challenge_arm", "case_id")):
            raise ValueError("normalized blind response leaks original arm or case labels")
    scores = score_records(responses, cases_by_code, {}, load(RUBRIC))
    return {
        "schema_version": "esi-experiment-run-r0",
        "protocol_id": protocol["protocol_id"],
        "run_status": "RUN",
        "execution_mode": "OFFLINE_RESPONSE_INGESTION",
        "provider": provider,
        "live_model_status": "NOT_RUN_LIVE_EXTERNAL",
        "reason": "Normalized response records were ingested; no external provider call was made by this runner.",
        "response_count": len(responses),
        "scores": scores,
        "claim_ceiling": "Offline ingestion and bounded scoring only; no ESI effect, external validity or authority is established."
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--responses", type=Path)
    parser.add_argument("--provider", default="none")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true", help="Record SKIPPED; this runner never initiates a live call.")
    args = parser.parse_args()
    if args.live:
        result = {
            "schema_version": "esi-experiment-run-r0",
            "protocol_id": load(PROTOCOL)["protocol_id"],
            "run_status": "SKIPPED",
            "execution_mode": "LIVE_REQUEST_NOT_EXECUTED",
            "provider": args.provider,
            "live_model_status": "SKIPPED_UNSAFE_OR_UNAVAILABLE",
            "reason": "This provider-neutral runner does not initiate live calls; supply a separately authorized adapter output.",
            "response_count": 0,
            "scores": [],
            "claim_ceiling": "No live model evidence is established."
        }
    else:
        result = run(read_records(args.responses), args.provider) if args.responses else run(None, args.provider)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
