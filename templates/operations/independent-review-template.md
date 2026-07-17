# Ignition Independent Review Template

Current method contract: `ITERATION.md` 1.1.0. Method 1.2.0 typed propagation remains Draft until independently accepted and merged.

Review target:

- Repository:
- PR:
- Exact HEAD:
- Base:

Review inputs:

- Artifact:
- Claim:
- Evidence:
- Mechanism or operation map:
- Failure conditions:

Checks:

- Exact HEAD matches the reported candidate.
- Candidate / accepted / merged / current states are not inflated.
- Claim ceiling is explicit and respected.
- Impact matrix covers README, current state, AI handoff, schemas, tools, tests, CI, reports and frozen surfaces.
- Registry-derived propagation closure covers every applicable human, AI/Agent, machine, version/history and deployment surface.
- For a 1.2 candidate, component seeds resolve through declared typed paths to a deterministic fixpoint, every required component has a decision, and the closure hash recomputes exactly.
- Relation domains preserve authority separation; no Git diff, dependency, traversal or map edge is treated as substantive causal proof.
- System-map impact matches a registry-derived projection and delta; hidden new components have a machine-verified representation/no-change reason.
- Implementation completion is separated from repository, external and whole-project synchronization completion.
- Every no-change decision includes evidence; green CI alone does not close propagation.
- Draft Pages evidence comes from the exact-head build artifact, not an unmerged production deployment.
- Pre-merge acceptance checks only surfaces that block `accepted`; post-merge-only Pages must still block `current` and `closed` until individually attested.
- Repository-local validator PASS is limited to artifact consistency and does not claim live GitHub truth.
- Exact HEAD and both required CI runs are recorded in the PR body and independent receipt.
- PR state, exact HEAD and CI conclusions were freshly re-fetched from GitHub before this decision.
- Strongest alternative failure mode was tested or preserved as residue.
- No forbidden surface was modified.

Decision:

- Accepted:
- Accepted with hygiene patch:
- Blocked:

Reason:

- Evidence supporting decision:
- Remaining limitations:
