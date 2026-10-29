# IGNITION-20260826-141 Step 16 — Post-publication projection gate repair

The first independent clean preflight against the newly published remote-main
clone did not pass. It reported five deterministic projection failures:
nonfunction claims, Knowledge Experience generation/validation, durability
hygiene and repository path classification. No side effect was detected.

The cause was ordering, not a live or full-suite regression. The
`step16-projection-preflight.json` receipt was created after path-manifest
generation, and the final Step16 progress/result records were added after the
nonfunction and Knowledge projections were generated. The final tracked tree
therefore contained one path absent from the manifest and stale deterministic
projections. The failed observation is preserved in the machine audit; it is
not relabeled as PASS.

The repair regenerates the path manifest only after all formal Step16 records
exist, then rebuilds nonfunction claims, Knowledge Experience, Current Facts,
Current Snapshot, compiler-owned Current surfaces and Fire Seeds before
rerunning the clean preflight. No new live process is authorized or started.

This audit does not self-witness the publication SHA. The exact remote-main
ref, fresh clone HEAD and post-repair gate belong to the independent `1111`
publication witness.
