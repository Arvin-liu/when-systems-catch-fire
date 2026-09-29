# IGNITION-20260929-228 — Policy Contract Reconciliation R0

Status: `REFERENCE_INSTRUMENT_SEMANTIC_AUDITS_PENDING`

Task228 is a bounded post-Task227 contract-reconciliation and reference-instrument task. It does not rerun transfer, revision generation, the full chain, R1, cross-model work, Model-RSI, or training.

## Contents

- `evidence-binding-receipt.md` — byte-bound Task227 Owner Packet, frozen source, and PR/CI facts; Task227 results remain historical evidence.
- `validator-failure-taxonomy.json` / `.csv` and `per-policy-validator-audit.md` — exhaustive non-mutating Task227 diagnostic and first-failure cross-check.
- `normative-contract-matrix.json` / `.csv` and `contract-gap-report.md` — contract-layer reconciliation and the A1 Owner/GPT resolution of the three prior questions.
- `normative-policy-contract.md` — prospective Task228 normative contract R1.
- `reference/policy-schema.json`, `tools/validate_policy.py`, `reference/reviewer-rubric.md`, and `reference/instrument-authoring-guide.md` — aligned Task228 machine and review contract.
- `mappings/reference-mapping-declarations.json` — six explicit researcher-authored, target-blind semantic mappings based only on the corresponding family M0 and raw E1.
- `tools/build_reference_instruments.py`, `policies/`, and `build/candidate-build-manifest.json` — deterministic serialization, six machine-valid candidates, and source/mapping/compiler/candidate hashes.
- `tests/` — exhaustive Task227 diagnostic regression plus positive, adversarial, byte-locator, and deterministic-rebuild conformance tests.
- `audit/` — two independent read-only semantic audit sheets, to be added after each auditor returns.
- `runtime-report.md` — complete gate results, exact formal branch/head/PR facts, and claim ceiling, to be finalized before publication.

## Current gates

- Task227 source packet and frozen input binding: complete; no Task227 artifact was edited.
- Task228 candidate contract/schema/validator/rubric/guide and conformance tests: complete; no substantive result-driven weakening was introduced.
- Candidate instrument count: 6 (two per family).
- Task228 validator: 6/6 pass; positive/adversarial conformance: 4/4; Task227 diagnostic regression: 3/3.
- Compiler rebuild: byte-identical; build manifest records zero target access and no experiment run.
- Two independent semantic audits: pending. Instrument readiness and formal Draft PR are not declared until both audits pass all six candidates.

## Claim ceiling

This subtree may establish why the historical human and machine review layers diverged; whether the Task228 contract layers can be aligned without result-driven scientific relaxation; and, only if both independent audits pass, whether six target-blind reference instrument candidates are machine-valid, semantically audited, and reproducibly rebuilt.

It does not establish transfer, revision generation, Cognitive Evolution, general inheritance, causal method effect, cross-model transfer, R1, Model-RSI, or training benefit. Transfer remains untested until a separately preregistered later task.
