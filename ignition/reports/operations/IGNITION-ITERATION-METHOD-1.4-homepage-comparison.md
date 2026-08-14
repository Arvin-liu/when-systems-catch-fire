# Current Main vs 1.4 Candidate Homepage Comparison

Task: `IGNITION-ITERATION-METHOD-1.4-CONTINUOUS-STAGE-SNAPSHOT-PUBLICATION-R1-20260726`

Baseline: formal `main` at `81edff4039619b8343a82cb1b84785c8a9f6a990`.

Candidate status: Draft only; exact final HEAD and CI belong in the PR body and 1111 receipt after the commit exists.

| Surface | Baseline Main | 1.4 Candidate exact-branch projection | Capability effect |
| --- | --- | --- | --- |
| README / Pages homepage | Current capability narrative and writing showcase; no structured recent-stage section | Adds registry-derived `正在炼化 / Recent Stage Results` with source PR, branch, exact HEAD, evidence, blockers and five explicit booleans | None |
| Method status | 1.3.0 Current | 1.3.0 remains Current; 1.4.0 explicitly Candidate | None until independent acceptance, merge and closeout |
| R5-A visibility | Not shown on formal Main homepage | `PR_VISIBLE / IMPLEMENTED_PENDING_REVIEW`; PR #130 OPEN/DRAFT; all capability booleans false | R5-A payload remains outside Main and unavailable |
| Registry authority | No stage snapshot registry | `data/operations/stage-snapshots.json` is the single snapshot authority | Does not modify the formal capability registry |
| Pages deploy | Main push only | Candidate workflow_dispatch can build an artifact; deploy remains Main push only | No candidate production deployment |
| Failure handling | No stage-specific gate | Schema, semantic, identity/HEAD, privacy, responsibility, succession and byte-identical projection checks fail closed | Green CI totals cannot hide an individual failed instance |

The comparison is repository-local. It does not claim that the candidate is live on production Pages. A future exact-head acceptance task must inspect the candidate artifact; a post-merge task must independently verify the Main deployment before marking the snapshot `PUBLISHED_SNAPSHOT`.
