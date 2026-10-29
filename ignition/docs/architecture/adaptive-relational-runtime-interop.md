# Adaptive Relational Runtime Interoperability / 互操作合同

Status: DRAFT SCAFFOLD (stacked on production/ignition-run-promote-evolve-r1 @ 6723cdfa) — not a Current capability

This document is the **interoperability contract** of the Adaptive Relational Runtime (ARR) R1 scaffold with the existing engines and registries: ARN, MCF, PSD, Function OS candidate, the production RUN/PROMOTE/EVOLVE runtime (`tools/ignition_runtime`), and the project registry / propagation topology. It is a Draft/candidate scaffold contract, not a Current capability. Every mapping here **consumes and references** the predecessors; nothing replaces, broadens or silently rewrites their schemas or semantics.

## 1. ARN interop — mapping without semantic replacement

- Routed relations project into the existing ARN object surface (`schemas/architecture/adaptive-relational-network.schema.json`: typed relations, hyper-relations, temporal activations, unmapped residue) **under ARN's own schema and validators**. The scaffold never writes ARN instances that ARN's own validator would reject, and never introduces relation classes outside ARN's existing vocabulary except the router-controlled `causal_delegated_to_mcf` back-write (§2).
- Relation-envelope → ARN mapping rules (R1–R13) and cue lexicons live in versioned registries (`registries/projection-routes.json`, cue lexicons, anti-overclaim matrix); the mapping is data-driven, not hard-coded.
- Anti-overclaim is enforced twice: at the router pre-gate (bindings B1–B6) and again by ARN's existing validators (causal-proof / centrality / similarity guards). The pre-gate never weakens ARN guards.
- Higher-order relations: members ≥ 3 map to ARN `hyper_relations` with `preserve_as_higher_order: true` and `residue_if_projected`; two-endpoint higher-order relations stay native ARR Relation records and register as `unmapped_residue` (`higher_order_loss`) — a third member is never fabricated. Pairwise projections require `pairwise_projection_allowed`, explicit projection rules, residue and `not_canonical: true`, with the original higher-order record preserved.
- Causal status remains delegated to MCF. No ARN mapping produced by this scaffold asserts causality.

## 2. MCF interop — handoff, never direct writes

- The scaffold never writes MCF fabric. Causal wording or intervention semantics produce a **CausalHandoff record** (`hof_<32hex>`) carrying: `source_relation_ref`, `proposer {agent_session, mechanism_ref, proposed_at_scope}`, verbatim `claim_text`, `trigger {matched_rule, matched_cues, cue_registry_version}`, `higher_order`, `review_questions` (minItems 1, from versioned templates), `proposed_mcf_initial_class ∈ {correlation_only, mechanism_hypothesis, unknown_relation}`, `evidence_refs` (minItems 1), `status`, `status_history`, `resolution`, plus the shared envelope fields with `alternatives` minItems 1 and claim ceiling "handoff is a review request, not a causal finding".
- Handoff state machine (closed, registered in the lifecycle/handoff registry segment):

```
PROPOSED --submit--> UNDER_REVIEW
UNDER_REVIEW --admit(initial_class ∈ {correlation_only, mechanism_hypothesis, unknown_relation},
                     mcf_fabric_ref, review_answers complete)--> ADMITTED_TO_MCF
UNDER_REVIEW --return(reason, retained_arn_class)--> RETURNED_TO_ARN
UNDER_REVIEW --reject(reason ∈ registry)--> REJECTED
PROPOSED --withdraw(scope_ref)--> WITHDRAWN
any non-terminal --supersede(new_handoff_ref)--> SUPERSEDED
```

- `experimentally_identified_causal`, `intervention_supported` and `physical_propagation` are never supplied as handoff initial classes; establishment stays an MCF-internal process.
- Only after ADMITTED_TO_MCF may the router back-write the source relation's ARN projection as `causal_delegated_to_mcf` with `causal_handoff_ref` set; on RETURNED_TO_ARN the relation keeps its non-causal ARN class and the handoff closes. A relation record holds no field that writes handoff status — status transitions are produced solely by the MCF review mechanism.
- A generic relation can never become an established cause by self-declaration: the Relation schema has no `causal_status` field; the only channel is the handoff state machine.

## 3. PSD interop — declared boundaries, no decorative probabilities

- Stochastic-dynamics or risk wording routes to PSD **only** with the complete five-part boundary declaration: (1) `system_context` ten-field set (system_id, boundary_rule, environment, open_closed_hybrid, inputs, outputs, exchanges, nested_systems, observer_frame, purpose_of_model); (2) `state_space` observed/latent variables declared separately; (3) `transition_law.assumptions` six assumptions explicit (markov, stationary, ergodic, linear, gaussian, closed_system); (4) `transition_law.law_type ∈ {deterministic, stochastic, hybrid}` with the deterministic-randomness guard; (5) `probability_semantics` minItems 1 with `semantic_type` in the seven-value vocabulary plus `not_intervention_unless_declared: true`. Any missing part ⇒ REJECT `psd_boundary_incomplete` — never degraded to a bare-probability ARN relation.
- No record in this scaffold carries a bare numeric probability (`probability: 0.8`, `confidence: 0.9`); the schemas do not contain such fields. Any probability claim requires the full ten-field `probability_value` object (value, event_or_variable, conditions, time_scope, system_boundary, source, estimation_method, sample_or_model, uncertainty, claim_ceiling); a missing field ⇒ REJECT, and probability values are never copied into ARN `weight`.
- Observational and interventional distributions stay distinct (`observation_intervention_distinct`); posterior semantics are never claimed as physical randomness without explicit negation.
- A PSD route whose assertions claim real-world intervention validity beyond the declared model boundary must simultaneously produce an MCF handoff (else REJECT `psd_causal_escape_attempt`); a PSD record never self-asserts causality — causal conclusions exist only inside MCF fabric. Receipt ceilings state `intervention_valid_within_model_only: true`.

## 4. Function OS interop — adapter, not executor

The Function OS adapter checks a seven-element contract before any routing (all elements required; missing input contract ⇒ reject):

1. `input_contract` — declared params with controlled type literals; `requires ⊆ params`.
2. `preconditions` — explicit array (possibly empty); expressions reference declared params only, over a controlled operator subset.
3. `executable_surface {kind, target}` — `kind ∈ {function_os_capability, deterministic_stub}` only.
4. `side_effects` — explicit declaration `{declared, real_world: false}`; undeclared side effects ⇒ reject; `real_world` is const `false`.
5. `rollback` — `strategy ∈ {not_applicable_pure, compensating_noop, receipt_only}`; strategies implying real-world writes are forbidden.
6. `output_contract` — `receipt_required` const `true`; every mechanism execution (including stubs) yields a receipt.
7. `claim_ceiling` — from the predecessor epistemic vocabulary (`PRIMARY_VERIFIED / SECONDARY / UNKNOWN`); execution success never raises a ceiling; a mechanism's ceiling never exceeds its weakest input.

Routing law (no third outcome): `function_os_capability` requires the target to hit exactly one **active** capability record in the read-only adapter capability registry (snapshot with per-entry interface hash and overall digest), with format, hash-chain and interface-compatibility checks; `deterministic_stub` requires a hit in the stub registry. Unregistered, inactive, format-invalid or interface-mismatched targets ⇒ reject. The adapter accesses registries only through a read-only `query_capability(capability_id)` contract and never calls registry write interfaces. Inside this R1 scaffold a routed `function_os_capability` terminates in a validated **adapter receipt** declaring which registered capability *should* carry the mechanism — real execution remains the predecessor Function OS's own flow; deterministic stubs emit receipts (`stub: true`, `side_effects_realized: []`, `real_world_action: false`) without real-world action.

## 5. Production runtime interop — read-only receipt adapter

- The scaffold consumes predecessor `operation_receipt` objects through a typed adapter: read → Draft 2020-12 schema validation (13 required fields, `additionalProperties: false`) → identity recomputation → mapping into an execution-receipt adapter record. The adapter reads production stores; it never writes.
- Recomputed invariants (fail-closed on any mismatch): `receipt_id` recomputation per predecessor formula; generation binding (`compute_gen_id` equivalence, dir/manifest/recomputed triple equality); closed-manifest triple equality (required files == digests == actual file set, per-op CANON file sets) with per-file sha256 and manifest self-digest; receipt↔manifest consistency (operation_id, op_type, resolvable parent); the two const gates `self_final_sha_claimed: false` and `live_refetch_required: true`; identical `canonical_json` serialization.
- Mode boundary: `run`/`bootstrap` receipts may be consumed, validated and mapped; `promote_request`/`promote_approval`/`evolve` receipts may be consumed read-only as evidence references. **The scaffold never imports or calls any RUN-write, PROMOTE or EVOLVE path**: import whitelist limited to pure function/data modules (`generation`, `hashutil`, `errors`, `schemas_loader`), directory isolation (no `promote.py`/`evolve.py`/`transaction.py` inside the scaffold package), text-level symbol scanning, and a runtime `sys.modules` assertion. The scaffold CLI exposes no `--authorize` parameter.
- Trust boundary is inherited unchanged: content addressing does not resist an attacker with complete local store write permission; cross-boundary truth rests on external Git commits, remote refetch and evidence anchors.
- Receipt-proven facts are execution facts only: a receipt proves the recorded execution happened; it is never evidence that a domain proposition is true.

## 6. Project registry / topology integration (commit-5 obligation)

- The scaffold registers into `data/operations/project-components.json` as a **horizontal infrastructure/overlay component — not L7** (`layer_or_overlay ∈ {overlay, infrastructure}`; `lifecycle.status: draft_candidate`; `authority: derived`), with `path_patterns` covering every new path prefix introduced by the scaffold.
- `data/operations/change-propagation-topology.json` gains declared relations from the scaffold component to foundation / function_os / arn / mcf / psd / ignition-runtime-related components / iteration / sync, with correct `relation_domain` classification; repository-dependency and synchronization-obligation domains only — no substantive-causal claims.
- The interactive system map, component execution profiles and human front-door surfaces are regenerated/synchronized per the repository-native chain (layout → materialized spec → SVG → front-door validator), with wording everywhere stating Draft/candidate scaffold status.
- **NonImpactProof commitment**: untouched formal cores (Foundation registries, Ψ₀ surfaces, Charter, legacy frozen assets, predecessor PR ancestors #109–#119 and Main) carry an explicit non-impact proof — byte-level or exact-output comparison demonstrating the child branch introduces no change to those surfaces. Inherited validation debt is reported exactly, distinguished from any new residue by exact-output comparison.

## 7. What this contract never does

- Never replaces or widens ARN/MCF/PSD/Function OS/production-runtime schemas or semantics.
- Never lets routing, adjacency, similarity, repetition or graph structure become causality, truth, importance, value or consensus.
- Never performs real-world actions, network calls, PROMOTE or EVOLVE.
- Never claims external acceptance, merge readiness, Main readiness, scientific validity or production deployment readiness.
