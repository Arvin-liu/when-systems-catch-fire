# V1 G1 Goal intake preflight

This package is an offline, read-only adapter for one closed synthetic `ResearchEpisodeRequest` envelope. It checks exact Intent, Goal, Completion Contract, version, parent, objective-digest, policy, budget, and stop-condition bindings, then emits a machine report and a short Markdown summary.

The report separates two questions. `structural_outcome=CANDIDATE_STRUCTURALLY_VALID_PROPOSAL_ONLY` means only that the supplied bytes satisfy the proposal shape and cross-field checks. The top-level `preflight_status=REQUIRES_OWNER_AUTHORITY` remains the result for every structurally valid input because this adapter has no trusted Owner identity, trust roots, or live canonical lookup. Forged Owner claims are recorded as claims and never authenticated.

The adapter does not register or update records, evaluate completion, create an approval receipt, or dispatch a task. `GoalEpisodeBinder` is used only to build an ephemeral in-memory projection from supplied fixture bytes; the report marks `canonical_binding_created=false`. A `RUN_PASS` outcome never implies Goal completion.

## Run the synthetic example

From the `ignition/` directory:

```sh
python -m research_os_v1.g1_goal_intake \
  --input research_os_v1/g1_goal_intake/fixtures/structurally-valid-proposal.json \
  --report-dir /tmp/g1-goal-intake-report
```

The CLI accepts only regular files below this package's `fixtures/` directory. The report directory must be a new or empty directory below the system temporary directory (or `/tmp` where present); a symlink output directory is rejected. The CLI makes no network or provider calls. It emits deterministic UTF-8 JSON and Markdown bytes; input time fields are part of the supplied fixture and no observation timestamp is added.

The exact synthetic fixture bytes are covered by `fixtures/structurally-valid-proposal.json`; its SHA-256 is captured in `RESULT.md` and `SHA256SUMS.txt`. Tests provide malformed, stale, detached, policy-expanding, and forged-authority variants without modifying the fixture.

## Existing Steering types

| Existing type | Dry-run compatibility use | Explicit boundary |
| --- | --- | --- |
| `IntentRecord` | Parse a supplied, closed Intent snapshot and inspect proposal scope/status. | No registry read or write; the snapshot is untrusted and may be stale. |
| `GoalRecord` | Parse a supplied Goal snapshot and call its existing `objective_digest()` method. | Digest omits parent, provenance, status, and canonical-currentness; those fields are checked separately where the input permits. |
| `CompletionContract` | Check exact acceptance predicates and required evidence metadata. | Never call `evaluate_completion`; preflight is not a completion decision. |
| `GoalEpisodeBinder` | Create an ephemeral projection for the supplied proposal/run IDs. | The binder is a local in-memory object and its result is labeled noncanonical. |
| `GoalDriftGuard` | Compare supplied digest and success predicates using existing reason codes. | `CLEAR` covers only supplied bytes; memory conflict and live currentness are not checked. |

The exact source anchors are recorded in each report and refer to the PR branch head at the start of this work, not to an assertion that those files remain current later.
