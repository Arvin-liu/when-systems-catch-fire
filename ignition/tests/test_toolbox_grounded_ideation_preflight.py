from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_grounded_ideation_preflight as tool  # noqa: E402


FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-grounded-ideation-preflight/valid-input-r0.json"
SCHEMA = IGNITION_ROOT / "schemas/operations/grounded-ideation-preflight-r0.schema.json"


class GroundedIdeationPreflightTests(unittest.TestCase):
    def packet(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def analyze(self, packet: dict) -> dict:
        raw = json.dumps(packet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return tool.analyze_bytes(raw)

    def codes(self, report: dict) -> set[str]:
        return {finding["code"] for finding in report["findings"]}

    def test_synthetic_packet_passes_structural_preflight_only(self) -> None:
        packet = self.packet()
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(packet)), [])

        report = self.analyze(packet)

        self.assertEqual(report["status"], "PREFLIGHT_READY_FOR_HUMAN_REVIEW")
        self.assertEqual(report["counts"], {
            "sources": 2,
            "used_sources": 1,
            "attached_sources": 1,
            "anchors": 3,
            "mechanism_mappings": 1,
        })
        self.assertEqual(report["quote_check"], "SUBSTRING_IN_CALLER_SUPPLIED_EXCERPT_ONLY")
        self.assertEqual(report["source_authenticity"], "NOT_ESTABLISHED")
        self.assertEqual(report["semantic_support"], "NOT_VERIFIED")
        self.assertEqual(report["independent_review"], "NOT_PERFORMED")
        self.assertEqual(report["scientific_acceptance"], "NOT_ESTABLISHED")
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["network_requests"], 0)
        self.assertEqual(report["repository_writes"], 0)

    def test_quote_must_appear_exactly_in_the_supplied_excerpt(self) -> None:
        packet = self.packet()
        packet["anchors"][0]["quote"] = "the source proves a real-world effect"

        report = self.analyze(packet)

        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("QUOTE_NOT_FOUND_IN_SUPPLIED_EXCERPT", self.codes(report))
        self.assertEqual(report["semantic_support"], "NOT_VERIFIED")

    def test_gap_requires_both_support_and_contrary_anchors(self) -> None:
        packet = self.packet()
        packet["gap"]["contrary_anchor_ids"] = []

        report = self.analyze(packet)

        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("REQUIRED_ITEMS_ABSENT", self.codes(report))

    def test_attached_source_cannot_be_counted_as_evidence(self) -> None:
        packet = self.packet()
        packet["sources"][0]["usage"] = "ATTACHED"

        report = self.analyze(packet)

        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("ATTACHED_SOURCE_USED_AS_EVIDENCE", self.codes(report))

    def test_cutoff_excludes_later_used_sources(self) -> None:
        packet = self.packet()
        packet["sources"][0]["publication_date"] = "2026-01-02"

        report = self.analyze(packet)

        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("USED_SOURCE_AFTER_CUTOFF", self.codes(report))

    def test_unknown_used_source_date_blocks_a_requested_cutoff(self) -> None:
        packet = self.packet()
        packet["sources"][0]["publication_date"] = None

        report = self.analyze(packet)

        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("USED_SOURCE_DATE_UNKNOWN", self.codes(report))

    def test_same_domain_transfer_and_missing_falsifier_remain_incomplete(self) -> None:
        packet = self.packet()
        packet["mechanism_transfer"]["target_domain"] = packet["mechanism_transfer"]["source_domain"]
        packet["proposal"]["falsifiers"] = []

        report = self.analyze(packet)

        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertIn("TRANSFER_DOMAINS_NOT_DISTINCT", self.codes(report))
        self.assertIn("REQUIRED_ITEMS_ABSENT", self.codes(report))

    def test_unresolved_source_and_unknown_fields_fail_closed(self) -> None:
        packet = self.packet()
        packet["anchors"][0]["source_id"] = "missing-source"
        packet["proposal"]["science_pass"] = True

        report = self.analyze(packet)

        self.assertEqual(report["status"], "INPUT_INVALID")
        self.assertIn("UNKNOWN_FIELD", self.codes(report))
        self.assertIn("ANCHOR_SOURCE_UNRESOLVED", self.codes(report))

    def test_duplicate_keys_and_oversized_input_are_rejected(self) -> None:
        duplicate = b'{"schema_version":"wrong","schema_version":"grounded-ideation-preflight-r0"}'
        duplicate_result = tool.analyze_bytes(duplicate)
        oversized_result = tool.analyze_bytes(b" " * (tool.MAX_INPUT_BYTES + 1))

        self.assertEqual(duplicate_result["status"], "INPUT_INVALID")
        self.assertIn("DUPLICATE_JSON_KEY", self.codes(duplicate_result))
        self.assertEqual(oversized_result["status"], "INPUT_INVALID")
        self.assertIn("INPUT_LIMIT_EXCEEDED", self.codes(oversized_result))

    def test_reference_ids_and_text_arrays_obey_the_published_schema_limits(self) -> None:
        malformed_id_packet = self.packet()
        malformed_id_packet["gap"]["support_anchor_ids"] = ["not an id"]
        malformed_id = self.analyze(malformed_id_packet)

        oversized_array_packet = self.packet()
        oversized_array_packet["gap"]["limitations"] = [f"limit {index}" for index in range(65)]
        oversized_array = self.analyze(oversized_array_packet)

        self.assertEqual(malformed_id["status"], "INPUT_INVALID")
        self.assertIn("IDENTIFIER_INVALID", self.codes(malformed_id))
        self.assertEqual(oversized_array["status"], "INPUT_INVALID")
        self.assertIn("ITEM_LIMIT_EXCEEDED", self.codes(oversized_array))

    def test_cli_is_repeatable_and_does_not_echo_source_text(self) -> None:
        command = [sys.executable, str(IGNITION_ROOT / "tools/toolbox_grounded_ideation_preflight.py"), "--stdin"]
        payload = FIXTURE.read_bytes()
        first = subprocess.run(command, input=payload, capture_output=True, check=False)
        second = subprocess.run(command, input=payload, capture_output=True, check=False)
        smoke = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-grounded-ideation-preflight-smoke-evidence-r0.json")
            .read_text(encoding="utf-8")
        )

        self.assertEqual(first.returncode, 0, first.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(smoke["input_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(smoke["output_sha256"], hashlib.sha256(first.stdout).hexdigest())
        self.assertEqual(smoke["status"], "PREFLIGHT_READY_FOR_HUMAN_REVIEW")
        self.assertTrue(smoke["synthetic_only"])
        self.assertNotIn(b"alerting before inspection", first.stdout)
        result = json.loads(first.stdout)
        self.assertEqual(result["status"], "PREFLIGHT_READY_FOR_HUMAN_REVIEW")


if __name__ == "__main__":
    unittest.main()
