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

    def test_offline_source_snapshots_preserve_bytes_and_anchor_claims_without_network(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            captures = root / "captures"
            captures.mkdir()
            web_capture = b"Test report observation.\nThe annual mean exceeded the stated threshold.\n"
            api_capture = b'{"status":"REQUEST_SUCCEEDED","Results":{"series":[{"seriesID":"TEST","data":[{"year":"2024","value":"101.2"}]}]}}'
            (captures / "report.txt").write_bytes(web_capture)
            (captures / "api.json").write_bytes(api_capture)
            manifest_rows = [
                {
                    "title": "Test report",
                    "source_url": "https://example.org/report",
                    "capture_path": "captures/report.txt",
                    "capture_kind": "web_run_observation",
                    "captured_at_utc": "2026-10-16T09:30:00Z",
                    "locator": "Results section, paragraph 1",
                    "query_ids": ["Q1"],
                },
                {
                    "title": "Test API response",
                    "source_url": "https://api.example.org/series",
                    "capture_path": "captures/api.json",
                    "capture_kind": "official_api_json",
                    "captured_at_utc": "2026-10-16T09:31:00+00:00",
                    "locator": "Results.series[0].data[0].value",
                    "query_ids": ["Q2"],
                },
            ]
            manifest = root / "source-snapshots.jsonl"
            manifest.write_text("".join(json.dumps(row) + "\n" for row in manifest_rows), encoding="utf-8")
            claim = {
                "claim_id": "C-1",
                "claim_text": "The captured report states the annual mean exceeded the threshold.",
                "source_id": "S1",
                "review_judgment": "SUPPORTS",
                "reviewer_type": "HUMAN",
                "reviewer": "test-reviewer",
                "reviewed_at_utc": "2026-10-16T09:32:00Z",
                "evidence_field": "captured_text",
                "evidence_quote": "The annual mean exceeded the stated threshold.",
            }
            claims = root / "claims.jsonl"
            claims.write_text(json.dumps(claim) + "\n", encoding="utf-8")
            out = root / "run"

            def unexpected_network(*_args, **_kwargs):
                raise AssertionError("offline snapshot mode called a network adapter")

            receipt = run_research(
                question="Test snapshot ingestion",
                queries=["frozen search query one", "frozen search query two"],
                output_dir=out,
                source_snapshots_path=manifest,
                claim_review_path=claims,
                searcher=unexpected_network,
                crossref_fetch=unexpected_network,
            )

            self.assertEqual(receipt["status"], "COMPLETED")
            self.assertEqual(receipt["ingestion_mode"], "OFFLINE_SOURCE_SNAPSHOTS")
            self.assertEqual(receipt["counts"]["query_ok"], 0)
            self.assertEqual(receipt["counts"]["queries_declared"], 2)
            self.assertEqual(receipt["counts"]["claim_review_anchored"], 1)
            self.assertEqual(receipt["source_snapshot_manifest_sha256"], hashlib.sha256(manifest.read_bytes()).hexdigest())
            saved_sources = [json.loads(line) for line in (out / "sources.jsonl").read_text().splitlines()]
            self.assertEqual([source["source_id"] for source in saved_sources], ["S1", "S2"])
            self.assertEqual((out / saved_sources[0]["raw_evidence"][0]["path"]).read_bytes(), web_capture)
            self.assertEqual((out / saved_sources[1]["raw_evidence"][0]["path"]).read_bytes(), api_capture)
            self.assertEqual(saved_sources[1]["capture_sha256"], hashlib.sha256(api_capture).hexdigest())
            ledger = json.loads((out / "claim-review.jsonl").read_text().splitlines()[0])
            self.assertEqual(ledger["evidence_anchor_status"], "EXACT_MATCH")
            self.assertEqual(ledger["source_url"], "https://example.org/report")
            query_rows = [json.loads(line) for line in (out / "query-manifest.jsonl").read_text().splitlines()]
            self.assertEqual(query_rows[0]["status"], "DECLARED_EXTERNALLY_NOT_VERIFIED")
            self.assertEqual(query_rows[0]["response_capture_status"], "NOT_CAPTURED_BY_CLI")
            report = (out / "report.md").read_text()
            self.assertIn("not the original publisher HTTP response", report)
            self.assertNotIn("DOI title/year metadata matches", report)

    def test_offline_source_snapshots_reject_path_escape_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "outside.txt").write_text("not allowed", encoding="utf-8")
            manifest = root / "source-snapshots.jsonl"
            row = {
                "title": "Outside file",
                "source_url": "https://example.org/report",
                "capture_path": "../outside.txt",
                "capture_kind": "web_run_observation",
                "captured_at_utc": "2026-10-16T09:30:00Z",
                "locator": "Section 1",
            }
            manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
            output = root / "run"
            with self.assertRaisesRegex(ValueError, "stay under the manifest directory"):
                run_research(
                    question="Question", queries=["query"], output_dir=output,
                    source_snapshots_path=manifest,
                )
            self.assertFalse(output.exists())

    def test_offline_source_snapshots_allow_only_one_official_api_response(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "one.json").write_text('{"status":"ok"}', encoding="utf-8")
            (root / "two.json").write_text('{"status":"ok"}', encoding="utf-8")
            manifest = root / "source-snapshots.jsonl"
            rows = [
                {
                    "title": f"API {index}",
                    "source_url": f"https://api.example.org/series/{index}",
                    "capture_path": f"{name}.json",
                    "capture_kind": "official_api_json",
                    "captured_at_utc": "2026-10-16T09:30:00Z",
                    "locator": "Results[0]",
                }
                for index, name in ((1, "one"), (2, "two"))
            ]
            manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "at most one official_api_json"):
                run_research(
                    question="Question", queries=["query"], output_dir=root / "run",
                    source_snapshots_path=manifest,
                )

    def test_cli_runs_offline_source_snapshot_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture = b"Saved source observation."
            (root / "capture.txt").write_bytes(capture)
            manifest = root / "manifest.jsonl"
            row = {
                "title": "Saved source",
                "source_url": "https://example.org/source",
                "capture_path": "capture.txt",
                "capture_kind": "web_run_observation",
                "captured_at_utc": "2026-10-16T09:30:00Z",
                "locator": "Summary",
            }
            manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
            out = root / "run"
            args = [
                "--question", "A source question",
                "--query", "one frozen query",
                "--source-snapshots", str(manifest),
                "--output-dir", str(out),
            ]
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = cli.main(args)
            self.assertEqual(exit_code, 0)
            saved_receipt = json.loads((out / "receipt.json").read_text())
            self.assertEqual(saved_receipt["ingestion_mode"], "OFFLINE_SOURCE_SNAPSHOTS")
            self.assertIn("Saved source observation", (out / "raw/source-S1.txt").read_text())

    def test_offline_source_snapshots_enforce_ten_mb_capture_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture = root / "large.txt"
            with capture.open("wb") as handle:
                handle.truncate(cli.MAX_SOURCE_SNAPSHOT_BYTES + 1)
            manifest = root / "manifest.jsonl"
            row = {
                "title": "Large capture",
                "source_url": "https://example.org/source",
                "capture_path": "large.txt",
                "capture_kind": "web_run_observation",
                "captured_at_utc": "2026-10-16T09:30:00Z",
                "locator": "Section 1",
            }
            manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
            output = root / "run"
            with self.assertRaisesRegex(ValueError, "10 MB capture limit"):
                run_research(
                    question="Question", queries=["query"], output_dir=output,
                    source_snapshots_path=manifest,
                )
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
