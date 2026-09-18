# Task185 Step08 — Inheritance Risk Model

## Scope and severity semantics

This is a research-only, noncanonical risk model anchored to Task181 exact head `7cab7541895620d68d5bce2d16c46871ebd03ac0` and the Task179 R0 package at `12e133c6d58a5e22437e42bb75fd912607bb4540`. It records architecture exposure and what is not measured; it is not a probability estimate, risk score, aggregate total, or ranking. `UNRESOLVED` means the available artifacts do not establish severity or observed frequency.

No Task182-R1 unfinished or historical held-out case-specific payload was read. The Task186 report was not used. No Successor/Evaluator ran; Foundation/Current canonical authority was not modified.

## Risk dispositions

| Risk | Severity | Evidence and existing mitigation | Remaining gap |
| --- | --- | --- | --- |
| `REPRESENTATION_LOCK_IN` | `MEDIUM` | R0 has explicit Cognitive IR, transition, and migration schemas. Complexity entries define consumers, rollback/replay, and retirement conditions; method/kernel claims remain provisional. | No field ablation or independent reconstruction comparison shows which representation fields are necessary or replaceable. |
| `ONTOLOGY_LOCK_IN` | `MEDIUM` | Function identities, nonfunction claim classes, route facets, and R0 method/evolution slots remain distinct. Task185 compared behavior and authority rather than names. | No versioned cross-registry ontology map resolves all recurring object/relation terms or governs future taxonomy migrations. |
| `GOVERNANCE_ACCUMULATION` | `MEDIUM` | R0 budgets schema surface and adds no runtime dependency, persistent authority, or provider binding; retirement conditions are explicit. | Governance overhead is a named independent metric but remains `NOT_YET_MEASURED`; surface counts do not measure ongoing review/coordination cost. |
| `GENERATOR_FANOUT` | `MEDIUM` | Knowledge Experience projections have pinned input/output hashes, deterministic generation, and anti-backflow rules; path accounting fails closed. | No change trace measures downstream regeneration size/time, reviewer effort, or partial/stale projection repair frequency. |
| `CONTEXT_RECONSTRUCTION_COST` | `UNRESOLVED` | Source references, fixtures, unknowns, transition records, and explicit package inputs exist. The R0 evaluation package defines provenance-resolution, inheritance-lag, compression, and migration-cost metrics. | Those metrics remain `NOT_YET_MEASURED`; no clean-context reconstruction cost was measured. |
| `MODEL_SPECIFIC_COUPLING` | `MEDIUM` | Provider/model fields are unbound and rediscovery triggers are specified; R0 rejects model-improvement inference. | No cross-provider behavior comparison establishes that methods or continuation behavior transfer beyond the static schema contract. |
| `HIDDEN_ASSUMPTION` | `MEDIUM` | Capability context assumptions, typed unknowns, provenance, claim ceilings, and route fallback reasons can be retained. | No complete audit shows that all implicit task framing, source selection, defaults, and inherited context are surfaced before they affect outputs. |
| `STALE_SELF_MODEL` | `UNRESOLVED` | The self-model is provisional, lists unknowns, and requires reprobe after specified changes; capability calibration and independent evaluation remain unmeasured. | No time-based expiry or behavioral refresh establishes when the profile becomes stale between declared change triggers. |
| `EVALUATOR_COUPLING` | `MEDIUM` | Blind-first, sealed criteria, separate Builder/Evaluator write surfaces, no Builder verdict, and Task181 evidence-isolation boundaries are specified. | No independent round demonstrates that shared history, output channels, CI, or repository artifacts cannot leak evaluator evidence into Builder claims. |
| `AUTHORITY_AMBIGUITY` | `MEDIUM` | Route index declares `authority_is_index=false`, fingerprints are revalidated, registries carry claim ceilings, and Knowledge Experience/ARN are derived projections. | No consumer contract joins candidate ID, current authority, typed relation, method-use event, and outcome while preserving all authority boundaries. |
| `KNOWLEDGE_SCALE_RETRIEVAL_FAILURE` | `UNRESOLVED` | Route fallback is explicit and bounded; every selected ID is to be checked against authority; Knowledge Experience provides search/alias/coverage projections. | The route snapshot has no topic or four-digit discipline values; precision/recall, missed candidates, alias drift, and relation-aware retrieval have not been benchmarked. |
| `METHOD_HISTORY_LOSS` | `HIGH` | R0 transition/migration contracts preserve anomalies, reframing, disposition, unknowns, lineage, rollback, and retirement; failure memory preserves source lineage. | The sampled surfaces still lack an end-to-end asset → method selection/use → context → outcome/failure → revision relation, so stored inventory cannot establish method-use history. |

`HIGH` here describes the consequence of losing an essential method-history link, not the probability of that loss. None of these qualitative severities is combined into a total or sorted as a global priority.

## Cross-risk reading

The main distinction is between **structural protections that are already specified** (typed unknowns, provenance, versioned transition/migration, explicit role separation, deterministic projections) and **behavioral or cost claims that remain unmeasured** (reconstruction, portability, retrieval quality, governance overhead, and whether a method was actually used or improved). Existing safeguards limit overclaim, but their presence does not prove successful cognitive inheritance.

The strongest specifically evidenced continuity gap is method-use history: Step07 sampled 450 route records with matching authority fingerprints and found dependencies/evidence relations, but no typed `METHOD_USE` relation in the inspected route/registry surfaces. A future authorized read-only reconstruction exercise could test one small set of IDs across registry → relation → method-use record and measure context cost, without running a Successor/Evaluator or promoting claims. Task185 does not implement or execute that experiment.

## Step08 status

Research-only risk disposition for the 12 required categories. No aggregate score, mitigation implementation, canonical change, lifecycle advancement, Successor/Evaluator execution, or authority expansion was performed. Per-risk evidence and residuals are in [inheritance-risk-model.jsonl](./inheritance-risk-model.jsonl).
