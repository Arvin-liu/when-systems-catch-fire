from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_compare_publication_metadata as tool  # noqa: E402


DOI = "10.3982/ecta15732"


def crossref(*, title="Policy Learning With Observational Data", year=2021, acquisition="OK", doi=DOI, digest="a" * 64):
    return {
        "tool_id": tool.CROSSREF_TOOL_ID,
        "result": {
            "schema_version": "ignition.crossref-metadata-verification-r0",
            "tool_id": tool.CROSSREF_TOOL_ID,
            "tool_version": "0.1.0",
            "status": "ALL_METADATA_MATCHED" if acquisition == "OK" else "COMPLETED_WITH_EXPLICIT_FAILURES",
            "rows": [{
                "canonical_identifier": doi,
                "acquisition_status": acquisition,
                "response_sha256": digest if acquisition == "OK" else None,
                "observed_title": title if acquisition == "OK" else None,
                "observed_year": year if acquisition == "OK" else None,
            }],
        },
    }


def openalex(*, title="Policy Learning With Observational Data", year=2021, row_status="EXACT_PRIMARY_DOI_MATCH", acquisition="OK", doi=DOI, digest="b" * 64):
    row = {"requested_doi": doi, "status": row_status}
    if row_status == "EXACT_PRIMARY_DOI_MATCH":
        row.update({"openalex_doi": "https://doi.org/" + doi, "title": title, "publication_year": year})
    return {
        "tool_id": tool.OPENALEX_TOOL_ID,
        "result": {
            "schema_version": "ignition.openalex-work-metadata-lookup-r0",
            "tool_id": tool.OPENALEX_TOOL_ID,
            "tool_version": "0.1.0",
            "status": "EXACT_DOI_WORKS_RESOLVED" if acquisition == "OK" else "COMPLETED_WITH_EXPLICIT_FAILURES",
            "acquisition_status": acquisition,
            "response_sha256": digest if acquisition == "OK" else None,
            "rows": [row],
        },
    }


def request(sources=None, doi=DOI):
    return {"schema_version": tool.SCHEMA_VERSION, "doi": doi, "source_results": sources or [crossref(), openalex()]}


class PublicationMetadataComparisonTests(unittest.TestCase):
    def test_live_task_fixture_reproduces_the_recorded_field_agreement(self):
        fixture = IGNITION_ROOT / "data/operations/toolbox-publication-metadata-cross-source-real-input-r0.json"
        result = tool.compare(fixture.read_bytes())
        self.assertEqual(result["status"], "METADATA_FIELDS_AGREE")
        self.assertEqual(result["field_comparisons"]["title"]["status"], "AGREE")
        self.assertEqual(result["field_comparisons"]["publication_year"]["status"], "AGREE")
        self.assertEqual(result["source_outcomes"][0]["provider_response_sha256"], "3f2f32d42cd289de9e36d00cfa5a97906e09df22fc78a1d4dba9f2241c222e1c")

    def test_matching_provider_fields_are_reported_without_authenticity_claims(self):
        result = tool.compare(json.dumps(request(), ensure_ascii=False).encode("utf-8"))
        self.assertEqual(result["status"], "METADATA_FIELDS_AGREE")
        self.assertEqual(result["field_comparisons"]["title"]["status"], "AGREE")
        self.assertEqual(result["field_comparisons"]["publication_year"]["status"], "AGREE")
        self.assertEqual(result["source_outcomes"][0]["provider_response_sha256"], "a" * 64)
        self.assertIn("not authenticated", result["claim_ceiling"])

    def test_title_comparison_normalizes_unicode_width_case_and_whitespace_only(self):
        raw_title = "Ａ  STUDY\nTitle"
        result = tool.compare(json.dumps(request([crossref(title=raw_title), openalex(title="a study title")])).encode())
        self.assertEqual(result["field_comparisons"]["title"]["status"], "AGREE")
        self.assertEqual(result["field_comparisons"]["title"]["observations"][0]["value"], raw_title)

    def test_title_and_year_disagreement_are_preserved_field_by_field(self):
        result = tool.compare(json.dumps(request([crossref(), openalex(title="Different title", year=2020)])).encode())
        self.assertEqual(result["status"], "METADATA_DISAGREEMENT_FOUND")
        self.assertEqual(result["field_comparisons"]["title"]["status"], "DISAGREE")
        self.assertEqual(result["field_comparisons"]["publication_year"]["status"], "DISAGREE")

    def test_missing_title_does_not_hide_year_disagreement(self):
        result = tool.compare(json.dumps(request([crossref(title=None), openalex(year=2020)])).encode())
        self.assertEqual(result["status"], "METADATA_DISAGREEMENT_FOUND")
        self.assertEqual(result["field_comparisons"]["title"]["status"], "INSUFFICIENT")
        self.assertEqual(result["field_comparisons"]["publication_year"]["status"], "DISAGREE")

    def test_provider_failure_is_explicit_and_never_treated_as_agreement(self):
        result = tool.compare(json.dumps(request([crossref(acquisition="NETWORK_ERROR"), openalex()])).encode())
        self.assertEqual(result["status"], "INSUFFICIENT_METADATA")
        self.assertEqual(result["source_outcomes"][0]["provider_response_sha256"], None)
        self.assertEqual(result["field_comparisons"]["title"]["status"], "INSUFFICIENT")

    def test_openalex_inconclusive_row_is_not_promoted_to_a_match(self):
        result = tool.compare(json.dumps(request([crossref(), openalex(row_status="INCONCLUSIVE_NO_PRIMARY_DOI_MATCH")])).encode())
        self.assertEqual(result["status"], "INSUFFICIENT_METADATA")
        self.assertEqual(result["source_outcomes"][1]["title"], None)

    def test_doi_row_mismatch_is_rejected(self):
        with self.assertRaisesRegex(tool.InputError, "requested DOI"):
            tool.compare(json.dumps(request([crossref(), openalex(doi="10.5555/wrong")])).encode())

    def test_both_supported_adapters_are_required_exactly_once(self):
        with self.assertRaisesRegex(tool.InputError, "exactly once"):
            tool.compare(json.dumps(request([crossref(), crossref()])).encode())
        with self.assertRaisesRegex(tool.InputError, "exactly one Crossref and one OpenAlex"):
            tool.compare(json.dumps(request([crossref()])).encode())

    def test_unsupported_adapter_version_and_invalid_response_digest_fail_closed(self):
        payload = request()
        payload["source_results"][1]["result"]["tool_version"] = "9.9.9"
        with self.assertRaisesRegex(tool.InputError, "unsupported tool identity or version"):
            tool.compare(json.dumps(payload).encode())
        payload = request()
        payload["source_results"][0]["result"]["rows"][0]["response_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(tool.InputError, "SHA-256"):
            tool.compare(json.dumps(payload).encode())

    def test_source_output_identity_and_schema_are_bound(self):
        payload = request()
        payload["source_results"][0]["result"]["tool_id"] = "research.other"
        with self.assertRaisesRegex(tool.InputError, "unsupported tool identity or version"):
            tool.compare(json.dumps(payload).encode())

    def test_duplicate_json_keys_nonstandard_numbers_and_extra_envelope_keys_reject(self):
        raw = b'{"schema_version":"x","schema_version":"x"}'
        with self.assertRaisesRegex(tool.InputError, "unique keys"):
            tool.compare(raw)
        with self.assertRaisesRegex(tool.InputError, "unique keys"):
            tool.compare(b'{"schema_version":NaN}')
        payload = request()
        payload["unexpected"] = True
        with self.assertRaisesRegex(tool.InputError, "exactly schema_version"):
            tool.compare(json.dumps(payload).encode())

    def test_oversized_input_and_unsafe_doi_reject_before_comparison(self):
        with self.assertRaisesRegex(tool.InputError, "byte limit"):
            tool.compare(b" " * (tool.MAX_INPUT_BYTES + 1))
        with self.assertRaisesRegex(tool.InputError, "bare DOI"):
            tool.compare(json.dumps(request(doi="https://attacker.invalid/10.3982/ecta15732")).encode())

    def test_openalex_exact_match_requires_matching_primary_doi(self):
        payload = request()
        payload["source_results"][1]["result"]["rows"][0]["openalex_doi"] = "https://doi.org/10.5555/wrong"
        with self.assertRaisesRegex(tool.InputError, "primary DOI"):
            tool.compare(json.dumps(payload).encode())


if __name__ == "__main__":
    unittest.main()
