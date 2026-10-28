# IGNITION-20260824-138 — Step 06 Capability / Auth / Billing Re-attestation

Before any real inference, the current public Codex CLI was re-observed in a
disposable read-only probe directory. The observed version is
`codex-cli 0.144.4`; the public `exec --help` interface digest is
`9f86f0115238ddde2514587e5f95b0ab0aa6b89495e5912878d49ad26038aa19`, and the
binary digest is
`134063e133f0b4244fa3b251acf973d4fe4b4aeeacbdc135211bf480f59f1477`.

The public login-status command returned an authenticated presence signal. No
credential, token, account identifier or config value was read or persisted;
the receipt records only `PUBLIC_LOGIN_STATUS_PRESENCE_ONLY`. Safe flags,
structured JSONL/output-schema support, explicit read-only workspace semantics
and the R3 attempt-runtime-scratch contract were observed. The new lease is
`lease-ignition-138-r3`, with lease digest
`a03b87bf019e787c30e9a858ed6fdd5cfb4f1f91ce396a9c3ab0800c73ce5675` and a
15-minute bounded TTL.

The lease is eligible for the next bounded read-only attempt with no blockers.
Its forbidden capabilities continue to include repository write/test,
terminal, browser, web, messaging, subagents and scheduler surfaces. The
budget authority remains `NO_NEW_BILLING_AUTHORITY`; configuration mutation and
re-login are not authorized actions.

No inference was started and no external state was changed.

Claim ceiling: public Codex capability/auth/billing re-attestation only; no
live result, validated completion, production readiness, external truth, Owner
acceptance or epistemic acceptance is inferred.
