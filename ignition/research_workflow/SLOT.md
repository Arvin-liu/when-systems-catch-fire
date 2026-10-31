# Fixed source-binding adapter slot

`slot.py` exposes one small Source/Evidence Binding slot with two fixed adapter
IDs. Select one adapter before each run; the choice and source commit are
recorded in `run-manifest.json` and `receipt.json`. The run never switches
adapters or overwrites a failed receipt. A later independent run can select
`legacy-openalex-v1` as the rollback path.

```bash
PYTHONPATH=. python3 -m ignition.research_workflow.slot \
  --adapter e37-source-snapshot-v1 \
  --source-snapshots path/to/manifest.jsonl \
  --expected-digests path/to/expected-digests.json \
  --expected-source-set-digest <sha256-of-canonical-source-set> \
  --question "What do the frozen sources show?" \
  --draft path/to/draft.md --claim-reviews path/to/claims.jsonl \
  --output-dir path/to/new-run \
  --task-id TASK-1 --episode-id EPISODE-1 --source-set-id SOURCES-V1 \
  --namespace research/example --authorization-scope read-only-public-abstracts \
  --implementation-commit <exact-slot-commit>
```

Both adapters require the same preregistered `--expected-source-set-digest`.
The digest binds source IDs, titles, URLs, and SHA-256 values of normalized
abstract text. Each receipt records the expected and observed value. The
candidate additionally records the digest-lock file hash and refuses missing,
malformed, extra, or mismatched per-capture hashes before writing run output.
Each run copies its draft and claim-review input under `inputs/` and records
their SHA-256 values in the run manifest and receipt, so a receipt binds the
reviewed text and claim rows as well as the source set.

The legacy adapter accepts normalized OpenAlex-shaped JSONL records only; it
marks original capture bytes unavailable. The e37 adapter accepts offline
source snapshots only and preserves each verified capture byte-for-byte. The
expected-digest and canonical-source-set locks are enforced by this slot layer,
not attributed to the upstream adapters. Both supply one common `abstract`
field to the same `_validate_draft()` and `_build_claim_review_ledger()`
consumer. The e37 adapter can also anchor `captured_text` against the saved
reader observation; the legacy adapter rejects that field because it has no raw
capture. Neither adapter authenticates the originating publisher or infers
semantic support. Retrieval and ranking capabilities are deliberately outside
this adapter comparison.

Run the slot's offline tests alongside the existing workflow tests with:

```bash
python3 -m unittest discover -s ignition/research_workflow -p 'test_*.py'
```
