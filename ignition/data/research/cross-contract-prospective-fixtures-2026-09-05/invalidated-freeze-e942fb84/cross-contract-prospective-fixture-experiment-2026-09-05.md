# Task156 prospective cross-contract fixture experiment — 2026-09-05

Status: `SYNTHETIC_FIXTURE_RESULT / BINDING_CHALLENGER_SUPPORTED_AS_RESEARCH_INVARIANT_CANDIDATE / RESEARCH_ONLY / NON_CURRENT`

## Observation

The exact Task156 command freezes a prospective synthetic-but-repository-shaped corpus before blinded scoring. The corpus has **48 paired fixtures / 96 instances** across F1–F6, with pair members kept in one deterministic split. Source contracts are referenced from the Task155 candidate head `9bed8e42ee824fc0c0a10717b6163fe7052423e8`. No live external effect, authenticated provider action, production validator, runtime, authority or lifecycle change was used.

Frozen model definitions are M0 `EXISTING_ONLY`, M3 `THREE_EDGE_V1`, M3R `THREE_EDGE_REFINED`, and M4B `THREE_EDGE_PLUS_BINDING_CHALLENGER`. M3R's refinement remains on the claim edge; M4B uses existing object/version/scope/lifecycle/reference fields and introduces no new authority or truth state.

## Synthetic fixture result

| Family | Defect instances | M0 sensitivity | M3 sensitivity | M3R sensitivity | M4B sensitivity |
|---|---:|---:|---:|---:|---:|
| F1 | 8 | 0.375 | 1.0 | 1.0 | 1.0 |
| F2 | 8 | 0.25 | 0.875 | 0.875 | 1.0 |
| F3 | 8 | 0.0 | 0.0 | 0.5 | 1.0 |
| F4 | 8 | 0.5 | 0.75 | 0.75 | 1.0 |
| F5 | 8 | 0.375 | 1.0 | 1.0 | 1.0 |
| F6 | 6 | 0.166667 | 0.5 | 0.5 | 1.0 |

Holdout M3 incremental defects beyond M0: **6**. M3R incremental defects beyond M0: **8** across `F1, F2, F3, F4, F5, F6`. M4B additional defects beyond M3R: **4**, binding subtypes `approval_action_object, claim_action_object, lifecycle_epoch`. The frozen survival thresholds are evaluated in `data/research/cross-contract-prospective-fixtures-2026-09-05/metrics.json`.

## Inference

The bounded verdict is **`BINDING_CHALLENGER_SUPPORTED_AS_RESEARCH_INVARIANT_CANDIDATE`**. This is a result about the frozen synthetic corpus and deterministic predicates. It is not a real-world prevalence, production accuracy, or Current capability claim. The two scoring passes must be byte-identical; metamorphic violations and ambiguous stress outcomes remain explicit even when the verdict survives.

CC-020-like path/identity/projection defects are testable by M3R without adding a fourth edge when the exact claim-edge binding predicate is sufficient. M4B only earns a research-invariant candidate if its additional holdout detections, subtype diversity and false-positive burden satisfy the pre-frozen table; it is not promoted automatically.

## Proposal

Keep any surviving structure as a replaceable research lens. If the binding challenger survives, the candidate predicate is: existing source, identity, projection, surface, release and admission records must agree on `(object_id, version, scope, lifecycle_epoch)`, while existing action references must equal the claim and approval object identities. This is a cross-family research predicate, not a new canonical contract.

## Non-claim / limitation

- Synthetic percentages are descriptive and cannot estimate real-world prevalence or production accuracy.
- The corpus is prospective and reproducible but authored with repository-history access; it is not cognitive independence or an independent replication.
- Existing local contracts were supplied to M0; detections also made by M0 are redundant, not incremental.
- `answer-key.jsonl` is not a scorer input. Frozen hashes, score-pass identity, split determinism and pair integrity are separate machine checks.
- Stale `1111/instructions/CURRENT.md` and `1111/relay/current` pointers are preserved as preflight residuals and are not modified.

## Diagnostic retirement tests

| Task155 label | Prospective disposition | Reason |
|---|---|---|
| `ABSTENTION_AS_AVOIDANCE` | `INSUFFICIENT_DISCRIMINATION` | No primary defect makes a safe authorized alternative available while the route is merely skipped; safe abstention is retained as a control. |
| `BUDGET_AS_HARM_LICENSE` | `INSUFFICIENT_DISCRIMINATION` | No fixture family operationalizes deadline passage as a harm license; the protocol deliberately does not manufacture support. |
| `COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY` | `SUPPORTED_BY_PROSPECTIVE_FIXTURE` | Prospective consequence/rollback junction pairs produced 10 M3R incremental detections beyond M0. |
| `PROVENANCE_WITHOUT_CEILING` | `SUPPORTED_BY_PROSPECTIVE_FIXTURE` | Prospective claim/admission/binding pairs produced 11 M3R incremental detections beyond M0. |
| `SIGNATURE_WITHOUT_CONTESTABILITY` | `INSUFFICIENT_DISCRIMINATION` | Signer-only stress cases omit a concrete consequence failure; a flag would overread incompleteness as an actionable historical class. |

Machine evidence: [`data/research/cross-contract-prospective-fixtures-2026-09-05/`](../../data/research/cross-contract-prospective-fixtures-2026-09-05/). The formal task report and independent receipt separately record Git/CI/PR evidence.
