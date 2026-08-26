# IGNITION-20260826-140 Step 15 — Candidate natural full regression

## Result

The exact Task140 candidate head
`86a188e4fc86037086f8d1ba7de0fd9130cd5249` completed the natural isolated
full regression with **1227 tests, 0 failures, 0 errors and 0 skips**. The
runner completed naturally in `3070.464s` runtime / `3071.522s` elapsed, with
no watchdog, arbitrary timeout or process kill. The isolated dependency
contract passed with Python `3.14.6`, SymPy `1.14.0`, z3-solver `4.16.0.0`
and jsonschema `4.26.0`; candidate tree snapshots were clean before and
after the run and generated-output drift was empty.

The machine receipt preserves both natural attempts. The first run was not
relabeled as green: it completed with **1201 tests, 19 failures, 1 error and
0 skips** because the canonical component registry overlap repair had not yet
been reflected in the generated component execution profiles. The profiles
were regenerated, their focused 45-test closure passed, and the second full
run above passed without adding skips, xfails, expected failures or ignores.

The successful capture remains external to the formal repository:

- stdout SHA-256: `447c8fc9507588ab4eeb13077bbcdf408820fbc00ace54050da628e460c64124`;
- stderr SHA-256: `f9b5f13dc70dc9c38421298bd5316682b79ee584bda8020c4788982a27fe8f8e`.

The first failed capture is also retained by digest in the machine receipt;
it is repair evidence, not a residual hidden by the passing run.

## Projection and live boundaries

The Step15 projection preflight is refreshed after this receipt and report are
present. It must remain a 25-check clean-tree PASS with no side effects before
the candidate is pushed for Step16 fresh-clone replay.

No new live invocation occurred in Step15. The canonical typed projection
remains at six attempts, zero validated completions, zero unreconciled
attempts and two observation-incomplete records. The
`LIVE_EXTERNAL_INVOCATION` obligation remains `OPEN`, retry remains
`NOT_AUTHORIZED`, and no completion claim is created by offline tests.

Claim ceiling: exact repository-local candidate natural offline full-suite and
projection-repair evidence only; no fresh-clone, formal-main publication,
validated live completion, external truth, production readiness, Owner
acceptance or epistemic acceptance is inferred.
