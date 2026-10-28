# Junction-invariant candidate assessment — Task156 — 2026-09-05

Status: `RESEARCH_ONLY / BINDING_CHALLENGER_SUPPORTED_AS_RESEARCH_INVARIANT_CANDIDATE / NON_CANONICAL / NON_CURRENT`

## Observation

The frozen challenger comparison is M3R versus M4B. M3R keeps the three original categories and adds only an exact source/identity/projection/public-surface binding predicate on the claim edge. M4B adds a neutral binding/integrity predicate over existing fields and references. Holdout results are M3R `8` incremental detections beyond M0 and M4B `4` additional detections beyond M3R.

## Synthetic fixture result

- Any cross-contract signal threshold: `PASS`.
- Binding challenger threshold: `PASS`.
- M4B additional binding subtypes: `approval_action_object, claim_action_object, lifecycle_epoch`.
- Additional holdout control false positives versus M3R: `0`.

## Inference

CC-020-like failures can be detected without a fourth edge when their observable defect is source/path/identity/projection/public-surface misbinding covered by M3R. The fourth-edge challenger is supported as a bounded research invariant candidate; this wording does not authorize production use.

## Exact candidate predicate

Only if the threshold table is passed, retain this as a research candidate: `source.binding == identity.binding == projection.binding == surface.binding == release.binding == admission.binding` over the existing tuple `(object_id, version, scope, lifecycle_epoch)`, plus `action.claim_id == claim.object_id` and `action.approval_id == authority.approval_id`. No new authority, truth, capability or lifecycle state is imported.

## Non-claim / limitation

The candidate is not a canonical layer, validator, gate, registry, runtime state, Current capability, production readiness or Owner acceptance. Digest-only equality is not sufficient; any future replication must preserve the subtype and actionability rules. Synthetic corpus results do not establish external truth.
