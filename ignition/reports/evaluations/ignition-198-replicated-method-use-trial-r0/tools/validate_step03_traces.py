#!/usr/bin/env python3
"""Validate Task198 Method-Use Trace R0 reuse and broken-control boundaries."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "trace-manifest.json"
DIGEST_PATH = ROOT / "trace-manifest.sha256"
SCHEMA = ROOT.parent / "ignition-190-method-use-trace-r0" / "schema" / "method-use-trace-r0.schema.json"
VALIDATOR = ROOT.parent / "ignition-190-method-use-trace-r0" / "tools" / "validate_method_use_trace_r0.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_validator(path: Path, expect_invalid: bool) -> str:
    command = [sys.executable, str(VALIDATOR), str(path)]
    if expect_invalid:
        command.append("--expect-invalid")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, (path, result.stdout, result.stderr)
    return result.stdout.strip()


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["task_id"] == "IGNITION-20260921-198"
    assert manifest["method_family"]["schema_path"] == "ignition/reports/evaluations/ignition-190-method-use-trace-r0/schema/method-use-trace-r0.schema.json"
    assert sha256(SCHEMA) == manifest["method_family"]["schema_sha256"]
    assert sha256(VALIDATOR) == manifest["method_family"]["validator_sha256"]
    history = ROOT / manifest["method_family"]["history_path"]
    provenance = ROOT / manifest["method_family"]["provenance_path"]
    assert sha256(history) == manifest["method_family"]["history_sha256"]
    assert sha256(provenance) == manifest["method_family"]["provenance_sha256"]

    forbidden_excerpt_keys = (
        '"selected_candidate_ref"',
        '"used_candidate_ref"',
        '"input_ref"',
        '"expected_observation"',
        '"use_segment_ref"',
        '"revision_type"',
        '"disposition"',
    )
    for case in manifest["cases"]:
        facts = ROOT / case["facts_path"]
        trace = ROOT / case["method_trace_path"]
        excerpt = ROOT / case["trace_excerpt_path"]
        assert sha256(facts) == case["facts_sha256"]
        assert sha256(trace) == case["method_trace_sha256"]
        assert sha256(excerpt) == case["trace_excerpt_sha256"]
        assert run_validator(trace, expect_invalid=False).startswith("VALID:")
        assert run_validator(excerpt, expect_invalid=True).startswith("EXPECTED_INVALID:")
        excerpt_text = excerpt.read_text(encoding="utf-8")
        assert not any(key in excerpt_text for key in forbidden_excerpt_keys)
        trace_data = json.loads(trace.read_text(encoding="utf-8"))
        assert len(trace_data["segments"]) == 6
        assert trace_data["segments"][0]["source_sha256"] == manifest["method_family"]["history_sha256"]
        assert trace_data["segments"][4]["source_sha256"] == case["facts_sha256"]

    digest_line = DIGEST_PATH.read_text(encoding="utf-8").strip().split()
    assert digest_line[1] == "trace-manifest.json"
    assert digest_line[0] == sha256(MANIFEST_PATH)
    print("TASK198_STEP03_METHOD_TRACE_R0_REUSE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
