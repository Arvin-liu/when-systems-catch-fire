# Evaluation Evidence Plane R0.1

`EVALUATION_EVIDENCE` is an auditable repository object class. The shared
repository path classifier accounts for it; the shared Knowledge admission
policy retains provenance while excluding it from function and nonfunction
semantic discovery. Nonfunction source-discovery continues to emit explicit
exclusion rows. The self-correction path selector uses this shared admission
policy too, so evaluator reports under `reports/` cannot re-enter its
Knowledge-oriented scan. No new canonical registry or provenance subsystem is
added.

The promotion helper is a pure validator: evidence stays in
`EVALUATION_EVIDENCE` by default. A well-formed, explicitly authorized
transition may create an `ADJUDICATION_CANDIDATE_ONLY` state; this helper has
no filesystem writes and never canonicalizes. Existing Foundation/Knowledge
admission gates still apply after a separate adjudication.

Task180 artifacts remain at their historical Task180 commit. Task181 records
their hashes as a frozen adjudication input and does not amend those artifacts
or claim to have run the evaluator.
