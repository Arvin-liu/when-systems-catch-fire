from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_pubmed_doi_update_audit.py"
SPEC = importlib.util.spec_from_file_location("toolbox_pubmed_doi_update_audit", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


DOI = "10.1016/j.ajhg.2010.04.006"
PMID = "20466091"


class FakeStdin:
    def __init__(self, payload: bytes) -> None:
        self.buffer = io.BytesIO(payload)


def request_bytes(doi: str = DOI) -> bytes:
    return json.dumps({"dois": [doi]}).encode("utf-8")


def resolution_row(*, pmid: str | None = PMID, status: str = "IDENTIFIER_RESOLVED") -> dict[str, object]:
    return {
        "doi": DOI,
        "acquisition_status": "OK",
        "http_status": 200,
        "response_sha256": "a" * 64,
        "identifier_status": status,
        "matched_doi": DOI,
        "pmid": pmid,
        "pmcid": "PMC2885863" if pmid else None,
    }


class PubMedDoiUpdateAuditTests(unittest.TestCase):
    def test_resolves_then_inspects_only_exact_resolved_pmid(self) -> None:
        resolver_result = {"status": "IDENTIFIERS_RESOLVED", "rows": [resolution_row()]}
        inspection_result = {
            "status": "RECORDS_INSPECTED",
            "rows": [{
                "pmid": PMID,
                "acquisition_status": "OK",
                "record_status": "RECORD_FOUND_WITH_RECORDED_RELATIONS",
                "relations": [{"ref_type": "CommentIn", "related_pmid": "12345", "reference_source": "Example citation"}],
                "response_sha256": "b" * 64,
            }],
        }
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_result) as resolve, patch.object(
            TOOL.update_reader, "inspect", return_value=inspection_result,
        ) as inspect:
            result = TOOL.audit([DOI])

        resolve.assert_called_once_with([DOI])
        inspect.assert_called_once_with([PMID])
        self.assertEqual(result["update_link_status"], "RECORDED_RELATIONS_RETURNED")
        self.assertEqual(result["identifier_resolution"], resolver_result)
        self.assertEqual(result["update_link_inspection"], inspection_result)
        self.assertEqual(result["tool_id"], "research.audit_pubmed_updates_from_doi")
        self.assertIn("does not establish that no update exists", result["claim_ceiling"])

    def test_does_not_call_pubmed_fetch_when_no_exact_pmid_is_returned(self) -> None:
        resolver_result = {"status": "NO_IDENTIFIERS_RESOLVED", "rows": [resolution_row(pmid=None, status="MATCHED_WITHOUT_PUBMED_OR_PMC_ID")]}
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_result), patch.object(
            TOOL.update_reader, "inspect",
        ) as inspect:
            result = TOOL.audit([DOI])

        inspect.assert_not_called()
        self.assertIsNone(result["update_link_inspection"])
        self.assertEqual(result["update_link_status"], "SKIPPED_NO_EXACT_PMID")

    def test_preserves_empty_relation_as_limited_observation(self) -> None:
        resolver_result = {"status": "IDENTIFIERS_RESOLVED", "rows": [resolution_row()]}
        inspection_result = {
            "status": "RECORDS_INSPECTED",
            "rows": [{"pmid": PMID, "acquisition_status": "OK", "record_status": "RECORD_FOUND_NO_RECORDED_RELATIONS", "relations": []}],
        }
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_result), patch.object(
            TOOL.update_reader, "inspect", return_value=inspection_result,
        ):
            result = TOOL.audit([DOI])
        self.assertEqual(result["update_link_status"], "NO_RELATIONS_RETURNED_IN_THIS_RESPONSE")
        self.assertIn("does not establish that no update exists", result["claim_ceiling"])

    def test_requires_network_flag_before_reading_input_or_running_either_stage(self) -> None:
        with patch.object(TOOL.identifier_resolver, "resolve") as resolve, patch.object(TOOL.update_reader, "inspect") as inspect:
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("--allow-public-network", stderr.getvalue())
        resolve.assert_not_called()
        inspect.assert_not_called()

    def test_rejects_multiple_dois_and_invalid_contract_before_stage_calls(self) -> None:
        with self.assertRaisesRegex(TOOL.ToolInputError, "exactly one DOI"):
            TOOL.parse_request(json.dumps({"dois": [DOI, "10.1234/other"]}).encode())
        with self.assertRaisesRegex(TOOL.ToolInputError, "bare DOI"):
            TOOL.parse_request(request_bytes("https://doi.org/" + DOI))
        with self.assertRaisesRegex(TOOL.ToolInputError, "duplicate JSON"):
            TOOL.parse_request(b'{"dois":["10.1016/j.ajhg.2010.04.006"],"dois":[]}')
        with self.assertRaisesRegex(TOOL.ToolInputError, "exceeds"):
            TOOL.parse_request(b" " * (TOOL.MAX_REQUEST_BYTES + 1))

    def test_explicit_stage_failures_remain_in_output(self) -> None:
        resolver_result = {"status": "COMPLETED_WITH_EXPLICIT_FAILURES", "rows": [{**resolution_row(pmid=None), "acquisition_status": "NETWORK_ERROR", "identifier_status": "NOT_AVAILABLE"}]}
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_result), patch.object(
            TOOL.update_reader, "inspect",
        ) as inspect:
            result = TOOL.audit([DOI])
        self.assertEqual(result["identifier_resolution"]["rows"][0]["acquisition_status"], "NETWORK_ERROR")
        self.assertEqual(result["update_link_status"], "SKIPPED_NO_EXACT_PMID")
        inspect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
