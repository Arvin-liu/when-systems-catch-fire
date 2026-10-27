import hashlib
import json
import unittest

from ignition.tools import toolbox_merge_selected_index_search_results as tool


def receipt(provider, records, *, acquisition="OK", hits=3):
    config = tool.PROVIDERS[provider]
    return {
        "schema_version": config["schema_version"],
        "tool_id": config["tool_id"],
        "tool_version": "0.1.0",
        "status": "FOUND" if acquisition == "OK" else "FAILED",
        "acquisition_status": acquisition,
        "source_endpoint": config["endpoint"],
        "retrieval_timestamp_utc": "2026-10-27T08:30:00Z",
        "max_results": 5,
        "query_sha256": hashlib.sha256((provider + " query").encode()).hexdigest(),
        "response_sha256": "a" * 64 if acquisition == "OK" else None,
        config["hit_count_key"]: hits if acquisition == "OK" else None,
        "returned_count": len(records),
        "records": records,
    }


def request(*receipts):
    return json.dumps({"source_results": list(receipts)}, ensure_ascii=False, separators=(",", ":")).encode()


class SelectedIndexSearchResultMergeTests(unittest.TestCase):
    def test_exact_normalized_doi_groups_across_sources_but_not_by_title(self):
        crossref = receipt("crossref", [
            {"doi": "10.1234/AbC.1", "title": "Shared title", "publication_year": 2022},
            {"doi": None, "title": "Another title", "publication_year": None},
        ])
        openalex = receipt("openalex", [
            {"openalex_id": "https://openalex.org/W123", "doi": "https://doi.org/10.1234/abc.1", "title": "Different title", "publication_year": 2022},
            {"openalex_id": "https://openalex.org/W124", "doi": None, "title": "Shared title", "publication_year": 2022},
        ])
        result = tool.merge(request(openalex, crossref))
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["match_basis"], "EXACT_NORMALIZED_DOI_ONLY")
        self.assertEqual(result["record_count_total"], 4)
        self.assertEqual(len(result["exact_normalized_doi_clusters"]), 1)
        self.assertEqual(result["exact_normalized_doi_clusters"][0]["normalized_doi"], "10.1234/abc.1")
        self.assertEqual(result["unclustered_record_count"], 2)
        self.assertEqual([row["provider"] for row in result["source_results"]], ["crossref", "openalex"])

    def test_two_or_three_distinct_source_receipts_are_required(self):
        c = receipt("crossref", [])
        with self.assertRaises(tool.ToolInputError):
            tool.merge(request(c))
        with self.assertRaises(tool.ToolInputError):
            tool.merge(request(c, c))

    def test_endpoint_version_and_count_mismatches_fail_closed(self):
        c = receipt("crossref", [])
        o = receipt("openalex", [])
        wrong_endpoint = dict(c, source_endpoint="https://example.invalid")
        with self.assertRaises(tool.ToolInputError):
            tool.merge(request(wrong_endpoint, o))
        wrong_count = dict(c, returned_count=1)
        with self.assertRaises(tool.ToolInputError):
            tool.merge(request(wrong_count, o))
        wrong_schema = dict(c, schema_version="future-version")
        with self.assertRaises(tool.ToolInputError):
            tool.merge(request(wrong_schema, o))

    def test_failed_source_is_preserved_and_status_is_partial(self):
        c = receipt("crossref", [{"doi": "10.1234/a", "title": "One"}])
        e = receipt("europe_pmc", [], acquisition="NETWORK_ERROR")
        result = tool.merge(request(c, e))
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual([row["acquisition_status"] for row in result["source_results"]], ["OK", "NETWORK_ERROR"])
        self.assertEqual(result["record_count_total"], 1)

    def test_all_failed_sources_remain_failed(self):
        c = receipt("crossref", [], acquisition="NETWORK_ERROR")
        e = receipt("europe_pmc", [], acquisition="HTTP_ERROR")
        result = tool.merge(request(c, e))
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["source_results"][0]["response_sha256"], None)

    def test_duplicate_json_keys_are_rejected(self):
        raw = b'{"source_results":[],"source_results":[]}'
        with self.assertRaises(tool.ToolInputError):
            tool.merge(raw)


if __name__ == "__main__":
    unittest.main()
