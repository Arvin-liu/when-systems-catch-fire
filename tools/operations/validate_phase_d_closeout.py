#!/usr/bin/env python3
"""Independent machine validator for the Q32I Phase D closeout report."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports/operations/121Q32I-phase-d-validation-closeout.json"
MARKDOWN = ROOT / "reports/operations/121Q32I-phase-d-validation-closeout.md"
Q29R = ROOT / "docs/publication/works/when-an-army-believes-its-own-back.md"
Q32_CLOSURE = ROOT / "data/operations/propagation/121Q32-closure.json"

EXPECTED_CHAIN = [
    ("A", "9bfba4bd03d1dff0b266940fe3964e770314d131", "4097e610eebfc65c739df4fe7d2900161c204a9d"),
    ("B", "989990dad83c778147a8f9e7ca6f9d8ddc0acd27", "9bfba4bd03d1dff0b266940fe3964e770314d131"),
    ("A1", "671fc5d8884cff78238ab80eed87f36d6187ca29", "989990dad83c778147a8f9e7ca6f9d8ddc0acd27"),
    ("B1", "c8e3e009671e0a21e00f66308e953127f41745d0", "671fc5d8884cff78238ab80eed87f36d6187ca29"),
    ("C", "3d8a90db164a4e41672e25adf1a7b824aba37e14", "c8e3e009671e0a21e00f66308e953127f41745d0"),
    ("D1", "aa9971d52287833beb728567f3c4c952d33778f2", "3d8a90db164a4e41672e25adf1a7b824aba37e14"),
    ("D2", "cb280f2bc546e5703aed99f5836f5a7c8bcc6da9", "aa9971d52287833beb728567f3c4c952d33778f2"),
    ("D3", "4dd038bd3caf5483c8bf3833a0382ed5bb3e2b8a", "cb280f2bc546e5703aed99f5836f5a7c8bcc6da9"),
]
EXPECTED_Q29R = "c135acd35a2232f0a6b3f933db482932a9fe5d5add51f870af97901faac90d4b"
REQUIRED = {
    "schema_version", "task_id", "candidate_head", "candidate_head_role", "parent_head",
    "preserved_commit_chain", "tests", "auxiliary_gates", "production_entrypoints",
    "stable_error_code_families", "q32_closure", "q29r", "forbidden_content_scan",
    "network_and_third_party", "lifecycle", "phase_e", "historical_f5_boundary",
    "evidence_basis", "validity_basis", "artifact_inventory", "markdown_report",
    "markdown_digest", "report_digest", "claim_ceiling",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def report_digest(document: dict[str, Any]) -> str:
    payload = copy.deepcopy(document)
    payload.pop("report_digest", None)
    return sha256_bytes(canonical(payload))


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    reason: str

    def value(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "reason": self.reason}


def _test_count(path: Path) -> int:
    return len(re.findall(r"^\s+def (test_[A-Za-z0-9_]+)\(", path.read_text(encoding="utf-8"), re.MULTILINE))


def _matrix_count(path: Path, prefix: str) -> int:
    return len(re.findall(rf"^\| {re.escape(prefix)}[^|]+\|", path.read_text(encoding="utf-8"), re.MULTILINE))


def _git_parent(root: Path, commit: str) -> str | None:
    result = subprocess.run(
        ["git", "show", "-s", "--format=%P", commit], cwd=root, text=True, capture_output=True, shell=False
    )
    if result.returncode:
        return None
    parents = result.stdout.strip().split()
    return parents[0] if len(parents) == 1 else None


def validate_closeout(document: dict[str, Any], *, root: Path = ROOT, markdown_path: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    markdown_path = markdown_path or root / "reports/operations/121Q32I-phase-d-validation-closeout.md"
    issues: list[Issue] = []

    def add(code: str, path: str, reason: str) -> None:
        issues.append(Issue(code, path, reason))

    missing = sorted(REQUIRED - set(document))
    if missing:
        add("E_D4_REQUIRED_FIELD", "$", f"missing fields: {missing}")
    if document.get("schema_version") != "1.0.0" or document.get("task_id") != "121Q32I-D4":
        add("E_D4_SCHEMA", "$", "schema version and task id must identify the D4 closeout")

    expected_entrypoints = [
        "tools/operations/generate_component_profiles.py",
        "tools/operations/validate_component_profiles.py",
        "tools/operations/plan_incremental_execution.py",
        "tools/operations/run_incremental_execution.py",
        "tools/operations/validate_incremental_execution.py",
        "tools/operations/compute_change_propagation.py",
        "tools/operations/validate_phase_d_closeout.py",
    ]
    if document.get("production_entrypoints") != expected_entrypoints or any(not (root / path).is_file() for path in expected_entrypoints):
        add("E_D4_ENTRYPOINT", "production_entrypoints", "all ordered production entrypoints must exist")
    auxiliary = document.get("auxiliary_gates", {})
    expected_auxiliary = {
        "canonical_plan_determinism", "dangerous_dynamic_execution_scan", "forbidden_asset_scan",
        "git_diff_check", "local_path_secret_private_key_scan", "production_change_propagation_check",
        "profile_generator_check", "profile_validator", "temporary_artifact_scan",
    }
    if not isinstance(auxiliary, dict) or set(auxiliary) != expected_auxiliary or any(value != "PASS" for value in auxiliary.values()):
        add("E_D4_AUXILIARY_GATE", "auxiliary_gates", "all required auxiliary gates must be explicit PASS")
    error_families = document.get("stable_error_code_families", [])
    if not isinstance(error_families, list) or not {"E_PLAN_*", "E_EXECUTION_*", "E_CACHE_*", "E_RECOVERY_*", "E_D4_*"} <= set(error_families):
        add("E_D4_ERROR_CODE_FAMILY", "stable_error_code_families", "required stable error-code families are missing")

    expected_chain = [{"phase": phase, "commit": commit, "parent": parent} for phase, commit, parent in EXPECTED_CHAIN]
    if document.get("preserved_commit_chain") != expected_chain:
        add("E_D4_COMMIT_CHAIN", "preserved_commit_chain", "chain must exactly match A through D3")
    for phase, commit, parent in EXPECTED_CHAIN:
        actual_parent = _git_parent(root, commit)
        if actual_parent != parent:
            add("E_D4_GIT_PARENT", f"preserved_commit_chain.{phase}", f"expected parent {parent}, got {actual_parent}")
    if document.get("candidate_head") != EXPECTED_CHAIN[-1][1] or document.get("parent_head") != EXPECTED_CHAIN[-1][2]:
        add("E_D4_CANDIDATE_IDENTITY", "candidate_head", "observed candidate and parent must be exact D3 and D2")
    if document.get("candidate_head_role") != "observed_identifier_only":
        add("E_D4_SELF_ATTESTATION", "candidate_head_role", "candidate HEAD may only be an observed identifier")

    source_counts = {
        "phase_a_profile": _test_count(root / "tests/test_component_profiles.py"),
        "phase_b_planner": _test_count(root / "tests/test_incremental_planner.py"),
        "phase_c_executor": _test_count(root / "tests/test_incremental_executor.py"),
        "phase_d1_validator": _test_count(root / "tests/test_incremental_execution_validator.py"),
        "phase_d2_acceptance": _test_count(root / "tests/test_incremental_execution.py"),
        "phase_d3_defensive": _test_count(root / "tests/test_incremental_execution_defensive_rejections.py"),
        "generated_output_authority": _test_count(root / "tests/test_generated_output_authority.py"),
        "tracked_symlink_gate": _test_count(root / "tests/test_tracked_symlink_gate.py"),
        "phase_d4_closeout": _test_count(root / "tests/test_phase_d_closeout.py"),
    }
    tests = document.get("tests", {})
    for key, expected in source_counts.items():
        value = tests.get(key, {}) if isinstance(tests, dict) else {}
        if value.get("count") != expected or value.get("passed") != expected or value.get("result") != "PASS":
            add("E_D4_TEST_COUNT", f"tests.{key}", f"expected {expected}/{expected} PASS")
    aggregate = sum(source_counts.values())
    aggregate_value = tests.get("aggregate", {}) if isinstance(tests, dict) else {}
    if aggregate_value.get("count") != aggregate or aggregate_value.get("passed") != aggregate or aggregate_value.get("result") != "PASS":
        add("E_D4_TEST_AGGREGATE", "tests.aggregate", f"expected {aggregate}/{aggregate} PASS")
    if _matrix_count(root / "tests/PHASE-D-ACCEPTANCE-MATRIX.md", "D2-") != source_counts["phase_d2_acceptance"]:
        add("E_D4_MATRIX_COUNT", "tests.phase_d2_acceptance", "D2 matrix and tests differ")
    if _matrix_count(root / "tests/PHASE-D-DEFENSIVE-REJECTION-MATRIX.md", "G") != source_counts["phase_d3_defensive"]:
        add("E_D4_MATRIX_COUNT", "tests.phase_d3_defensive", "D3 matrix and tests differ")

    if document.get("report_digest") != report_digest(document):
        add("E_D4_REPORT_DIGEST", "report_digest", "deterministic report digest mismatch")
    if document.get("markdown_report") != "reports/operations/121Q32I-phase-d-validation-closeout.md":
        add("E_D4_MARKDOWN_PATH", "markdown_report", "Markdown report path mismatch")
    if not markdown_path.is_file() or document.get("markdown_digest") != sha256_file(markdown_path):
        add("E_D4_MARKDOWN_DIGEST", "markdown_digest", "Markdown report digest mismatch")
    else:
        markdown = markdown_path.read_text(encoding="utf-8")
        for required_text in (EXPECTED_CHAIN[-1][1], "D1 18/18", "D2 14/14", "D3 26/26", "Phase E: NOT_STARTED"):
            if required_text not in markdown:
                add("E_D4_MARKDOWN_CONSISTENCY", "markdown_report", f"missing report fact: {required_text}")

    closure = json.loads((root / "data/operations/propagation/121Q32-closure.json").read_text(encoding="utf-8"))
    if document.get("q32_closure", {}).get("closure_hash") != closure.get("closure_hash") or document.get("q32_closure", {}).get("production_check") != "PASS":
        add("E_D4_Q32_CLOSURE", "q32_closure", "closure hash or production check mismatch")
    if document.get("q29r", {}).get("sha256") != EXPECTED_Q29R or sha256_file(root / "docs/publication/works/when-an-army-believes-its-own-back.md") != EXPECTED_Q29R:
        add("E_D4_Q29R_HASH", "q29r.sha256", "Q29R frozen hash mismatch")

    lifecycle = document.get("lifecycle", {})
    if lifecycle != {"state": "candidate_only", "accepted": False, "merged": False, "current": False}:
        add("E_D4_LIFECYCLE", "lifecycle", "Phase D report must remain candidate-only")
    if document.get("phase_e") != {"state": "NOT_STARTED", "pr_created": False, "merge_performed": False}:
        add("E_D4_PHASE_E", "phase_e", "Phase E, PR, and merge must remain unstarted")
    if document.get("historical_f5_boundary", {}).get("status") != "DEFERRED_TO_PHASE_E_NOT_RUN":
        add("E_D4_F5_BOUNDARY", "historical_f5_boundary.status", "historical F5 must not be claimed PASS in D4")

    evidence_text = json.dumps(document.get("evidence_basis", {}), sort_keys=True)
    validity_text = json.dumps(document.get("validity_basis", []), sort_keys=True)
    if EXPECTED_CHAIN[-1][1] in evidence_text or re.search(r"\bHEAD\b", evidence_text + validity_text, re.IGNORECASE):
        add("E_D4_SELF_ATTESTATION", "evidence_basis", "current/candidate HEAD cannot establish report validity")
    for raw, expected in document.get("evidence_basis", {}).items() if isinstance(document.get("evidence_basis"), dict) else []:
        path = root / raw
        if not path.is_file() or sha256_file(path) != expected:
            add("E_D4_EVIDENCE_DIGEST", f"evidence_basis.{raw}", "evidence file digest mismatch")

    raw_document = json.dumps(document, ensure_ascii=False)
    if re.search(r"/Users/|[A-Za-z]:\\", raw_document):
        add("E_D4_LOCAL_PATH", "$", "local absolute path is forbidden")
    if re.search(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}", raw_document):
        add("E_D4_SECRET", "$", "secret or private-key material is forbidden")
    artifacts = document.get("artifact_inventory", [])
    if not isinstance(artifacts, list):
        add("E_D4_ARTIFACT_INVENTORY", "artifact_inventory", "must be an array")
        artifacts = []
    for index, raw in enumerate(artifacts):
        if not isinstance(raw, str) or raw.startswith("/") or ".." in Path(raw).parts:
            add("E_D4_ARTIFACT_PATH", f"artifact_inventory[{index}]", "artifact must be repository-relative")
            continue
        if re.search(r"(^|/)(?:\.cache|recovery-[^/]*)(?:/|$)", raw, re.IGNORECASE):
            add("E_D4_TEMP_ARTIFACT", f"artifact_inventory[{index}]", "cache/recovery temporary artifact forbidden")
        if re.search(r"(^|/)(?:q3[3-9]|q40|lab|shadow|phase[-_]?e)(?:/|$)", raw, re.IGNORECASE):
            add("E_D4_UNAUTHORIZED_ASSET", f"artifact_inventory[{index}]", "unauthorized phase or experiment asset")
    if document.get("forbidden_content_scan", {}).get("result") != "PASS":
        add("E_D4_FORBIDDEN_SCAN", "forbidden_content_scan", "forbidden-content scan must pass")
    network = document.get("network_and_third_party", {})
    if network.get("network_access") != "NONE" or network.get("third_party_targets") != "NONE" or network.get("credential_operations") != "NONE" or network.get("privilege_operations") != "NONE":
        add("E_D4_NETWORK_BOUNDARY", "network_and_third_party", "all external and privileged operations must be NONE")

    return {
        "ok": not issues,
        "validator": "Q32I-D4-phase-d-closeout-validator",
        "error_count": len(issues),
        "errors": [issue.value() for issue in issues],
        "observed_test_count": aggregate,
        "summary": "PASS: Phase D closeout is valid" if not issues else f"FAIL: {len(issues)} Phase D closeout error(s)",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--markdown", type=Path, default=MARKDOWN)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        document = json.loads(args.report.read_text(encoding="utf-8"))
        result = validate_closeout(document, root=args.root, markdown_path=args.markdown)
    except Exception as exc:
        result = {
            "ok": False,
            "validator": "Q32I-D4-phase-d-closeout-validator",
            "error_count": 1,
            "errors": [{"code": "E_D4_VALIDATOR_EXCEPTION", "path": "$", "reason": f"{type(exc).__name__}: {exc}"}],
            "summary": "FAIL: Phase D closeout validator exception",
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print(result["summary"], file=sys.stderr)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
