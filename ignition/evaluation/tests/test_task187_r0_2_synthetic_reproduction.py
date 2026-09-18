from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

IGNITION_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))

from evaluation.tools import task_branch_guard_r0_2 as branch_guard  # noqa: E402
from evaluation.tools import validate_successor_read_ledger_r0_2 as ledger_validator  # noqa: E402


TASK_ID = "IGNITION-20260918-182-R2"
SOURCE_COMMIT = "047fb0ef0b4a734e42efb4a29b4e70b831ef0be4"
MANIFEST_REL = ledger_validator.MANIFEST_REL
COMPONENT_ID = "synthetic-final-read-ledger-validator"
COMPONENT_PATH = "synthetic/final-read-ledger-validator.py"
LOGIN = "Arvin-liu"
EMAIL = "49422864+Arvin-liu@users.noreply.github.com"
REPO_URL = "https://github.com/Arvin-liu/when-systems-catch-fire.git"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def synthetic_manifest(path: str = MANIFEST_REL) -> dict[str, Any]:
    return {
        "schema_version": "heldout-successor-packet-manifest-r0.2",
        "manifest_path": path,
        "cognitive_evidence_surface": {
            "files": [{"path": "synthetic/source.txt", "sha256": "1" * 64}]
        },
        "operational_control_surface": {
            "components": [
                {
                    "component_id": COMPONENT_ID,
                    "path": COMPONENT_PATH,
                    "successor_access": "EXECUTE_STATUS_ONLY",
                    "permitted_actions": ["EXECUTE", "OBSERVE_STATUS"],
                    "allowed_status_codes": [
                        ledger_validator.PASS,
                        ledger_validator.CONTAMINATED,
                        ledger_validator.INVALID,
                    ],
                }
            ]
        },
    }


def ledger_entry(
    *,
    action: str,
    path: str,
    component_id: str | None = None,
    content_exposure: str = "NO",
    case_specific: bool = False,
    digest: str | None = None,
    status: str | None = None,
    disposition: str = "CLEAN",
) -> dict[str, Any]:
    return {
        "path": path,
        "component_id": component_id,
        "action_kind": action,
        "purpose": "synthetic protocol reproduction",
        "content_exposure": content_exposure,
        "case_specific_information_exposed": case_specific,
        "digest": digest,
        "observed_status_code": status,
        "contamination_disposition": disposition,
    }


def make_ledger(
    entries: list[dict[str, Any]], manifest_bytes: bytes, *, trial_disposition: str = "CLEAN"
) -> dict[str, Any]:
    return {
        "schema_version": "successor-read-ledger-r0.2",
        "task_id": TASK_ID,
        "allowed_manifest_sha256": sha256(manifest_bytes),
        "entries": entries,
        "summary": {
            "cognitive_reads": sum(row["action_kind"] == "COGNITIVE_READ" for row in entries),
            "operational_executions": sum(row["action_kind"] == "OPERATIONAL_EXECUTION" for row in entries),
            "operational_status_observations": sum(
                row["action_kind"] == "OPERATIONAL_STATUS_OBSERVED" for row in entries
            ),
            "prohibited_cognitive_reads": sum(
                row["action_kind"] == "PROHIBITED_COGNITIVE_READ" for row in entries
            ),
            "contaminated_entries": sum(
                row["contamination_disposition"] == "CONTAMINATED" for row in entries
            ),
        },
        "trial_disposition": trial_disposition,
    }


def validate_synthetic(
    payload: dict[str, Any], manifest: dict[str, Any], manifest_bytes: bytes
) -> str:
    return ledger_validator.validate_payload(payload, manifest, manifest_bytes)


def operational_rows(status: str = ledger_validator.PASS) -> list[dict[str, Any]]:
    return [
        ledger_entry(
            action="OPERATIONAL_EXECUTION",
            path=COMPONENT_PATH,
            component_id=COMPONENT_ID,
        ),
        ledger_entry(
            action="OPERATIONAL_STATUS_OBSERVED",
            path=COMPONENT_PATH,
            component_id=COMPONENT_ID,
            status=status,
        ),
    ]


def closure_sequence(manifest: dict[str, Any], manifest_bytes: bytes) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    for invocation in range(1, 4):
        payload = make_ledger(entries, manifest_bytes)
        ledger_sha = sha256(canonical_bytes(payload))
        status = validate_synthetic(payload, manifest, manifest_bytes)
        runs.append(
            {
                "invocation": invocation,
                "input_entry_count": len(entries),
                "input_ledger_sha256": ledger_sha,
                "status": status,
            }
        )
        # R0.2 operational accounting records this invocation and its returned status.
        entries.extend(operational_rows(status))
    return {
        "runs": runs,
        "entry_counts_after_recording_each_invocation": [2, 4, 6],
        "all_invocations_return_clean": all(row["status"] == ledger_validator.PASS for row in runs),
        "each_recording_changes_the_certified_ledger": len(
            {row["input_ledger_sha256"] for row in runs}
        ) == len(runs),
        "finite_fixed_point": False,
    }


def run_guard_staging_fixture() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="task187-r0-2-guard-") as temp_dir:
        root = Path(temp_dir) / "repo"
        root.mkdir()

        def git(*args: str) -> str:
            result = subprocess.run(
                ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            return result.stdout.strip()

        git("init", "--initial-branch=main")
        git("config", "--local", "user.name", LOGIN)
        git("config", "--local", "user.email", EMAIL)
        marker = root / "ignition" / "AI-START-HERE.md"
        marker.parent.mkdir(parents=True)
        marker.write_text("synthetic repository marker\n", encoding="utf-8")
        synthetic_ledger = root / "synthetic-ledger.json"
        synthetic_ledger.write_text('{"cognitive_disposition":"CLEAN","entries":[]}\n', encoding="utf-8")
        git("add", "ignition/AI-START-HERE.md", "synthetic-ledger.json")
        git("commit", "-m", "synthetic base")
        base = git("rev-parse", "HEAD")

        branch = "work/IGNITION-20260918-187-r3-synthetic-guard"
        git("checkout", "-b", branch)
        git("remote", "add", "origin", REPO_URL)
        git("remote", "set-url", "--push", "origin", REPO_URL)
        git("config", "--local", "core.hooksPath", branch_guard.HOOKS_PATH)
        git("config", "--local", f"branch.{branch}.pushRemote", "origin")
        git("config", "--local", "push.default", "current")

        authorization = {
            "schema_version": "task-branch-authorization-r0.2",
            "authority": {
                "source_kind": "TEST_FIXTURE",
                "command_repository_full_name": "synthetic/control",
                "command_path": "synthetic/task.md",
                "command_ref": "a" * 40,
                "command_blob_sha": "b" * 40,
            },
            "repository_full_name": "Arvin-liu/when-systems-catch-fire",
            "task_id": "IGNITION-20260918-187-R3",
            "authorized_base_head": base,
            "authorized_branch": branch,
            "expected_push_remote": "origin",
            "expected_push_url": REPO_URL,
            "public_noreply_identity": {"login": LOGIN, "email": EMAIL},
            "allowed_operation_class": "TASK_BRANCH_COMMIT_AND_PUSH",
        }
        authorization_path = root / ".git" / "ignition" / "task-authorization.json"
        authorization_path.parent.mkdir(mode=0o700, parents=True)
        authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
        authorization_path.chmod(0o600)

        evidence = root / "synthetic-evidence.json"
        evidence.write_text('{"source":"synthetic"}\n', encoding="utf-8")
        before_stage = branch_guard.preflight(root, operation="COMMIT")
        git("add", "synthetic-evidence.json")
        after_stage = branch_guard.preflight(root, operation="COMMIT")

        synthetic_ledger.write_text(
            '{"cognitive_disposition":"CLEAN","entries":[{"status":"PASS_BRANCH_AUTHORIZED"}]}\n',
            encoding="utf-8",
        )
        after_status_record_added = branch_guard.preflight(root, operation="COMMIT")
        git("add", "synthetic-ledger.json")
        after_status_record_staged = branch_guard.preflight(root, operation="COMMIT")

        return {
            "untracked_evidence_status": before_stage,
            "staged_evidence_status": after_stage,
            "new_status_record_unstaged_status": after_status_record_added,
            "new_status_record_staged_status": after_status_record_staged,
            "cognitive_disposition_before_and_after": "CLEAN",
        }


def reproduction_summary() -> dict[str, Any]:
    manifest = synthetic_manifest()
    manifest_bytes = canonical_bytes(manifest)
    manifest_sha = sha256(manifest_bytes)
    cases: list[dict[str, Any]] = []

    def record(
        fixture_id: str,
        payload: dict[str, Any],
        current_manifest: dict[str, Any],
        current_manifest_bytes: bytes,
        expected: str,
    ) -> None:
        cases.append(
            {
                "fixture_id": fixture_id,
                "synthetic": True,
                "schema_valid": ledger_validator._validate_schema(payload),
                "expected_status": expected,
                "observed_status": validate_synthetic(payload, current_manifest, current_manifest_bytes),
            }
        )

    summary_mismatch = make_ledger([], manifest_bytes)
    summary_mismatch["summary"]["cognitive_reads"] = 1
    record("schema-valid-summary-mismatch", summary_mismatch, manifest, manifest_bytes, ledger_validator.INVALID)

    trial_mismatch = make_ledger([], manifest_bytes, trial_disposition="PROTOCOL_CONTAMINATED")
    record("schema-valid-trial-disposition-mismatch", trial_mismatch, manifest, manifest_bytes, ledger_validator.INVALID)

    row_mismatch = make_ledger(
        [
            ledger_entry(
                action="COGNITIVE_READ",
                path=MANIFEST_REL,
                content_exposure="YES",
                digest=manifest_sha,
            )
        ],
        manifest_bytes,
    )
    row_mismatch["entries"][0]["contamination_disposition"] = "CONTAMINATED"
    row_mismatch["summary"]["contaminated_entries"] = 0
    record("schema-valid-row-disposition-mismatch", row_mismatch, manifest, manifest_bytes, ledger_validator.INVALID)

    digest_mismatch = make_ledger([], manifest_bytes)
    digest_mismatch["allowed_manifest_sha256"] = "0" * 64
    record("manifest-digest-mismatch", digest_mismatch, manifest, manifest_bytes, ledger_validator.INVALID)

    wrong_path_manifest = synthetic_manifest("synthetic/wrong-packet-manifest.json")
    wrong_path_bytes = canonical_bytes(wrong_path_manifest)
    path_mismatch = make_ledger([], wrong_path_bytes)
    record("manifest-path-mismatch", path_mismatch, wrong_path_manifest, wrong_path_bytes, ledger_validator.INVALID)

    unknown_component = make_ledger(
        [
            ledger_entry(
                action="OPERATIONAL_STATUS_OBSERVED",
                path=COMPONENT_PATH,
                component_id="not-listed-in-synthetic-manifest",
                status=ledger_validator.PASS,
            )
        ],
        manifest_bytes,
    )
    record("unknown-operational-component", unknown_component, manifest, manifest_bytes, ledger_validator.CONTAMINATED)

    status_leak = make_ledger(
        [
            ledger_entry(
                action="OPERATIONAL_STATUS_OBSERVED",
                path=COMPONENT_PATH,
                component_id=COMPONENT_ID,
                case_specific=True,
                status=ledger_validator.PASS,
            )
        ],
        manifest_bytes,
    )
    record("case-specific-information-in-operational-status", status_leak, manifest, manifest_bytes, ledger_validator.CONTAMINATED)

    clean_operational = make_ledger(operational_rows(), manifest_bytes)
    record("legal-operational-execution-and-status", clean_operational, manifest, manifest_bytes, ledger_validator.PASS)

    closure = closure_sequence(manifest, manifest_bytes)
    source_files = {
        "read_ledger_schema": IGNITION_ROOT / "evaluation/heldout/r0.2/successor-visible/successor-read-ledger-r0.2.schema.json",
        "validator": IGNITION_ROOT / "evaluation/tools/validate_successor_read_ledger_r0_2.py",
        "branch_guard": IGNITION_ROOT / "evaluation/tools/task_branch_guard_r0_2.py",
        "authorization_schema": IGNITION_ROOT / "evaluation/operational-control/r0.2/task-branch-authorization-r0.2.schema.json",
    }
    guard_lifecycle = run_guard_staging_fixture()
    return {
        "schema_version": "ignition-187-r0-2-synthetic-reproduction-r0.1",
        "task_id": "IGNITION-20260918-187",
        "source_commit": SOURCE_COMMIT,
        "evidence_scope": "Synthetic fixtures only. No Task182-R2 local case record, read ledger, or packet manifest was opened.",
        "source_sha256": {name: sha256(path.read_bytes()) for name, path in source_files.items()},
        "cases": cases,
        "validator_self_reference": closure,
        "commit_guard_staging_lifecycle": guard_lifecycle,
        "root_cause_classification": {
            "R0_2_IMPLEMENTATION_BUG": "NOT_DEMONSTRATED_BY_SYNTHETIC_REPRODUCTION",
            "R0_2_PROTOCOL_SELF_REFERENCE": "REPRODUCED_CONDITIONALLY_IF_FINAL_VALIDATOR_INVOCATION_AND_STATUS_MUST_BE_IN_CERTIFIED_LEDGER",
            "SUCCESSOR_BOOKKEEPING_ERROR": "NOT_ESTABLISHED_WITHOUT_PRIVATE_LEDGER",
            "UNRESOLVED_WITHOUT_PRIVATE_LEDGER": "RETAINED_FOR_THE_ACTUAL_TASK182_R2_INVALID_RESULT",
        },
    }


class Task187R02SyntheticReproductionTests(unittest.TestCase):
    def test_schema_valid_invalid_and_contaminated_cases_match_validator(self) -> None:
        result = reproduction_summary()
        self.assertTrue(all(row["schema_valid"] for row in result["cases"]))
        self.assertTrue(all(row["expected_status"] == row["observed_status"] for row in result["cases"]))
        observed = {row["fixture_id"]: row["observed_status"] for row in result["cases"]}
        self.assertEqual(observed["schema-valid-summary-mismatch"], ledger_validator.INVALID)
        self.assertEqual(observed["schema-valid-trial-disposition-mismatch"], ledger_validator.INVALID)
        self.assertEqual(observed["schema-valid-row-disposition-mismatch"], ledger_validator.INVALID)
        self.assertEqual(observed["manifest-digest-mismatch"], ledger_validator.INVALID)
        self.assertEqual(observed["manifest-path-mismatch"], ledger_validator.INVALID)
        self.assertEqual(observed["unknown-operational-component"], ledger_validator.CONTAMINATED)
        self.assertEqual(observed["case-specific-information-in-operational-status"], ledger_validator.CONTAMINATED)
        self.assertEqual(observed["legal-operational-execution-and-status"], ledger_validator.PASS)

    def test_validator_status_recording_changes_the_ledger_after_each_pass(self) -> None:
        result = reproduction_summary()["validator_self_reference"]
        self.assertTrue(result["all_invocations_return_clean"])
        self.assertTrue(result["each_recording_changes_the_certified_ledger"])
        self.assertFalse(result["finite_fixed_point"])
        self.assertEqual([row["input_entry_count"] for row in result["runs"]], [0, 2, 4])

    def test_commit_guard_staging_lifecycle_does_not_change_cognitive_disposition(self) -> None:
        result = reproduction_summary()["commit_guard_staging_lifecycle"]
        self.assertEqual(result["untracked_evidence_status"], "FAIL_UNEXPLAINED_WORKTREE")
        self.assertEqual(result["staged_evidence_status"], branch_guard.PASS)
        self.assertEqual(result["new_status_record_unstaged_status"], "FAIL_UNEXPLAINED_WORKTREE")
        self.assertEqual(result["new_status_record_staged_status"], branch_guard.PASS)
        self.assertEqual(result["cognitive_disposition_before_and_after"], "CLEAN")


if __name__ == "__main__":
    if sys.argv[1:] == ["--json"]:
        print(json.dumps(reproduction_summary(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        unittest.main()
