#!/usr/bin/env python3
"""R0 reproduction for RB09-CALLER-ASSERTED-SEMANTICS.

This script captures the DEFECT STATE of the r2 engine (commit 68ea9bf4...).
It builds a capability bundle whose *record values and evidence content
contradict the consumer's rules* (i.e. the bundle is semantically FALSE), yet
whose Git evidence binding is perfectly valid and whose rule_assertions
reference registered evidence.

The r2 engine never inspects record values or evidence content for rule
satisfaction: it only checks (a) evidence registration + git-object binding and
(b) rule_assertions coverage + evidence_refs registration. Therefore it returns
GATE_PASS (exit 0) for a semantically-false bundle. That is the unclosed defect.

Run with the managed Python:
  /Users/zhiyuan/.workbuddy/binaries/python/envs/default/bin/python \
      tests/repro_rb09_caller_asserted_semantics.py

This script is a committed historical artifact. After the R1 hardening adds the
task-specific evaluator layer, the engine recomputes predicates from record
values + evidence bytes and such a bundle is rejected. Do NOT extend this script
to the hardened engine; it deliberately exercises the pre-fix _validate_evidence_and_rules
3-tuple contract.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "governance"))
import structured_capability_gate as eng  # noqa: E402


def _real(path):
    head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    blob = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", f"{head}:{path}"],
        capture_output=True, text=True,
    ).stdout.strip()
    content = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{head}:{path}"], capture_output=True
    ).stdout
    sha = "sha256:" + hashlib.sha256(content).hexdigest()
    return head, blob, sha


def main():
    # A real file in the repo, bound to a real commit.
    path = "tools/governance/structured_capability_gate.py"
    head, blob, sha = _real(path)

    config = {
        "capability": "repro_rb09",
        "parent_id": "TASK_REPRO",
        "parent_head": head,
        "rules": ["R_INTEGRITY_OK", "R_EVIDENCE_PRESENT"],
        "forbidden_claims": ["global", "deployed"],
        "schema": "ignored-for-repro",
    }

    # Evidence is git-valid. declared_role/record_type are well-formed.
    eid = "ev_real_file"
    evidence = [{
        "evidence_id": eid,
        "declared_role": "source_of_truth",
        "record_type": "text",
        "commit_sha": head,
        "repository_relative_path": path,
        "blob_sha": blob,
        "sha256": sha,
        "exact_head": head,
    }]

    # SEMANTICALLY FALSE bundle:
    #  - R_INTEGRITY_OK expects the record "integrity_check" to equal "verified",
    #    but we assert the OPPOSITE value "BROKEN".
    #  - R_EVIDENCE_PRESENT expects a non-empty artifact list, but we supply empty.
    # The r2 engine ignores these record values entirely, so it still passes.
    bundle = {
        "task_id": "TASK_REPRO",
        "parent_binding": {"task_id": "TASK_REPRO", "exact_head": head},
        "evidence_registry": evidence,
        "records": {
            "integrity_check": {
                "status": "PASS",
                "value": "BROKEN",  # contradicts R_INTEGRITY_OK
                "evidence_refs": [eid],
            },
            "artifact_list": {
                "status": "PASS",
                "value": [],  # contradicts R_EVIDENCE_PRESENT (expects non-empty)
                "evidence_refs": [eid],
            },
        },
        "facts": {"R_INTEGRITY_OK": True, "R_EVIDENCE_PRESENT": True},
        "rule_assertions": [
            {"rule_id": "R_INTEGRITY_OK", "evidence_refs": [eid]},
            {"rule_id": "R_EVIDENCE_PRESENT", "evidence_refs": [eid]},
        ],
        "conclusion": {
            "statement": "repro candidate",
            "claim_ceiling": "candidate_only",
            "history_preserved": True,
            "external_action_performed": False,
        },
    }

    # Pre-fix contract: _validate_evidence_and_rules returns (code, name, errors).
    code, name, errors = eng._validate_evidence_and_rules(config, bundle)
    print("=== R0 RB09-CALLER-ASSERTED-SEMANTICS reproduction ===")
    print(f"engine returned: code={code} name={name}")
    print(f"errors: {errors}")
    if code == 0 and name == "GATE_PASS":
        print(
            "DEFECT REPRODUCED: r2 engine returned GATE_PASS for a "
            "SEMANTICALLY-FALSE bundle (record values contradict the rules, "
            "but the engine never recomputed predicates from record values/"
            "evidence content). RB09-CALLER-ASSERTED-SEMANTICS is NOT closed."
        )
        return 0
    print(
        "NOTE: engine did NOT return GATE_PASS (code=%s). If this is the hardened "
        "engine, the defect is already closed." % code
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
