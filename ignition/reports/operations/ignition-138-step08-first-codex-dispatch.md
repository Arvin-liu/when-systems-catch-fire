# IGNITION-20260824-138 — Step 08 First Real Codex Bounded Dispatch

The first real Codex R3 child used new identities
`dispatch-138-live-01` / `attempt-138-live-01`, the fresh lease
`lease-ignition-138-live-01-repaired`, the Task138 fixture, an external strict
schema, a mode-0555 task workspace and an attempt-specific runtime scratch.
The default persistent-document root was rejected before child launch because
it contains historical symlinks; the invocation was then rerun only after the
specific, fail-closed repair of selecting the independently verified
symlink-free `~/我的笔记` root. No workspace permission was widened and no
symlink check was bypassed.

The repaired first real child process exited in 61.166 ms with return code 1.
It produced zero stdout bytes and no structured JSONL result; stderr was
bounded to 521 bytes with digest
`79bf39ba628c787ae5baf83ed84bff92b2a4f36583dd820f3b64c1698e0120f3`. The
process group was `CONFIRMED_GONE`, no session pointer was observed, no timeout
or output truncation occurred, and the workspace digest remained
`40ab9b327e6bf1044e3f57e00aaf483fe6d7f2f77a3bcddc4c414d1825556fba`.
Runtime scratch had empty metadata digest before and after
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, and
cleanup was `CLEANED`.

A separate non-inference public `login status` probe under the exact isolated
runtime environment reproduced the public configuration error: the declared
`CODEX_HOME` directory did not exist, so configuration loading failed before
any model result. This is classified as the concrete
`CODEX_RUNTIME_PATH_PRE_INFERENCE_STARTUP_FAILURE` with known no effect for
the second-attempt gate. It is not a model, quota, billing or timeout failure.

The Step09 gate predicates are all satisfied: process group gone, no session,
no structured result, no timeout/effect uncertainty, unchanged workspace,
cleaned scratch, no observed external side effect, and a narrow repair that
only prepares declared runtime directories inside scratch. No blind retry is
authorized; the second invocation remains conditional on that repair and its
targeted regression.

Claim ceiling: one bounded Codex startup failure and its machine-observed
known-no-effect pre-inference classification only; no validated live
completion, production readiness, external truth, Owner acceptance or
epistemic acceptance is inferred.
