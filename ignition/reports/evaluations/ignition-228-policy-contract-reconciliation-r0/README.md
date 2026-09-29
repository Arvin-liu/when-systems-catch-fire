# IGNITION-20260929-228 — Policy Contract Reconciliation R0

Status: `REFERENCE_INSTRUMENTS_AUDITED_READY_DRAFT_PR_OPEN`

Task228 is a bounded post-Task227 contract-reconciliation and reference-instrument task. Phases 01–06 are complete. Phase 07 packaging and Draft PR publication follow after this report commit. The relay receipt records the final PR URL/state, exact Formal head, and exact-head CI proof.

It does not rerun transfer, revision generation, the full chain, R1, cross-model work, Model-RSI, or training.

## Contents

- `evidence-binding-receipt.md` — byte-bound Task227 Owner Packet, frozen source, and PR/CI facts; Task227 results remain historical evidence.
- `validator-failure-taxonomy.json` / `.csv` and `per-policy-validator-audit.md` — exhaustive non-mutating Task227 diagnostic and first-failure cross-check.
- `normative-contract-matrix.json` / `.csv` and `contract-gap-report.md` — contract-layer reconciliation and the A1 Owner/GPT resolution of the three prior questions.
- `normative-policy-contract.md` — prospective Task228 normative contract R1.
- `reference/policy-schema.json`, `tools/validate_policy.py`, `reference/reviewer-rubric.md`, and `reference/instrument-authoring-guide.md` — aligned Task228 machine and review contract.
- `mappings/reference-mapping-declarations.json` — six explicit researcher-authored, target-blind semantic mappings based only on the corresponding family M0 and raw E1.
- `tools/build_reference_instruments.py`, `policies/`, and `build/candidate-build-manifest.json` — deterministic serialization, six machine-valid candidates, and source/mapping/compiler/candidate hashes.
- `tests/` — exhaustive Task227 diagnostic regression plus positive, adversarial, byte-locator, and deterministic-rebuild conformance tests.
- `audit/round-1/` and `audit/round-2/` — separate raw independent audit sheets. `audit/round-2/package-manifest.json` records the identical read-only input file hashes supplied in separate copies.
- `runtime-report.md` — gate results and final branch/PR/CI references; terminal exact-head facts are pinned in the 1111 relay receipt.

## Current gates

- Task227 source packet and frozen input binding: complete; no Task227 artifact was edited.
- Task228 contract, schema, validator, rubric, authoring guide, and conformance tests: aligned; no substantive result-driven weakening was introduced.
- Candidate instruments: 6 (two per family); Task228 validator passes 6/6.
- Positive/adversarial conformance: 4/4; Task227 diagnostic regression: 3/3.
- Compiler rebuild: byte-identical; source, mapping, compiler, and candidate hashes are recorded. No target access or experiment run.
- Audit round 1: raw disagreement preserved. Auditor A passed all six; Auditor B identified nested report evidence not included in the parent action evidence for F02_A and F02_B.
- Audit round 2: both independent auditors passed all six candidates across the 15 machine predicates and nine semantic dimensions. The first-round sheets remain unchanged as history; no third auditor or audit reconciliation was used.
- Phase 07: Draft PR #238 is OPEN + DRAFT + UNMERGED against the exact Task227 head branch. A publication-metadata update follows PR creation; the terminal relay receipt records the final head SHA and applicable exact-head CI conclusions.

## Claim ceiling

This subtree establishes why the historical human and machine review layers diverged; that the Task228 contract layers were aligned without result-driven scientific relaxation; and that six target-blind reference instrument candidates are machine-valid, independently semantically audited, and reproducibly rebuilt.

It does not establish transfer, revision generation, Cognitive Evolution, general inheritance, causal method effect, cross-model transfer, R1, Model-RSI, or training benefit. Transfer remains untested until a separately preregistered later task.
