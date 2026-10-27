# Pointfire crosswalk against external mechanisms

## Present at Task181

Pointfire already has several mechanisms that resemble parts of external agent architectures while remaining inside an auditable bounded platform:

- **Operational memory:** typed summaries include source run, provenance, visibility, sensitivity, expiry/forget policy, supersession lineage, and integrity digest. The store supports query, redacting forget/expire tombstones, and bounded context capsules. It rejects secrets, prompts, and hidden reasoning and is explicitly not a Knowledge truth registry.
- **Recovery and rollback:** the local action protocol records checkpoints and execution state, supports bounded preimage rollback where defined, and makes ambiguous or non-reversible actions explicit. Supervisor resume preserves episode lineage.
- **Routing:** Profile projection can only narrow authority. Pack-aware routing targets only declared, loaded, profile-allowed capabilities; the Pack Bus returns proposals rather than actions.
- **Evidence governance:** the evaluation plane types evidence artifacts and permits only a separately authorized transition to an adjudication candidate. The claim-admission protocol separates mathematical and external-evidence maturity, requires explicit gates and replication scope, and forbids treating repository inclusion, AI agreement, deterministic generation, or green CI as evidence of truth.
- **Operational bounds:** action/time/output/write/retry budgets, path and capability scopes, and bounded context capsules constrain the existing executor workflow.

These mechanisms are meaningful analogues for accountable memory, routing, and recovery. They are not evidence of general intelligence. The Task181 architecture states `EPISTEMICALLY_ACCEPTED=0` and keeps the system ceiling at `CURRENT_WITH_OPEN_OBLIGATIONS`.

## Partial gaps

The Pack Registry offers bounded, reusable declarative components, but the inspected baseline does not extract skills from experience or measure skill-library growth. The Agent Profile describes allowed capabilities and authority; it is not a calibrated self-model inferred from independent task outcomes. Profile narrowing and memory expiration do not automatically refresh capability beliefs after a model, pack, or evaluator changes.

Operational Memory has explicit forgetting and bounded context export, but the safe source snapshot does not establish semantic deduplication, evidence-based consolidation, or retirement of reusable methods. The evaluation plane supplies typed records and candidate-only transitions; it does not itself run an independent successor evaluator or physically isolate a protected holdout. Existing routing is scoped orchestration, not adaptive scheduling among self-improvement operators.

## Real gaps and governance conflicts

The reviewed Task181 sources do not contain an experience-to-method pipeline, a revision procedure for the method that proposes or evaluates changes, or measured cross-model cognitive-method transfer. Provider-neutral interfaces and executor substitution describe compatibility boundaries, not behavioral inheritance.

A future Data-RSI mechanism would need a separate, reviewed research protocol and could not write canonical claims as though generated data were accepted evidence. Model-RSI or weight mutation conflicts with this task's explicit prohibition and is absent from the bounded platform sources. Automatic promotion from an evaluator result to canonical truth conflicts with the evaluation contract, which sets automatic promotion to false and stops at `ADJUDICATION_CANDIDATE_ONLY`.

## Boundary

This crosswalk was derived only from safe architecture/runtime documentation and the Task181 evaluation/claim contracts pinned at `7cab7541895620d68d5bce2d16c46871ebd03ac0`. No held-out payload, evaluator answer, successor output, or Task182 R1 unfinished output was used. The sources establish a Pointfire baseline and research gaps; they do not authorize integration or implementation of those gaps. Detailed status labels and locators are in `pointfire-external-crosswalk.jsonl`.
