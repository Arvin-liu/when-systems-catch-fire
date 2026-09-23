# Task207 representation sufficiency audit

Status: `EXPERIMENT_ONLY`; this audit selects input representations and does not claim capability, inheritance, or efficacy.

## Decision

No existing representation cleanly expresses a reusable local skill without also expressing method lineage. Task207 therefore needs one narrow, experiment-only skill artifact schema. Its only consumers are the Task207 artifact validator, the skill-only packet, and the predeclared Task207 evaluator criteria. The schema remains inside this Task207 report subtree and is retired to historical experimental material after the future trials and evaluation are frozen. It will not become a global skill registry.

## Existing representations

- Cognitive IR R0 has `METHOD` but no `SKILL` object type. Reusing `METHOD` would blur the skill-versus-method distinction. Its task-specific package status also makes it an unsuitable new task input contract.
- Method-Use Trace R0 requires six linked segments: candidate, selection, context, use, outcome/failure, and revision/disposition. It is the correct existing method-lineage representation and will be reused unchanged with its existing validator. Task207 provenance and source hashes will be bound in the Task207 manifest, following Task198's reuse pattern.
- The prior Task190 `skill-only-not-applicable.json` records that no skill was supplied; it contains no reusable procedure artifact.
- Pack manifests declare capabilities and dependencies, not a standalone reusable skill representation.
- The existing R0.1 successor output schema remains the common response schema for all future packets and is not modified.

## Chosen representation boundaries

The new skill artifact will contain a local procedure, applicability preconditions, stop conditions, and observable fields to record. It will omit candidate selection rationale, method-use history, validation outcomes, revision lineage, and case answers.

The complete method artifact will use Method-Use Trace R0. Broken excerpts will remain incomplete and must be rejected as complete traces by that same validator. The output format remains the existing R0.1 schema.

No global Cognitive IR enum, global skill registry, second method schema, or R0.1 output-schema change is authorized or planned.

## Retirement condition

After Task207's future successor trials and independent evaluation are frozen and the handoff is complete, retain the skill schema only as Task207 historical experimental material. Another task must perform a fresh sufficiency audit before reusing or extending it.
