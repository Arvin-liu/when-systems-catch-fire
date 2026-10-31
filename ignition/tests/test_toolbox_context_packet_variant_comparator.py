from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


IGNITION = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION / "tools/toolbox_context_packet_variant_comparator.py"
sys.path.insert(0, str(IGNITION / "tools"))
import toolbox_context_packet_variant_comparator as tool  # noqa: E402
import toolbox_context_packet as assembler  # noqa: E402


def packet(packet_id: str, excerpt: str, *, declared: list[str] | None = None) -> dict:
    current = hashlib.sha256(b"source").hexdigest()
    present = ["O1"] if declared is None else declared
    missing = [item for item in ["O1", "O2"] if item not in present]
    return {
        "schema_version": "toolbox-context-packet-r0",
        "tool_id": "knowledge.assemble_context_packet",
        "tool_version": "0.1.0",
        "packet_id": packet_id,
        "packet_status": "ASSEMBLED_STRUCTURAL_CONTEXT_WITH_OPEN_GAPS" if missing else "ASSEMBLED_STRUCTURAL_CONTEXT_NO_DECLARED_GAPS",
        "current_ref": "refs/heads/main@caller-supplied",
        "operation_or_question_id": "question-context-compare",
        "context_items": [
            {
                "context_item_id": packet_id + "-item",
                "canonical_source_ref": "ignition/KNOWLEDGE/current.md",
                "source_version_or_digest": current,
                "source_kind": "CANONICAL_SOURCE",
                "materialization_status": "CURRENT_BYTES_MATCH_EXPECTED_DIGEST",
                "current_source_sha256": current,
                "source_bytes_read": 64,
                "context_excerpt": [{"line": 1, "text": excerpt}],
            }
        ],
        "coverage": {
            "required": ["O1", "O2"],
            "declared_present": present,
            "source_required_present": [item for item in present if item == "O1"],
            "missing": missing,
            "stale_or_invalid": [],
            "generated_only": [],
            "semantic_coverage": "NOT_EVALUATED",
            "sufficiency_decision": "NOT_EVALUATED",
        },
        "budgets": {"source_bytes_read": 64},
        "execution_authorized": False,
    }


def request(baseline: dict | None = None, candidate: dict | None = None) -> dict:
    return {
        "comparison_id": "comparison-context-1",
        "baseline_packet": baseline or packet("baseline", "full source line one\\nfull source line two"),
        "candidate_packet": candidate or packet("candidate", "selected line"),
    }


class ContextPacketVariantComparatorTests(unittest.TestCase):
    def test_matched_comparison_reports_exact_text_bytes_without_echo_or_sufficiency_claim(self) -> None:
        raw = json.dumps(request(), ensure_ascii=False).encode()
        output = tool.compare_context_packets(json.loads(raw), raw_input_sha256=hashlib.sha256(raw).hexdigest())

        self.assertEqual(output["comparison_status"], "MATCHED_STRUCTURAL_COMPARISON")
        self.assertLess(output["candidate"]["excerpt_text_utf8_bytes"], output["baseline"]["excerpt_text_utf8_bytes"])
        self.assertEqual(output["interpretation"]["sufficiency_decision"], "NOT_EVALUATED")
        self.assertEqual(output["interpretation"]["provider_token_usage"], "NOT_MEASURED")
        self.assertFalse(output["interpretation"]["execution_authorized"])
        self.assertNotIn("full source line", json.dumps(output))
        self.assertEqual(output["deltas"]["dropped_source_required_obligation_ids"], [])

    def test_accepts_actual_context_packet_assembler_excerpt_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "ignition/KNOWLEDGE/current.md"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()

            def assembled(packet_id: str, line_end: int) -> dict:
                packet_request = {
                    "packet_id": packet_id,
                    "current_ref": "refs/heads/main@caller-supplied",
                    "operation_or_question_id": "question-context-compare",
                    "obligations": [{
                        "obligation_id": "O1",
                        "description": "Current source bytes are structurally linked.",
                        "source_required": True,
                    }],
                    "context_items": [{
                        "context_item_id": packet_id + "-item",
                        "canonical_source_ref": "ignition/KNOWLEDGE/current.md",
                        "source_version_or_digest": digest,
                        "source_kind": "CANONICAL_SOURCE",
                        "line_start": 1,
                        "line_end": line_end,
                        "evidence_role": "LOCAL_CONTEXT_ONLY",
                        "epistemic_status": "CALLER_SAYS_CURRENT",
                        "freshness_or_as_of": "caller supplied",
                        "inclusion_reason": "Focused shape compatibility check.",
                        "obligation_ids": ["O1"],
                    }],
                    "max_total_source_bytes": 1000,
                    "max_excerpt_chars": 200,
                }
                return assembler.build_context_packet(packet_request, repo_root=root)

            baseline = assembled("baseline", 3)
            candidate = assembled("candidate", 1)
            output = tool.compare_context_packets(
                request(baseline, candidate), raw_input_sha256="2" * 64,
            )

        self.assertEqual(output["comparison_status"], "MATCHED_STRUCTURAL_COMPARISON")
        self.assertEqual(output["baseline"]["excerpt_line_count"], 3)
        self.assertEqual(output["candidate"]["excerpt_line_count"], 1)
        self.assertEqual(output["deltas"]["dropped_source_required_obligation_ids"], [])

    def test_dropped_source_required_obligation_is_reported_without_being_hidden(self) -> None:
        candidate = packet("candidate", "selected line", declared=[])
        output = tool.compare_context_packets(request(candidate=candidate), raw_input_sha256="a" * 64)

        self.assertEqual(output["deltas"]["dropped_declared_obligation_ids"], ["O1"])
        self.assertEqual(output["deltas"]["dropped_source_required_obligation_ids"], ["O1"])
        self.assertEqual(output["interpretation"]["semantic_coverage"], "NOT_EVALUATED")

    def test_mismatched_question_or_current_ref_fails_closed(self) -> None:
        baseline = packet("baseline", "baseline")
        candidate = packet("candidate", "candidate")
        candidate["operation_or_question_id"] = "different-question"
        with self.assertRaisesRegex(tool.ContextVariantError, "same operation_or_question_id"):
            tool.compare_context_packets(request(baseline, candidate), raw_input_sha256="b" * 64)
        candidate["operation_or_question_id"] = baseline["operation_or_question_id"]
        candidate["current_ref"] = "refs/heads/other@caller-supplied"
        with self.assertRaisesRegex(tool.ContextVariantError, "same current_ref"):
            tool.compare_context_packets(request(baseline, candidate), raw_input_sha256="c" * 64)

    def test_mismatched_required_obligations_fails_closed(self) -> None:
        baseline = packet("baseline", "baseline")
        candidate = packet("candidate", "candidate")
        candidate["coverage"]["required"] = ["O1"]
        candidate["coverage"]["missing"] = []
        with self.assertRaisesRegex(tool.ContextVariantError, "same ordered required obligations"):
            tool.compare_context_packets(request(baseline, candidate), raw_input_sha256="d" * 64)

    def test_packet_cannot_grant_execution_or_upgrade_semantics(self) -> None:
        candidate = packet("candidate", "candidate")
        candidate["execution_authorized"] = True
        with self.assertRaisesRegex(tool.ContextVariantError, "execution_authorized=false"):
            tool.compare_context_packets(request(candidate=candidate), raw_input_sha256="e" * 64)
        candidate = packet("candidate", "candidate")
        candidate["coverage"]["sufficiency_decision"] = "SUFFICIENT"
        with self.assertRaisesRegex(tool.ContextVariantError, "sufficiency_decision=NOT_EVALUATED"):
            tool.compare_context_packets(request(candidate=candidate), raw_input_sha256="f" * 64)

    def test_source_digest_mismatch_in_claimed_current_item_fails_closed(self) -> None:
        candidate = packet("candidate", "candidate")
        candidate["context_items"][0]["current_source_sha256"] = "0" * 64
        with self.assertRaisesRegex(tool.ContextVariantError, "does not match"):
            tool.compare_context_packets(request(candidate=candidate), raw_input_sha256="1" * 64)

    def test_duplicate_input_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(tool.ContextVariantError, "duplicate JSON input key"):
            json.loads('{"comparison_id":"a","comparison_id":"b"}', object_pairs_hook=tool._reject_duplicate_keys)

    def test_cli_emits_summary_and_does_not_echo_context_text(self) -> None:
        raw = json.dumps(request(), ensure_ascii=False).encode()
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=raw,
            cwd=IGNITION.parent,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        result = json.loads(completed.stdout)
        self.assertEqual(result["input_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotIn("full source line", completed.stdout.decode())
        self.assertFalse(result["interpretation"]["execution_authorized"])

    def test_cli_rejects_oversized_input_before_comparison(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=b" " * (tool.MAX_REQUEST_BYTES + 1),
            cwd=IGNITION.parent,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn(b"256000-byte limit", completed.stderr)


if __name__ == "__main__":
    unittest.main()
