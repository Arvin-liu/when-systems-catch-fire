from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import jsonschema


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_pubmed_doi_update_audit.py"
OUTPUT_SCHEMA = json.loads((IGNITION_ROOT / "schemas/operations/pubmed-doi-update-audit-output-r0.schema.json").read_text(encoding="utf-8"))
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


def resolution_row(
    *,
    pmid: str | None = PMID,
    status: str = "IDENTIFIER_RESOLVED",
    acquisition_status: str = "OK",
    http_status: int | None = 200,
) -> dict[str, object]:
    return {
        "doi": DOI,
        "retrieval_timestamp_utc": "2026-10-26T00:00:00Z",
        "source_url": "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids=10.1016%2Fj.ajhg.2010.04.006&format=json",
        "acquisition_status": acquisition_status,
        "http_status": http_status,
        "response_sha256": "a" * 64 if acquisition_status == "OK" else None,
        "identifier_status": status,
        "matched_doi": DOI,
        "pmid": pmid,
        "pmcid": "PMC2885863" if pmid else None,
    }


def make_resolver_result(row: dict[str, object]) -> dict[str, object]:
    failures = int(row["acquisition_status"] != "OK")
    resolved = int(row["identifier_status"] == "IDENTIFIER_RESOLVED")
    return {
        "schema_version": "ignition.pubmed-identifier-resolution-r0",
        "tool_id": "research.resolve_pubmed_identifiers",
        "tool_version": "0.1.1",
        "status": "COMPLETED_WITH_EXPLICIT_FAILURES" if failures else ("IDENTIFIERS_RESOLVED" if resolved else "NO_IDENTIFIERS_RESOLVED"),
        "doi_count": 1,
        "resolved_count": resolved,
        "acquisition_failure_count": failures,
        "rows": [row],
        "source_code_sha256": {"wrapper": "c" * 64},
        "claim_ceiling": "DOI identifier lookup only.",
    }


def inspection_row(
    *,
    pmid: str = PMID,
    record_status: str = "RECORD_FOUND_WITH_RECORDED_RELATIONS",
    relations: list[dict[str, str | None]] | None = None,
    acquisition_status: str = "OK",
    http_status: int | None = 200,
    expected_doi: str | None = DOI,
    doi_binding_status: str | None = "EXACT_MATCH",
) -> dict[str, object]:
    row: dict[str, object] = {
        "pmid": pmid,
        "retrieval_timestamp_utc": "2026-10-26T00:00:01Z",
        "source_url": f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml&tool=IgnitionToolbox",
        "pubmed_record_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "acquisition_status": acquisition_status,
        "http_status": http_status,
        "response_sha256": "b" * 64 if acquisition_status == "OK" else None,
        "record_status": record_status,
        "relations": relations or [],
        "relations_truncated": False,
    }
    if expected_doi is not None:
        row["expected_doi"] = expected_doi
    if doi_binding_status is not None:
        row["doi_binding_status"] = doi_binding_status
    return row


def make_inspection_result(row: dict[str, object]) -> dict[str, object]:
    failures = int(row["acquisition_status"] != "OK")
    found = int(row["record_status"] in {"RECORD_FOUND_WITH_RECORDED_RELATIONS", "RECORD_FOUND_NO_RECORDED_RELATIONS"})
    return {
        "schema_version": "ignition.pubmed-update-link-inspection-r0",
        "tool_id": "research.inspect_pubmed_update_links",
        "tool_version": "0.2.0",
        "status": "COMPLETED_WITH_EXPLICIT_FAILURES" if failures else ("RECORDS_INSPECTED" if found else "NO_RECORDS_FOUND"),
        "pmid_count": 1,
        "records_found": found,
        "acquisition_failure_count": failures,
        "rows": [row],
        "source_code_sha256": {"wrapper": "d" * 64},
        "claim_ceiling": "Raw relation fields for this response only.",
    }


class PubMedDoiUpdateAuditTests(unittest.TestCase):
    def test_resolves_then_inspects_only_exact_resolved_pmid(self) -> None:
        resolver_stage = make_resolver_result(resolution_row())
        reader_stage = make_inspection_result(inspection_row(relations=[{"ref_type": "CommentIn", "related_pmid": "12345", "reference_source": "Example citation"}]))
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage) as resolve, patch.object(
            TOOL.update_reader, "inspect", return_value=reader_stage,
        ) as inspect:
            result = TOOL.audit([DOI])

        resolve.assert_called_once_with([DOI])
        inspect.assert_called_once_with([PMID], expected_doi=DOI)
        self.assertEqual(result["update_link_status"], "RECORDED_RELATIONS_RETURNED")
        self.assertEqual(result["identifier_resolution"], resolver_stage)
        self.assertEqual(result["update_link_inspection"], reader_stage)
        self.assertEqual(result["tool_id"], "research.audit_pubmed_updates_from_doi")
        self.assertIn("does not establish that no update exists", result["claim_ceiling"])
        jsonschema.Draft202012Validator(OUTPUT_SCHEMA).validate(result)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(OUTPUT_SCHEMA).validate({**result, "identifier_resolution": {"untyped": True}})

        historical_row = resolution_row(pmid=None)
        historical_row["identifier_status"] = "IDENTIFIER_RESOLVED"
        historical_row["pmcid"] = "PMC2885863"
        historical_resolution = make_resolver_result(historical_row)
        historical_resolution["tool_version"] = "0.1.0"
        legacy_reader = make_inspection_result(inspection_row())
        legacy_reader["tool_version"] = "0.1.0"
        legacy_row = legacy_reader["rows"][0]
        legacy_row.pop("expected_doi")
        legacy_row.pop("doi_binding_status")
        historical = {
            **result,
            "tool_version": "0.1.0",
            "identifier_resolution": historical_resolution,
            "update_link_inspection": legacy_reader,
            "update_link_status": "RECORDED_RELATIONS_RETURNED",
        }
        jsonschema.Draft202012Validator(OUTPUT_SCHEMA).validate(historical)

    def test_does_not_call_pubmed_fetch_when_no_exact_pmid_is_returned(self) -> None:
        resolver_stage = make_resolver_result(resolution_row(pmid=None, status="MATCHED_WITHOUT_PUBMED_OR_PMC_ID"))
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage), patch.object(
            TOOL.update_reader, "inspect",
        ) as inspect:
            result = TOOL.audit([DOI])

        inspect.assert_not_called()
        self.assertIsNone(result["update_link_inspection"])
        self.assertEqual(result["update_link_status"], "SKIPPED_NO_VALID_PMID")
        jsonschema.Draft202012Validator(OUTPUT_SCHEMA).validate(result)

    def test_invalid_numeric_pmid_is_not_passed_to_reader(self) -> None:
        resolver_stage = make_resolver_result(resolution_row(pmid="0"))
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage), patch.object(
            TOOL.update_reader, "inspect",
        ) as inspect:
            result = TOOL.audit([DOI])

        inspect.assert_not_called()
        self.assertIsNone(result["update_link_inspection"])
        self.assertEqual(result["update_link_status"], "SKIPPED_NO_VALID_PMID")

    def test_preserves_empty_relation_as_limited_observation(self) -> None:
        resolver_stage = make_resolver_result(resolution_row())
        reader_stage = make_inspection_result(inspection_row(record_status="RECORD_FOUND_NO_RECORDED_RELATIONS"))
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage), patch.object(
            TOOL.update_reader, "inspect", return_value=reader_stage,
        ):
            result = TOOL.audit([DOI])
        self.assertEqual(result["update_link_status"], "NO_RELATIONS_RETURNED_IN_THIS_RESPONSE")
        self.assertIn("does not establish that no update exists", result["claim_ceiling"])
        jsonschema.Draft202012Validator(OUTPUT_SCHEMA).validate(result)

    def test_withholds_update_claim_when_same_response_doi_binding_is_not_exact(self) -> None:
        resolver_stage = make_resolver_result(resolution_row())
        mismatch_row = inspection_row(
            record_status="DOI_IDENTITY_NOT_CONFIRMED",
            relations=[],
            doi_binding_status="MISMATCH",
        )
        reader_stage = make_inspection_result(mismatch_row)
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage), patch.object(
            TOOL.update_reader, "inspect", return_value=reader_stage,
        ):
            result = TOOL.audit([DOI])
        self.assertEqual(result["update_link_status"], "RECORD_IDENTITY_NOT_CONFIRMED")
        jsonschema.Draft202012Validator(OUTPUT_SCHEMA).validate(result)

        legacy_row = inspection_row(expected_doi=None, doi_binding_status=None)
        legacy_reader_stage = make_inspection_result(legacy_row)
        legacy_reader_stage["tool_version"] = "0.1.0"
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage), patch.object(
            TOOL.update_reader, "inspect", return_value=legacy_reader_stage,
        ):
            legacy = TOOL.audit([DOI])
        self.assertEqual(legacy["update_link_status"], "RECORD_IDENTITY_NOT_CONFIRMED")
        jsonschema.Draft202012Validator(OUTPUT_SCHEMA).validate(legacy)

    def test_missing_pubmed_record_is_not_reported_as_an_identity_mismatch(self) -> None:
        resolver_stage = make_resolver_result(resolution_row())
        no_record_row = inspection_row(record_status="NO_RECORD", doi_binding_status="NOT_EVALUATED")
        reader_stage = make_inspection_result(no_record_row)
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage), patch.object(
            TOOL.update_reader, "inspect", return_value=reader_stage,
        ):
            result = TOOL.audit([DOI])
        self.assertEqual(result["update_link_status"], "RECORD_NOT_CONFIRMED")
        jsonschema.Draft202012Validator(OUTPUT_SCHEMA).validate(result)

    def test_empty_reader_stage_is_reported_as_unavailable(self) -> None:
        resolver_stage = make_resolver_result(resolution_row())
        reader_stage = {"rows": []}
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage), patch.object(
            TOOL.update_reader, "inspect", return_value=reader_stage,
        ):
            result = TOOL.audit([DOI])
        self.assertEqual(result["update_link_status"], "INSPECTION_UNAVAILABLE")
        self.assertEqual(result["update_link_inspection"], reader_stage)

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
        resolver_stage = make_resolver_result(resolution_row(pmid=None, status="NOT_AVAILABLE", acquisition_status="NETWORK_ERROR", http_status=None))
        with patch.object(TOOL.identifier_resolver, "resolve", return_value=resolver_stage), patch.object(
            TOOL.update_reader, "inspect",
        ) as inspect:
            result = TOOL.audit([DOI])
        self.assertEqual(result["identifier_resolution"]["rows"][0]["acquisition_status"], "NETWORK_ERROR")
        self.assertEqual(result["update_link_status"], "SKIPPED_NO_VALID_PMID")
        inspect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
