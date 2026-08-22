# IGNITION-20260822-134 Step 11 — Current projection closure

Status: `PASS`

Step 10's actionable current failures were deterministic projection drift, not permission to enlarge a residual. The native builders were run in their normal write mode. Function asset census followed by deep adjudication produced `5623` canonical cards; the census and 46-check function closure both passed. Nonfunction claim adjudication produced `16468` canonical claims across `4421` accounted tracked files; its 14-file deterministic check and 54-check evidence-lineage closure both passed.

The current path manifest was regenerated after the Step 11 artifacts were present. It now has `tracked=2992`, `manifest=2992`, `missing=0`, `stale=0`, `unresolved=0`, `category_changed=0` and `anti_backflow=0`.

The regenerated closure was then propagated through the Current chain: `current-facts.json` / `current-facts.md`, `current-snapshot-r1.json`, and all 7 Current Surface compiler outputs were regenerated and passed their deterministic checks. `validate_current_state_sync.py --check` returned `CURRENT_STATE_SYNC_OK`, and the projection hygiene gate returned `DURABILITY_PROJECTION_HYGIENE_OK`.

This exposed and closed a genuine projection cycle: materiality bookkeeping names Current Surface sources, while Current Facts previously hashed the raw materiality file and fed that digest into the Current Surface compiler. The generator now fingerprints the materiality selection/count/policy while excluding only the two reciprocal bookkeeping fields (`machine_record_sha256` and `source_sha256`). A regression test proves that changing those fields does not change the Current Facts input fingerprint, while changing selection still does. After the final audited fingerprint refresh, `CURRENT_FACTS_DETERMINISTIC_OK` and `CURRENT_SNAPSHOT_DETERMINISTIC_OK` still pass.

That downstream regeneration changed the source digest in the seven compiler-owned Current blocks, so the 11 named Human Surface entries were audited again before any fingerprint refresh. All 11 remain `SOURCE_CHANGED_HUMAN_SURFACE_STILL_SEMANTICALLY_VALID`: the six function records changed only source-evidence provenance, the five non-function records changed only evidence line anchors, and no human claim text, disposition, or claim ceiling changed. There were 0 regeneration-required cases, 0 superseded cases, and 0 semantic conflicts. The 11 current source and machine fingerprints were refreshed only after that itemized audit; the Human Surface contract then passed with `48` entries, `94` machine components, `82` visible graph nodes, and `128` typed graph edges.

This step did not rewrite the raw Step 10 full-suite result, add a skip, expand the residual ledger, or claim the full suite is clean. Task identity migration remains a Step 13 obligation. The historical Task104–106 mismatch, default-environment SymPy observation and repository-root cwd fixture errors remain explicitly classified. The five existing residual tuples were not reset or enlarged.

Claim ceiling: repository-local current projection regeneration, closure and path-accounting evidence only; no external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.
