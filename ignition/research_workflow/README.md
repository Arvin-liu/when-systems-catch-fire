# Research workflow R0

This stdlib-only CLI captures OpenAlex search responses, rechecks DOI title/year
metadata through the repository's existing Crossref runner, checks citations in an
optional agent-authored Markdown synthesis, and writes a report, JSONL manifests,
raw provider responses, and a SHA-256 receipt.

Run from the repository root:

```bash
python3 ignition/research_workflow/cli.py \
  --question "What does recent evidence show about example topic?" \
  --query "example topic empirical study" \
  --query "example topic replication" \
  --max-sources 12 \
  --output-dir /tmp/example-research-run
```

To include an agent-authored synthesis, pass `--draft draft.md`; the file must
cite at least one source with `[S1]` markers that exist in this run. The workflow
checks marker resolution only. It does not decide whether claims follow from
papers. A report without `--draft` is an evidence brief containing captured
metadata and abstracts, not a generated conclusion.

The output directory must be new or empty. A missing DOI, failed request,
Crossref mismatch, or absent abstract remains explicit in the machine records.
When `--max-sources` truncates results, selection proceeds round-robin in query
order, by each query's captured rank, so a broad early query cannot consume the
entire cap before later query areas are represented. Duplicate works are kept
once, with their query IDs and per-query ranks retained in `sources.jsonl`.
Run `python3 -m unittest discover -s ignition/research_workflow -p 'test_*.py'`
for offline tests.
