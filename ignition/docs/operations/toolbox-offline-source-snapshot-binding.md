# Offline source-snapshot binding tool

`research.bind_offline_source_snapshot_run` runs the existing E37 saved-source
adapter through a fixed, offline-only entry point. It binds each capture to a
caller-supplied SHA-256 lock, binds the normalized source set to a separate
expected digest, and preserves the selected captures, draft, claim-review rows,
manifest, run receipt, and artifact hashes in one new run directory.

The tool never selects the legacy adapter, performs a search, or makes a network
request. Its digest preview verifies the per-capture lock and prints the
canonical source-set SHA-256 without creating files:

```bash
python3 ignition/tools/toolbox_bind_offline_source_snapshot_run.py \
  --source-snapshots /path/to/manifest.jsonl \
  --expected-digests /path/to/expected-digests.json \
  --query-count 2 \
  --print-source-set-digest
```

For a run, supply that digest and a new output path outside the checked-out
repository:

```bash
python3 ignition/tools/toolbox_bind_offline_source_snapshot_run.py \
  --source-snapshots /path/to/manifest.jsonl \
  --expected-digests /path/to/expected-digests.json \
  --expected-source-set-digest <canonical-sha256> \
  --question "What do these saved sources report?" \
  --draft /path/to/draft.md \
  --claim-reviews /path/to/claims.jsonl \
  --output-dir /path/to/new-run \
  --task-id TASK-1 --episode-id EPISODE-1 --source-set-id SOURCES-V1 \
  --namespace research/example --authorization-scope offline-saved-captures-only
```

The output directory must be absent or empty, cannot be a symlink, and must not
be inside or contain the repository checkout. The tool records the checked-out
implementation commit itself. All paths, identifiers, and review judgments are
caller inputs. Passing a citation, quote, or judgment does not validate its
meaning.

## Limits and comparison

An exact quote match proves only that the text occurs in the selected frozen
capture. The tool does not authenticate the publisher, assess source
completeness, decide whether a quote supports a claim, or validate scientific
conclusions. Source authenticity and semantic validation remain unperformed.

The frozen adapter comparison in PR #259 used the same source abstracts, draft,
claim rows, and downstream consumer. The first comparison version had a shared
Unicode-space mismatch and produced 6/7 anchors in both arms. A preregistered
corrective version produced 7/7 anchors in both arms. The narrow observed
difference was recovery of 2/2 raw capture streams in the E37 arm versus 1/2
after auditing all legacy output artifacts. This supports a specialized
offline-capture use case; it does not establish general quality, semantic
accuracy, or cost superiority. Existing evidence-program validation,
repository-local raw-evidence navigation, and live OpenAlex metadata tools
cover different input and permission scopes and remain available.

The card is experimental and default-off. Routing it requires an explicit
candidate allowlist, and a route proposal never authorizes invocation.
