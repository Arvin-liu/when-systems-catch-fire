from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError
from urllib.parse import urlsplit
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_noaa_sf6_annual_growth_lookup as TOOL  # noqa: E402


TABLE = b"""# NOAA Global Monitoring Laboratory
# Annual SF6 mole fraction increase (ppt) from Jan 1 through Dec 31.
# year     ann inc         unc
  2023        0.41        0.00
  2024        0.40        0.00
  2025        0.48        0.00
"""


class FakeResponse:
    def __init__(self, body: bytes = TABLE, *, content_type: str = "text/plain; charset=utf-8") -> None:
        self.body = body
        self.offset = 0
        self.status = 200
        self.headers = {
            "Content-Type": content_type,
            "ETag": '"test-etag"',
            "Last-Modified": "Fri, 09 Oct 2026 19:13:01 GMT",
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
    return json.dumps({
        "schema_version": TOOL.INPUT_SCHEMA_VERSION,
        "start_year": start,
        "end_year": end,
    }).encode("utf-8")


class NoaaSf6AnnualGrowthLookupTests(unittest.TestCase):
    def test_lookup_makes_one_fixed_host_request_and_preserves_raw_precision(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL._core.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = TOOL.lookup(request_bytes())

        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "gml.noaa.gov")
        self.assertEqual(parsed.path, "/webdata/ccgg/trends/sf6/sf6_gr_gl.txt")
        self.assertEqual(parsed.query, "")
        self.assertEqual(timeout, TOOL._core.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(result["source"]["records"], [
            {"year": 2023, "annual_increase_ppt": "0.41", "uncertainty_ppt": "0.00"},
            {"year": 2024, "annual_increase_ppt": "0.40", "uncertainty_ppt": "0.00"},
            {"year": 2025, "annual_increase_ppt": "0.48", "uncertainty_ppt": "0.00"},
        ])
        self.assertEqual(result["source"]["response_sha256"], hashlib.sha256(TABLE).hexdigest())
        self.assertFalse(result["source"]["raw_response_retained"])
        self.assertEqual(result["invocation"]["requests_made"], 1)
        self.assertIn("rounded precision", " ".join(result["source_caveats"]))
        self.assertNotIn("body", result)

    def test_cli_requires_per_call_network_flag_before_any_request(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL._core.urllib.request, "build_opener", return_value=opener):
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(opener.calls, [])
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("NETWORK_CALL_REQUIRES_ALLOW_PUBLIC_NETWORK", stderr.getvalue())

    def test_request_rejects_extra_duplicate_boolean_wrong_schema_and_unbounded_ranges(self) -> None:
        invalid = [
            b'{"schema_version":"toolbox-noaa-sf6-annual-growth-lookup-input-r0","start_year":2023,"end_year":2025,"url":"https://example.org"}',
            b'{"schema_version":"toolbox-noaa-sf6-annual-growth-lookup-input-r0","start_year":2023,"start_year":2024,"end_year":2025}',
            b'{"schema_version":"toolbox-noaa-sf6-annual-growth-lookup-input-r0","start_year":true,"end_year":2025}',
            request_bytes(2025, 2024),
            request_bytes(1998, 2048),
            request_bytes(1997, 1998),
            b'{"schema_version":"wrong","start_year":2023,"end_year":2025}',
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_partial_and_no_match_are_explicit_not_zero_filled(self) -> None:
        partial = TOOL._core._parse_raw_table(TABLE, 2024, 2026, TOOL.PROFILE)
        self.assertEqual(partial["status"], "PARTIAL_DATA")
        self.assertEqual([row["year"] for row in partial["records"]], [2024, 2025])
        missing = TOOL._core._parse_raw_table(TABLE, 2026, 2027, TOOL.PROFILE)
        self.assertEqual(missing, {"status": "NO_MATCH", "records": []})

    def test_redirect_wrong_content_type_oversize_wrong_species_and_malformed_rows_fail_closed(self) -> None:
        redirect = HTTPError(TOOL.PROFILE.raw_url, 302, "Found", {}, None)
        redirect_opener = FakeOpener(error=redirect)
        with patch.object(TOOL._core.urllib.request, "build_opener", return_value=redirect_opener):
            self.assertEqual(
                TOOL._core._fetch(TOOL.PROFILE.raw_url, TOOL.PROFILE.raw_path, "text/plain", TOOL.PROFILE)["acquisition_status"],
                "REDIRECT_BLOCKED",
            )

        wrong_type = FakeOpener(FakeResponse(content_type="application/json"))
        with patch.object(TOOL._core.urllib.request, "build_opener", return_value=wrong_type):
            self.assertEqual(
                TOOL._core._fetch(TOOL.PROFILE.raw_url, TOOL.PROFILE.raw_path, "text/plain", TOOL.PROFILE)["acquisition_status"],
                "NON_TEXT_RESPONSE",
            )

        oversized = FakeOpener(FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)))
        with patch.object(TOOL._core.urllib.request, "build_opener", return_value=oversized):
            with patch.object(TOOL._core, "MAX_RESPONSE_DURATION_SECONDS", 30):
                self.assertEqual(
                    TOOL._core._fetch(TOOL.PROFILE.raw_url, TOOL.PROFILE.raw_path, "text/plain", TOOL.PROFILE)["acquisition_status"],
                    "RESPONSE_TOO_LARGE",
                )

        wrong_species = TABLE.replace(b"Annual SF6", b"Annual N2O")
        malformed = TABLE.replace(b"2024        0.40", b"2024        bad ")
        negative_uncertainty = TABLE.replace(b"2024        0.40        0.00", b"2024        0.40       -0.01")
        for body in (wrong_species, malformed, negative_uncertainty):
            with self.subTest(body=body):
                self.assertEqual(
                    TOOL._core._parse_raw_table(body, 2023, 2025, TOOL.PROFILE)["status"],
                    "INVALID_PROVIDER_RESPONSE",
                )


if __name__ == "__main__":
    unittest.main()
