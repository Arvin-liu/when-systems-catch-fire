from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator

from tools.toolbox_handoff_advisory_selector import (
    INPUT_SCHEMA_VERSION,
    MAX_INPUT_BYTES,
    OUTPUT_SCHEMA_VERSION,
    evaluate,
    message_digest,
)
from tools.operations import plan_ignition_operation_run as planner


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
FIXTURE = IGNITION_ROOT / "tests/fixtures/toolbox-handoff-advisory-selection/valid-input-r0.json"
INPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-handoff-advisory-selection-input-r0.schema.json"
OUTPUT_SCHEMA = IGNITION_ROOT / "schemas/operations/toolbox-handoff-advisory-selection-output-r0.schema.json"
SCRIPT = IGNITION_ROOT / "tools/toolbox_handoff_advisory_selector.py"


def _message(
    message_id: str = "advice-1",
    *,
    kind: str = "ADVISORY",
    must_forward: bool = False,
    text: str = "Keep the unresolved question visible.",
    source_refs: list[str] | None = None,
) -> dict[str, object]:
    return {
        "message_id": message_id,
        "kind": kind,
        "must_forward": must_forward,
        "text": text,
        "source_refs": ["receipt://task/1"] if source_refs is None else source_refs,
    }


def _request(messages: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "schema_version": INPUT_SCHEMA_VERSION,
        "task_scope_id": "task-1",
        "receiver_state_ref": "receiver-r7",
        "receiver_context_message_digests": [],
        "messages": [_message()] if messages is None else messages,
    }


class HandoffAdvisorySelectorTests(unittest.TestCase):
    def test_checked_in_fixture_suggests_only_exact_duplicate_advisory(self):
        request = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result, code = evaluate(request)
        self.assertEqual(code, 0)
        self.assertEqual(result["selection_status"], "REVIEW_ONLY_CANDIDATE")
        self.assertEqual(result["retained_message_ids"], ["required-witness", "new-advice"])
        self.assertEqual([row["message_id"] for row in result["suggested_omissions"]], ["advice-already-seen"])
        self.assertFalse(result["send_authorized"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["handoff_transformed"])

    def test_exact_hash_matches_only_optional_advisory(self):
        message = _message()
        request = _request([message])
        request["receiver_context_message_digests"] = [
            message_digest("task-1", "receiver-r7", message["text"], message["source_refs"])
        ]
        result, code = evaluate(request)
        self.assertEqual(code, 0)
        self.assertEqual(result["retained_message_ids"], [])
        self.assertEqual(result["metrics"]["suggested_omission_count"], 1)

    def test_protected_and_unknown_kinds_are_never_omitted(self):
        messages = [
            _message(f"protected-{kind.lower()}", kind=kind)
            for kind in ("ACTION", "AUTHORITY", "OUTCOME", "WITNESS", "SOURCE", "UNKNOWN")
        ]
        request = _request(messages)
        request["receiver_context_message_digests"] = [
            message_digest("task-1", "receiver-r7", messages[0]["text"], messages[0]["source_refs"])
        ]
        result, code = evaluate(request)
        self.assertEqual(code, 0)
        self.assertEqual(result["retained_message_ids"], [item["message_id"] for item in messages])
        self.assertEqual(result["suggested_omissions"], [])

    def test_caller_marked_must_forward_advisory_is_retained(self):
        message = _message(must_forward=True)
        request = _request([message])
        request["receiver_context_message_digests"] = [
            message_digest("task-1", "receiver-r7", message["text"], message["source_refs"])
        ]
        result, _ = evaluate(request)
        self.assertEqual(result["retained_message_ids"], [message["message_id"]])
        self.assertEqual(result["suggested_omissions"], [])

    def test_text_match_with_different_source_refs_is_retained(self):
        message = _message(source_refs=["source://new-version"])
        request = _request([message])
        request["receiver_context_message_digests"] = [
            message_digest("task-1", "receiver-r7", message["text"], ["source://old-version"])
        ]
        result, _ = evaluate(request)
        self.assertEqual(result["retained_message_ids"], [message["message_id"]])
        self.assertEqual(result["suggested_omissions"], [])

    def test_task_scope_is_bound_into_message_hash(self):
        message = _message()
        request = _request([message])
        request["receiver_context_message_digests"] = [
            message_digest("another-task", "receiver-r7", message["text"], message["source_refs"])
        ]
        result, _ = evaluate(request)
        self.assertEqual(result["retained_message_ids"], [message["message_id"]])

    def test_repeated_pending_advisories_are_retained_even_if_context_has_hash(self):
        first = _message("advice-a")
        second = _message("advice-b")
        request = _request([first, second])
        request["receiver_context_message_digests"] = [
            message_digest("task-1", "receiver-r7", first["text"], first["source_refs"])
        ]
        result, _ = evaluate(request)
        self.assertEqual(result["retained_message_ids"], ["advice-a", "advice-b"])
        self.assertEqual(result["suggested_omissions"], [])

    def test_source_reference_order_is_preserved_as_identity(self):
        message = _message(source_refs=["source://a", "source://b"])
        request = _request([message])
        request["receiver_context_message_digests"] = [
            message_digest("task-1", "receiver-r7", message["text"], ["source://b", "source://a"])
        ]
        result, _ = evaluate(request)
        self.assertEqual(result["retained_message_ids"], [message["message_id"]])

    def test_receiver_revision_is_bound_into_message_hash(self):
        message = _message()
        request = _request([message])
        request["receiver_context_message_digests"] = [
            message_digest("task-1", "receiver-r6", message["text"], message["source_refs"])
        ]
        result, _ = evaluate(request)
        self.assertEqual(result["retained_message_ids"], [message["message_id"]])
        self.assertEqual(result["suggested_omissions"], [])

    def test_invalid_duplicate_ids_and_extra_fields_fail_closed(self):
        duplicate = _request([_message("same"), _message("same")])
        result, code = evaluate(duplicate)
        self.assertEqual(code, 2)
        self.assertEqual(result["selection_status"], "INPUT_INVALID")
        extra = _request([dict(_message(), authorization="yes")])
        result, code = evaluate(extra)
        self.assertEqual(code, 2)
        self.assertEqual(result["suggested_omissions"], [])

    def test_duplicate_source_refs_are_rejected(self):
        result, code = evaluate(_request([_message(source_refs=["x", "x"])]))
        self.assertEqual(code, 2)
        self.assertEqual(result["selection_status"], "INPUT_INVALID")

    def test_fixture_and_output_validate_against_schemas(self):
        request = json.loads(FIXTURE.read_text(encoding="utf-8"))
        input_schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(input_schema).validate(request)
        result, _ = evaluate(request)
        Draft202012Validator(output_schema).validate(result)
        self.assertEqual(result["schema_version"], OUTPUT_SCHEMA_VERSION)

    def test_route_is_default_off_and_explicit_allowlist_does_not_authorize_execution(self):
        catalog = json.loads(
            (IGNITION_ROOT / "data/operations/toolbox-candidate-cards-r0.json").read_text(encoding="utf-8")
        )
        card = next(row for row in catalog["candidates"] if row["tool_id"] == "collaboration.select_handoff_advisories")
        profile = {
            "task_id": "handoff-advisory-route-c1-01",
            "current_ref": "receiver-handoff-composition-review",
            "input_types": card["accepted_input_types"],
            "required_outputs": card["output_types"],
            "allowed_execution_modes": ["READ_ONLY_RUN"],
        }

        default = planner.plan_tool_route(profile)
        opted_in = planner.plan_tool_route(profile, include_experimental_tool_ids=[card["tool_id"]])

        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(opted_in["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in opted_in["selected_tools"]], [card["tool_id"]])
        self.assertFalse(opted_in["execution_authorized"])
        self.assertFalse(opted_in["selected_tools"][0]["permissions"]["network"])
        self.assertEqual(opted_in["selected_tools"][0]["permissions"]["write_paths"], [])
        self.assertRegex(opted_in["source_refs"]["experimental_candidate_catalog_git_blob_sha1"], r"^[0-9a-f]{40}$")
        route_path = IGNITION_ROOT / "data/operations/toolbox-handoff-advisory-selection-route-evidence-r0.json"
        c1_path = IGNITION_ROOT / "data/operations/toolbox-handoff-advisory-selection-c1-evidence-r0.json"
        route_evidence = json.loads(route_path.read_text(encoding="utf-8"))
        c1_evidence = json.loads(c1_path.read_text(encoding="utf-8"))
        self.assertEqual(route_evidence["candidate_catalog_blob_sha1"], opted_in["source_refs"]["experimental_candidate_catalog_git_blob_sha1"])
        self.assertEqual(route_evidence["default_off"]["decision"], default["decision"])
        self.assertEqual(route_evidence["explicit_allowlist"]["selected_tool_ids"], [card["tool_id"]])
        self.assertEqual(
            c1_evidence["route_experiment"]["receipt_sha256"],
            hashlib.sha256(route_path.read_bytes()).hexdigest(),
        )

    def test_cli_emits_one_machine_readable_result(self):
        request = FIXTURE.read_bytes()
        proc = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--stdin"],
            input=request,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", errors="replace"))
        result = json.loads(proc.stdout.decode("utf-8"))
        self.assertEqual(result["suggested_omissions"][0]["message_id"], "advice-already-seen")
        self.assertEqual(proc.stderr, b"")

    def test_duplicate_json_keys_and_oversized_stdin_fail_closed(self):
        for data in (b'{"schema_version":"x","schema_version":"y"}', b" " * (MAX_INPUT_BYTES + 1)):
            proc = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--stdin"],
                input=data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=REPO_ROOT,
                check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(proc.stdout.decode("utf-8"))["selection_status"], "INPUT_INVALID")
            self.assertEqual(proc.stderr, b"")


if __name__ == "__main__":
    unittest.main()
