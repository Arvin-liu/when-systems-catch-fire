"""Offline regression tests for the bounded research workflow."""
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import cli
from cli import openalex_client, run_research


def openalex_response(items):
    works = []
    for row in items:
        abstract_index = {}
        for position, word in enumerate((row.get("abstract") or "").split()):
            abstract_index.setdefault(word, []).append(position)
        works.append({
            "id": row.get("openalex_id", ""),
            "doi": row.get("doi", ""),
            "title": row.get("title", ""),
            "publication_year": row.get("year"),
            "authorships": [{"author": {"display_name": name}} for name in row.get("authors", [])],
            "abstract_inverted_index": abstract_index or None,
            "open_access": {"oa_url": row.get("oa_url", "")},
            "primary_location": {"source": {"display_name": row.get("venue", "")}},
            "type": row.get("type", "journal-article"),
            "cited_by_count": row.get("cited_by_count", 0),
            "is_retracted": row.get("is_retracted", False),
            "concepts": [],
            "language": "en",
        })
    body = json.dumps({"results": works}, ensure_ascii=False).encode("utf-8")
    parsed = openalex_client.parse_search_response(body)
    return {
        "request_url": "https://api.openalex.org/works?search=fixture&mailto=private%40example.test",
        "response_body": body,
        **parsed,
    }


def item(doi="10.1234/example", title="Example study", year=2024, openalex_id="https://openalex.org/W1"):
    return {
        "openalex_id": openalex_id,
        "doi": doi,
        "title": title,
        "year": year,
        "authors": ["A. Author"],
        "venue": "Example Journal",
        "abstract": "A short captured abstract.",
        "is_retracted": False,
        "oa_url": "https://example.org/paper",
    }


def crossref_response(title="Example study", year=2024):
    body = json.dumps({"message": {
        "title": [title],
        "published": {"date-parts": [[year]]},
        "type": "journal-article",
        "relation": {},
    }}).encode()
    return {"http_ok": True, "status": 200, "body": body}


class ResearchWorkflowTests(unittest.TestCase):
    def test_openalex_evidence_api_preserves_raw_bytes_and_compatibility(self):
        body = json.dumps({"results": [{
            "id": "https://openalex.org/W1",
            "doi": "https://doi.org/10.1234/example",
            "title": "Example study",
            "publication_year": 2024,
            "authorships": [],
            "abstract_inverted_index": None,
            "open_access": {},
            "primary_location": {},
        }]}).encode("utf-8")

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return body

        with patch.object(openalex_client.urllib.request, "urlopen", return_value=Response()):
            evidence = openalex_client.search_with_evidence("fixture", limit=1)
        self.assertEqual(evidence["response_body"], body)
        self.assertEqual(evidence["results"][0]["title"], "Example study")

        with patch.object(openalex_client.urllib.request, "urlopen", return_value=Response()):
            results = openalex_client.search("fixture", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["openalex_id"], "https://openalex.org/W1")

    def test_positive_report_manifest_and_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            receipt = run_research(
                question="What does the evidence show?",
                queries=["evidence question"],
                output_dir=out,
                draft_path=None,
                searcher=lambda *a, **k: openalex_response([item()]),
                crossref_fetch=lambda doi: crossref_response(),
                command=["cli.py", "--mailto", "private@example.test", "--output-dir", "/private/run"],
            )
            self.assertEqual(receipt["status"], "COMPLETED")
            self.assertEqual(receipt["counts"]["crossref_matches"], 1)
            self.assertTrue((out / "raw/openalex-query-01.json").is_file())
            source = json.loads((out / "sources.jsonl").read_text().splitlines()[0])
            self.assertEqual(source["source_id"], "S1")
            verification = json.loads((out / "verification.jsonl").read_text().splitlines()[0])
            raw_crossref = out / verification["raw_response_path"]
            self.assertTrue(raw_crossref.is_file())
            self.assertEqual(verification["response_sha256"], hashlib.sha256(raw_crossref.read_bytes()).hexdigest())
            report = (out / "report.md").read_text()
            self.assertIn("[S1] Example study", report)
            self.assertIn("[S1]: https://doi.org/10.1234/example", report)
            query = json.loads((out / "query-manifest.jsonl").read_text().splitlines()[0])
            self.assertNotIn("private", query["request_url"])
            self.assertEqual(query["normalized_output_status"], "MATCHES_RAW_RESPONSE")
            raw_doc = json.loads((out / query["raw_response_path"]).read_bytes())
            raw_record = json.dumps(raw_doc["results"][0], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            self.assertEqual(source["raw_evidence"][0]["raw_record_sha256"], hashlib.sha256(raw_record).hexdigest())
            saved_receipt = json.loads((out / "receipt.json").read_text())
            self.assertEqual(saved_receipt["artifacts"][-1]["path"], "verification.jsonl")
            self.assertNotIn("private@example.test", saved_receipt["command"])
            self.assertNotIn("/private/run", saved_receipt["command"])

    def test_source_cap_round_robins_queries_and_deduplicates(self):
        broad = [
            item(doi="10.1234/a", title="Broad result A", openalex_id="W-A"),
            item(doi="10.1234/b", title="Broad result B", openalex_id="W-B"),
            item(doi="10.1234/c", title="Broad result C", openalex_id="W-C"),
        ]
        later = [
            item(doi="10.1234/a", title="Broad result A", openalex_id="W-A"),
            item(doi="10.1234/x", title="Later question result X", openalex_id="W-X"),
        ]

        def searcher(query, **_):
            return openalex_response(broad if query == "broad query" else later)

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            run_research(
                question="A broad question with a later distinct subquestion",
                queries=["broad query", "later query"],
                output_dir=out,
                max_sources=2,
                searcher=searcher,
                crossref_fetch=lambda doi: crossref_response(),
            )
            sources = [json.loads(line) for line in (out / "sources.jsonl").read_text().splitlines()]

        self.assertEqual([source["openalex_id"] for source in sources], ["W-A", "W-X"])
        self.assertEqual(sources[0]["rank_by_query"], {"Q1": 1, "Q2": 1})
        self.assertEqual(sources[0]["query_ids"], ["Q1", "Q2"])
        self.assertEqual(sources[1]["rank_by_query"], {"Q2": 2})

    def test_mismatch_and_no_doi_are_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            receipt = run_research(
                question="Compare two records",
                queries=["record"],
                output_dir=out,
                max_sources=2,
                searcher=lambda *a, **k: openalex_response([
                    item(doi="10.1234/mismatch", title="OpenAlex title", openalex_id="W1"),
                    item(doi=None, title="No DOI record", openalex_id="W2"),
                ]),
                crossref_fetch=lambda doi: crossref_response(title="Different title", year=2020),
            )
            rows = [json.loads(line) for line in (out / "verification.jsonl").read_text().splitlines()]
            self.assertEqual(rows[0]["metadata_match_status"], "MISMATCH")
            self.assertEqual(rows[1]["acquisition_status"], "NO_DOI")
            self.assertEqual(receipt["counts"]["crossref_mismatches"], 1)

    def test_crossref_inline_markup_does_not_create_false_title_mismatch(self):
        plain_title = "ReplicatorBench: Benchmarking LLM Agents for Replicability in Social and Behavioral Sciences"
        crossref_title = (
            "<scp>ReplicatorBench:</scp>\n"
            "                    Benchmarking LLM Agents for Replicability in Social and Behavioral Sciences"
        )
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            run_research(
                question="Does Crossref metadata match the source title?",
                queries=["ReplicatorBench"],
                output_dir=out,
                searcher=lambda *a, **k: openalex_response([
                    item(
                        doi="10.1145/3770855.3819003",
                        title=plain_title,
                        year=2026,
                        openalex_id="https://openalex.org/W7196968176",
                    )
                ]),
                crossref_fetch=lambda doi: crossref_response(title=crossref_title, year=2026),
            )
            verification = json.loads((out / "verification.jsonl").read_text().splitlines()[0])

        self.assertTrue(verification["title_match"])
        self.assertTrue(verification["year_match"])
        self.assertEqual(verification["metadata_match_status"], "MATCH")

    def test_query_failure_is_preserved_and_empty_result_does_not_claim_success(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            receipt = run_research(
                question="Question with no source access",
                queries=["query"],
                output_dir=out,
                searcher=lambda *a, **k: (_ for _ in ()).throw(TimeoutError("fixture timeout")),
                crossref_fetch=lambda doi: crossref_response(),
            )
            self.assertEqual(receipt["status"], "FAILED")
            self.assertEqual(receipt["acquisition_status"], "FAILED")
            query = json.loads((out / "query-manifest.jsonl").read_text().splitlines()[0])
            self.assertEqual(query["status"], "ERROR")
            self.assertEqual(query["error_type"], "TimeoutError")
            self.assertIn("no conclusion is supported", (out / "report.md").read_text())

    def test_partial_query_failure_is_not_reported_as_completed(self):
        def searcher(query, **_):
            if query == "failed query":
                raise TimeoutError("fixture timeout")
            return openalex_response([item()])

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            receipt = run_research(
                question="Question with partial source coverage",
                queries=["successful query", "failed query"],
                output_dir=out,
                searcher=searcher,
                crossref_fetch=lambda doi: crossref_response(),
            )
            rows = [json.loads(line) for line in (out / "query-manifest.jsonl").read_text().splitlines()]
        self.assertEqual(receipt["status"], "PARTIAL")
        self.assertEqual(receipt["counts"]["query_error"], 1)
        self.assertEqual([row["status"] for row in rows], ["OK", "ERROR"])

    def test_successful_empty_queries_are_not_validated(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt = run_research(
                question="Question with no matching records",
                queries=["empty search"],
                output_dir=Path(temp) / "run",
                searcher=lambda *a, **k: openalex_response([]),
                crossref_fetch=lambda doi: crossref_response(),
            )
        self.assertEqual(receipt["status"], "NOT_VALIDATED")
        self.assertEqual(receipt["counts"]["query_ok"], 1)
        self.assertEqual(receipt["counts"]["sources_captured"], 0)

    def test_injected_normalized_rows_detached_from_raw_bytes_are_rejected(self):
        detached = openalex_response([item()])
        detached["response_body"] = b'{"results":[]}'
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            receipt = run_research(
                question="Question with injected result mismatch",
                queries=["query"],
                output_dir=out,
                searcher=lambda *a, **k: detached,
                crossref_fetch=lambda doi: crossref_response(),
            )
            query = json.loads((out / "query-manifest.jsonl").read_text().splitlines()[0])
            saved_raw = out / query["raw_response_path"]
            self.assertEqual(saved_raw.read_bytes(), b'{"results":[]}')
        self.assertEqual(receipt["status"], "FAILED")
        self.assertEqual(receipt["counts"]["sources_captured"], 0)
        self.assertIn("normalized source records do not match", query["error_summary"])

    def test_claim_review_exact_quote_links_manual_judgment_to_source_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reviews = root / "claims.jsonl"
            reviews.write_text(json.dumps({
                "claim_id": "C-1",
                "claim_text": "The example study reports its stated abstract result.",
                "source_id": "S1",
                "review_judgment": "SUPPORTS",
                "reviewer_type": "HUMAN",
                "reviewer": "reviewer-1",
                "reviewed_at_utc": "2026-10-16T08:00:00Z",
                "evidence_field": "abstract",
                "evidence_quote": "A short captured abstract.",
            }) + "\n")
            out = root / "run"
            receipt = run_research(
                question="Question",
                queries=["query"],
                output_dir=out,
                claim_review_path=reviews,
                searcher=lambda *a, **k: openalex_response([item()]),
                crossref_fetch=lambda doi: crossref_response(),
            )
            ledger = json.loads((out / "claim-review.jsonl").read_text().splitlines()[0])
            report = (out / "report.md").read_text()
        self.assertEqual(receipt["claim_review_status"], "COMPLETED")
        self.assertEqual(ledger["evidence_anchor_status"], "EXACT_MATCH")
        self.assertEqual(ledger["row_status"], "REVIEWED_AND_ANCHORED")
        self.assertEqual(ledger["source_raw_evidence"][0]["record_index"], 1)
        self.assertIn("does not establish", report)

    def test_claim_review_missing_excerpt_fails_closed_without_claiming_truth(self):
        review = {
            "claim_id": "C-1", "claim_text": "A claim", "source_id": "S1",
            "review_judgment": "SUPPORTS", "reviewer_type": "HUMAN",
            "reviewer": "reviewer-1", "reviewed_at_utc": "2026-10-16T08:00:00Z",
            "evidence_field": "abstract", "evidence_quote": "not in the abstract",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "claims.jsonl"
            path.write_text(json.dumps(review) + "\n")
            receipt = run_research(
                question="Question", queries=["query"], output_dir=root / "run",
                claim_review_path=path,
                searcher=lambda *a, **k: openalex_response([item()]),
                crossref_fetch=lambda doi: crossref_response(),
            )
            ledger = json.loads((root / "run/claim-review.jsonl").read_text().splitlines()[0])
        self.assertEqual(receipt["status"], "COMPLETED")
        self.assertEqual(receipt["claim_review_status"], "FAILED")
        self.assertEqual(ledger["evidence_anchor_status"], "NOT_FOUND")
        self.assertEqual(ledger["review_judgment"], "SUPPORTS")

    def test_claim_review_unknown_source_is_explicit(self):
        review = {"claim_id": "C-1", "claim_text": "A claim", "source_id": "S99", "review_judgment": "NOT_REVIEWED"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "claims.jsonl"
            path.write_text(json.dumps(review) + "\n")
            receipt = run_research(
                question="Question", queries=["query"], output_dir=root / "run",
                claim_review_path=path,
                searcher=lambda *a, **k: openalex_response([item()]),
                crossref_fetch=lambda doi: crossref_response(),
            )
            ledger = json.loads((root / "run/claim-review.jsonl").read_text().splitlines()[0])
        self.assertEqual(receipt["claim_review_status"], "FAILED")
        self.assertEqual(ledger["evidence_anchor_status"], "UNKNOWN_SOURCE")
        self.assertEqual(ledger["source_raw_evidence"], [])

    def test_no_claim_review_input_is_not_validated_not_implicitly_approved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt = run_research(
                question="Question", queries=["query"], output_dir=root / "run",
                searcher=lambda *a, **k: openalex_response([item()]),
                crossref_fetch=lambda doi: crossref_response(),
            )
            self.assertEqual((root / "run/claim-review.jsonl").read_text(), "")
        self.assertEqual(receipt["claim_review_status"], "NOT_VALIDATED")
        self.assertEqual(receipt["counts"]["claim_review_rows"], 0)

    def test_claim_review_invalid_human_record_is_rejected_before_output(self):
        review = {"claim_id": "C-1", "claim_text": "A claim", "source_id": "S1", "review_judgment": "SUPPORTS"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "claims.jsonl"
            path.write_text(json.dumps(review) + "\n")
            output = root / "run"
            with self.assertRaisesRegex(ValueError, "reviewer_type HUMAN"):
                run_research(
                    question="Question", queries=["query"], output_dir=output,
                    claim_review_path=path,
                    searcher=lambda *a, **k: openalex_response([item()]),
                    crossref_fetch=lambda doi: crossref_response(),
                )
            self.assertFalse(output.exists())

    def test_claim_review_duplicate_claim_source_pair_is_rejected(self):
        review = {"claim_id": "C-1", "claim_text": "A claim", "source_id": "S1", "review_judgment": "NOT_REVIEWED"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "claims.jsonl"
            path.write_text(json.dumps(review) + "\n" + json.dumps(review) + "\n")
            with self.assertRaisesRegex(ValueError, "duplicates claim_id/source_id"):
                run_research(
                    question="Question", queries=["query"], output_dir=root / "run",
                    claim_review_path=path,
                    searcher=lambda *a, **k: openalex_response([item()]),
                    crossref_fetch=lambda doi: crossref_response(),
                )

    def test_cli_exit_code_preserves_acquisition_and_claim_review_failures(self):
        argv = ["--question", "q", "--query", "q", "--output-dir", "/tmp/unused"]
        cases = [
            ({"status": "COMPLETED", "acquisition_status": "COMPLETED", "claim_review_status": "NOT_VALIDATED", "counts": {"sources_captured": 1}}, 0),
            ({"status": "PARTIAL", "acquisition_status": "PARTIAL", "claim_review_status": "NOT_VALIDATED", "counts": {"sources_captured": 1}}, 2),
            ({"status": "COMPLETED", "acquisition_status": "COMPLETED", "claim_review_status": "FAILED", "counts": {"sources_captured": 1}}, 2),
        ]
        for receipt, expected in cases:
            with self.subTest(receipt=receipt), patch.object(cli, "run_research", return_value=receipt), redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(argv), expected)

    def test_crossref_exception_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "run"
            receipt = run_research(
                question="Question with metadata outage",
                queries=["query"],
                output_dir=out,
                searcher=lambda *a, **k: openalex_response([item()]),
                crossref_fetch=lambda doi: (_ for _ in ()).throw(TimeoutError("private detail")),
            )
            row = json.loads((out / "verification.jsonl").read_text().splitlines()[0])
            self.assertEqual(row["acquisition_status"], "NETWORK_ERROR")
            self.assertEqual(row["error_type"], "TimeoutError")
            self.assertEqual(receipt["counts"]["crossref_unresolved"], 1)

    def test_blank_question_and_existing_output_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "question is required"):
                run_research(question=" ", queries=["q"], output_dir=Path(temp) / "blank")
            occupied = Path(temp) / "occupied"
            occupied.mkdir()
            (occupied / "keep.txt").write_text("do not overwrite")
            with self.assertRaises(FileExistsError):
                run_research(question="q", queries=["q"], output_dir=occupied)
            self.assertEqual((occupied / "keep.txt").read_text(), "do not overwrite")

    def test_draft_unknown_citation_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            draft = Path(temp) / "draft.md"
            draft.write_text("Claim with a citation [S2].")
            out = Path(temp) / "run"
            receipt = run_research(
                question="Question",
                queries=["query"],
                output_dir=out,
                draft_path=draft,
                searcher=lambda *a, **k: openalex_response([item()]),
                crossref_fetch=lambda doi: crossref_response(),
            )
            self.assertEqual(receipt["status"], "INVALID_DRAFT")
            self.assertIn("unknown source IDs", receipt["draft_error"])
            self.assertTrue((out / "receipt.json").is_file())
            self.assertIn("synthesis was rejected", (out / "report.md").read_text())


if __name__ == "__main__":
    unittest.main()
