# IGNITION-128 Step 04 — deterministic rebuild and regression

The current-facts JSON and Markdown projections were rebuilt twice. Their two
passes were byte-identical (`3fd2156c...` and `c2cebc4b...`), and the generator
check passed. The canonical lineage validator, integrated
`CURRENT_STATE_SYNC` validator, 17 scoped tests, four negative fixture classes,
Human visibility, map generation, geometry, map fixtures, Agent Platform Human
Surface, iteration synchronization, generated-output authority structure, and
the changed-path privacy/local-path/secret scan passed.

The unique map remains `0.11.0` with `0.10.0` Historical; no map source file was
changed by Task 128. `CURRENT_WITH_OPEN_OBLIGATIONS` and
`EPISTEMICALLY_ACCEPTED=0` remain unchanged.

Two non-green commands are pre-existing and classified rather than repaired:
the Human Surface contract reports ten source-hash drifts in existing
`docs/human/*/entries` files, none of which is in the Task128 changed path set;
the append-only changelog validator reports historical entry 17 missing
`stale_knowledge`, while the new Task128 entry has all required fields and an
exact baseline SHA. The narrow task explicitly does not rewrite those unrelated
historical/Foundation/Knowledge records.

Machine-readable details are in
`ignition/data/operations/iterations/128/step04-regression-evidence.json`.
