from __future__ import annotations

import io
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_compare_crossref_reference_metadata.py"
SPEC = importlib.util.spec_from_file_location("toolbox_crossref_reference_metadata_comparison", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


def request(references: list[dict] | None = None) -> dict:
    return {
        "source_work_doi": "10.1186/s12884-025-07725-7",
        "references": references
        if references is not None
        else [{
            "key": "7725_CR2",
            "doi": "10.1136/bjsports-2020-102955",
            "article_title": "A reference article title",
            "year": 2020,
            "journal_title": "British Journal of Sports Medicine",
            "volume": "54",
            "issue": "12",
            "first_page": "1451",
        }],
    }


def fetched(message: dict, *, body: bytes | None = None) -> dict:
    payload = body if body is not None else json.dumps({"message": message}).encode("utf-8")
    return {"acquisition_status": "OK", "http_status": 200, "body": payload}


def work_message(**overrides: object) -> dict:
    message = {
        "DOI": "10.1136/bjsports-2020-102955",
        "title": ["A reference article title"],
        "published": {"date-parts": [[2020, 5, 1]]},
        "container-title": ["British Journal of Sports Medicine"],
        "volume": "54",
        "issue": "12",
        "page": "1451-1458",
    }
    message.update(overrides)
    return message


def source_work_message(reference_rows: list[dict] | None = None, **overrides: object) -> dict:
    message = {
        "DOI": "10.1186/s12884-025-07725-7",
        "title": ["Source work title"],
        "reference": reference_rows if reference_rows is not None else [{
            "key": "7725_CR2",
            "DOI": "10.1136/bjsports-2020-102955",
            "first-page": "1451",
            "journal-title": "Br J Sports Med",
            "volume": "54",
            "year": 2020,
        }],
    }
    message.update(overrides)
    return message


class CrossrefReferenceMetadataComparisonTests(unittest.TestCase):
    def test_matches_only_supplied_fields_after_normalization(self) -> None:
        with patch.object(TOOL.crossref, "_fetch_one", return_value=fetched(work_message())) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(request()).encode("utf-8")))

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(fetch.call_args.args[0], "10.1136/bjsports-2020-102955")
        self.assertNotEqual(fetch.call_args.args[0], "10.1186/s12884-025-07725-7")
        row = result["rows"][0]
        self.assertEqual(result["tool_id"], "research.compare_crossref_reference_metadata")
        self.assertEqual(row["doi_identity_status"], "EXACT_DOI_MATCH")
        self.assertEqual(row["comparison_status"], "ALL_PROVIDED_FIELDS_NORMALIZED_EQUAL")
        self.assertEqual(
            {key: value["status"] for key, value in row["field_comparisons"].items()},
            {
                "article_title": "NORMALIZED_EQUAL",
                "year": "NORMALIZED_EQUAL",
                "journal_title": "NORMALIZED_EQUAL",
                "volume": "NORMALIZED_EQUAL",
                "issue": "NORMALIZED_EQUAL",
                "first_page": "NORMALIZED_EQUAL",
            },
        )
        self.assertEqual(row["crossref_work"]["page"], "1451-1458")
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["doi_identity_failure_count"], 0)
        self.assertEqual(result["source_binding_mode"], "NOT_REQUESTED")
        self.assertEqual(result["schema_version"], "ignition.crossref-reference-metadata-comparison-r1")
        self.assertTrue(result["rows"][0]["target_request_attempted"])

    def test_optional_source_binding_checks_key_doi_and_both_field_projections(self) -> None:
        inputs = request()
        inputs["verify_source_link"] = True
        inputs["references"][0]["journal_title"] = "Br J Sports Med"
        with patch.object(
            TOOL.crossref,
            "_fetch_one",
            side_effect=[fetched(source_work_message()), fetched(work_message())],
        ) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(fetch.call_args_list[0].args[0], "10.1186/s12884-025-07725-7")
        self.assertEqual(fetch.call_args_list[1].args[0], "10.1136/bjsports-2020-102955")
        self.assertEqual(result["request_count"], 2)
        self.assertEqual(result["source_work_doi_status"], "EXACT_DOI_MATCH")
        self.assertNotIn("raw_reference_rows", result["source_work_verification"])
        row = result["rows"][0]
        self.assertEqual(row["source_reference_binding"]["status"], "SOURCE_REFERENCE_DOI_MATCH")
        self.assertEqual(row["source_reference_binding"]["source_reference_metadata"]["key"], "7725_CR2")
        self.assertEqual(
            row["source_reference_binding"]["source_field_comparisons"]["journal_title"]["status"],
            "NORMALIZED_EQUAL",
        )
        self.assertEqual(row["field_comparisons"]["journal_title"]["status"], "NORMALIZED_DIFFERENT")
        self.assertEqual(result["source_reference_binding_failure_count"], 0)

    def test_source_reference_key_absence_prevents_target_fetch(self) -> None:
        inputs = request()
        inputs["verify_source_link"] = True
        with patch.object(TOOL.crossref, "_fetch_one", return_value=fetched(source_work_message(reference_rows=[]))) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["status"], "COMPLETED_WITH_EXPLICIT_FAILURES")
        self.assertEqual(result["source_reference_binding_failure_count"], 1)
        self.assertEqual(result["rows"][0]["source_reference_binding"]["status"], "SOURCE_REFERENCE_KEY_NOT_FOUND")
        self.assertEqual(result["rows"][0]["acquisition_status"], "NOT_ATTEMPTED")
        self.assertFalse(result["rows"][0]["target_request_attempted"])

    def test_source_reference_doi_mismatch_prevents_target_fetch(self) -> None:
        inputs = request()
        inputs["verify_source_link"] = True
        source = source_work_message(reference_rows=[{
            "key": "7725_CR2",
            "DOI": "10.9999/different",
            "year": 2020,
        }])
        with patch.object(TOOL.crossref, "_fetch_one", return_value=fetched(source)) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["rows"][0]["source_reference_binding"]["status"], "SOURCE_REFERENCE_DOI_MISMATCH")
        self.assertFalse(result["rows"][0]["target_request_attempted"])

    def test_source_work_fetch_failure_is_preserved_and_target_is_skipped(self) -> None:
        inputs = request()
        inputs["verify_source_link"] = True
        unavailable = {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None}
        with patch.object(TOOL.crossref, "_fetch_one", return_value=unavailable) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result["source_work_verification"]["status"], "SOURCE_WORK_ACQUISITION_FAILED")
        self.assertEqual(result["source_acquisition_failure_count"], 1)
        self.assertEqual(result["source_work_verification_failure_count"], 0)
        self.assertEqual(result["rows"][0]["comparison_status"], "NOT_COMPARED_SOURCE_REFERENCE_NOT_BOUND")
        self.assertFalse(result["rows"][0]["target_request_attempted"])

    def test_source_work_returned_doi_mismatch_prevents_target_fetch(self) -> None:
        inputs = request()
        inputs["verify_source_link"] = True
        with patch.object(
            TOOL.crossref,
            "_fetch_one",
            return_value=fetched(source_work_message(DOI="10.9999/different")),
        ) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result["source_work_doi_status"], "RETURNED_DOI_DIFFERS")
        self.assertEqual(result["source_work_verification_failure_count"], 1)
        self.assertEqual(result["source_acquisition_failure_count"], 0)
        self.assertEqual(result["rows"][0]["source_reference_binding"]["status"], "SOURCE_WORK_DOI_IDENTITY_UNRESOLVED")
        self.assertFalse(result["rows"][0]["target_request_attempted"])

    def test_ambiguous_source_reference_key_prevents_target_fetch(self) -> None:
        inputs = request()
        inputs["verify_source_link"] = True
        duplicate_rows = [
            {"key": "7725_CR2", "DOI": "10.1136/bjsports-2020-102955"},
            {"key": "7725_CR2", "DOI": "10.1136/bjsports-2020-102955"},
        ]
        with patch.object(
            TOOL.crossref,
            "_fetch_one",
            return_value=fetched(source_work_message(reference_rows=duplicate_rows)),
        ) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result["rows"][0]["source_reference_binding"]["status"], "SOURCE_REFERENCE_KEY_AMBIGUOUS")
        self.assertEqual(result["source_reference_binding_failure_count"], 1)
        self.assertFalse(result["rows"][0]["target_request_attempted"])

    def test_source_link_mode_is_bounded_to_one_source_and_five_target_attempts(self) -> None:
        inputs = request([
            {"key": f"ref-{index}", "doi": f"10.1136/bjsports-2020-1029{index}"}
            for index in range(5)
        ])
        inputs["verify_source_link"] = True
        source_rows = [
            {"key": item["key"], "DOI": item["doi"]}
            for item in inputs["references"]
        ]
        target_messages = [
            fetched(work_message(DOI=item["doi"]))
            for item in inputs["references"]
        ]
        with patch.object(
            TOOL.crossref,
            "_fetch_one",
            side_effect=[fetched(source_work_message(reference_rows=source_rows)), *target_messages],
        ) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        self.assertEqual(fetch.call_count, 6)
        self.assertEqual(result["request_count"], 6)
        self.assertEqual(result["source_reference_binding_failure_count"], 0)
        self.assertTrue(all(row["target_request_attempted"] for row in result["rows"]))

    def test_source_work_without_reference_projection_skips_all_targets(self) -> None:
        inputs = request()
        inputs["verify_source_link"] = True
        source_message = source_work_message()
        source_message.pop("reference")
        with patch.object(TOOL.crossref, "_fetch_one", return_value=fetched(source_message)) as fetch:
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result["source_work_verification"]["status"], "SOURCE_REFERENCES_NOT_REPORTED")
        self.assertEqual(result["source_work_verification_failure_count"], 1)
        self.assertEqual(result["source_acquisition_failure_count"], 0)
        self.assertEqual(result["rows"][0]["source_reference_binding"]["status"], "SOURCE_REFERENCES_NOT_REPORTED")
        self.assertFalse(result["rows"][0]["target_request_attempted"])

    def test_difference_is_reported_as_metadata_difference_not_citation_error(self) -> None:
        inputs = request([{
            "key": "7725_CR2",
            "doi": "10.1136/bjsports-2020-102955",
            "article_title": "A different title",
        }])
        with patch.object(TOOL.crossref, "_fetch_one", return_value=fetched(work_message())):
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        row = result["rows"][0]
        self.assertEqual(row["comparison_status"], "FIELD_DIFFERENCES_OBSERVED")
        self.assertEqual(row["field_comparisons"]["article_title"]["status"], "NORMALIZED_DIFFERENT")
        self.assertIn(
            "A difference is not proof of an incorrect citation",
            result["claim_ceiling"],
        )

    def test_missing_provider_field_is_not_counted_as_a_mismatch(self) -> None:
        with patch.object(TOOL.crossref, "_fetch_one", return_value=fetched(work_message().copy() | {"issue": None})):
            row = TOOL.compare(TOOL.parse_request(json.dumps(request()).encode("utf-8")))["rows"][0]

        self.assertEqual(row["field_comparisons"]["issue"]["status"], "WORK_FIELD_NOT_REPORTED")
        self.assertEqual(row["comparison_status"], "PARTIAL_COMPARISON")

    def test_doi_only_reference_resolves_without_claiming_a_comparison(self) -> None:
        inputs = request([{"key": "7725_CR2", "doi": "10.1136/bjsports-2020-102955"}])
        with patch.object(TOOL.crossref, "_fetch_one", return_value=fetched(work_message())):
            result = TOOL.compare(TOOL.parse_request(json.dumps(inputs).encode("utf-8")))

        row = result["rows"][0]
        self.assertEqual(row["comparison_status"], "NO_COMPARABLE_REFERENCE_FIELDS")
        self.assertEqual(row["field_comparisons"], {})
        self.assertIsNotNone(row["crossref_work"]["article_title"])
        self.assertEqual(result["status"], "NO_COMPARABLE_REFERENCE_FIELDS")

    def test_duplicate_provider_json_keys_fail_closed(self) -> None:
        bad = fetched({}, body=b'{"message":{"DOI":"10.1136/bjsports-2020-102955","DOI":"10.9999/other"}}')
        with patch.object(TOOL.crossref, "_fetch_one", return_value=bad):
            row = TOOL.compare(TOOL.parse_request(json.dumps(request()).encode("utf-8")))["rows"][0]

        self.assertEqual(row["acquisition_status"], "INVALID_JSON_RESPONSE")
        self.assertEqual(row["comparison_status"], "NOT_COMPARED_ACQUISITION_FAILED")

    def test_returned_doi_mismatch_prevents_field_comparison(self) -> None:
        with patch.object(TOOL.crossref, "_fetch_one", return_value=fetched(work_message(DOI="10.9999/other"))):
            row = TOOL.compare(TOOL.parse_request(json.dumps(request()).encode("utf-8")))["rows"][0]

        self.assertEqual(row["doi_identity_status"], "RETURNED_DOI_DIFFERS")
        self.assertEqual(row["comparison_status"], "NOT_COMPARED_DOI_IDENTITY_UNRESOLVED")
        self.assertEqual(row["field_comparisons"], {})

    def test_acquisition_failure_is_preserved_without_comparison(self) -> None:
        unavailable = {"acquisition_status": "NETWORK_ERROR", "http_status": None, "body": None}
        with patch.object(TOOL.crossref, "_fetch_one", return_value=unavailable):
            result = TOOL.compare(TOOL.parse_request(json.dumps(request()).encode("utf-8")))

        row = result["rows"][0]
        self.assertEqual(result["status"], "COMPLETED_WITH_EXPLICIT_FAILURES")
        self.assertEqual(result["acquisition_failure_count"], 1)
        self.assertEqual(row["comparison_status"], "NOT_COMPARED_ACQUISITION_FAILED")
        self.assertIsNone(row["response_sha256"])
        self.assertEqual(row["field_comparisons"], {})

    def test_malformed_provider_json_is_hashed_and_not_compared(self) -> None:
        bad = fetched({}, body=b"{")
        with patch.object(TOOL.crossref, "_fetch_one", return_value=bad):
            row = TOOL.compare(TOOL.parse_request(json.dumps(request()).encode("utf-8")))["rows"][0]

        self.assertEqual(row["acquisition_status"], "INVALID_JSON_RESPONSE")
        self.assertEqual(row["comparison_status"], "NOT_COMPARED_ACQUISITION_FAILED")
        self.assertEqual(len(row["response_sha256"]), 64)

    def test_rejects_invalid_or_over_limit_input_before_any_request(self) -> None:
        invalid_inputs = [
            request([{"key": "x", "doi": "https://doi.org/10.1136/bjsports-2020-102955"}]),
            request([{"key": "x", "doi": "10.1136/bjsports-2020-102955", "year": True}]),
            request([{"key": "x", "doi": "10.1136/bjsports-2020-102955", "article_title": " title "}]),
            request([{"key": "same", "doi": "10.1136/bjsports-2020-102955"}, {"key": "same", "doi": "10.1136/bjsports-2019-101413"}]),
            request([{"key": "a", "doi": "10.1136/bjsports-2020-102955"}, {"key": "b", "doi": "10.1136/BJSports-2020-102955"}]),
            request([{"key": "x", "doi": "10.1136/bjsports-2020-102955", "unexpected": "ignored fields are unsafe"}]),
            request() | {"verify_source_link": "true"},
            request([{"key": str(index), "doi": f"10.1136/bjsports-2020-10295{index}"} for index in range(6)]),
        ]
        with patch.object(TOOL.crossref, "_fetch_one") as fetch:
            for invalid in invalid_inputs:
                with self.subTest(invalid=invalid):
                    with self.assertRaises(TOOL.ToolInputError):
                        TOOL.parse_request(json.dumps(invalid).encode("utf-8"))
            fetch.assert_not_called()

    def test_duplicate_json_keys_are_rejected(self) -> None:
        raw = b'{"source_work_doi":"10.1186/s12884-025-07725-7","source_work_doi":"10.1186/s12884-025-07725-7","references":[]}'
        with self.assertRaises(TOOL.ToolInputError):
            TOOL.parse_request(raw)

    def test_public_network_flag_is_required_before_stdin_is_read(self) -> None:
        stdin = io.TextIOWrapper(io.BytesIO(json.dumps(request()).encode("utf-8")))
        with patch.object(TOOL.sys, "stdin", stdin), patch.object(TOOL.crossref, "_fetch_one") as fetch:
            with patch("sys.stderr", new_callable=io.StringIO) as stderr:
                status = TOOL.main(["--stdin"])

        self.assertEqual(status, 2)
        self.assertIn("--allow-public-network", stderr.getvalue())
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
