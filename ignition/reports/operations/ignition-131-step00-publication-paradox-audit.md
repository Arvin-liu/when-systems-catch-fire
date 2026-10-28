# IGNITION-131 Step 00 — Release publication paradox audit

## Baseline

This audit was completed before any IGNITION-131 repair. The formal remote `main`
ref and an isolated fresh checkout both resolve to
`11e5ed0f8f16f7f315179b540f08018c2e6e45d1`, the terminal IGNITION-130 tip.

The static Current release record still says:

| Surface | Observed value |
| --- | --- |
| `current-release-lifecycle-r1.json` phase | `PREPARED_FOR_RELEASE` |
| lifecycle task-branch projection | `RELEASE_READY` |
| lifecycle publication state | `NOT_PUBLISHED` |
| lifecycle post-publication check status | `PENDING` |
| generated Current Snapshot phase | `PREPARED_FOR_RELEASE` |
| generated Current Snapshot publication | `NOT_PUBLISHED` |

The isolated checkout was clean, on branch `main`, had local `HEAD` equal to the
remote `refs/heads/main`, and passed the existing lifecycle validator.

## Exact false-pass reproduction

The existing command returned:

```text
POST_PUBLICATION_CURRENT_CHECK_OK mode=POST_PUBLICATION head=11e5ed0f8f16f7f315179b540f08018c2e6e45d1
```

This reproduces the Task130 false-closure class: the validator passes while the
Current surface still presents `NOT_PUBLISHED/PENDING` as its static publication
state. The result is not merely a prose mismatch. The validator's post-publication
branch accepts `PREPARED_FOR_RELEASE`, verifies only the local branch name and
local `HEAD` against the caller-provided expected SHA, and never observes
`git ls-remote origin refs/heads/main`. The lifecycle schema/validator also treats
the old static fields as a valid Current record. Therefore a local checkout can be
called post-publication without a remote-ref proof or a publication-state semantic
closure.

Task130's result correctly described its task-branch state as release-ready and
deferred the post-publication check until `main` moved, but the resulting static
Current projection had no separate authority class for the later remote fact. A
post-publication receipt can prove the remote observation; it must not be encoded
by adding a new formal commit that would itself need publication proof.

## Step 00 boundary

This artifact records repository-local evidence only. It does not establish
external truth, production readiness, Owner acceptance, live executor completion,
or epistemic acceptance. The repair must separate content-owned release readiness,
ref-observed publication, and the 1111 publication witness without changing the
architecture identity or map epoch.
