# R0.3 Complexity Budget

## Count at the end of Step07

Compared with the stable Task182-R1 starting head, the Task187 branch contains
37 changed paths and 3,456 added lines. The line count includes the required
new successor packet, two synthetic case sources and provenance files, five
Task187 test modules, protocol and control documentation, and synthetic
reproduction and handoff records. It is not a count of new runtime code.

The new R0.3 control surface is:

- Six JSON Schemas: case manifest, packet manifest, successor output, read
  ledger, final-validation receipt, and task-scoped branch authorization.
- One ledger finalization and validation tool:
  `finalize_successor_read_ledger_r0_3.py`.
- One task-scoped authorization guard:
  `task_branch_guard_r0_3.py`.
- Two nine-line hook adapters for commit and push.
- Five new Python test modules and twelve changed Markdown files. The Markdown
  count includes case sources and reports as well as protocol documentation.

Thus there are four executable entrypoints, of which only one implements the
new final-ledger attestation. The guard and hooks enforce the already-required
task authorization boundary; they do not add another ledger validator.

## Duplication and judgment

The R0.3 branch guard is a versioned copy of the 327-line R0.2 guard. Its
authorization and preflight logic is unchanged; the differences are the
version label and the R0.3 authorization-schema and hook paths. This is the
clearest avoidable duplication in the repair.

The 498-line R0.3 finalizer combines semantic ledger checks, frozen-byte
binding, deterministic receipt construction and verification, and guarded
file output. It is one implementation boundary, rather than a collection of
new validators. The version-specific ledger and receipt schemas are needed
because the closure metadata and final attestation are new protocol
requirements.

The branch is broader than the closure fix alone, but most of its files are
required to create a fresh held-out packet, prove its provenance and
isolation, and test the repair. The implementation adds one ledger
finalization path and does not create a parallel promotion or candidate
framework. The duplicated authorization guard should be unified only after
the R0.3 trial contract is stable; refactoring it in this repair would widen
the control-surface change.

## Retirement and migration candidate

- Keep all R0.2 schemas, validator, authorization guard, hooks, tests, and
  packet artifacts as historical evidence for the earlier protocol. This
  step deletes or rewrites none of them.
- Use the R0.3 read-ledger and receipt schemas, finalizer, task contract,
  authorization guard, and hooks for a future R0.3 trial. The R0.2 validator
  and packet contract are not the R0.3 execution specification.
- After the R0.3 trial, consider moving the shared repository, identity,
  branch, worktree, and remote checks into one version-neutral authorization
  core with thin versioned adapters. Keep version-specific authorization
  schemas and packet contracts, and retain the existing R0.2 artifacts.

No historical evidence is retired by this report.

## Step08 path accounting

This report is classified as `EVALUATION_EVIDENCE`. After adding its path, two
successive runs of the existing path generator each produced 4,694 rows with
zero unresolved paths. The generated manifest reached a byte-identical
fixed point at SHA256
`441a6faea10fd78d2296b747a117854fa69229d4df14e0299488071c81b6c765`; the
path validator passed all 10 checks.
