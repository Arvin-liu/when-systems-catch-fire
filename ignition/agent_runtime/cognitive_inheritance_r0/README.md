# Cognitive Inheritance & Evolution Architecture R0

Status: `READY_FOR_INDEPENDENT_EVALUATION` is the only permitted final
status for this package.  This directory is a repository-local candidate
substrate, not a new Foundation authority, Current capability, truth layer,
or claim registry.

## Scope and ceiling

This R0 package records observable, auditable cognitive artifacts.  It does
not request, store, or reconstruct hidden chain-of-thought.  A passing schema
validator or a structured package is implementation conformance only; it is
not cognitive inheritance success, model improvement, external validity,
Owner acceptance, or epistemic acceptance.

The package starts from the frozen `PRE_CAPABILITY_INHERITANCE_BASELINE`:

- Formal repository: `Arvin-liu/when-systems-catch-fire`
- exact base/head: `68565f2afb50989d2c2b0d346d774e3388702743`
- baseline PR: `#218`, `OPEN + DRAFT + unmerged`
- new branch: `work/IGNITION-20260916-179-cognitive-inheritance-evolution-r0`
- PR relationship: stacked Draft PR, base temporarily set to
  `work/IGNITION-20260912-172-knowledge-routing-universal-corpus`
- command authority: `Arvin-liu/1111@main`,
  `agent-commands/IGNITION-20260916-179.md`

The R0 package never retargets to `main`, merges #218, changes #218's branch,
marks any PR Ready, auto-merges, rebases, amends, squashes, force-pushes, or
claims that a Builder independently evaluated its own inheritance.

## Step00 architecture crosswalk

The machine-readable crosswalk is in `step00-architecture-crosswalk.json`.
The classification vocabulary is intentionally closed:

- `ALREADY_PRESENT`
- `PARTIAL_GAP`
- `REAL_GAP`
- `NOT_APPLICABLE`
- `CONFLICTS_WITH_GOVERNANCE`
- `RESEARCH_ONLY`

The current architecture already provides repository identity, task/lifecycle
state, capability and permission boundaries, external-executor routing,
checkpoint/resume, handoff, provenance, generated-output authority,
fixed-point propagation, Current/Knowledge projections, Foundation claim
ceilings, and mechanical validators.  R0 therefore adds only a bounded
namespace for typed cognitive artifacts and their migration/evaluation
contracts.  It does not duplicate those authorities.

## R0 planes

The seven planes are a working hypothesis, not a permanent ontology:

1. External Intelligence Plane — replaceable models and Agents.
2. Capability Interface Plane — observable, provider-neutral contracts.
3. Harness / Orchestration Plane — task decomposition, routing, tools,
   Skills, context and bounded parallelism.
4. Structured Cognitive Substrate — typed objects, relations, evidence,
   boundaries, history, obligations and lineage.
5. Output Structuralization / Compiler Plane — converts observable output
   into typed artifacts; it does not create evidence or truth.
6. Independent Evaluation Plane — freezes acceptance rules outside the
   Builder write surface.
7. Evolution Plane — proposes reinterpretation, replacement, coexistence,
   rollback or retirement while preserving migration lineage.

## CURRENT_SELF_MODEL_R0

`CURRENT_SELF_MODEL_R0` is an explicitly provisional self-model.  It is not
the essence of Ignition and does not claim that the repository has acquired a
new cognitive capability.

### Representation / phenotype

Files, JSON/JSONL, schemas, Python validators, Agents, prompts, Skills,
workflows, taxonomies, routing overlays, Git commits and external provider
bindings are replaceable carriers.  Their existence is not itself a method,
capability, evidence, or truth.

### Cognitive method

R0 makes the following observable method slots explicit: frame the object;
decompose the task; retrieve by provenance; separate observation, evidence,
analogy and hypothesis; preserve uncertainty; expose counterexamples and
boundaries; select an action; and record evaluation/revision.  These slots
are descriptions of artifacts, not hidden reasoning traces.

### Cognitive evolution

R0 records anomaly/failure, reframing, alternative model proposal,
independent evaluation, adopt/reject/coexist/unresolved disposition,
migration lineage, rollback and retirement.  A code diff without an
observable transition record is not treated as cognitive evolution.

## Existing authority boundaries

The R0 namespace is platform provenance.  It must remain separate from:

- Foundation function/nonfunction canonical registries and their M/E,
  evidence, proof, disposition and claim-ceiling fields;
- Current identity/facts/snapshot and the formal task lifecycle;
- Knowledge Experience, Human Results, Fire Seeds and generated public
  projections;
- executor/provider identity, permission, Owner authority and external
  validity.

The two real fixtures intentionally point back to existing Task172 records
instead of copying book text or rewriting canonical rows.

## Contents

- `schema/` — versioned IR, transition, evaluator, capability, complexity and
  migration contracts.
- `fixtures/` — two provenance-bound real fixtures and the R0a→R0b migration
  fixture.
- `packages/` — frozen evaluator and successor handoff packages.
- `src/contracts.py` — deterministic, stdlib-only record and migration helper.
- `step00-architecture-crosswalk.json` — baseline adoption and minimum gap
  list.
- `external-source-provenance.json` — primary MetaRSI paper and pinned
  RSI-Harness repository provenance, with local analogy kept separate.

## Final handoff rule

The Builder may run mechanical tests and produce this package.  Only a later,
independent Evaluator conversation may judge reconstruction fidelity,
continuation correctness, or cognitive improvement.  Until then the package
remains `READY_FOR_INDEPENDENT_EVALUATION` with unresolved/unknown items
visible.
