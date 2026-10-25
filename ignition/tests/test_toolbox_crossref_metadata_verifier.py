from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlsplit


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_crossref_metadata_verifier.py"
SPEC = importlib.util.spec_from_file_location("toolbox_crossref_metadata_verifier", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


SAMPLE_MESSAGE = {
    "message": {
        "title": ["Causal inference in the medical domain: a survey"],
        "published": {"date-parts": [[2024]]},
        "type": "journal-article",
        "relation": {},
    }
}


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/json") -> None:
        self.body = body
        self.offset = 0
        self.read_calls = 0
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        end = len(self.body) if size < 0 else min(len(self.body), self.offset + size)
        value = self.body[self.offset:end]
        self.offset = end
        return value


class FakeOpener:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None) -> None:
        self.response = response or FakeResponse(json.dumps(SAMPLE_MESSAGE).encode("utf-8"))
        self.error = error
        self.calls: list[tuple[object, int]] = []

    def open(self, request: object, timeout: int) -> FakeResponse:
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


class FakeStdin:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


def request_bytes(records: list[dict[str, object]] | None = None) -> bytes:
    if records is None:
        records = [{
            "source_id": "GAP001-01",
            "doi": "10.1007/s10489-024-05338-9",
            "expected_title": SAMPLE_MESSAGE["message"]["title"][0],
            "expected_year": 2024,
        }]
    return json.dumps({"records": records}).encode("utf-8")


class CrossrefMetadataVerifierTests(unittest.TestCase):
    def test_live_lookup_is_fixed_host_and_returns_hashed_metadata_comparison(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin", "--allow-public-network"])

        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        request, timeout = opener.calls[0]
        self.assertEqual(urlsplit(request.full_url).hostname, "api.crossref.org")
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["status"], "ALL_METADATA_MATCHED")
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["rows"][0]["acquisition_status"], "OK")
        self.assertTrue(result["rows"][0]["full_match"])
        self.assertEqual(len(result["rows"][0]["response_sha256"]), 64)
        self.assertIn("does not validate article content", result["claim_ceiling"])

    def test_no_network_occurs_without_per_call_flag(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(len(opener.calls), 0)
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_rejects_url_like_doi_duplicate_json_keys_and_over_limit_batches(self) -> None:
        base = json.loads(request_bytes())
        bad_url = json.dumps({"records": [{**base["records"][0], "doi": "https://doi.org/10.1007/s10489-024-05338-9"}]}).encode()
        duplicate = b'{"records":[],"records":[]}'
        too_many = request_bytes([{
            "source_id": f"id-{i}", "doi": f"10.1234/test-{i}", "expected_title": "title", "expected_year": 2020,
        } for i in range(TOOL.MAX_RECORDS + 1)])
        for raw in (bad_url, duplicate, too_many):
            with self.subTest(raw=raw[:40]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_rejects_duplicate_dois_before_network(self) -> None:
        first = json.loads(request_bytes())["records"][0]
        second = {**first, "source_id": "GAP001-02"}
        with self.assertRaisesRegex(TOOL.ToolInputError, "unique"):
            TOOL.parse_request(request_bytes([first, second]))

    def test_explicitly_preserves_not_found_as_a_row(self) -> None:
        opener = FakeOpener(error=HTTPError("https://api.crossref.org/works/not-found", 404, "not found", {}, None))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            result = TOOL.verify(TOOL.parse_request(request_bytes()))
        self.assertEqual(result["status"], "COMPLETED_WITH_EXPLICIT_FAILURES")
        self.assertEqual(result["acquisition_failure_count"], 1)
        self.assertEqual(result["rows"][0]["acquisition_status"], "NOT_FOUND")
        self.assertIsNone(result["rows"][0]["title_match"])

    def test_redirects_are_blocked_and_response_size_is_bounded(self) -> None:
        redirect = FakeOpener(error=HTTPError("https://api.crossref.org/works/x", 302, "redirect", {}, None))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=redirect):
            result = TOOL._fetch_one("10.1234/example")
        self.assertEqual(result["acquisition_status"], "REDIRECT_BLOCKED")

        oversized = FakeOpener(response=FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=oversized):
            result = TOOL._fetch_one("10.1234/example")
        self.assertEqual(result["acquisition_status"], "RESPONSE_TOO_LARGE")

        slow = FakeOpener(response=FakeResponse(json.dumps(SAMPLE_MESSAGE).encode("utf-8")))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=slow), patch.object(TOOL.time, "monotonic", side_effect=[0.0, 8.0]):
            result = TOOL._fetch_one("10.1234/example")
        self.assertEqual(result["acquisition_status"], "RESPONSE_TIMEOUT")
        self.assertEqual(slow.response.read_calls, 0)

        slow_read = FakeOpener(response=FakeResponse(json.dumps(SAMPLE_MESSAGE).encode("utf-8")))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=slow_read), patch.object(TOOL.time, "monotonic", side_effect=[0.0, 0.0, 8.0]):
            result = TOOL._fetch_one("10.1234/example")
        self.assertEqual(result["acquisition_status"], "RESPONSE_TIMEOUT")
        self.assertEqual(slow_read.response.read_calls, 1)

    def test_malformed_request_emits_no_partial_result_and_creates_no_file(self) -> None:
        opener = FakeOpener()
        with tempfile.TemporaryDirectory() as directory:
            before = set(Path(directory).iterdir())
            with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                with patch.object(TOOL.sys, "stdin", FakeStdin(b'{"records":[]}')):
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                        code = TOOL.main(["--stdin", "--allow-public-network"])
            self.assertEqual(code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(set(Path(directory).iterdir()), before)
            self.assertEqual(len(opener.calls), 0)

    def test_network_error_is_not_silently_dropped(self) -> None:
        opener = FakeOpener(error=TimeoutError("timed out"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            result = TOOL.verify(TOOL.parse_request(request_bytes()))
        self.assertEqual(result["status"], "COMPLETED_WITH_EXPLICIT_FAILURES")
        self.assertEqual(result["rows"][0]["acquisition_status"], "NETWORK_ERROR")
        self.assertEqual(result["rows"][0]["http_status"], None)

    def test_upstream_helper_hash_mismatch_fails_before_import_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "unexpected-side-effect"
            helper = Path(directory) / "changed_helper.py"
            helper.write_text(f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n", encoding="utf-8")
            with patch.object(TOOL, "UPSTREAM_HELPERS_PATH", helper), patch.object(TOOL, "_sha256", return_value="0" * 64):
                with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                    TOOL._load_upstream_helpers()
            self.assertFalse(sentinel.exists())


if __name__ == "__main__":
    unittest.main()
