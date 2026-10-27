#!/usr/bin/env python3
"""Validate Evaluation Evidence R0.1 contracts and frozen Task180 inputs."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.tools import evaluation_plane_r0_1 as plane  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_receipt(path: Path) -> dict:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    plane.validate_evidence_artifact(artifact)
    return artifact


def verify_source_ref(reference: dict) -> None:
    ref, path = reference["ref"], reference["path"]
    result = subprocess.run(
        ["git", "rev-parse", f"{ref}:{path}"], cwd=REPO_ROOT,
        text=True, capture_output=True, check=False,
    )
    require(result.returncode == 0, f"Task180 evidence ref unavailable: {ref}:{path}")
    require(result.stdout.strip() == reference["git_blob_sha"], f"Task180 Git blob mismatch: {path}")
    raw = subprocess.check_output(["git", "cat-file", "blob", reference["git_blob_sha"]], cwd=REPO_ROOT)
    require(hashlib.sha256(raw).hexdigest() == reference["sha256"], f"Task180 raw SHA256 mismatch: {path}")


def main() -> int:
    plane.validate_contract()
    bootstrap = validate_receipt(ROOT / "evaluation/bootstrap-receipt-r0.1.json")
    task180 = validate_receipt(ROOT / "evaluation/task180-adjudication-input-r0.1.json")
    require(bootstrap["status"] == "BOOTSTRAP_PREFLIGHT_PASS", "bootstrap status drift")
    require(task180["source"]["ref"] == "81c8ccc48d9db9a2932f178e2cc3cf32bcd26a06", "Task180 head drift")
    require(task180["finding_summary"]["evaluator_verdict"] == "R0_INHERITANCE_EVIDENCE_PARTIAL", "Task180 verdict drift")
    require(task180["authority_summary"]["general_cognitive_inheritance"] == "NOT_ESTABLISHED", "claim ceiling drift")
    require(task180["authority_summary"]["r1"] == "NOT_AUTHORIZED", "R1 boundary drift")
    require(task180["authority_summary"]["source_verdict_owner_gpt_adjudication_field"] == "NOT_YET_RUN", "Owner/GPT artifact field drift")
    require(task180["ci_snapshot"] == [
        {"workflow": "architecture-pages", "run_id": 35191224296, "conclusion": "SUCCESS"},
        {"workflow": "repository-path-accounting-preflight", "run_id": 35191224309, "conclusion": "FAILURE"},
        {"workflow": "foundation-validation", "run_id": 35191224321, "conclusion": "FAILURE"},
    ], "Task180 official CI snapshot drift")
    verify_source_ref(bootstrap["source"])
    verify_source_ref(task180["source"])
    for evidence in task180["evidence_refs"]:
        verify_source_ref(evidence)

    policy = json.loads((ROOT / "data/foundation/knowledge-corpus-admission-policy.json").read_text(encoding="utf-8"))
    rule = next((row for row in policy["rules"] if row["classification"] == "EVALUATION_EVIDENCE_ONLY"), None)
    require(rule is not None and set(rule["prefixes"]) == {"evaluation/", "reports/evaluations/"}, "evaluation admission path policy drift")
    require(policy["classes"]["EVALUATION_EVIDENCE_ONLY"].get("auto_discovery") is False, "evaluation evidence became auto-discoverable")
    category, _ = __import__("tools.foundation.validate_repository_path_classification", fromlist=["classify"]).classify("ignition/reports/evaluations/fixture/result.json")
    require(category == "EVALUATION_EVIDENCE", "evaluation path classification drift")

    manifest_tool = ROOT / "evaluation/heldout/r0.1/build_packet_manifest.py"
    result = subprocess.run([sys.executable, str(manifest_tool), "--check"], cwd=REPO_ROOT, text=True, capture_output=True)
    require(result.returncode == 0, "held-out successor manifest invalid: " + result.stdout + result.stderr)
    print("EVALUATION_PLANE_R0_1_VALID; TASK180_INPUTS_HASHED; SUCCESSOR_NOT_RUN; EVALUATOR_NOT_RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
