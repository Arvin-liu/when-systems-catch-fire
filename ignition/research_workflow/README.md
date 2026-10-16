# Research workflow R1 candidate

This stdlib-only CLI captures OpenAlex search responses, rechecks DOI title/year
metadata through the repository's existing Crossref runner, checks citations in an
optional agent-authored Markdown synthesis, and writes a report, JSONL manifests,
raw provider responses, and a SHA-256 receipt. It also links a manually authored
claim-to-source review row to an exact excerpt and the raw query record that
contained it. It does not decide whether the claim is true or supported.

Run from the repository root:

```bash
python3 ignition/research_workflow/cli.py \
  --question "What does recent evidence show about example topic?" \
  --query "example topic empirical study" \
  --query "example topic replication" \
  --max-sources 12 \
  --claim-reviews /tmp/claim-reviews.jsonl \
  --output-dir /tmp/example-research-run
```

The fixed source-input interface is one research question, one or more explicit
OpenAlex queries, and a source cap. Lane C can pass the same frozen question and
queries directly at these flags. If a claim review file is supplied, it is
UTF-8 JSONL, one object per claim/source pair. A reviewed row has this shape:

```json
{"claim_id":"C1","claim_text":"Claim from the draft","source_id":"S1","review_judgment":"SUPPORTS","reviewer_type":"HUMAN","reviewer":"<reviewer-id>","reviewed_at_utc":"<review-time>","evidence_field":"abstract","evidence_quote":"<verbatim captured excerpt>"}
```

`review_judgment` must be supplied by the reviewer (`SUPPORTS`, `CONTRADICTS`,
`CONTEXT_ONLY`, or `INSUFFICIENT`). The tool checks that `source_id` resolves and
that the quote is an exact substring of the captured title or abstract. The row
also carries the source response path/hash and per-record hash. Those checks
make the evidence handoff easier to reconstruct; they are not semantic fact
checking. Rows without review input are explicitly `NOT_VALIDATED`.

To include an agent-authored synthesis, pass `--draft draft.md`; the file must
cite at least one source with `[S1]` markers that exist in this run. The workflow
checks marker resolution only. It does not decide whether claims follow from
papers. A report without `--draft` is an evidence brief containing captured
metadata and abstracts, not a generated conclusion.

The output directory must be new or empty. Acquisition status is `COMPLETED`
when all queries succeeded and returned at least one source, `PARTIAL` when some
queries failed, `FAILED` when all queries failed, and `NOT_VALIDATED` when every
query succeeded but no source was returned. The CLI exits nonzero for partial or
failed retrieval, empty retrieval, invalid drafts, or an incomplete/failed
provided claim ledger. A missing DOI, failed request, Crossref mismatch, or
absent abstract remains explicit in machine records.

The CLI re-parses every captured response body and derives normalized rows from
those bytes. If an injected searcher also supplies normalized rows, they must
exactly match the derived rows; otherwise the response is preserved as an error
and contributes no source. Existing `search()` remains a list-returning API for
older callers.
When `--max-sources` truncates results, selection proceeds round-robin in query
order, by each query's captured rank, so a broad early query cannot consume the
entire cap before later query areas are represented. Duplicate works are kept
once, with their query IDs and per-query ranks retained in `sources.jsonl`.
Run `python3 -m unittest discover -s ignition/research_workflow -p 'test_*.py'`
for offline tests.

## Offline source snapshots

Use `--source-snapshots manifest.jsonl` when research uses official pages or
data that are not available through OpenAlex. The CLI makes no network request
in this mode. It records the query strings as researcher-provided inputs, but
does not claim that it executed or verified those searches.

```bash
python3 ignition/research_workflow/cli.py \
  --question "What does the official evidence show?" \
  --query "frozen search query one" \
  --source-snapshots /tmp/source-snapshots/manifest.jsonl \
  --output-dir /tmp/example-snapshot-run
```

Each manifest line points to one UTF-8 capture file beside the manifest:

```json
{"title":"Official report section","source_url":"https://example.org/report","capture_path":"captures/report-section.txt","capture_kind":"web_run_observation","captured_at_utc":"2026-10-16T09:30:00Z","locator":"Section 2, table 1","query_ids":["Q1","Q2"],"content_type":"text/plain; charset=utf-8"}
```

`web_run_observation` means the saved rendered text returned by the web search/open
tool. It is not the publisher's original HTTP response. `official_api_json` is
for an actual UTF-8 JSON response body; at most one such response and at most
five source captures are allowed per run, and each capture is limited to 10 MB.
The `source_url`, title, locator, timestamp, query IDs, and capture kind are
manifest metadata supplied by the caller. The tool preserves the capture bytes,
hashes the manifest and each capture, and links those hashes from `sources.jsonl`
and `claim-review.jsonl`. It does not authenticate the capture's origin.

In a human claim-review row, use `"evidence_field":"captured_text"` to check
that the quoted excerpt appears exactly in the saved capture bytes. An exact
match only confirms an anchor; it does not determine whether the excerpt
supports the claim. The source note and receipt keep this limitation explicit.
