from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT))
sys.path.insert(0, str(IGNITION_ROOT / "tools"))

from agent_federation import ArtifactRef, HandoffEligibility, build_handoff_bundle  # noqa: E402
from agent_federation.contracts import FederatedResultReceipt  # noqa: E402
import toolbox_receiver_handoff_preflight as receiver_preflight  # noqa: E402
import toolbox_context_packet as context_packet  # noqa: E402
import toolbox_verify_handoff_artifact_files as verifier  # noqa: E402


TOOL_PATH = IGNITION_ROOT / "tools/toolbox_verify_handoff_artifact_files.py"
FIXTURE_ROOT = IGNITION_ROOT / "tests/fixtures/toolbox-handoff-artifact-byte-check"


def make_receipt(refs: tuple[ArtifactRef, ...]) -> FederatedResultReceipt:
    return FederatedResultReceipt.build(
        federation_task_id="handoff-artifact-byte-task-001",
        executor_id="external.codex",
        terminal_state="COMPLETED_VALIDATED",
        claimed_actions=("record artifact digest",),
        artifact_refs=refs,
        validation_refs=("validator/artifact-ref-v1",),
        external_session_ref=None,
        executor_telemetry={"transport": "controlled-test"},
        unresolveds=(),
        handoff_eligibility=HandoffEligibility(True, "controlled artifact byte check"),
    )


def artifact(ref: str, payload: bytes, kind: str = "manifest") -> ArtifactRef:
    return ArtifactRef(ref, hashlib.sha256(payload).hexdigest(), kind)


def document(receipt: FederatedResultReceipt) -> dict:
    return {"schema_version": "handoff-artifact-byte-check-r0", "source_receipt": receipt.to_dict()}


def context_request(path: str, digest: str) -> dict:
    return {
        "packet_id": "binary-artifact-comparison-001",
        "current_ref": "refs/heads/main@caller-supplied",
        "operation_or_question_id": "binary-artifact-byte-check",
        "obligations": [
            {"obligation_id": "O1", "description": "Check the declared artifact bytes", "source_required": True}
        ],
        "context_items": [
            {
                "context_item_id": "C1",
                "canonical_source_ref": path,
                "source_version_or_digest": digest,
                "source_kind": "CANONICAL_SOURCE",
                "line_start": 1,
                "line_end": 1,
                "evidence_role": "digest comparison",
                "epistemic_status": "CALLER_SAYS_CURRENT",
                "freshness_or_as_of": None,
                "inclusion_reason": "same local artifact for a matched capability comparison",
                "obligation_ids": ["O1"],
            }
        ],
        "max_total_source_bytes": 1_000_000,
        "max_excerpt_chars": 200,
    }


def matching_receiver_preflight(receipt: FederatedResultReceipt) -> dict:
    bundle = build_handoff_bundle(
        handoff_id="handoff-artifact-byte-handoff-001",
        source_receipt=receipt,
        goal="Check a source-bound local artifact before a separate takeover decision",
        pending_work=("independently decide whether to continue",),
        allowed_capabilities=("repo.read",),
        workspace_refs=("fixture/",),
        acceptance_criteria=("artifact bytes match the source receipt digest",),
    )
    return {
        "schema_version": "receiver-handoff-preflight-r0",
        "source_receipt": receipt.to_dict(),
        "handoff_bundle": bundle.to_dict(),
        "target_executor_id": "external.hermes",
        "target_capabilities": ["repo.read"],
        "workspace_reobserved": True,
        "observed_artifact_refs": [item.ref for item in receipt.artifact_refs],
    }


class HandoffArtifactFileVerifierTests(unittest.TestCase):
    def workspace(self) -> tempfile.TemporaryDirectory:
        return tempfile.TemporaryDirectory(dir=IGNITION_ROOT, prefix=".toolbox-handoff-byte-test-")

    def test_matching_artifact_bytes_return_digest_only_read_only_result(self) -> None:
        payload = b'{"version":1,"state":"expected"}\n'
        receipt = make_receipt((artifact("fixture/manifest.json", payload),))
        with self.workspace() as temp:
            root = Path(temp)
            (root / "fixture").mkdir()
            (root / "fixture/manifest.json").write_bytes(payload)
            result, code = verifier.evaluate(document(receipt), root)

        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "ALL_DIGESTS_MATCH")
        self.assertEqual(result["source_receipt_canonical_digest"], "PASS")
        self.assertEqual(result["artifacts"][0]["status"], "DIGEST_MATCH")
        self.assertEqual(result["artifacts"][0]["observed_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["receipt_authenticity"], "NOT_ESTABLISHED_UNKEYED_DIGEST")
        self.assertNotIn(payload.decode(), json.dumps(result))

    def test_binary_artifact_is_hashable_without_content_where_context_packet_is_text_only(self) -> None:
        payload = b"\x00\xff\xfe\x80"
        receipt = make_receipt((artifact("fixture/data.bin", payload),))
        with self.workspace() as temp:
            root = Path(temp)
            (root / "fixture").mkdir()
            artifact_path = root / "fixture/data.bin"
            artifact_path.write_bytes(payload)

            result, code = verifier.evaluate(document(receipt), root)
            repo_relative_path = artifact_path.relative_to(REPO_ROOT).as_posix()
            packet = context_packet.build_context_packet(
                context_request(repo_relative_path, hashlib.sha256(payload).hexdigest()),
                repo_root=REPO_ROOT,
            )

        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "ALL_DIGESTS_MATCH")
        self.assertEqual(result["artifacts"][0]["status"], "DIGEST_MATCH")
        self.assertNotIn(payload.decode("latin-1"), json.dumps(result))
        self.assertEqual(packet["context_items"][0]["materialization_status"], "SOURCE_NOT_UTF8")
        self.assertIsNone(packet["context_items"][0]["context_excerpt"])
        self.assertEqual(packet["context_items"][0]["current_source_sha256"], hashlib.sha256(payload).hexdigest())

    def test_matched_negative_control_detects_changed_bytes_missed_by_receiver_preflight(self) -> None:
        declared = b'{"version":1,"state":"declared"}\n'
        changed = b'{"version":1,"state":"changed"}\n'
        receipt = make_receipt((artifact("fixture/manifest.json", declared),))
        with self.workspace() as temp:
            root = Path(temp)
            (root / "fixture").mkdir()
            (root / "fixture/manifest.json").write_bytes(changed)
            result, code = verifier.evaluate(document(receipt), root)

        prior, prior_code = receiver_preflight.evaluate(matching_receiver_preflight(receipt))
        self.assertEqual(prior_code, 0)
        self.assertEqual(prior["status"], "PREFLIGHT_READY_NO_AUTHORITY")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "DIGEST_MISMATCH")
        self.assertEqual(result["artifacts"][0]["status"], "DIGEST_MISMATCH")
        self.assertNotEqual(
            result["artifacts"][0]["observed_sha256"],
            result["artifacts"][0]["expected_sha256"],
        )
        self.assertFalse(result["execution_authorized"])

    def test_parent_traversal_and_external_uri_are_not_read(self) -> None:
        payload = b"fixture"
        for ref, expected in (("../outside.bin", "UNSAFE_REFERENCE"), ("https://example.invalid/a", "UNSUPPORTED_REFERENCE")):
            receipt = make_receipt((artifact(ref, payload),))
            with self.workspace() as temp:
                result, code = verifier.evaluate(document(receipt), Path(temp))
            self.assertEqual(code, 2)
            self.assertEqual(result["artifacts"][0]["status"], expected)
            self.assertNotIn("observed_sha256", result["artifacts"][0])

    def test_symlink_target_is_never_followed(self) -> None:
        payload = b"do not follow a link"
        receipt = make_receipt((artifact("fixture/manifest.json", payload),))
        with self.workspace() as temp:
            root = Path(temp)
            (root / "fixture").mkdir()
            outside = root / "outside.bin"
            outside.write_bytes(payload)
            (root / "fixture/manifest.json").symlink_to(outside)
            result, code = verifier.evaluate(document(receipt), root)

        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "ARTIFACTS_UNVERIFIED")
        self.assertNotEqual(result["artifacts"][0]["status"], "DIGEST_MATCH")
        self.assertNotIn("observed_sha256", result["artifacts"][0])

    def test_symlink_directory_component_is_never_followed(self) -> None:
        payload = b"outside the selected tree"
        receipt = make_receipt((artifact("fixture/linked/manifest.json", payload),))
        with self.workspace() as temp:
            root = Path(temp)
            (root / "fixture").mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "manifest.json").write_bytes(payload)
            (root / "fixture/linked").symlink_to(outside, target_is_directory=True)
            result, code = verifier.evaluate(document(receipt), root)

        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "ARTIFACTS_UNVERIFIED")
        self.assertEqual(result["artifacts"][0]["status"], "UNSAFE_PATH")
        self.assertNotIn("observed_sha256", result["artifacts"][0])

    def test_workspace_root_must_be_inside_ignition(self) -> None:
        payload = b"outside root"
        receipt = make_receipt((artifact("fixture/manifest.json", payload),))
        with tempfile.TemporaryDirectory(prefix="toolbox-byte-outside-") as outside:
            result, code = verifier.evaluate(document(receipt), outside)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "WORKSPACE_ROOT_OUTSIDE_IGNITION")
        self.assertEqual(result["source_receipt_canonical_digest"], "PASS")

    def test_non_regular_file_is_rejected(self) -> None:
        receipt = make_receipt((artifact("fixture/directory", b""),))
        with self.workspace() as temp:
            root = Path(temp)
            (root / "fixture/directory").mkdir(parents=True)
            result, code = verifier.evaluate(document(receipt), root)
        self.assertEqual(code, 2)
        self.assertEqual(result["artifacts"][0]["status"], "NOT_REGULAR_FILE")

    def test_per_file_limit_stops_before_reading_oversized_file(self) -> None:
        payload = b"four"
        receipt = make_receipt((artifact("fixture/data.bin", payload),))
        with self.workspace() as temp:
            root = Path(temp)
            (root / "fixture").mkdir()
            (root / "fixture/data.bin").write_bytes(payload)
            with patch.object(verifier, "MAX_FILE_BYTES", 3):
                result, code = verifier.evaluate(document(receipt), root)
        self.assertEqual(code, 2)
        self.assertEqual(result["artifacts"][0]["status"], "FILE_SIZE_LIMIT")
        self.assertEqual(result["total_bytes_read"], 0)

    def test_total_byte_budget_stops_before_reading_next_file(self) -> None:
        first, second = b"12", b"34"
        receipt = make_receipt((artifact("fixture/a.bin", first), artifact("fixture/b.bin", second)))
        with self.workspace() as temp:
            root = Path(temp)
            (root / "fixture").mkdir()
            (root / "fixture/a.bin").write_bytes(first)
            (root / "fixture/b.bin").write_bytes(second)
            with patch.object(verifier, "MAX_TOTAL_BYTES", 3):
                result, code = verifier.evaluate(document(receipt), root)
        self.assertEqual(code, 2)
        self.assertEqual(result["artifacts"][0]["status"], "DIGEST_MATCH")
        self.assertEqual(result["artifacts"][1]["status"], "TOTAL_SIZE_LIMIT")
        self.assertEqual(result["total_bytes_read"], 2)

    def test_bad_receipt_digest_and_empty_or_excessive_artifact_lists_fail_closed(self) -> None:
        payload = b"x"
        receipt = make_receipt((artifact("fixture/x", payload),))
        bad = receipt.to_dict()
        bad["receipt_digest"] = "0" * 64
        with self.workspace() as temp:
            invalid, invalid_code = verifier.evaluate({"schema_version": verifier.INPUT_SCHEMA_VERSION, "source_receipt": bad}, temp)
            empty_receipt = make_receipt(())
            empty, empty_code = verifier.evaluate(document(empty_receipt), temp)
            too_many_refs = tuple(artifact(f"fixture/{index}.bin", payload) for index in range(verifier.MAX_ARTIFACTS + 1))
            too_many, too_many_code = verifier.evaluate(document(make_receipt(too_many_refs)), temp)
        self.assertEqual(invalid_code, 2)
        self.assertEqual(invalid["findings"][0]["code"], "SOURCE_RECEIPT_INVALID")
        self.assertEqual(empty_code, 2)
        self.assertEqual(empty["status"], "NO_ARTIFACTS_TO_VERIFY")
        self.assertEqual(too_many_code, 2)
        self.assertEqual(too_many["status"], "ARTIFACT_COUNT_LIMIT")

    def test_cli_smoke_duplicate_keys_and_oversized_input(self) -> None:
        fixture = FIXTURE_ROOT / "valid-input-r0.json"
        workspace = FIXTURE_ROOT / "workspace"
        args = [sys.executable, "-B", str(TOOL_PATH), "--stdin", "--workspace-root", str(workspace)]
        good = subprocess.run(
            args,
            input=fixture.read_text(encoding="utf-8"),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["status"], "ALL_DIGESTS_MATCH")

        duplicate = subprocess.run(
            args,
            input='{"schema_version":"x","schema_version":"y"}',
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(duplicate.returncode, 2)
        self.assertEqual(json.loads(duplicate.stdout)["findings"][0]["code"], "DUPLICATE_JSON_KEY")

        oversized = subprocess.run(
            args,
            input=" " * (verifier.MAX_INPUT_BYTES + 1),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(oversized.returncode, 2)
        self.assertEqual(json.loads(oversized.stdout)["status"], "INPUT_INVALID")


if __name__ == "__main__":
    unittest.main()
