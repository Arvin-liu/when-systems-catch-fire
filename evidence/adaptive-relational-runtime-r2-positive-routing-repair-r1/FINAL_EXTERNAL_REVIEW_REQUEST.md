# Final External Review Request — ARR R2 Positive Routing Repair R1

**Requested verdict:** `ARR_R2_POSITIVE_ROUTING_REPAIR_DRAFT_AWAITING_EXTERNAL_REVIEW`
**R3 scale run remains UNAUTHORIZED** until independent external acceptance.

## What this is
A narrow, stacked repair of the five defects the external review found in the
frozen R2 head `bfe90c65` (Draft PR #121). It does not erase or rewrite the
original R2 fail-closed / privacy-boundary result; it reruns the **exact same**
48-object selection (manifest digest `d132c825…`) after fixing the positive-path
defects so the real-object pilot actually completes end-to-end.

## Predecessor negative result (measured honestly on frozen R2)
- selected: 48
- extraction (adapter-dispatch) failures: **40** (5 non-mechanism adapter classes ×
  8 objects each raised `TypeError` on the unsupported `declared_capabilities` kwarg)
- runtime (Source-validation) failures: **8** (all 8 mechanism objects reached
  `eng.run` and failed schema validation)
- projection executed: 0 · all inputs immutable: false · positive successes: 0

> The IGNITION §5 prose stated 42/6; the synthetic manifest assigns exactly 8
> objects/class via `(i-1)%6`, so the genuine frozen behavior is 40/8. This
> request reports the true measurement.

## After (repaired head, same 48 objects)
selected 48 · receipts 48 · adapter success 48 · runtime success 48 ·
projection executed 48 · input immutable 48/48 · replay stable 48/48 ·
expected/actual route match 48/48 · positive successes 48 ·
real_world_actions 0 · privacy_boundary_ok 48/48 · unexpected extraction 0 ·
unexpected runtime 0 · promote 0 · evolve 0.

## Defects repaired
- **4.1** registry-driven adapter dispatch protocol (fail-closed; only the
  mechanism adapter forwards `declared_capabilities`)
- **4.2** schema-valid Source / Observation (locator, rights boundary,
  `private_corpus`/`hash_only`, 64-hex digest, tier, deterministic ids)
- **4.3** locked-manifest immutability (deep-copy inputs + `adapter_ref`)
- **4.4** real projection routing via `eng._project` (never `None`)
- **4.5** explicit per-object outcome semantics
- **4.6** aggregation semantics (coverage measures success, not receipt presence)

## Commit plan (exactly four ordinary commits, noreply identity)
1. `a643c72` repair contract, ADRs, failing regression tests
2. `800cdf1` adapter protocol + schema-valid Source/Observation + immutability + projection + receipt
3. `4363d5a` aggregation semantics (4.6)
4. (this commit) exact 48-object replay, before/after evidence, propagation/docs/CI

No amend / rebase / squash / force-push / history rewrite. Predecessor PR #109–#121
and Main untouched.

## Remote publication (live state at publication time)
- Formal child branch `repair/adaptive-relational-runtime-r2-positive-routing-r1`
  pushed to `Arvin-liu/when-systems-catch-fire`.
- Draft PR **#122** opened: head = child branch, base =
  `runtime/adaptive-relational-runtime-r2-real-object-pilot`.
- Annotated frozen tag `archive/adaptive-relational-runtime-r2-positive-routing-repair-r1-frozen-head`
  created on the final repair head and pushed (see closing refetch).
- 1111 evidence branch `agent/adaptive-relational-runtime-r2-positive-routing-repair-r1-20260725`
  (separate repository `Arvin-liu/1111`) to be pushed with this evidence.
- `REMOTE_IDENTITY_RECEIPT.json` records the live remote refetch at publication time.

## Evidence (this directory)
REPAIR_ADRS · PREDECESSOR_NEGATIVE_RESULT · ADAPTER_PROTOCOL_MATRIX ·
SOURCE_OBSERVATION_VALIDATION · MANIFEST_IMMUTABILITY_PROOF ·
REAL_OBJECT_SELECTION_MANIFEST (digest `d132c825…`) · BEFORE_AFTER_COMPARISON ·
REAL_OBJECT_RUN_LEDGER_REPAIRED + 48 receipts · CAPABILITY_COVERAGE_MATRIX_REPAIRED ·
FAILURE_ATTRIBUTION_LEDGER_REPAIRED · REPRESENTATION_RESIDUE_REPAIRED ·
ROUTING_RESIDUE_REPAIRED · REPLAY_IDEMPOTENCY_REPORT_REPAIRED ·
FALSE_CONSENSUS_CASES_REPAIRED · ENGINEERING_SIGNALS_REPAIRED ·
NO_EVOLVE_JUSTIFICATIONS_REPAIRED · RIGHTS_AND_PRIVACY_AUDIT · ATTACK_MATRIX_REPAIR_64
(71 repair checks ≥ 64) · SUBAGENT_LEDGER · PROPAGATION_CLOSURE · NONIMPACT_PROOFS ·
COUNTERS · REMOTE_IDENTITY_RECEIPT.

## Key counters
REAL_OBJECTS_SELECTED 48 · REAL_OBJECTS_RUN 48 · POSITIVE_PATH_OBJECTS 48 ·
PROJECTION_EXECUTED 48 · UNEXPECTED_EXTRACTION_FAILURES 0 · UNEXPECTED_RUNTIME_FAILURES 0 ·
REAL_WORLD_ACTIONS 0 · PRIVATE_CONTENT_PUBLICATION_EVENTS 0 · FORMAL_NEW_BRANCHES 1 ·
FORMAL_NEW_PRS 1 · FORMAL_DRAFT_PRS 1 · FORMAL_READY_PRS 0 · FORMAL_MERGES 0 ·
MAIN_CHANGES 0 · PREDECESSOR_PR_CHANGES 0 · FORCE_PUSHES 0 · HISTORY_REWRITES 0 ·
EXTERNAL_ACCEPTANCE_CLAIMED 0.

## Independent checks the reviewer should confirm
1. Exactly four ordinary commits; no history rewrite; noreply identity.
2. Frozen R2 still demonstrates fail-closed + privacy containment (untouched).
3. Repair head: 48/48 receipts, adapter/runtime/projection success, replay stable,
   expected/actual route match, 0 real-world actions, 0 privacy leak.
4. 71 repair checks pass on the repair head and fail to collect on frozen R2.
5. Manifest digest retained (`d132c825…`); exact same 48 objects.
6. Draft PR #122 base is `runtime/...real-object-pilot`; predecessor PRs/Main/tags unchanged.

## Closing gate
A final live remote refetch is performed after all publication (branch + PR + tag +
1111 evidence branch). Its result is recorded in `REMOTE_IDENTITY_RECEIPT.json` and
reported in the final agent message. Until independent external acceptance, do not
merge, mark Ready, modify Main, promote assets, or start R3.
