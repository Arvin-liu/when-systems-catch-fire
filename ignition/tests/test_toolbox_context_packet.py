from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


IGNITION = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION / "tools/toolbox_context_packet.py"
sys.path.insert(0, str(IGNITION / "tools"))
import toolbox_context_packet as tool  # noqa: E402


def fixture_repo(root: Path, body: bytes = b"Current source line one.\nCurrent source line two.\n") -> tuple[Path, str, str]:
    source = root / "ignition/KNOWLEDGE/current.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(body)
    relative = "ignition/KNOWLEDGE/current.md"
    return root, relative, hashlib.sha256(body).hexdigest()


def make_request(path: str, digest: str, **overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "packet_id": "packet-test-1",
        "current_ref": "refs/heads/main@caller-supplied",
        "operation_or_question_id": "question-test-1",
        "obligations": [
            {
                "obligation_id": "O1",
                "description": "A current source is available for this context requirement.",
                "source_required": True,
            }
        ],
        "context_items": [
            {
                "context_item_id": "C1",
                "canonical_source_ref": path,
                "source_version_or_digest": digest,
                "source_kind": "CANONICAL_SOURCE",
                "line_start": 1,
                "line_end": 2,
                "evidence_role": "LOCAL_CONTEXT_ONLY",
                "epistemic_status": "CALLER_SAYS_CURRENT",
                "freshness_or_as_of": "caller supplied",
                "inclusion_reason": "Explicitly selected for a bounded task context.",
                "obligation_ids": ["O1"],
            }
        ],
        "max_total_source_bytes": 10_000,
        "max_excerpt_chars": 200,
    }
    request.update(overrides)
    return request


class ContextPacketTests(unittest.TestCase):
    def test_cli_entrypoint_emits_structured_packet_and_never_authorizes_execution(self) -> None:
        source_path = IGNITION / "AI-START-HERE.md"
        source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        request = make_request("ignition/AI-START-HERE.md", source_digest)
        request["context_items"][0]["line_end"] = 1
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=json.dumps(request).encode("utf-8"),
            cwd=IGNITION.parent,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        packet = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(packet["tool_id"], "knowledge.assemble_context_packet")
        self.assertEqual(packet["coverage"]["semantic_coverage"], "NOT_EVALUATED")
        self.assertEqual(packet["coverage"]["sufficiency_decision"], "NOT_EVALUATED")
        self.assertFalse(packet["execution_authorized"])

    def test_current_digest_yields_bounded_structural_packet_not_semantic_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, path, digest = fixture_repo(Path(temp))
            before = hashlib.sha256((root / path).read_bytes()).hexdigest()

            packet = tool.build_context_packet(make_request(path, digest), repo_root=root)

            item = packet["context_items"][0]
            self.assertEqual(packet["packet_status"], "ASSEMBLED_STRUCTURAL_CONTEXT_NO_DECLARED_GAPS")
            self.assertEqual(item["materialization_status"], "CURRENT_BYTES_MATCH_EXPECTED_DIGEST")
            self.assertEqual(item["current_source_sha256"], digest)
            self.assertEqual(item["source_kind_provenance"], "CALLER_DECLARED_NOT_AUTHORITY_VERIFIED")
            self.assertEqual(item["epistemic_status_caller_declared"], "CALLER_SAYS_CURRENT")
            self.assertEqual(item["context_excerpt"][1]["text"], "Current source line two.")
            self.assertEqual(packet["coverage"]["source_required_present"], ["O1"])
            self.assertEqual(packet["coverage"]["semantic_coverage"], "NOT_EVALUATED")
            self.assertEqual(packet["coverage"]["sufficiency_decision"], "NOT_EVALUATED")
            self.assertFalse(packet["execution_authorized"])
            self.assertEqual(hashlib.sha256((root / path).read_bytes()).hexdigest(), before)

    def test_stale_source_digest_withholds_excerpt_and_keeps_gap_open(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, path, _ = fixture_repo(Path(temp))
            stale = "0" * 64

            packet = tool.build_context_packet(make_request(path, stale), repo_root=root)

            item = packet["context_items"][0]
            self.assertEqual(item["materialization_status"], "SOURCE_STALE_DIGEST_MISMATCH")
            self.assertIsNone(item["context_excerpt"])
            self.assertEqual(packet["coverage"]["stale_or_invalid"], ["O1"])
            self.assertEqual(packet["gaps"][0]["gap_class"], "STALE")
            self.assertEqual(packet["coverage"]["sufficiency_decision"], "NOT_EVALUATED")

    def test_generated_summary_cannot_satisfy_source_required_obligation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, path, digest = fixture_repo(Path(temp))
            request = make_request(path, digest)
            item = request["context_items"][0]
            assert isinstance(item, dict)
            item["source_kind"] = "GENERATED_SUMMARY"

            packet = tool.build_context_packet(request, repo_root=root)

            self.assertEqual(packet["coverage"]["declared_present"], [])
            self.assertEqual(packet["coverage"]["generated_only"], ["O1"])
            self.assertEqual(packet["gaps"][0]["gap_class"], "GENERATED_CONTEXT_NOT_SOURCE")
            self.assertEqual(packet["context_items"][0]["materialization_status"], "CURRENT_BYTES_MATCH_EXPECTED_DIGEST")

    def test_absent_obligation_input_becomes_explicit_missing_gap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, _, _ = fixture_repo(Path(temp))
            request = make_request("ignition/KNOWLEDGE/absent.md", "0" * 64, context_items=[])

            packet = tool.build_context_packet(request, repo_root=root)

            self.assertEqual(packet["coverage"]["missing"], ["O1"])
            self.assertEqual(packet["gaps"][0]["gap_class"], "MISSING")
            self.assertFalse(packet["gaps"][0]["retrieval_authorized"])

    def test_byte_budget_does_not_turn_unopened_source_into_presence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, path, digest = fixture_repo(Path(temp))
            request = make_request(path, digest, max_total_source_bytes=1)

            packet = tool.build_context_packet(request, repo_root=root)

            self.assertEqual(packet["context_items"][0]["materialization_status"], "SOURCE_NOT_OPENED_BUDGET")
            self.assertEqual(packet["budgets"]["source_bytes_read"], 0)
            self.assertEqual(packet["gaps"][0]["gap_class"], "BUDGET")
            self.assertEqual(packet["coverage"]["declared_present"], [])

    def test_incomplete_line_range_is_not_counted_as_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, path, digest = fixture_repo(Path(temp))
            request = make_request(path, digest)
            assert isinstance(request["context_items"], list)
            request["context_items"][0]["line_end"] = 5

            packet = tool.build_context_packet(request, repo_root=root)

            self.assertEqual(packet["context_items"][0]["materialization_status"], "LINE_RANGE_PARTIAL")
            self.assertEqual(packet["coverage"]["declared_present"], [])
            self.assertEqual(packet["gaps"][0]["gap_class"], "UNREADABLE")

    def test_path_traversal_is_rejected_before_any_excerpt_is_returned(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = make_request("ignition/../outside.md", "0" * 64)

            with self.assertRaisesRegex(tool.ContextPacketError, "traversal"):
                tool.build_context_packet(request, repo_root=root)

    def test_symlink_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root / "outside.md"
            outside.write_text("should not be read\n", encoding="utf-8")
            knowledge = root / "ignition/KNOWLEDGE"
            knowledge.mkdir(parents=True)
            (knowledge / "linked.md").symlink_to(outside)
            request = make_request("ignition/KNOWLEDGE/linked.md", hashlib.sha256(outside.read_bytes()).hexdigest())

            with self.assertRaisesRegex(tool.ContextPacketError, "symlink"):
                tool.build_context_packet(request, repo_root=root)

    def test_unknown_obligation_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root, path, digest = fixture_repo(Path(temp))
            request = make_request(path, digest)
            assert isinstance(request["context_items"], list)
            request["context_items"][0]["obligation_ids"] = ["UNKNOWN"]

            with self.assertRaisesRegex(tool.ContextPacketError, "unknown obligation_id"):
                tool.build_context_packet(request, repo_root=root)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(tool.ContextPacketError, "duplicate JSON input key"):
            json.loads('{"packet_id":"a","packet_id":"b"}', object_pairs_hook=tool._reject_duplicate_keys)


if __name__ == "__main__":
    unittest.main()
