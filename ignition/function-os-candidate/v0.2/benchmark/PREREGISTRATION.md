# Task 105 — Function OS v0.2 Core Capability Benchmark: Preregistration

> Locked instrument + preregistration. This file is committed **before** any
> outcome-bearing run. `run.py` records `prereg_commit()` and asserts
> `ancestry_ok(prereg_commit(), HEAD) == True`, so every result commit must
> descend from the commit that first adds this file (RELAY-PROTOCOL §5.3 / §6.1).

## 0. Binding (frozen references)

| Item | Value |
|------|-------|
| Control commit (`origin/relay/current`) | `d2167c3472e32c0c053c7413c03219cac0389dcc` |
| Task | `relay/tasks/IGNITION-FUNCTION-OS-CORE-CAPABILITY-BENCHMARK-AND-ADVERSARIAL-VALIDATION-R1-20260730.md` + `relay/tasks/105.md` |
| Recovery contract | `relay/tasks/105-REMOTE-CLOSEOUT-RECOVERY.md` |
| Target implementation commit | `16f640045b3dc9d411f015a51e45de07299d31fc` (origin/main, PR #160 merge = task 104 terminal) |
| Execution discipline | Protocol-compliant re-execution from current `main` (recovery Path B/C) |

The 5 locked control files at the control commit are recorded in the task-105
receipt (`01_CONTROL_LOCK.json`). Their SHA-256 was re-verified this session.

## 1. Object of test (bounded only)

Function OS v0.2 candidate reference implementation under
`function-os-candidate/v0.2/` — the bounded symbolic-function pipeline
`N1FunctionSpecParser → N2RepresentationEncoder → N3SymbolicCompiler →
N4ArtifactPackager → N5Interpreter → N6TraceCapture → N7Validator →
N8ComposerRouter → N9RegistryStore/Updater/Validator`.

We test **only the bounded claims the implementation actually makes**. We do
**not** test or imply: universal proof system, complete security sandbox,
mature production platform, or external-truth machine. Honest negative / null
outcomes are valid success outcomes for this task.

## 2. Claim matrix — 7 claims → metric → threshold

Thresholds are frozen in `THRESHOLDS.json` and MUST NOT change after results
are visible (§5.3 / §5.5). "Crit" marks a critical fail-open override that
defeats any aggregate score.

| # | Claim (corpus label) | Formalized bounded claim | Metric | Threshold | Crit |
|---|----------------------|--------------------------|--------|-----------|------|
| A1 | `SUPPORTED_SEMANTIC_FIDELITY` | Over the bounded symbolic domain, FOS-computed value equals the independent oracle value | `semantic_agreement_rate` | ≥ 0.99 | |
| A2 | `CONTRACT_ENFORCEMENT` | Declared pre/postconditions are enforced; a failed execution cannot enter the successful-registry path | `precondition_enforcement_rate`, `postcondition_enforcement_rate` (≥1.0), `registry_contamination_count` (=0) | as listed | |
| A3 | `FAIL_CLOSED_LANGUAGE_BOUNDARY` | A forbidden / unsupported construct is rejected, never silently executed | `false_accept_rate` | ≤ 0.0 | ✔ |
| A4 | `ARTIFACT_AND_TRACE_INTEGRITY` | Mutations to spec / representation / artifact / execution-record / hash are detected by the validation chain | `mutation_detection_rate` | ≥ 1.0 | ✔ |
| A5 | `REGISTRY_REVISION_AND_ROLLBACK_INTEGRITY` | Revisions and rollbacks preserve an auditable, internally consistent history and do not silently rewrite prior states | `revision_history_consistency_rate`, `rollback_restoration_rate` (≥1.0) | as listed | |
| A6 | `BOUNDED_SEQUENTIAL_COMPOSITION` | The actually-implemented N8 sequential-plan behavior preserves declared ordering / inputs / outputs / traceability within stated scope | `sequential_composition_correctness_rate` | ≥ 1.0 | |
| A7 | `FAILURE_PROPAGATION` (within N8 cases) | Missing/erroring functions are propagated as SKIPPED with errors; no silent partial plan | `failure_propagation_correctness_rate` | ≥ 1.0 | |

Cross-cutting: `crash_rate` ≤ 0.0 (no harness/execution crash); `false_reject_rate`
≤ 0.01 (a valid construct must not be wrongly rejected).

Overall verdict is chosen from: `SUPPORTED_WITHIN_BOUNDED_DOMAIN`,
`PARTIALLY_SUPPORTED_WITH_IDENTIFIED_FAILURES`, `NULL_OR_INCONCLUSIVE`,
`CONTRADICTED_WITHIN_BOUNDED_DOMAIN`, `TEST_INVALID_OR_ABORTED`.

## 3. Strata & corpus

Determinism: exhaustive bounded enumeration, seed `20260730`, no case content
depends on RNG. Corpus = 479 cases (authoritative counts in `CORPUS_MANIFEST.json`).

- **S1_reference_semantic (398)** — symbolic expressions over bounded integer
  grids; fidelity compares FOS-computed value to the independent oracle value.
- **S2_boundary_adversarial (62)** — forbidden AST forms, malformed/runtime
  specs, pre/postcondition failures, type/shape boundaries, and mutation/tamper
  cases.
- **S3_stateful_lifecycle (19)** — registry revision/update/rollback/audit
  history, N8 sequential-plan histories, and execution-trace integrity.

Boolean templates (`and`/`or`/`not`) receive the BOOLEAN grid, not the integer
grid, so FOS's correct type-rejection is not mis-scored as a spurious
false-reject.

## 4. Oracle (independent cross-check)

`oracle/reference.py` is an independent re-implementation of the bounded
symbolic semantics. Its `ALLOWED_NODES` mirrors the FOS-permitted AST (no
`ast.Call`, etc.). It computes the expected value for fidelity comparison and
identifies unsupported constructs. The oracle is **not** the FOS code; it is a
separate check, so agreement is meaningful and disagreement is diagnostic.

## 5. Instrument & immutability

Locked in this commit (no later edits to thresholds, seeds, corpus, oracle, or
primary metrics):

- `run.py` (harness), `generate_corpus.py` (generator)
- `oracle/` (independent reference)
- `THRESHOLDS.json`, `CORPUS_MANIFEST.json`, `RESULT_SCHEMA.json`
- `corpus/` (the exact generated inputs)

Post hoc, only clearly-labelled supplementary diagnostics may be added, and they
are excluded from the preregistered verdict (§5.5).

## 6. Classification scheme (honest, methodology-correct)

These are methodology decisions baked into the harness — they govern how cases
are counted, and are not outcome-dependent:

- **Fail-closed boundary (A3).** A forbidden/unsupported construct must not be
  silently executed. If FOS returns `status == OK` but produced **no execution**
  (empty `outputs`, N3 compile-blocked on undeclared symbols), it is classified
  `blocked_not_executed` + `status_signal_defect` — a status-signaling defect,
  **not** a critical fail-open. `critical_fail_open` is reserved for
  `status == OK` **and** actually executed. This separates "rejected-but-
  mislabeled" from "silently executed" and prevents over-counting critical
  violations.
- **Mutation / tamper (A4).** Trace kinds `trace_output_flip`,
  `trace_status_flip`, `trace_input_flip` mutate the recorded trace and must be
  detected by the validation chain; artifact/spec/representation mutations are
  likewise detected.
- **N8 sequential (A6/A7).** Ordering is compared against the **real (mapped)**
  function ids (`req_real`), not symbolic names. Failure propagation requires
  missing functions to be `SKIPPED` with errors (no silent partial plan).
- **Boolean corpus inputs.** Boolean templates use the BOOLEAN grid (see §3).

## 7. Preregistration-before-results (§5.3 / §6.1)

- This is the first commit that adds `benchmark/PREREGISTRATION.md`.
- `run.py` records `prereg_commit()` and asserts
  `ancestry_ok(prereg_commit(), HEAD)`. Every result commit descends from this
  commit.
- The **original-target run** (FOS @ `16f64004`, no repair) is preserved as the
  "before-repair" evidence **before** any FOS defect-repair commit exists.

## 8. Defect-correction discipline (§7 / recovery supplement)

Procedure: **seal original → classify → bounded repair + regression → rerun
exact original + regressions → report original vs repaired separately.**

- Only genuinely identified **implementation** defects are repaired, in a
  separate bounded commit, each with a regression test. The postcondition/
  equality expression parser is a known fragility to scrutinize; any defect found
  there (or elsewhere) is corrected under this discipline, never silently.
- Claim / documentation defects are **reported and corrected in public docs**,
  not patched to make the benchmark pass.
- The original-target and repaired results are reported **separately** so the
  reviewer can see exactly what changed and why.

## 9. Outcome-agnostic success criteria

Task-105 success = protocol-compliant execution + the 18 remote-evidence items
present (per `105-REMOTE-CLOSEOUT-RECOVERY.md`). It is **not** "all claims
pass". A `PARTIALLY_SUPPORTED` or `CONTRADICTED` verdict, with honest preserved
evidence, is a valid completion. No result may promote unrelated Pointfire
claims.

## 10. Reproducibility

- Managed Python 3.13; deterministic corpus; `run.py --replay-from` verifies
  deterministic replay.
- A fresh clean-clone rerun + deterministic verification is required at T11
  (post-merge) and is part of the remote-evidence set.
