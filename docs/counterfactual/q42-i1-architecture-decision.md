# Q42-I1 Architecture Decision — Counterfactual & Unrealized-Path Ledger

Status: stacked Draft candidate. Direct parent is `D2-I1` at the frozen exact head declared in the task receipt.

## Decision

Counterfactuals, alternative decompositions, unrealized paths and speculative narratives can be kept distinct, and only identifiable portions receive bounded counterfactual status.

The contract uses typed evidence bindings and bounded fields. Each material assertion names repository evidence, its digest and the parent exact head. Required rule assertions are deterministic inputs to a fail-closed production CLI; missing, duplicated, unsupported or false assertions block the bundle.

## Core objects

- `counterfactuals`
- `alternative_decompositions`
- `unrealized_paths`
- `speculative_narratives`
- `intervention_differences`
- `identifiability_status`
- `observable_portion`
- `unobservable_portion`
- `evidence`
- `claim_ceiling`

## Fail-closed rules

- `types_separated`
- `identifiability_gate_required`
- `unobservable_not_promoted`
- `evidence_required`
- `intervention_difference_explicit`
- `speculation_labeled`
- `no_if_then_causal_upgrade`
- `claim_ceiling_preserved`

## Explicit non-claims

- if-then story is not causal fact
- unobservable portion remains unobservable
- alternative decomposition is not counterfactual proof
- no external intervention

The pilot is repository-local and self-authored. It performs no real-world external action, does not modify Main, and cannot establish L7, a new truth layer or universal causal truth.
