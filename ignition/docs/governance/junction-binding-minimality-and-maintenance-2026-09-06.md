# Task157 Binding Minimality and Maintenance — 2026-09-06

## Candidate

The candidate is a typed relation over existing tuple dimensions: subject_id, version, scope, and lifecycle_epoch, together with existing claim/action, approval/action, Base/Delta, source/identity/projection/surface, release/admission/provider, and consequence/obligation/owner references. It introduces no authority, truth, capability, or lifecycle state.

Strict equality is insufficient for the controls because an explicitly allowed version migration and surface delay are not defects. Typed compatibility is bounded by the existing transition marker, exact subject/scope/epoch equality, and the explicit delay boundary.

## Ablation

- remove subject_id: 7 holdout defects missed
- remove version: 7 holdout defects missed
- remove scope: 7 holdout defects missed
- remove lifecycle_epoch: 7 holdout defects missed
- remove claim_action_reference: 6 holdout defects missed
- remove approval_action_reference: 10 holdout defects missed
- remove provider_relation: 4 holdout defects missed
- remove consequence_relation: 7 holdout defects missed

These are counterfactual research observations, not a prescription to add fields to canonical schemas.

## Maintenance topology

- Local patchwork registry size: 16 direct predicates and relation sites.
- Junction candidate tuple dimensions: 4; relation groups: 6.
- Distributed drift risk: each local predicate can diverge at its own site.
- Centralized blast radius: a shared candidate can make one semantic error affect all adapters; this is recorded as a residual.

The perturbation ledger keeps both costs visible: duplicated semantic updates in ML and centralized blast radius in MJ.
