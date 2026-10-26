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


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import toolbox_compare_noaa_co2_surfaces as TOOL  # noqa: E402


PAGE = b"""<!doctype html>
<html><body>
<h3>Annual Mean Global Carbon Dioxide Growth Rates</h3>
<table>
<thead><tr><th>Year</th><th>Growth (ppm)</th><th>Uncertainty (ppm)</th></tr></thead>
<tbody>
<tr><td>2023</td><td>2.69</td><td>0.13</td></tr>
<tr><td>2024</td><td>3.76</td><td>0.11</td></tr>
<tr><td>2025</td><td>2.06</td><td>0.08</td></tr>
</tbody></table></body></html>
"""
PAGE_DIFFERENT = PAGE.replace(b"<td>2.69</td>", b"<td>2.70</td>", 1)
RAW = b"""# NOAA Global Monitoring Laboratory
# Annual CO2 mole fraction increase (ppm) from Jan 1 through Dec 31.
# year     ann inc         unc
  2023       2.69        0.13
  2024       3.76        0.11
  2025       2.06        0.08
"""


class FakeResponse:
    def __init__(self, body: bytes, content_type: str, *, status: int = 200) -> None:
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
        self.response = response or FakeResponse(PAGE, "text/html")
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


def fetch_with_bodies(page: bytes = PAGE, raw: bytes = RAW):
    page_opener = FakeOpener(FakeResponse(page, "text/html; charset=utf-8"))
    raw_opener = FakeOpener(FakeResponse(raw, "text/plain; charset=utf-8"))
    with patch.object(
        TOOL.urllib.request,
        "build_opener",
        side_effect=[page_opener, raw_opener],
    ) as build_opener:
        result = TOOL.lookup(request_bytes())
    return result, build_opener, page_opener, raw_opener


class NoaaCo2SourceSurfaceComparisonTests(unittest.TestCase):
    def test_live_contract_compares_only_two_fixed_noaa_surfaces(self) -> None:
        result, build_opener, page_opener, raw_opener = fetch_with_bodies()
        self.assertEqual(build_opener.call_count, 2)
        self.assertIsInstance(build_opener.call_args_list[0].args[0], TOOL._NoRedirectHandler)
        self.assertIsInstance(build_opener.call_args_list[1].args[0], TOOL._NoRedirectHandler)
        expected = [
            (page_opener, TOOL.PAGE_URL, TOOL.PAGE_PATH),
            (raw_opener, TOOL.RAW_URL, TOOL.RAW_PATH),
        ]
        for opener, url, path in expected:
            request, timeout = opener.calls[0]
            parsed = urlsplit(request.full_url)
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.hostname, "gml.noaa.gov")
            self.assertEqual(parsed.path, path)
            self.assertEqual(parsed.query, "")
            self.assertEqual(request.full_url, url)
            self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(result["status"], "COMPARED")
        self.assertEqual(result["comparison"]["status"], "EXACT_MATCH")
        self.assertEqual(result["comparison"]["exact_match_count"], 3)
        self.assertEqual(result["comparison"]["numeric_difference_count"], 0)
        self.assertEqual(
            result["sources"]["provider_page"]["response_sha256"],
            hashlib.sha256(PAGE).hexdigest(),
        )
        self.assertEqual(
            result["sources"]["fixed_raw_table"]["response_sha256"],
            hashlib.sha256(RAW).hexdigest(),
        )
        self.assertFalse(result["sources"]["provider_page"]["raw_response_retained"])
        self.assertFalse(result["sources"]["fixed_raw_table"]["raw_response_retained"])
        self.assertIn("does not authenticate the source", result["claim_ceiling"])

    def test_literal_source_difference_is_reported_without_ranking_surfaces(self) -> None:
        result, *_ = fetch_with_bodies(page=PAGE_DIFFERENT)
        self.assertEqual(result["comparison"]["status"], "DIFFERENT")
        row = result["comparison"]["rows"][0]
        self.assertEqual(row["status"], "NUMERIC_DIFFERENCE")
        self.assertEqual(row["page_annual_increase_ppm"], "2.70")
        self.assertEqual(row["raw_table_annual_increase_ppm"], "2.69")
        self.assertEqual(row["page_minus_raw_annual_increase_ppm"], "0.01")
        self.assertIn("does not judge rounding", " ".join(result["non_claims"]))

    def test_request_is_bounded_and_rejects_duplicate_keys_and_boolean_years(self) -> None:
        invalid = [
            b'{"schema_version":"toolbox-noaa-co2-source-surface-comparison-input-r0","start_year":2023,"start_year":2024,"end_year":2025}',
            b'{"schema_version":"toolbox-noaa-co2-source-surface-comparison-input-r0","start_year":true,"end_year":2025}',
            b'{"schema_version":"toolbox-noaa-co2-source-surface-comparison-input-r0","start_year":2025,"end_year":2024}',
            request_bytes(1959, 2009),
            request_bytes(1958, 1959),
            b'{"schema_version":"wrong","start_year":2023,"end_year":2025}',
            b'{"schema_version":"toolbox-noaa-co2-source-surface-comparison-input-r0","start_year":2023,"end_year":2025,"url":"https://example.org"}',
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(raw)

    def test_cli_refuses_network_before_any_request_without_per_call_flag(self) -> None:
        with patch.object(TOOL.urllib.request, "build_opener") as build_opener:
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        build_opener.assert_not_called()
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("NETWORK_CALL_REQUIRES_ALLOW_PUBLIC_NETWORK", stderr.getvalue())

    def test_cli_records_explicit_network_flag_and_two_request_count(self) -> None:
        page_opener = FakeOpener(FakeResponse(PAGE, "text/html"))
        raw_opener = FakeOpener(FakeResponse(RAW, "text/plain"))
        with patch.object(TOOL.urllib.request, "build_opener", side_effect=[page_opener, raw_opener]):
            with patch.object(sys, "stdin", FakeStdin(request_bytes())):
                stdout, stderr = io.StringIO(), io.StringIO()
                with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                    code = TOOL.main(["--stdin", "--allow-public-network"])
        self.assertEqual(code, 0, stderr.getvalue())
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["invocation"], {
            "allow_public_network_flag": True,
            "requests_made": 2,
        })

    def test_wrong_page_header_wrong_species_redirect_and_bad_raw_fail_closed(self) -> None:
        wrong_heading = PAGE.replace(b"Growth (ppm)", b"Growth (ppb)")
        self.assertEqual(
            TOOL._parse_page(wrong_heading, 2023, 2025)["status"],
            "INVALID_PROVIDER_RESPONSE",
        )
        wrong_species = RAW.replace(b"Annual CO2 mole fraction", b"Annual CH4 mole fraction")
        self.assertEqual(
            TOOL._parse_raw_table(wrong_species, 2023, 2025)["status"],
            "INVALID_PROVIDER_RESPONSE",
        )
        malformed = RAW.replace(b"2024       3.76", b"2024       bad ")
        self.assertEqual(
            TOOL._parse_raw_table(malformed, 2023, 2025)["status"],
            "INVALID_PROVIDER_RESPONSE",
        )

        redirect = HTTPError(TOOL.PAGE_URL, 302, "Found", {}, None)
        opener = FakeOpener(error=redirect)
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            result = TOOL._fetch(TOOL.PAGE_URL, TOOL.PAGE_PATH, "text/html")
        self.assertEqual(result["acquisition_status"], "REDIRECT_BLOCKED")
        self.assertEqual(len(opener.calls), 1)


if __name__ == "__main__":
    unittest.main()
