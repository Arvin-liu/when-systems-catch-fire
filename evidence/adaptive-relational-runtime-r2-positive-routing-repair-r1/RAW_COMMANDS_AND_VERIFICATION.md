# Raw Commands, Exit Codes & Decisive Artifact Pointers

All commands run from `tools/...` repo root on branch
`repair/adaptive-relational-runtime-r2-positive-routing-r1` (HEAD = final repair
commit). Identity: `49422864+Arvin-liu@users.noreply.github.com`.

## Verification commands (read-only gate, all exit 0)
| command | result |
|---|---|
| `git ls-remote origin 'refs/tags/archive/adaptive-relational-runtime-r2-real-object-pilot-frozen-head^{}'` | `bfe90c65a80619e6c6c81586a2befb15796b93bb` (predecessor frozen tag → exact head) |
| `gh pr view 121 --json state,isDraft,headRefOid,baseRefName` | `OPEN`, `isDraft:true`, head `bfe90c65…`, base `architecture/adaptive-relational-runtime-r1-scaffold` |
| `git ls-remote origin runtime/adaptive-relational-runtime-r2-real-object-pilot` | `bfe90c65…` (base branch exists) |
| `git ls-remote origin refs/pull/121/head` | `bfe90c65…` (predecessor PR head unchanged) |

## Repair build / measurement
| command | result |
|---|---|
| `python3 /tmp/measure_before.py` (frozen R2 worktree) | selected 48, extraction 40, runtime 8, projection 0, immutable false, positive 0, digest `d132c825…` |
| `python3 /tmp/gen_evidence.py` (repair head) | AFTER: receipts/adapter/runtime/projection/immutable/replay/match/positive = 48, real_world 0, privacy true |
| `python3 -m pytest tests/adaptive_relational_runtime/ -q` | `182 passed` (111 inherited R1/R2 + 71 repair) |
| `python3 tools/adaptive_relational_runtime/static_gate.py` | `result: ZERO VIOLATIONS` |

## Publication (write) commands
| command | result |
|---|---|
| `gitops push --dry-run` | would push `repair/adaptive-relational-runtime-r2-positive-routing-r1` → origin |
| `gitops push` | `[new branch] repair/… -> repair/…` (rc 0) |
| `gh pr create --draft --base runtime/…real-object-pilot --head repair/…` | PR **#122** created (OPEN, DRAFT) |
| `git tag -a archive/adaptive-relational-runtime-r2-positive-routing-repair-r1-frozen-head -m "…" <final-repair-head>` | annotated tag created on final repair head |
| `git push origin archive/adaptive-relational-runtime-r2-positive-routing-repair-r1-frozen-head` | tag pushed (rc 0) |
| 1111 evidence branch `agent/adaptive-relational-runtime-r2-positive-routing-repair-r1-20260725` | created in `Arvin-liu/1111`, evidence copied, pushed |

## Decisive artifact pointers (this directory)
- Before/after proof: `BEFORE_AFTER_COMPARISON.json`, `PREDECESSOR_NEGATIVE_RESULT.json`
- Manifest immutability: `MANIFEST_IMMUTABILITY_PROOF.json`, `REAL_OBJECT_SELECTION_MANIFEST.json`
- Source/Observation: `SOURCE_OBSERVATION_VALIDATION.json`
- Adapter protocol: `ADAPTER_PROTOCOL_MATRIX.json`
- Run ledger + 48 receipts: `REAL_OBJECT_RUN_LEDGER_REPAIRED.json`, `receipts/OBJ-*.json`
- Aggregation: `CAPABILITY_COVERAGE_MATRIX_REPAIRED.json`, `FAILURE_ATTRIBUTION_LEDGER_REPAIRED.json`,
  `REPRESENTATION_RESIDUE_REPAIRED.json`, `ROUTING_RESIDUE_REPAIRED.json`,
  `REPLAY_IDEMPOTENCY_REPORT_REPAIRED.json`, `FALSE_CONSENSUS_CASES_REPAIRED.json`,
  `ENGINEERING_SIGNALS_REPAIRED.json`, `NO_EVOLVE_JUSTIFICATIONS_REPAIRED.json`
- Audits: `RIGHTS_AND_PRIVACY_AUDIT.md`, `ATTACK_MATRIX_REPAIR_64.md`
- Provenance: `SUBAGENT_LEDGER.json`, `PROPAGATION_CLOSURE.json`, `NONIMPACT_PROOFS.json`,
  `COUNTERS.json`, `REMOTE_IDENTITY_RECEIPT.json`, `FINAL_EXTERNAL_REVIEW_REQUEST.md`
- Repair ADRs: `REPAIR_ADRS.md`

## Counter invariants confirmed
REAL_OBJECTS_SELECTED 48 · REAL_OBJECTS_RUN 48 · POSITIVE_PATH_OBJECTS 48 ·
PROJECTION_EXECUTED 48 · UNEXPECTED_EXTRACTION_FAILURES 0 · UNEXPECTED_RUNTIME_FAILURES 0 ·
REAL_WORLD_ACTIONS 0 · PRIVATE_CONTENT_PUBLICATION_EVENTS 0 · FORMAL_MERGES 0 · MAIN_CHANGES 0 ·
PREDECESSOR_PR_CHANGES 0 · FORCE_PUSHES 0 · HISTORY_REWRITES 0 · EXTERNAL_ACCEPTANCE_CLAIMED 0.
