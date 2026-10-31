from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import toolbox_arxiv_metadata_lookup as TOOL  # noqa: E402

ARXIV_ID = "2610.04074"
ENTRY = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
<opensearch:totalResults>1</opensearch:totalResults><entry>
<id>https://arxiv.org/abs/2610.04074v2</id><title>  Example   title </title>
<author><name>Author One</name></author><published>2026-10-09T00:00:00Z</published><updated>2026-10-09T00:00:00Z</updated>
<arxiv:primary_category term="cs.AI"/><category term="cs.AI"/><arxiv:journal_ref>Journal ref</arxiv:journal_ref><arxiv:doi>10.1234/example</arxiv:doi>
<summary>abstract must not leave the parser</summary></entry></feed>'''


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/atom+xml") -> None:
        self.body = body
        self.offset = 0
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        end = len(self.body) if size < 0 else min(len(self.body), self.offset + size)
        chunk = self.body[self.offset:end]
        self.offset = end
        return chunk


class FakeOpener:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None) -> None:
        self.response = response or FakeResponse(ENTRY)
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


def request_bytes(arxiv_id: str = ARXIV_ID) -> bytes:
    return json.dumps({"arxiv_id": arxiv_id}).encode("utf-8")


class ArxivMetadataLookupTests(unittest.TestCase):
    def test_live_lookup_uses_one_fixed_host_request_and_returns_selected_metadata_only(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = TOOL.lookup(request_bytes())
        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "export.arxiv.org")
        self.assertEqual(parsed.path, "/api/query")
        self.assertEqual(parse_qs(parsed.query), {"id_list": [ARXIV_ID]})
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(result["record"]["entry_id"], "https://arxiv.org/abs/2610.04074v2")
        self.assertEqual(result["record"]["title"], "Example title")
        self.assertEqual(result["record"]["authors"], ["Author One"])
        self.assertEqual(result["record"]["primary_category"], "cs.AI")
        self.assertNotIn("summary", json.dumps(result))
        self.assertNotIn("Example abstract", json.dumps(result))
        self.assertEqual(len(result["response_sha256"]), 64)

    def test_network_requires_per_call_flag_and_exact_single_identifier(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.calls, [])
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_cli_explicit_opt_in_emits_one_json_receipt(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                code = TOOL.main(["--arxiv-id", ARXIV_ID, "--allow-public-network"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(json.loads(stdout.getvalue())["tool_id"], TOOL.TOOL_ID)

    def test_rejects_urls_dois_old_ids_malformed_versions_duplicate_keys_and_large_inputs(self) -> None:
        bad_inputs = [
            b'{"arxiv_id":"https://arxiv.org/abs/2610.04074"}',
            b'{"arxiv_id":"10.1234/example"}',
            b'{"arxiv_id":"cs/9901001"}',
            b'{"arxiv_id":"2613.04074"}',
            b'{"arxiv_id":"2610.04074v0"}',
            b'{"arxiv_id":"2610.04074","arxiv_id":"2610.04075"}',
            b" " * (TOOL.MAX_REQUEST_BYTES + 1),
        ]
        for raw in bad_inputs:
            with self.subTest(raw=raw[:40]), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_no_match_api_error_and_malformed_xml_do_not_emit_partial_metadata(self) -> None:
        cases = [
            (b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>0</opensearch:totalResults></feed>', "NO_MATCH"),
            (b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>1</opensearch:totalResults><entry><id>http://arxiv.org/api/errors#bad</id></entry></feed>', "PROVIDER_ERROR_ENTRY"),
            (b'<!DOCTYPE feed [<!ENTITY x "x">]><feed/>', "INVALID_XML_RESPONSE"),
            (b'<not-feed/>', "INVALID_PROVIDER_RESPONSE"),
        ]
        for body, expected in cases:
            opener = FakeOpener(FakeResponse(body))
            with self.subTest(status=expected), patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                result = TOOL.lookup(request_bytes())
            self.assertEqual(result["status"], expected)
            self.assertIsNone(result["record"])

    def test_rejects_unbound_provider_links_and_oversized_responses(self) -> None:
        for unsafe in [b"https://arxiv.org:443/abs/2610.04074v2", b"https://arxiv.org:bad/abs/2610.04074v2", b"https://[broken/abs/2610.04074v2"]:
            bad_entry = ENTRY.replace(b"https://arxiv.org/abs/2610.04074v2", unsafe)
            opener = FakeOpener(FakeResponse(bad_entry))
            with self.subTest(provider_entry_id=unsafe), patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                result = TOOL.lookup(request_bytes())
            self.assertEqual(result["status"], "INVALID_PROVIDER_RESPONSE")
            self.assertIsNone(result["record"])

        oversized = FakeOpener(FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=oversized):
            result = TOOL.lookup(request_bytes())
        self.assertEqual(result["status"], "RESPONSE_TOO_LARGE")
        self.assertIsNone(result["record"])

    def test_rejects_wrong_content_type_redirects_and_network_errors(self) -> None:
        non_xml = FakeOpener(FakeResponse(ENTRY, content_type="text/html"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=non_xml):
            self.assertEqual(TOOL.lookup(request_bytes())["status"], "NON_ATOM_RESPONSE")
        redirect = FakeOpener(error=HTTPError("https://export.arxiv.org", 302, "redirect", {}, None))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=redirect):
            self.assertEqual(TOOL.lookup(request_bytes())["status"], "REDIRECT_BLOCKED")
        offline = FakeOpener(error=OSError("offline"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=offline):
            self.assertEqual(TOOL.lookup(request_bytes())["status"], "NETWORK_ERROR")


if __name__ == "__main__":
    unittest.main()
