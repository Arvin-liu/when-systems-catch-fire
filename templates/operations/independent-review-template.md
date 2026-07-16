# Ignition Independent Review Template

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
