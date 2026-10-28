# IGNITION-20260828-144 Step 02 — Owner Editorial Authority Contract R1

Step 02 passes with a deliberately small machine boundary in
`data/governance/owner-editorial-authority-r1.json` and its validator. The
contract keeps `DRAFT_GENERATED`, `OWNER_SELECTED` and
`PUBLICATION_ACCEPTED` as separate fields/states. Only
`OWNER_EXPLICIT_PRODUCTION_BRIEF` or `OWNER_EXPLICIT_SELECTION` can supply the
authority required to move beyond the candidate state or accept publication.

Five negative fixtures fail closed for model-ranked topic selection,
auto-cluster book initiation, draft-to-accepted promotion, registry-item
acceptance and fire-seed-score project activation. The validator also checks
all six Task143 smoke outputs against the non-selected/non-accepted defaults.
No runtime adapter, Agent shell, provider SDK or parallel editorial system was
introduced.
