# IGNITION-20260824-137 — Step 03 Codex Live Eligibility Re-attestation

The current public Codex CLI was re-observed on the disposable probe surface:
`codex-cli 0.144.4`, with `exec --help` digest
`9f86f0115238ddde2514587e5f95b0ab0aa6b89495e5912878d49ad26038aa19`. The
public boundary includes `--json`, `--output-schema`, `--ephemeral`,
`--ignore-user-config`, `--ignore-rules`, `--sandbox read-only`, and explicit
`--cd`. The public resume help was also observed, but the attempt lease marks
resume unsupported because the planned child is ephemeral and must not inherit
or resume a session.

Login status reported presence without exposing a token. No auth file contents,
session database, prompt history, or provider telemetry was read. There is no
public cancel flag; cancellation is the OS transport's bounded process-group
SIGTERM/SIGKILL path. No new billing/provider authority was created.

The fresh 15-minute `LiveCapabilityLease` is
`live-codex-137-lease`, with digest
`c3a1c9d4e6d364832ad331768d4a0c6a7237b0d93e48d7e6735b242a9ab82d47`, and its
eligibility is `ELIGIBLE_FOR_LIVE_READONLY`. The adapter now requires the
observed output-schema flag and records a digest of the observed executable
when available. Targeted adapter/preflight tests passed: `6 / 0 / 0 / 0`.

Claim ceiling: this is a current public-interface eligibility observation. It
does not claim that a real dispatch will return, validate, or complete.
