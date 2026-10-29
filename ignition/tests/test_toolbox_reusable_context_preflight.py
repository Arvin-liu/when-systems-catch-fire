from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_reusable_context_preflight.py"
SPEC = importlib.util.spec_from_file_location("reusable_context_preflight", TOOL_PATH)
assert SPEC and SPEC.loader
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


class ReusableContextPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source_path = self.root / "ignition/source.txt"
        self.source_path.parent.mkdir()
        self.source_bytes = b"stable source bytes for a derived context card\n"
        self.source_path.write_bytes(self.source_bytes)
        self.source_digest = hashlib.sha256(self.source_bytes).hexdigest()
        self.source = {
            "source_id": "source-a",
            "path": "ignition/source.txt",
            "version": "v1",
            "sha256": self.source_digest,
            "access_scope_id": "scope-a",
            "access_state": "ACTIVE",
            "authorized": True,
        }
        self.card = {
            "card_id": "card-a",
            "source_bindings": [{
                "source_id": self.source["source_id"],
                "path": self.source["path"],
                "version": self.source["version"],
                "sha256": self.source["sha256"],
                "access_scope_id": self.source["access_scope_id"],
            }],
            "derived_context": "A caller-written, source-bound summary.",
        }
        self.request = {
            "schema_version": "toolbox-reusable-context-preflight-r0",
            "task": {
                "task_id": "task-a",
                "raw_source_required": False,
                "max_context_bytes": 1024,
                "max_source_bytes": 1024,
            },
            "current_sources": [self.source],
            "cached_cards": [self.card],
        }
        self.root_patch = patch.object(tool, "REPO_ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.temp.cleanup)

    def test_matching_bytes_and_scope_return_only_derived_context(self) -> None:
        before = self.source_path.read_bytes()
        result = tool.preflight(self.request)
        self.assertEqual(result["decision"], "CONTEXT_REUSED")
        self.assertEqual(result["decisions"][0]["decision"], "REUSE")
        self.assertEqual(result["reused_context_cards"][0]["context_kind"], "DERIVED_CONTEXT_ONLY")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["evidential_sufficiency"], "NOT_EVALUATED")
        self.assertEqual(result["resource_observation"]["source_bytes_read"], len(self.source_bytes))
        self.assertEqual(result["resource_observation"]["source_files_hashed"], 1)
        self.assertEqual(self.source_path.read_bytes(), before)

    def test_version_and_digest_change_invalidates_and_requests_refresh(self) -> None:
        changed = b"new source bytes\n"
        self.source_path.write_bytes(changed)
        self.request["current_sources"][0]["version"] = "v2"
        self.request["current_sources"][0]["sha256"] = hashlib.sha256(changed).hexdigest()
        result = tool.preflight(self.request)
        self.assertEqual(result["decision"], "NO_ELIGIBLE_CONTEXT")
        self.assertEqual(result["decisions"][0]["reason"], "SOURCE_VERSION_OR_DIGEST_CHANGED")
        self.assertEqual(result["refresh_required"][0]["reason"], "SOURCE_VERSION_OR_DIGEST_CHANGED")
        self.assertEqual(result["reused_context_cards"], [])

    def test_local_bytes_that_disagree_with_declared_current_digest_are_not_reused(self) -> None:
        self.source_path.write_bytes(b"changed without updating source declaration\n")
        result = tool.preflight(self.request)
        self.assertEqual(result["decisions"][0]["reason"], "CURRENT_SOURCE_DECLARATION_STALE")
        self.assertEqual(result["refresh_required"][0]["observed_local_sha256"], hashlib.sha256(self.source_path.read_bytes()).hexdigest())
        self.assertEqual(result["reused_context_cards"], [])

    def test_revoked_or_unauthorized_source_is_never_read(self) -> None:
        for state, authorized, reason in (
            ("REVOKED", True, "ACCESS_REVOKED"),
            ("ACTIVE", False, "CALLER_NOT_AUTHORIZED"),
            ("UNREADABLE", True, "ACCESS_UNREADABLE"),
            ("MISSING", True, "ACCESS_MISSING"),
        ):
            with self.subTest(state=state, authorized=authorized):
                self.request["current_sources"][0]["access_state"] = state
                self.request["current_sources"][0]["authorized"] = authorized
                result = tool.preflight(self.request)
                self.assertEqual(result["decision"], "NO_ELIGIBLE_CONTEXT")
                self.assertEqual(result["decisions"][0]["reason"], reason)
                self.assertEqual(result["resource_observation"]["source_bytes_read"], 0)
                self.assertEqual(result["reused_context_cards"], [])
        self.request["current_sources"][0].update(access_state="ACTIVE", authorized=True)

    def test_changed_access_scope_invalidates_without_returning_context(self) -> None:
        self.request["current_sources"][0]["access_scope_id"] = "scope-b"
        result = tool.preflight(self.request)
        self.assertEqual(result["decisions"][0]["reason"], "ACCESS_SCOPE_CHANGED")
        self.assertEqual(result["reused_context_cards"], [])

    def test_raw_source_requirement_skips_cards_and_requests_raw_reopen(self) -> None:
        self.request["task"]["raw_source_required"] = True
        result = tool.preflight(self.request)
        self.assertEqual(result["decisions"][0]["reason"], "RAW_SOURCE_REQUIRED")
        self.assertEqual(result["reused_context_cards"], [])
        self.assertEqual(result["raw_reopen_required"][0]["source_id"], "source-a")
        self.assertEqual(result["resource_observation"]["source_bytes_read"], 0)

    def test_context_budget_skips_without_invalidation(self) -> None:
        self.request["task"]["max_context_bytes"] = 3
        result = tool.preflight(self.request)
        self.assertEqual(result["decisions"][0]["decision"], "SKIP")
        self.assertEqual(result["decisions"][0]["reason"], "CONTEXT_BUDGET_EXCEEDED")
        self.assertEqual(result["refresh_required"], [])
        self.assertEqual(result["resource_observation"]["source_bytes_read"], 0)

    def test_unknown_source_binding_is_invalidated(self) -> None:
        self.request["current_sources"] = []
        result = tool.preflight(self.request)
        self.assertEqual(result["decisions"][0]["reason"], "CURRENT_SOURCE_NOT_DECLARED")
        self.assertEqual(result["reused_context_cards"], [])

    def test_traversal_and_symlink_paths_fail_closed(self) -> None:
        self.request["current_sources"][0]["path"] = "ignition/../outside.txt"
        with self.assertRaises(tool.ReusableContextError):
            tool.preflight(self.request)
        link = self.root / "ignition/link.txt"
        link.symlink_to(self.source_path)
        self.request["current_sources"][0]["path"] = "ignition/link.txt"
        self.request["cached_cards"][0]["source_bindings"][0]["path"] = "ignition/link.txt"
        with self.assertRaises(tool.ReusableContextError):
            tool.preflight(self.request)

    def test_duplicate_keys_and_duplicate_ids_fail_closed(self) -> None:
        stdin = io.StringIO('{"x":1,"x":2}')
        self.assertEqual(tool.run(stdin, io.StringIO(), io.StringIO()), 2)
        self.request["cached_cards"].append(dict(self.card))
        with self.assertRaises(tool.ReusableContextError):
            tool.preflight(self.request)

    def test_cli_writes_one_machine_readable_result(self) -> None:
        stdin = io.StringIO(json.dumps(self.request))
        stdout = io.StringIO()
        stderr = io.StringIO()
        self.assertEqual(tool.run(stdin, stdout, stderr), 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue())["decision"], "CONTEXT_REUSED")

    def _r1_request(self, expires_at_utc: str) -> dict:
        request = deepcopy(self.request)
        request["schema_version"] = "toolbox-reusable-context-preflight-r1"
        request["cached_cards"][0]["expires_at_utc"] = expires_at_utc
        return request

    def test_expired_r1_card_is_invalidated_before_source_bytes_are_read(self) -> None:
        now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
        result = tool.preflight(
            self._r1_request("2026-10-27T11:59:59Z"),
            now_utc=now,
        )
        self.assertEqual(result["schema_version"], "toolbox-reusable-context-preflight-result-r1")
        self.assertEqual(result["decision"], "NO_ELIGIBLE_CONTEXT")
        self.assertEqual(result["decisions"][0]["reason"], "MEMORY_CARD_EXPIRED")
        self.assertEqual(result["reused_context_cards"], [])
        self.assertEqual(result["resource_observation"]["source_bytes_read"], 0)
        self.assertEqual(result["resource_observation"]["source_files_hashed"], 0)
        self.assertEqual(result["refresh_required"][0]["expires_at_utc"], "2026-10-27T11:59:59Z")
        self.assertEqual(result["evaluated_at_utc"], "2026-10-27T12:00:00Z")

    def test_r1_expiry_boundary_is_inclusive_and_future_card_still_checks_sources(self) -> None:
        now = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)
        at_boundary = tool.preflight(
            self._r1_request("2026-10-27T12:00:00Z"),
            now_utc=now,
        )
        self.assertEqual(at_boundary["decisions"][0]["reason"], "MEMORY_CARD_EXPIRED")
        self.assertEqual(at_boundary["resource_observation"]["source_bytes_read"], 0)

        future = tool.preflight(
            self._r1_request("2026-10-27T12:00:01Z"),
            now_utc=now,
        )
        self.assertEqual(future["decision"], "CONTEXT_REUSED")
        self.assertEqual(future["reused_context_cards"][0]["expires_at_utc"], "2026-10-27T12:00:01Z")
        self.assertEqual(future["resource_observation"]["source_bytes_read"], len(self.source_bytes))
        self.assertEqual(future["evaluated_at_utc"], "2026-10-27T12:00:00Z")

    def test_r1_rejects_missing_noncanonical_and_invalid_expiry_timestamps(self) -> None:
        for value in (
            "2026-10-27T12:00:00+00:00",
            "2026-10-27T12:00:00.000Z",
            "2026-2-27T12:00:00Z",
            "2026-02-30T12:00:00Z",
            None,
        ):
            with self.subTest(value=value):
                request = self._r1_request("2026-10-27T12:00:00Z")
                request["cached_cards"][0]["expires_at_utc"] = value
                with self.assertRaises(tool.ReusableContextError):
                    tool.preflight(request)

        request = self._r1_request("2026-10-27T12:00:00Z")
        del request["cached_cards"][0]["expires_at_utc"]
        with self.assertRaises(tool.ReusableContextError):
            tool.preflight(request)

    def test_r1_requires_timezone_aware_evaluation_time(self) -> None:
        with self.assertRaises(tool.ReusableContextError):
            tool.preflight(
                self._r1_request("2026-10-27T12:00:01Z"),
                now_utc=datetime(2026, 10, 27, 12, 0, 0),
            )

    def test_legacy_r0_output_matches_v0_1_after_only_version_normalization(self) -> None:
        operations = IGNITION_ROOT / "data/operations"
        request = json.loads((operations / "toolbox-reusable-context-expiry-baseline-input-r0.json").read_text(encoding="utf-8"))
        baseline = json.loads((operations / "toolbox-reusable-context-expiry-baseline-output-v0-1.json").read_text(encoding="utf-8"))
        with patch.object(tool, "REPO_ROOT", IGNITION_ROOT.parent):
            result = tool.preflight(request)
        self.assertNotIn("evaluated_at_utc", result)
        self.assertEqual(result["schema_version"], "toolbox-reusable-context-preflight-result-r0")
        self.assertEqual(result["claim_ceiling"], baseline["claim_ceiling"])
        result["tool_version"] = "0.1.0"
        self.assertEqual(result, baseline)

    def test_real_expired_task_receipt_replays_without_reading_source(self) -> None:
        operations = IGNITION_ROOT / "data/operations"
        request = json.loads((operations / "toolbox-reusable-context-expiry-real-task-input-r1.json").read_text(encoding="utf-8"))
        expected = json.loads((operations / "toolbox-reusable-context-expiry-real-task-output-r1.json").read_text(encoding="utf-8"))
        timestamp = expected["evaluated_at_utc"]
        now = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        with patch.object(tool, "REPO_ROOT", IGNITION_ROOT.parent):
            result = tool.preflight(request, now_utc=now)
        self.assertEqual(result, expected)
        self.assertEqual(result["decisions"][0]["reason"], "MEMORY_CARD_EXPIRED")
        self.assertEqual(result["resource_observation"]["source_bytes_read"], 0)
        self.assertEqual(result["reused_context_cards"], [])

    def test_versioned_expiry_schemas_validate_real_task_and_comparison_evidence(self) -> None:
        operations = IGNITION_ROOT / "data/operations"
        schemas = IGNITION_ROOT / "schemas/operations"
        cases = (
            ("toolbox-reusable-context-preflight-r0.schema.json", "toolbox-reusable-context-expiry-baseline-input-r0.json"),
            ("toolbox-reusable-context-preflight-result-r0.schema.json", "toolbox-reusable-context-expiry-baseline-output-v0-1.json"),
            ("toolbox-reusable-context-preflight-r1.schema.json", "toolbox-reusable-context-expiry-real-task-input-r1.json"),
            ("toolbox-reusable-context-preflight-result-r1.schema.json", "toolbox-reusable-context-expiry-real-task-output-r1.json"),
            ("toolbox-reusable-context-expiry-c1-evidence-r0.schema.json", "toolbox-reusable-context-expiry-c1-evidence-r0.json"),
        )
        for schema_name, instance_name in cases:
            with self.subTest(schema=schema_name, instance=instance_name):
                schema = json.loads((schemas / schema_name).read_text(encoding="utf-8"))
                instance = json.loads((operations / instance_name).read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)
                self.assertEqual(list(Draft202012Validator(schema).iter_errors(instance)), [])

    def test_historical_real_task_receipt_is_not_treated_as_current_after_upgrade(self) -> None:
        receipt_path = IGNITION_ROOT / "data/operations/toolbox-reusable-context-preflight-real-task-r0.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        source = receipt["input"]["current_sources"][0]
        source_path = IGNITION_ROOT.parent / source["path"]
        tool_digest = hashlib.sha256(TOOL_PATH.read_bytes()).hexdigest()
        current_source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(receipt["tool_source_sha256"], r"^[0-9a-f]{64}$")
        self.assertNotEqual(current_source_digest, source["sha256"])
        self.assertNotEqual(receipt["tool_source_sha256"], tool_digest)
        self.assertEqual(receipt["output"]["decision"], "CONTEXT_REUSED")
        self.assertFalse(receipt["output"]["execution_authorized"])
        self.assertEqual(receipt["output"]["authority_effect"], "NONE")
        self.assertEqual(receipt["checks"]["semantic_relevance"], "NOT_EVALUATED")
        with patch.object(tool, "REPO_ROOT", IGNITION_ROOT.parent):
            current_result = tool.preflight(receipt["input"])
        self.assertEqual(current_result["decisions"][0]["reason"], "CURRENT_SOURCE_DECLARATION_STALE")
        self.assertEqual(current_result["reused_context_cards"], [])
        self.assertEqual(current_result["refresh_required"][0]["observed_local_sha256"], current_source_digest)


if __name__ == "__main__":
    unittest.main()
