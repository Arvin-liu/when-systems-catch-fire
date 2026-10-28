# Q37-I1 Architecture Decision — Analogy Audit, Mechanism Boundary & Transportability Gate

- task_id: `121Q37-I1`
- executor (this build): **WorkBuddy acting as Fallback Builder** (Kimi-K3 Max unavailable per user-confirmed `Fallback Builder 全量构建`); role `BUILDER_ONLY`
- parent checkpoint: `121Q36-INT-I1@02a87221b86cf39217f8c6b3c63e0737a0e2de98`
- target branch: `agent/121q37-i1-analogy-audit-transportability`
- trusted Main base: `81edff4039619b8343a82cb1b84785c8a9f6a990`

## 1. What Q37 actually audits

Q37 audits **the mapping itself**, not the real world:

- **type of the mapping** — surface similarity / metaphor / structural analogy / mechanism candidate / transportability candidate / counteranalogy / insufficiently specified;
- **what is preserved** — explicit correspondence pairs, relation preservation, invariants, directionality, cardinality and its legal rationale;
- **what is lost** — known mismatches, omitted variables, hidden premises, scale/time/context differences, representation-level gaps;
- **whether it may migrate within a bounded scope** — transportability assessment with declared invariances, shifts, overlap, boundary conditions, uncertainty and falsifiers;
- **what it may NOT become** — mechanism identity, universal law, or proven real-world causal transport.

Q37 does **not** prove that any two domains share a mechanism, does **not** prove real-world causal transportability, and does **not** perform Q38 case retrieval.

## 2. Boundary between Q37 and Q38 / Q39

| Concern | Owner |
| --- | --- |
| Classify mapping, expose mismatches/shifts, downgrade claim ceiling, gate transportability | **Q37** |
| Retrieve external cases / counterexamples using *audited restricted seeds* | **Q38** (not started here) |
| Record failed mappings / negative evidence into failure memory | **Q39** (interface only, not started) |

Q37 may emit `q38_search_permission = ALLOWED_AS_RESTRICTED_SEED`, but that only means "the analogy may enter Q38 as a *restricted* retrieval seed." It does **not** assert the analogy is true or the mechanism holds. Q37 must not perform large-scale external case collection.

## 3. Non-negotiable distinctions (fail-closed)

- `STRUCTURAL_ANALOGY` ≠ `MECHANISM_EQUIVALENCE`.
- `MECHANISM_CANDIDATE` stays a candidate **unless** there is independent mechanism evidence (`INDEPENDENT_MECHANISM_EVIDENCE` / `INTERVENTION_RESPONSE_EVIDENCE` with an external ref).
- Shared vocabulary, shared mathematical form, correlation, or similar shape are **not** independent mechanism evidence.
- `TRANSPORTABILITY_CANDIDATE` must state assumptions, scope, shifts and failure conditions; empty overlap / invariances / boundary / falsifier ⇒ `NOT_TRANSPORTABLE` or fail closed.
- A Q36-OBS residual / anomaly may trigger an analogy candidate or a counteranalogy search, but it **cannot** prove a shared cause.
- Repo-internal mapping consistency ≠ real mechanism, real causality, or universal law.
- `MECHANISM_EQUIVALENCE_PROVEN` and `UNIVERSAL_LAW_PROVEN` are **deliberately absent** from the `candidate_type` enum; any attempt to assert them fails closed.

## 4. Contract shape (mirrors Q36-INT)

`analogy-audit-contract.schema.json` (draft 2020-12, `additionalProperties:false`) expresses five parts:

1. `analogy_candidates` — source/target domain+definition, proposer, Q35 authority ref, originating Q34 claim ref, purpose, `candidate_type`, evidence refs, provenance, `claim_ceiling`, lifecycle, `exact_head`.
2. `mappings` — correspondence pairs (with quality), relation preservation, directionality, cardinality + rationale, invariants, `known_mismatches`, `omitted_variables`, `hidden_premises`, `scale_time_context_differences`, representation level, `mapping_digest`.
3. `mechanism_evidence` — `evidence_kind`, `status`, prohibited promotions, no self-circular evidence.
4. `transportability_assessments` — populations, required invariances, covariate/concept/mechanism/scale-time-regime shifts, support overlap, boundary conditions, excluded scopes, uncertainty, falsification conditions, `status`.
5. `audit_decisions` — classification, mapping consistency, mechanism-evidence sufficiency, transportability status, counteranalogy status, Q38 search permission, allowed use, forbidden inference, downgraded claim ceiling, unresolved issues, verifier, `exact_head`.

Embedded **read-only** snapshots (copied, never modified): `q34_claims`, `q35_grants`, `q36_obs_snapshots`, `q36_int_snapshots`, `q33_rights`.

## 5. Reuse of Q34–Q36 contracts

- **Q34** `ANALOGY_AS_MECHANISM` fail-closed rule, claim state, claim ceiling, evidence binding → `candidate_type`, `claim_ceiling`, `originating_q34_claim_ref`.
- **Q35** actor / grant / action trajectory → `q35_authority_ref`, `q35_grants`.
- **Q36-OBS** observation / prediction / residual / uncertainty / scope → `q36_obs_snapshots` (read-only signal; `do_not_infer_cause`).
- **Q36-INT** mechanism hypothesis / intervention outcome / failure / rollback / `do_not_infer_cause` → `q36_int_snapshots` (read-only; `do_not_upgrade_to_universal`).
- **Q33** source-rights / publication gate → `q33_rights` (never bypassed).
- Cross-cutting: L0–L6, F08 migration/cross-domain, isomorphism judgment, typed change propagation, `exact_head`, provenance, attestation, manifest/seal.

## 6. Builder discipline (this execution)

- **Fallback Builder**: Kimi-K3 Max unavailable; WorkBuddy executes the full build under the protocol's Fallback Builder clause. `BUILDER_ONLY`: no independent review, no Ready, no merge of PR #65–#68 / Q37 PR / Main, no rewrite of frozen heads, no Q38/Q39 start, no large-scale external case retrieval, no materialization of F15/D1/D2.
- **Credit reserve**: hard floor 1500; the Agent cannot read the balance — the user monitors it. Each stable phase is committed and pushed immediately; when the visible balance reaches 1500 or lower, execution stops at the next stable remote checkpoint (`Q37_I1_PARTIAL_REMOTE_CHECKPOINT`). No squash / rebase / amend / force-push.
- **Baseline debt**: Q36-INT recorded 8 inherited reds (`era_resolver` ×2, `generated-output-authority` ×3, `production_execution_authority` ×3). These are reproduced, not fixed; Q37 regressions must be green.
- **Legacy salvage**: `lab/121q37-analogy-audit-night` (`178c3b1226`) is preserved via annotated tag `archive/lab-121q37-analogy-audit-night`; only concepts still conforming to Q34–Q36 contracts are re-implemented (see `q37-legacy-lab-salvage-matrix.json`). The lab's schema/validator/test implementations are rejected as under-specified.
