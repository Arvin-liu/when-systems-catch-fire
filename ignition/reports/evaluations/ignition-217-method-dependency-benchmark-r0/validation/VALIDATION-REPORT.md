# IGNITION-20260925-217 R1 — Validation Report

This report supersedes the R0 preparation report for current scoring and packet definitions. R0 files, commits, and the initial local-validator pass remain preserved as reviewed-and-superseded history. R1 remains preparation-only and is not authorized for launch.

## Owner review and exact starting state

At the required starting head `29ae2b3f507a988d34362821ed7f8a0060a566e8`, PR #234 was Open + Draft + unmerged on `work/IGNITION-20260925-217-method-dependency-benchmark-r0`, based on `24198effb2e2d94c19fe212244bbfcf47f995b2a`. Foundation validation run `36127648408` completed with failure, not pending: `discovery:every-repository-path-accounted listed=6644 tracked=6738` and `generator:deterministic NONFUNCTION_CLAIM_OUTPUT_DRIFT`. The generated projections named by that failure were source-discovery, closure-summary, discovery-coverage, and the nonfunction-claim adjudication index.

The initial freeze remains recorded as locally valid but rejected for launch because the primary endpoint was circular, retained atoms leaked target actions, and Foundation discovery had drift. No successor or evaluator output existed before repair. Three fresh read-only reviewers completed endpoint, leakage, and ambiguity proposals in parallel; their frozen reports are under `design/r1-independent-reviews/`.

## R1 endpoint and case controls

The primary endpoint is `TARGET_DECISION_SUCCESS`, a condition-neutral binary score in FACTS_ONLY, SKILL_ONLY, METHOD, and LINKLESS_METHOD_CONTROL. It scores the externally visible decision, boundary/precondition, required observation or stop condition, overclaims, and critical errors. It requires neither a source locator nor a METHOD relation locator. `METHOD_TRACE_USE_SUCCESS` is secondary and descriptive; the four 0–2 domains remain secondary descriptive measures.

All six synthetic case families have byte-identical METHOD and LINKLESS atom blocks. Each METHOD record contains five structured relations. LINKLESS removes exactly the sealed decision-bearing relation set: one relation in CASE01, CASE02, CASE03, CASE05, and CASE06; R01 and R04 in CASE04, where measurement selection and threshold interpretation are separate decision-bearing relations. Every LINKLESS case has two materially different licensed alternatives checked against facts, atoms, and retained relations, plus a human review row. The review records no target leakage from FACTS, SKILL, or LINKLESS atoms and demonstrates two-way ambiguity in all six cases.

## Frozen future packets

The R2 target, criteria, and preregistered outcome rule were frozen before any outputs. Matched outcomes use M/L/F/S = METHOD/LINKLESS/FACTS/SKILL `TARGET_DECISION_SUCCESS`:

- `METHOD_LINKLESS_WIN = M and not L`
- `METHOD_CONTRAST_SUCCESS = M and not L and (not F or not S)`
- `FAMILY_DEPENDENCY_REPLICATED = METHOD_CONTRAST_SUCCESS in >=2 of 3 replicates`

The design contains six families, four conditions, three replicates per condition, and twelve opaque future task IDs. All twelve manifests point to the same byte-identical neutral prompt, preserve matched order within each replicate, and expose exactly the prompt, assigned payload, and output schema. No manifest or payload contains a condition label. The condition map remains sealed and unreleased. Task217 selected no runtime.

The Task217 output schema remains byte-identical to the Task207 schema at `ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/packets/PKT-B6092E/output-schema.json` (SHA-256 `fdf46bbe7f92dbc5a8340ad95381a0932b5b55f49f3c88f48f33c502a52c0133`). The neutral prompt SHA-256 remains `4b5dc76b563aa6f45a9c3fa5ee155bc20fc8a82902da2a7a77d4dcc859d7a913`.

## Repository closure

The Task217 validator now has hard gates for the condition-neutral endpoint, exact atom identity and relation cuts, target-bearing atom phrases, ambiguity proofs, identical prompts, hidden manifest labels, and zero Successor/Evaluator outputs. It also verifies the sealed map, R2 target/outcome definitions, Task207 schema parity, generated path-index coverage, clean worktree, and freeze inventory/sidecar.

Repository path accounting passed 10/10. The prescribed generator refreshed only `ignition/data/foundation/repository-path-classification/classification-manifest.jsonl`, accounting for all 111 tracked Task217 paths under the existing EVALUATION_EVIDENCE rule. Nonfunction generation changed exactly four generator-owned projections: `source-discovery.jsonl` added 111 new tracked paths; `closure-summary.json` and `discovery-coverage.json` moved tracked/excluded-evidence counts from 6644/608 to 6755/719; `nonfunction-claim-adjudication-index.md` refreshed the tracked-file total from 6644 to 6755. The nonfunction claim registry remains 18003 records and its dispositions were not promoted. `adjudicate_nonfunction_claims.py --check` passed deterministic generation across 14 files; `validate_nonfunction_claim_closure.py` passed 54/54; `validate_foundation.py` passed 63/63 locally. No generator-owned file was edited by hand. The classification rules/schema and frozen Task207 subtree remain unchanged. Exact-head GitHub workflows are checked against the final pushed commit.

The first final-head Foundation workflow (`36146123903`, head `7fe8e2a5f53f7080b3c1a3f143c1e388a62fc003`) reached the human-results gate and found `HUMAN_RESULT_OUTPUT_DRIFT`. The configured human-results generator scans Markdown under `reports/`; all 80 newly indexed source documents are under the Task217 evaluation subtree. Running `python3 tools/governance/build_human_results.py` regenerated only these generator-owned navigation projections: `ignition/data/governance/human-results/result-ledger.jsonl`, `ignition/data/governance/human-results/census.json`, and `ignition/RESULTS/CHRONOLOGY.md`. The result ledger now has 757 source records; its configured claim ceiling remains navigation-only. These projections add no scientific adjudication or lifecycle promotion, and their exact paths and hashes are recorded in the freeze manifest.

## Final state

```text
PRIMARY_ENDPOINT=TARGET_DECISION_SUCCESS
PRIMARY_ENDPOINT_CONDITION_NEUTRAL=true
METHOD_RELATION_CITATION_REQUIRED_FOR_PRIMARY=false
METHOD_LINKLESS_ATOMS_BYTE_IDENTICAL_PER_CASE=true
LINKLESS_TWO_WAY_AMBIGUITY_PROVEN=6/6
CASE_FAMILIES=6
CONDITIONS=4
FUTURE_SUCCESSORS=12
SUCCESSORS_LAUNCHED=0
EVALUATORS_LAUNCHED=0
CONDITION_MAP_RELEASED=false
RUNTIME_CHOSEN_BY_TASK=false
REPOSITORY_PATH_ACCOUNTING=PASS
FOUNDATION_VALIDATION=PASS
R1_NOT_AUTHORIZED
CROSS_MODEL_NOT_AUTHORIZED
PR_STATE=OPEN_DRAFT_UNMERGED
```
