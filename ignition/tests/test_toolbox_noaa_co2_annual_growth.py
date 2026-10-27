from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError
from urllib.parse import urlsplit
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import toolbox_noaa_co2_annual_growth as TOOL  # noqa: E402


TABLE = b"""# NOAA Global Monitoring Laboratory
# Annual CO2 mole fraction increase (ppm) from Jan 1 through Dec 31.
# year     ann inc         unc
  2023       2.69        0.13
  2024       3.76        0.11
  2025       2.06        0.08
"""


class FakeResponse:
    def __init__(self, body: bytes = TABLE, *, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
        self.body = body
        self.offset = 0
        self.status = status
        self.headers = {
            "Content-Type": content_type,
            "ETag": '"test-etag"',
            "Last-Modified": "Fri, 09 Oct 2026 19:23:08 GMT",
        }

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
        self.response = response or FakeResponse()
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


def request_bytes(start: int = 2023, end: int = 2025) -> bytes:
    return json.dumps({"start_year": start, "end_year": end}).encode("utf-8")


class NoaaCo2AnnualGrowthTests(unittest.TestCase):
    def test_lookup_uses_fixed_host_and_returns_requested_records_and_provenance(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = TOOL.lookup(request_bytes())
        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "gml.noaa.gov")
        self.assertEqual(parsed.path, "/webdata/ccgg/trends/co2/co2_gr_gl.txt")
        self.assertEqual(parsed.query, "")
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(result["records"], [
            {"year": 2023, "annual_increase_ppm": 2.69, "uncertainty_ppm": 0.13},
            {"year": 2024, "annual_increase_ppm": 3.76, "uncertainty_ppm": 0.11},
            {"year": 2025, "annual_increase_ppm": 2.06, "uncertainty_ppm": 0.08},
        ])
        self.assertEqual(result["etag"], '"test-etag"')
        self.assertEqual(len(result["response_sha256"]), 64)
        self.assertIn("not an emissions inventory", " ".join(result["source_caveats"]))

    def test_cli_requires_per_call_network_flag_before_any_request(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(opener.calls, [])
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_request_rejects_extra_keys_duplicates_bools_and_unbounded_ranges(self) -> None:
        invalid = [
            b'{"start_year":2023,"end_year":2025,"url":"https://example.org"}',
            b'{"start_year":2023,"start_year":2024,"end_year":2025}',
            b'{"start_year":true,"end_year":2025}',
            request_bytes(1984, 2034),
            request_bytes(2025, 2024),
            json.dumps({"start_year": 1958, "end_year": 1959}).encode(),
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_table_returns_partial_or_no_match_without_inventing_missing_years(self) -> None:
        partial = TOOL._parse_table(TABLE, 2024, 2026)
        self.assertEqual(partial["status"], "PARTIAL_DATA")
        self.assertEqual([row["year"] for row in partial["records"]], [2024, 2025])
        missing = TOOL._parse_table(TABLE, 2026, 2027)
        self.assertEqual(missing, {"status": "NO_MATCH", "records": []})

    def test_redirect_wrong_content_type_oversize_and_malformed_table_fail_closed(self) -> None:
        redirect = HTTPError(TOOL.SOURCE_URL, 302, "Found", {}, None)
        for error, expected in ((redirect, "REDIRECT_BLOCKED"),):
            opener = FakeOpener(error=error)
            with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
                self.assertEqual(TOOL._fetch()["acquisition_status"], expected)

        wrong_type = FakeOpener(FakeResponse(content_type="application/json"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=wrong_type):
            self.assertEqual(TOOL._fetch()["acquisition_status"], "NON_TEXT_RESPONSE")

        oversized = FakeOpener(FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=oversized):
            with patch.object(TOOL, "MAX_RESPONSE_DURATION_SECONDS", 30):
                self.assertEqual(TOOL._fetch()["acquisition_status"], "RESPONSE_TOO_LARGE")

        malformed = TABLE.replace(b"2024       3.76", b"2024 bad row")
        self.assertEqual(TOOL._parse_table(malformed, 2023, 2025)["status"], "INVALID_PROVIDER_RESPONSE")
        wrong_species = TABLE.replace(b"Annual CO2 mole fraction", b"Annual CH4 mole fraction")
        self.assertEqual(TOOL._parse_table(wrong_species, 2023, 2025)["status"], "INVALID_PROVIDER_RESPONSE")


if __name__ == "__main__":
    unittest.main()
