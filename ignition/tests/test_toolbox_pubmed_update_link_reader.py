from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_pubmed_update_link_reader.py"
SPEC = importlib.util.spec_from_file_location("toolbox_pubmed_update_link_reader", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


PMID = "9500320"
SAMPLE_DOI = "10.1234/example.1"
SAMPLE_XML = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMed 3.0//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/in/PubMed.dtd">
<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID Version="1">{PMID}</PMID>
<Article><ArticleTitle>Ignored title.</ArticleTitle><Abstract><AbstractText>Ignored abstract.</AbstractText></Abstract><ELocationID EIdType="doi">{SAMPLE_DOI}</ELocationID></Article>
<CommentsCorrectionsList>
 <CommentsCorrections RefType="RetractionIn"><RefSource>Lancet. 2004 Mar 6;363(9411):750.</RefSource><PMID Version="1">15022645</PMID></CommentsCorrections>
 <CommentsCorrections RefType="CommentIn"><RefSource>BMJ. 2004;328(7438):394.</RefSource><PMID Version="1">14962870</PMID></CommentsCorrections>
</CommentsCorrectionsList></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">{SAMPLE_DOI}</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'''.encode("utf-8")


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, content_type: str = "application/xml") -> None:
        self.body = body
        self.offset = 0
        self.read_calls = 0
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        end = len(self.body) if size < 0 else min(len(self.body), self.offset + size)
        value = self.body[self.offset:end]
        self.offset = end
        return value


class FakeOpener:
    def __init__(self, response: FakeResponse | None = None, error: Exception | None = None) -> None:
        self.response = response or FakeResponse(SAMPLE_XML)
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


def request_bytes(pmids: list[str] | None = None) -> bytes:
    return json.dumps({"pmids": [PMID] if pmids is None else pmids}).encode("utf-8")


class PubMedUpdateLinkReaderTests(unittest.TestCase):
    def test_reads_only_raw_relation_fields_from_exact_fixed_host_record(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener) as build_opener:
            result = TOOL.inspect([PMID])
        self.assertEqual(build_opener.call_count, 1)
        self.assertIsInstance(build_opener.call_args.args[0], TOOL._NoRedirectHandler)
        request, timeout = opener.calls[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "eutils.ncbi.nlm.nih.gov")
        self.assertEqual(parsed.path, "/entrez/eutils/efetch.fcgi")
        self.assertEqual(parse_qs(parsed.query), {"db": ["pubmed"], "id": [PMID], "retmode": ["xml"], "tool": ["IgnitionToolbox"]})
        self.assertEqual(timeout, TOOL.REQUEST_TIMEOUT_SECONDS)
        row = result["rows"][0]
        self.assertEqual(result["status"], "RECORDS_INSPECTED")
        self.assertEqual(row["record_status"], "RECORD_FOUND_WITH_RECORDED_RELATIONS")
        self.assertEqual(row["relations"], [
            {"ref_type": "RetractionIn", "related_pmid": "15022645", "reference_source": "Lancet. 2004 Mar 6;363(9411):750."},
            {"ref_type": "CommentIn", "related_pmid": "14962870", "reference_source": "BMJ. 2004;328(7438):394."},
        ])
        self.assertNotIn("Ignored title", json.dumps(result))
        self.assertNotIn("Ignored abstract", json.dumps(result))
        self.assertEqual(len(row["response_sha256"]), 64)
        self.assertIn("empty relation list does not prove", result["claim_ceiling"])

    def test_expected_doi_binding_is_checked_in_the_same_efetch_record(self) -> None:
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener()):
            result = TOOL.inspect([PMID], expected_doi=SAMPLE_DOI)
        row = result["rows"][0]
        self.assertEqual(row["expected_doi"], SAMPLE_DOI)
        self.assertEqual(row["doi_binding_status"], "EXACT_MATCH")
        self.assertEqual(row["record_status"], "RECORD_FOUND_WITH_RECORDED_RELATIONS")
        self.assertEqual(len(row["relations"]), 2)

        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener()):
            mismatch = TOOL.inspect([PMID], expected_doi="10.9999/other")
        mismatch_row = mismatch["rows"][0]
        self.assertEqual(mismatch_row["doi_binding_status"], "MISMATCH")
        self.assertEqual(mismatch_row["record_status"], "DOI_IDENTITY_NOT_CONFIRMED")
        self.assertEqual(mismatch_row["relations"], [])
        self.assertEqual(mismatch["records_found"], 1)

    def test_expected_doi_is_not_confirmed_when_missing_or_ambiguous(self) -> None:
        no_doi = f"<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>{PMID}</PMID></MedlineCitation></PubmedArticle></PubmedArticleSet>".encode()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(no_doi))):
            missing = TOOL.inspect([PMID], expected_doi=SAMPLE_DOI)["rows"][0]
        self.assertEqual(missing["doi_binding_status"], "NOT_REPORTED")
        self.assertEqual(missing["record_status"], "DOI_IDENTITY_NOT_CONFIRMED")
        self.assertEqual(missing["relations"], [])

        multiple = SAMPLE_XML.replace(
            b"</Article>", b'<ELocationID EIdType="doi">10.9999/other</ELocationID></Article>',
        )
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(multiple))):
            ambiguous = TOOL.inspect([PMID], expected_doi=SAMPLE_DOI)["rows"][0]
        self.assertEqual(ambiguous["doi_binding_status"], "MULTIPLE_VALUES")
        self.assertEqual(ambiguous["record_status"], "DOI_IDENTITY_NOT_CONFIRMED")
        self.assertEqual(ambiguous["relations"], [])

        invalid = SAMPLE_XML.replace(
            b"</Article>", b'<ELocationID EIdType="doi">https://doi.org/10.1234/example.1</ELocationID></Article>',
        )
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(invalid))):
            malformed = TOOL.inspect([PMID], expected_doi=SAMPLE_DOI)["rows"][0]
        self.assertEqual(malformed["doi_binding_status"], "INVALID_VALUE")
        self.assertEqual(malformed["record_status"], "DOI_IDENTITY_NOT_CONFIRMED")
        self.assertEqual(malformed["relations"], [])

    def test_expected_doi_is_bounded_to_one_valid_bare_doi_and_one_pmid(self) -> None:
        with self.assertRaisesRegex(TOOL.ToolInputError, "bare DOI"):
            TOOL.parse_request_with_options(json.dumps({"pmids": [PMID], "expected_doi": None}).encode())
        with self.assertRaisesRegex(TOOL.ToolInputError, "exactly one PMID"):
            TOOL.parse_request_with_options(json.dumps({"pmids": [PMID, "9500321"], "expected_doi": SAMPLE_DOI}).encode())
        self.assertEqual(
            TOOL.parse_request_with_options(json.dumps({"pmids": [PMID], "expected_doi": SAMPLE_DOI}).encode()),
            ([PMID], SAMPLE_DOI),
        )
        with self.assertRaisesRegex(TOOL.ToolInputError, "exactly one PMID"):
            TOOL.inspect([PMID, "9500321"], expected_doi=SAMPLE_DOI)

    def test_requires_explicit_network_flag_and_makes_no_request_without_it(self) -> None:
        opener = FakeOpener()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=opener):
            with patch.object(TOOL.sys, "stdin", FakeStdin(request_bytes())):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                    code = TOOL.main(["--stdin"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(opener.calls, [])
        self.assertIn("--allow-public-network", stderr.getvalue())

    def test_rejects_invalid_duplicate_and_over_limit_pmids_before_network(self) -> None:
        for invalid in ("0", "-1", "https://pubmed.ncbi.nlm.nih.gov/123/", "1 2", "001"):
            with self.subTest(invalid=invalid), self.assertRaises(TOOL.ToolInputError):
                TOOL.parse_request(request_bytes([invalid]))
        with self.assertRaisesRegex(TOOL.ToolInputError, "unique"):
            TOOL.parse_request(request_bytes([PMID, PMID]))
        with self.assertRaisesRegex(TOOL.ToolInputError, "between 1 and"):
            TOOL.parse_request(request_bytes([str(i + 1) for i in range(TOOL.MAX_RECORDS + 1)]))
        with self.assertRaisesRegex(TOOL.ToolInputError, "duplicate JSON"):
            TOOL.parse_request(b'{"pmids":[],"pmids":[]}')

    def test_empty_record_and_wrong_record_are_not_interpreted_as_no_retraction(self) -> None:
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(b"<PubmedArticleSet/>"))):
            row = TOOL.inspect([PMID])["rows"][0]
        self.assertEqual(row["record_status"], "NO_RECORD")
        self.assertEqual(row["relations"], [])

        wrong = b"<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>100</PMID></MedlineCitation></PubmedArticle></PubmedArticleSet>"
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(wrong))):
            row = TOOL.inspect([PMID])["rows"][0]
        self.assertEqual(row["record_status"], "UPSTREAM_RECORD_MISMATCH")

    def test_empty_relation_list_is_a_limited_observation(self) -> None:
        no_relations = f"<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>{PMID}</PMID></MedlineCitation></PubmedArticle></PubmedArticleSet>".encode()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(no_relations))):
            result = TOOL.inspect([PMID])
        self.assertEqual(result["status"], "RECORDS_INSPECTED")
        self.assertEqual(result["rows"][0]["record_status"], "RECORD_FOUND_NO_RECORDED_RELATIONS")
        self.assertEqual(result["rows"][0]["relations"], [])
        self.assertFalse(result["rows"][0]["relations_truncated"])

    def test_rejects_entity_expansion_and_invalid_xml_without_exposing_content(self) -> None:
        entity = f'<!DOCTYPE x [<!ENTITY x "expanded">]><PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>{PMID}</PMID></MedlineCitation></PubmedArticle></PubmedArticleSet>'.encode()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(entity))):
            row = TOOL.inspect([PMID])["rows"][0]
        self.assertEqual(row["acquisition_status"], "XML_ENTITY_DECLARATION_REJECTED")
        self.assertEqual(row["relations"], [])

        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(b"<not-closed"))):
            row = TOOL.inspect([PMID])["rows"][0]
        self.assertEqual(row["acquisition_status"], "INVALID_XML_RESPONSE")

    def test_redirect_size_content_type_and_timeout_fail_explicitly(self) -> None:
        redirect = FakeOpener(error=HTTPError(TOOL.API_BASE, 302, "redirect", {}, None))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=redirect):
            self.assertEqual(TOOL._fetch_one(PMID)["acquisition_status"], "REDIRECT_BLOCKED")

        oversized = FakeOpener(FakeResponse(b"x" * (TOOL.MAX_RESPONSE_BYTES + 1)))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=oversized):
            self.assertEqual(TOOL._fetch_one(PMID)["acquisition_status"], "RESPONSE_TOO_LARGE")

        html = FakeOpener(FakeResponse(b"<html/>", content_type="text/html"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=html):
            self.assertEqual(TOOL._fetch_one(PMID)["acquisition_status"], "NON_XML_RESPONSE")

        slow = FakeOpener(FakeResponse(SAMPLE_XML))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=slow), patch.object(TOOL.time, "monotonic", side_effect=[0.0, 8.0]):
            self.assertEqual(TOOL._fetch_one(PMID)["acquisition_status"], "RESPONSE_TIMEOUT")
        self.assertEqual(slow.response.read_calls, 0)

    def test_network_failures_remain_visible(self) -> None:
        failed = FakeOpener(error=TimeoutError("timed out"))
        with patch.object(TOOL.urllib.request, "build_opener", return_value=failed):
            result = TOOL.inspect([PMID])
        self.assertEqual(result["status"], "COMPLETED_WITH_EXPLICIT_FAILURES")
        self.assertEqual(result["rows"][0]["acquisition_status"], "NETWORK_ERROR")
        self.assertEqual(result["rows"][0]["record_status"], "NOT_AVAILABLE")

    def test_noncanonical_relation_values_and_long_reference_text_are_bounded(self) -> None:
        source = "x" * (TOOL.MAX_RELATION_SOURCE_LENGTH + 50)
        xml = f'<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>{PMID}</PMID><CommentsCorrectionsList><CommentsCorrections RefType="PublisherUpdate"><RefSource>{source}</RefSource><PMID>not-a-pmid</PMID></CommentsCorrections></CommentsCorrectionsList></MedlineCitation></PubmedArticle></PubmedArticleSet>'.encode()
        with patch.object(TOOL.urllib.request, "build_opener", return_value=FakeOpener(FakeResponse(xml))):
            relation = TOOL.inspect([PMID])["rows"][0]["relations"][0]
        self.assertEqual(relation["ref_type"], "PublisherUpdate")
        self.assertIsNone(relation["related_pmid"])
        self.assertEqual(len(relation["reference_source"]), TOOL.MAX_RELATION_SOURCE_LENGTH)


if __name__ == "__main__":
    unittest.main()
