from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_declared_permission_delta_preflight as tool  # noqa: E402


FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-declared-permission-delta/valid-input-r0.json"
SCHEMA = IGNITION_ROOT / "schemas/operations/declared-permission-delta-r0.schema.json"


class DeclaredPermissionDeltaPreflightTests(unittest.TestCase):
    def packet(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def analyze(self, packet: dict) -> dict:
        raw = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return tool.analyze_bytes(raw)

    def codes(self, result: dict) -> set[str]:
        return {finding["code"] for finding in result["findings"]}

    def test_synthetic_snapshot_pair_passes_schema_and_reports_exact_set_diff_only(self) -> None:
        packet = self.packet()
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(packet)), [])

        result = self.analyze(packet)

        self.assertEqual(result["status"], "MIXED_DECLARED_DIFF_REVIEW_REQUIRED")
        self.assertEqual(result["counts"], {
            "baseline_grants": 2,
            "candidate_grants": 2,
            "declared_additions": 1,
            "declared_removals": 1,
        })
        self.assertEqual(result["declared_additions"], [
            {"capability": "filesystem.write", "scope": "repo:ignition/reports/"}
        ])
        self.assertEqual(result["declared_removals"], [
            {"capability": "network.connect", "scope": "api.crossref.org"}
        ])
        self.assertFalse(result["effective_policy_resolved"])
        self.assertEqual(result["snapshot_authenticity"], "NOT_ESTABLISHED")
        self.assertFalse(result["sandbox_enforced"])
        self.assertFalse(result["permission_granted"])
        self.assertFalse(result["owner_authorization_granted"])
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(result["repository_writes"], 0)

    def test_exact_no_change_does_not_claim_policy_equivalence(self) -> None:
        packet = self.packet()
        packet["candidate"]["grants"] = copy.deepcopy(packet["baseline"]["grants"])

        result = self.analyze(packet)

        self.assertEqual(result["status"], "NO_EXACT_DECLARED_DIFF")
        self.assertEqual(result["declared_additions"], [])
        self.assertEqual(result["declared_removals"], [])
        self.assertFalse(result["effective_policy_resolved"])

    def test_new_grant_requires_review_without_being_called_safe_or_authorized(self) -> None:
        packet = self.packet()
        packet["candidate"]["grants"] = copy.deepcopy(packet["baseline"]["grants"]) + [
            {"capability": "network.connect", "scope": "*"}
        ]

        result = self.analyze(packet)

        self.assertEqual(result["status"], "DECLARED_ADDITIONS_REVIEW_REQUIRED")
        self.assertEqual(result["declared_additions"], [{"capability": "network.connect", "scope": "*"}])
        self.assertIn("Exact string-set differences", result["claim_ceiling"])
        self.assertFalse(result["permission_granted"])
        self.assertFalse(result["owner_authorization_granted"])

    def test_unknown_capabilities_and_extra_fields_fail_closed(self) -> None:
        packet = self.packet()
        packet["candidate"]["grants"][0]["capability"] = "kernel.escape"
        packet["candidate"]["effective_permission"] = True

        result = self.analyze(packet)

        self.assertEqual(result["status"], "INPUT_INVALID")
        self.assertIn("CAPABILITY_UNSUPPORTED", self.codes(result))
        self.assertIn("UNKNOWN_FIELD", self.codes(result))
        self.assertEqual(result["declared_additions"], [])

    def test_snapshots_must_bind_the_same_policy_and_subject(self) -> None:
        for field in ("policy_id", "subject_id"):
            with self.subTest(field=field):
                packet = self.packet()
                packet["candidate"][field] = "different-binding"
                result = self.analyze(packet)
                self.assertEqual(result["status"], "INPUT_INVALID")
                self.assertIn("COMPARISON_BINDING_MISMATCH", self.codes(result))

    def test_duplicate_grants_are_rejected(self) -> None:
        packet = self.packet()
        packet["candidate"]["grants"].append(copy.deepcopy(packet["candidate"]["grants"][0]))

        result = self.analyze(packet)

        self.assertEqual(result["status"], "INPUT_INVALID")
        self.assertIn("DUPLICATE_GRANT", self.codes(result))

    def test_duplicate_json_keys_and_oversized_payload_are_rejected(self) -> None:
        duplicate = b'{"schema_version":"wrong","schema_version":"declared-permission-delta-r0"}'
        duplicate_result = tool.analyze_bytes(duplicate)
        oversized_result = tool.analyze_bytes(b" " * (tool.MAX_INPUT_BYTES + 1))

        self.assertEqual(duplicate_result["status"], "INPUT_INVALID")
        self.assertIn("DUPLICATE_JSON_KEY", self.codes(duplicate_result))
        self.assertEqual(oversized_result["status"], "INPUT_INVALID")
        self.assertIn("INPUT_LIMIT_EXCEEDED", self.codes(oversized_result))

    def test_cli_is_repeatable_and_smoke_evidence_matches_the_synthetic_fixture(self) -> None:
        command = [sys.executable, str(IGNITION_ROOT / "tools/toolbox_declared_permission_delta_preflight.py"), "--stdin"]
        payload = FIXTURE.read_bytes()
        first = subprocess.run(command, input=payload, capture_output=True, check=False)
        second = subprocess.run(command, input=payload, capture_output=True, check=False)
        smoke = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-declared-permission-delta-smoke-evidence-r0.json")
            .read_text(encoding="utf-8")
        )

        self.assertEqual(first.returncode, 0, first.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(smoke["input_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(smoke["output_sha256"], hashlib.sha256(first.stdout).hexdigest())
        self.assertEqual(smoke["status"], "MIXED_DECLARED_DIFF_REVIEW_REQUIRED")
        self.assertTrue(smoke["synthetic_only"])
        self.assertFalse(smoke["permission_granted"])
        self.assertFalse(smoke["owner_authorization_granted"])


if __name__ == "__main__":
    unittest.main()
