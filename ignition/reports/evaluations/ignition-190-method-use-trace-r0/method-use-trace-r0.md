# Method-Use Trace R0

## Decision

Step01 found that existing R0, Cognitive IR, Transition, provenance, observation,
failure, and self-correction contracts carry the source material but do not
provide a reconstructable, ordered candidate-to-use-to-revision event chain.
This file defines one task-local adapter surface. It is not a Method Registry.

The adapter does not alter or replace any existing authority-bearing schema. It
adds no global relation, no universal method ontology, no second provenance
service, and no parallel lifecycle state machine.

## Required chain

Every valid trace has exactly six ordered segments:

1. `METHOD_CANDIDATE`: candidate method identity and source fingerprint.
2. `SELECTION_RATIONALE`: why the candidate was selected and which alternatives
   were considered.
3. `CONTEXT`: the task/context reference and constraints under which selection
   was made.
4. `METHOD_USE_EVENT`: the bound candidate, input context, expected
   discriminating observation, and order.
5. `OBSERVED_OUTCOME_OR_FAILURE`: observed result or failure, confounders, and
   no-causation-overclaim field.
6. `REVISION_OR_DISPOSITION`: revision/no-revision rationale, disposition,
   target candidate, and optional rollback reference.

Every segment has an exact source reference, a 64-character SHA-256 fingerprint,
an exact locator, uncertainty, and observation-only claim ceiling.

## Validation boundary

The JSON Schema closes the record shape. The accompanying validator checks the
ordered chain, cross-segment links, source fingerprints, uncertainty fields,
confounders, and non-causation ceiling.

Fixed statement:

`METHOD_USE_TRACE_IS_EVIDENCE_ARTIFACT_NOT_CAPABILITY_PROOF`.

A valid trace can support later reconstruction of recorded lineage. It cannot
establish method capability, transfer, general cognitive inheritance, R1,
Model-RSI, weight training, external truth, Owner acceptance, or canonical
promotion.

The schema and validator are research/evaluation preparation artifacts. This
task does not run Successor or Evaluator.
