from __future__ import annotations

import hashlib
import json
import os
import signal
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import runtime_executor as runtime  # noqa: E402
import runtime_supervisor as supervisor  # noqa: E402


class RequestEnvelopeTests(unittest.TestCase):
    def test_request_has_explicit_empty_tool_surface_and_no_state_fields(self) -> None:
        body = runtime.build_canary_request()
        decoded = json.loads(body.decode("utf-8"))
        self.assertEqual(body, runtime.canonical_json_bytes(decoded))
        self.assertEqual(decoded["model"], "gpt-6-astra")
        self.assertEqual(decoded["reasoning"], {"effort": "medium"})
        self.assertEqual(decoded["tools"], [])
        self.assertEqual(decoded["tool_choice"], "none")
        self.assertIs(decoded["store"], False)
        self.assertFalse({"conversation", "previous_response_id", "prompt_cache_key"} & set(decoded))
        self.assertFalse({"temperature", "top_p", "seed", "background"} & set(decoded))

    def test_unit_hash_mismatch_fails_before_request_construction(self) -> None:
        fields = {
            "case_prose": "synthetic",
            "policy_json_utf8": "{}",
            "reference_execution_json_utf8": "{}",
            "typed_binding_json_utf8": "{}",
        }
        hashes = {
            "case_prose_sha256": hashlib.sha256(b"wrong").hexdigest(),
            "policy_sha256": hashlib.sha256(b"{}").hexdigest(),
            "reference_execution_sha256": hashlib.sha256(b"{}").hexdigest(),
            "binding_sha256": hashlib.sha256(b"{}").hexdigest(),
            "source_case_record_sha256": "0" * 64,
            "prompt_template_sha256": "0" * 64,
            "response_schema_sha256": "0" * 64,
            "route_trace_schema_sha256": "0" * 64,
        }
        row = {"run_id": "fixture", "successor_inputs": fields, "input_hashes": hashes}
        with self.assertRaisesRegex(runtime.RuntimeContractError, "SUCCESSOR_INPUT_HASH_MISMATCH"):
            runtime.load_unit_record(runtime.canonical_json_bytes(row))

    def test_model_input_framing_is_byte_deterministic(self) -> None:
        inputs = {key: "fixture" for key in runtime.SUCCESSOR_KEYS}
        got = runtime.build_model_input(b"prompt\n", b"{\"type\":\"object\"}", inputs)
        expected = (
            b"prompt\n\n\nFROZEN_RESPONSE_SCHEMA_JSON_UTF8:\n"
            b"{\"type\":\"object\"}\n\nSUCCESSOR_INPUTS_CANONICAL_JSON_UTF8:\n"
            + runtime.canonical_json_bytes(inputs)
        )
        self.assertEqual(got, expected)
        self.assertEqual(runtime.build_model_input(b"prompt\n", b"{\"type\":\"object\"}", inputs), got)

    def test_canary_request_contains_only_synthetic_target_blind_input(self) -> None:
        request = json.loads(runtime.build_canary_request().decode("utf-8"))
        self.assertEqual(request["input"], runtime.CANARY_TEXT)
        self.assertNotIn("R4-", request["input"])
        self.assertNotIn("policy", request["input"].lower())

    def test_live_cli_is_inert_without_follow_on_owner_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ, {}, clear=True):
            rc = runtime.main(["--execute-live", "--canary", "--capture-dir", temp])
            self.assertEqual(rc, 3)
            self.assertEqual(list(Path(temp).iterdir()), [])


class ResponseCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ROOT / "tests" / "fixtures" / "response-completed.json"
        self.tool_fixture = ROOT / "tests" / "fixtures" / "response-tool-call.json"
        self.refusal_fixture = ROOT / "tests" / "fixtures" / "response-refusal.json"

    def test_capture_preserves_transport_then_exact_payload_hash_before_schema(self) -> None:
        raw = self.fixture.read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            result = runtime.persist_response(raw, target, http_status=200, headers={"content-encoding": "identity"})
            self.assertEqual((target / "transport-response.bin").read_bytes(), raw)
            self.assertEqual((target / "transport-response.sha256").read_text().strip(), hashlib.sha256(raw).hexdigest())
            payload = b'{"fixture":"ok"}'
            self.assertEqual((target / "successor-payload.bin").read_bytes(), payload)
            self.assertEqual((target / "successor-payload.sha256").read_text().strip(), hashlib.sha256(payload).hexdigest())
            self.assertFalse(result["schema_parse_performed"])
            self.assertEqual(result["status"], "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION")

    def test_payload_cap_below_at_and_above_without_truncation(self) -> None:
        for size, expected_status in [
            (runtime.SUCCESSOR_PAYLOAD_MAX_BYTES - 1, "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION"),
            (runtime.SUCCESSOR_PAYLOAD_MAX_BYTES, "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION"),
            (runtime.SUCCESSOR_PAYLOAD_MAX_BYTES + 1, "SUCCESSOR_PAYLOAD_TOO_LARGE"),
        ]:
            text = "x" * size
            raw = json.dumps({
                "id": "resp_fixture", "model": runtime.MODEL, "status": "completed",
                "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}],
            }, separators=(",", ":")).encode("utf-8")
            with self.subTest(size=size), tempfile.TemporaryDirectory() as temp:
                target = Path(temp)
                result = runtime.persist_response(raw, target, http_status=200, headers={})
                self.assertEqual(result["status"], expected_status)
                self.assertEqual(result["successor_payload_bytes"], size)
                self.assertEqual(len((target / "successor-payload.bin").read_bytes()), size)

    def test_payload_cap_counts_utf8_bytes_not_characters(self) -> None:
        text = "界" * 5461 + "a"  # 16,384 UTF-8 bytes, 5,462 Unicode characters.
        raw = json.dumps({
            "id": "resp_fixture", "model": runtime.MODEL, "status": "completed",
            "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}],
        }, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        with tempfile.TemporaryDirectory() as temp:
            result = runtime.persist_response(raw, Path(temp), http_status=200, headers={})
            self.assertEqual(result["successor_payload_bytes"], 16_384)
            self.assertEqual(result["status"], "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION")

    def test_malformed_and_ambiguous_responses_fail_closed(self) -> None:
        invalid_cases = [
            b"\xff",
            b'{"status":"completed","status":"failed"}',
            self.tool_fixture.read_bytes(),
            self.refusal_fixture.read_bytes(),
            b'{"id":"x","model":"gpt-6-astra","status":"incomplete","output":[]}',
            json.dumps({"id": "x", "model": runtime.MODEL, "status": "completed", "output": [
                {"type": "message", "role": "assistant", "content": [
                    {"type": "output_text", "text": "a"}, {"type": "output_text", "text": "b"}
                ]}
            ]}).encode(),
            b'{"id":"x","model":"gpt-6-astra","status":"completed","output":[{"type":"message","role":"assistant","content":[{"type":"output_text","text":"\\ud800"}]}]}',
        ]
        for raw in invalid_cases:
            with self.subTest(prefix=raw[:30]), tempfile.TemporaryDirectory() as temp:
                result = runtime.persist_response(raw, Path(temp), http_status=200, headers={})
                self.assertEqual(result["status"], "RESPONSE_EXTRACTION_REJECTED")
                self.assertTrue((Path(temp) / "transport-response.bin").exists())

    def test_non_200_and_content_encoding_do_not_extract(self) -> None:
        raw = self.fixture.read_bytes()
        for status, headers, expected in [
            (429, {}, "HTTP_STATUS_NOT_200"),
            (200, {"content-encoding": "gzip"}, "UNSUPPORTED_CONTENT_ENCODING"),
        ]:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temp:
                result = runtime.persist_response(raw, Path(temp), http_status=status, headers=headers)
                self.assertEqual(result["status"], expected)
                self.assertFalse((Path(temp) / "successor-payload.bin").exists())

    def test_incomplete_transport_capture_is_never_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            raw = self.fixture.read_bytes()[:10]
            result = runtime.persist_response(
                raw, target, http_status=200, headers={"content-length": "999"},
                transport_capture_complete=False,
                transport_incomplete_reason="INCOMPLETE_HTTP_RESPONSE_BODY",
            )
            self.assertEqual(result["status"], "INCOMPLETE_HTTP_RESPONSE_BODY")
            self.assertEqual((target / "transport-response.bin").read_bytes(), raw)
            self.assertFalse((target / "successor-payload.bin").exists())

    def test_worker_process_enforces_one_provider_request(self) -> None:
        raw_response = self.fixture.read_bytes()
        requests = []

        class FakeResponse:
            status = 200
            headers = {}

            def read(self, _limit: int) -> bytes:
                return raw_response

        class FakeConnection:
            def __init__(self, _host: str, *, timeout: int, context: object) -> None:
                self.timeout = timeout
                self.context = context

            def request(self, method: str, path: str, *, body: bytes, headers: dict[str, str]) -> None:
                requests.append((method, path, body, headers))

            def getresponse(self) -> FakeResponse:
                return FakeResponse()

            def close(self) -> None:
                pass

        with mock.patch.object(runtime, "_REQUESTS_STARTED", 0), \
                mock.patch.object(runtime.http.client, "HTTPSConnection", FakeConnection), \
                tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            result = runtime.send_one_request(runtime.build_canary_request(), target / "one", "fixture-key")
            self.assertEqual(result["status"], "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION")
            with self.assertRaisesRegex(runtime.RuntimeContractError, "ONE_PROVIDER_REQUEST_PER_PROCESS"):
                runtime.send_one_request(runtime.build_canary_request(), target / "two", "fixture-key")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0][0:2], ("POST", "/v1/responses"))

    def test_canary_passes_only_on_exact_synthetic_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / "successor-payload.bin").write_bytes(runtime.CANARY_EXPECTED.encode("ascii"))
            good = {
                "status": "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION",
                "http_status": 200,
                "accepted_model_echo": runtime.MODEL,
                "request_body_sha256": "1" * 64,
                "transport_response_sha256": "2" * 64,
                "successor_payload_sha256": hashlib.sha256(runtime.CANARY_EXPECTED.encode("ascii")).hexdigest(),
                "successor_payload_bytes": len(runtime.CANARY_EXPECTED.encode("ascii")),
                "transport_response_bytes": 128,
            }
            outcome = runtime.record_canary_outcome(good, target)
            self.assertEqual(outcome["status"], "CANARY_RUNTIME_GATE_PASSED")
            self.assertFalse(outcome["backend_effort_echo_claimed"])
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            (target / "successor-payload.bin").write_bytes(b"different")
            outcome = runtime.record_canary_outcome(good, target)
            self.assertEqual(outcome["status"], "CANARY_OUTPUT_MISMATCH")


class SupervisorTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "process-group enforcement requires POSIX")
    def test_timeout_kills_entire_process_group_without_retry(self) -> None:
        self.assertEqual(supervisor.SUPERVISOR_TIMEOUT_SECONDS, 300)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            marker = target / "grandchild-terminated"
            grandchild = (
                "import signal,time,pathlib,sys\n"
                f"p=pathlib.Path({str(marker)!r})\n"
                "def stop(*_):\n    p.write_text('terminated')\n    sys.exit(0)\n"
                "signal.signal(signal.SIGTERM, stop)\n"
                "time.sleep(60)\n"
            )
            parent = (
                "import signal,subprocess,sys,time\n"
                f"child=subprocess.Popen([sys.executable,'-c',{grandchild!r}])\n"
                "def stop(*_):\n    child.wait(timeout=2)\n    sys.exit(0)\n"
                "signal.signal(signal.SIGTERM, stop)\n"
                "time.sleep(60)\n"
            )
            result = supervisor.run_supervised([sys.executable, "-c", parent], timeout_seconds=0.25)
            self.assertEqual(result["status"], "EXTERNAL_TIMEOUT")
            self.assertEqual(result["retry_count"], 0)
            self.assertEqual(result["timeout_seconds"], 0.25)
            self.assertEqual(result["session_id"], result["pid"])
            self.assertTrue(result["cleanup_complete"])
            self.assertTrue(marker.exists(), "grandchild did not receive process-group termination")


if __name__ == "__main__":
    unittest.main()
