# 121Q38-I1 Architecture Decision — Case, Counterexample and Boundary Evidence Retrieval

- Parent checkpoint: `121Q37-I1@927cae48f3c65d3c23543dac4b9262704fabb6f1`
- Trusted Main: `81edff4039619b8343a82cb1b84785c8a9f6a990`
- Branch: `agent/121q38-i1-case-counterexample-boundary-evidence`
- Lifecycle: builder-only stacked Draft candidate; unreviewed, unready, unmerged and not Current.

## Decision

Q38 owns an auditable retrieval process, not a vote over examples. It accepts only a Q37 decision whose `q38_search_permission` is `ALLOWED_AS_RESTRICTED_SEED`, freezes the question, scope, query plan, inclusion/exclusion policy and stop condition before retrieval, and preserves every included support item, counterexample, boundary case, negative result and failed retrieval with provenance, rights, digest, access time, grade, freshness, representativeness and duplicate-family identity.

The new conclusion is limited to repository-native retrieval governance: a bounded search can be replayed and checked for seed authorization, balanced search, rights, provenance, source-family deduplication, freshness, representativeness, selection integrity, negative-result retention, stop-condition integrity and claim ceiling. Case count never establishes mechanism identity or real-world causality.

## Ownership boundaries

- Q37 classifies and audits the analogy and emits the restricted seed. Q38 does not reclassify it or raise its ceiling.
- Q33 remains authority for publication rights. Unknown/pending/rejected rights allow citation-only metadata at most, never publishable body text.
- Q34 supplies the committed claim ceiling; Q35 supplies repository authority; Q36 evidence remains read-only.
- Q38 exports negative and failed retrieval records to Q39. Q38 does not construct the append-only failure lineage.
- External retrieval is optional. The I1 pilot uses traceable repository artifacts and a small bounded metadata-only source set; it does not copy protected long-form content.

## Contract

The typed bundle contains `audited_search_seed`, `search_plan`, `evidence_items`, `selection_log`, `stop_assessment`, `unresolved_evidence_gaps`, `q39_failure_exports`, and read-only Q37/Q33/Q34/Q35 snapshots. Evidence kinds are `SUPPORT`, `COUNTEREXAMPLE`, `BOUNDARY_CASE`, `NEGATIVE_RESULT`, and `FAILED_RETRIEVAL`.

Every source declares a stable source-family key so mirrors, syndication and shared upstream material cannot be counted as independent evidence. `evidence_grade` constrains use but never lets a high-grade support item erase a lower-grade counterexample. `representativeness` is mandatory before any population/domain generalization. Temporal claims require a valid freshness assessment.

## Fail-closed decisions

The validator rejects unaudited seeds, support-only plans, silent negative-result deletion, duplicate-family counting, unknown rights in publishable evidence, stale time-sensitive evidence, missing representativeness, quantity voting, similarity-to-mechanism upgrades, rewritten stop conditions, selective exclusion, unresolved references/digests, and a Q38 ceiling above Q37.

## Legacy disposition

`lab/121q38-structural-retrieval-night@b9dae182da28614f04b0d3c5c124f5ec3b621e9f` is preserved at annotated tag `archive/lab-121q38-structural-retrieval-night`. Its relation-signature, case-structure and counterexample concepts are selectively reimplemented as typed evidence metadata. Its permissive schema, global-data validator, hard-coded Main assertion, absence of rights/freshness/selection/stop controls and non-CLI tests are rejected.

## Claim ceiling and non-claims

`candidate_only: deterministic repository-local evidence-retrieval governance and replay; no case-count voting, no mechanism proof, no universal generalization, no real-world causal identification, no independent review, no external intervention, no L7 or truth layer.`
