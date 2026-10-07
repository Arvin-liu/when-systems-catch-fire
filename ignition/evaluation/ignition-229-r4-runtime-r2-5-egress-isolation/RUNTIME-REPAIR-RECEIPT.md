# Lane B Task229 R4 R2.5 runtime isolation receipt

**Marker:** `TASK229_R4_RUNTIME_ADMISSION_BLOCKED_BY_EGRESS_SCOPE_LIMIT`

**Execution status:** `LIVE_CANARY_NOT_ADMITTED`

**Decision:** Preserve the Stage 01 hard stop. Local isolation and cleanup checks now have reproducible evidence, but the current exact-head Foundation failure cannot be repaired inside the authorized Lane B read boundary. No Codex app-server, native-auth preflight, canary, or R4 unit was launched.

## Authority and preserved starting state

- Stage 02 controller: `Arvin-liu/1111@ccf0c3689369b135aca42fda98dfafa1e923a127`.
- Stage 01 hard-stop receipt: `Arvin-liu/1111@244b301c30eb89924ea6c19c7932d3307f34a75a`.
- Formal Draft PR #249 was `OPEN` and `DRAFT`, unmerged, at exact head `e6a36ee79b6427cbce528c2e97c67630f39d01f7` and base `ef819228adf52bd162ba834095fb2489b348cb8e` at preflight. This successor branch starts from that exact head; #249 and the Stage 01 receipt were not mutated.
- R1 runtime/canary contract and prompt policy remain unchanged. The only request text in the local source fixture is the fixed non-scientific `R4_RUNTIME_AUTH_PREFLIGHT_OK` check; it was not sent.
- No Lane A / AB-19 hidden or pilot answer content was opened, used, or included in this package.

## Runtime isolation architecture

- `egress_broker.py` binds only to `127.0.0.1`, accepts bounded HTTP CONNECT requests, normalizes exact DNS host-and-port entries, and denies all unlisted destinations before DNS or upstream connection. Wildcards, lookalike hosts, and wrong ports are rejected. The local TLS-like fixture passed through the allowlisted tunnel byte-for-byte; the broker never terminates TLS, parses TLS content, or logs proxy header values.
- The candidate Codex process is to run under a Seatbelt profile that denies all outbound networking and permits one `localhost:<ephemeral-broker-port>` destination. The macOS probe reached the actual deny-first broker, confirmed the broker returned 403 without forwarding, denied another loopback port, and denied a direct TEST-NET destination. The verified profile hash for this run is recorded in `local-gates.json`.
- `process_supervisor.py` records the supervised process group and observed descendant PID/start-time pairs, sends TERM, waits a bounded grace period, sends KILL to survivors, and reports whether observed processes remain. Local tests covered normal exit, a parent/child process group, and an observed child that changes process group. The Codex app-server itself was not launched, so its runtime descendants and cleanup were not observed.
- The patched runtime source constructs only the first-party `POST https://api.openai.com/v1/responses` body, includes `tools: []` and `tool_choice: "none"`, verifies the exact body before transport, records the body and pre-send hash before `transport.execute`, checks native ChatGPT auth presence without recording its value, and captures the bounded response before JSON parsing. These are source/build checks only; no trusted pre-send capture exists because no model request was made.

## Local-only evidence

- Ten local tests passed: five broker tests, three cleanup tests, and two macOS profile tests.
- The deny-first integration record contains one synthetic blocked host attempt, `stage02.local-probe.invalid:443`, with no upstream IP or header value. The broker had an empty allowlist during this integration. Other tests exercised `api.openai.com:443` against a local fixture connector only; no network connection to that host was attempted.
- Codex source base: upstream commit `ff6aec96948b70d94983af2641a6b67c94faeff5`. The local patched source snapshot was committed as `0e76e6b4d63539595e073eb8fdfe90649e50f669` after verifying the authenticated GitHub account and noreply identity. Selected-source digest: `a62a68bb01f96698d2e55fb77914e67d3879f698976f8f53f57d5411bbb5b22e`; local binary SHA-256: `33626f845897d8d90afd28de8204b0765ebc66b7c20a7fe52a666f5b908fbac3`.
- `cargo +stable build --offline -p codex-cli --bin codex` passed under Rust 1.97. The pinned 1.95 toolchain could not be used because its local rustup toolchain is missing a manifest and fetching it failed. Cargo 1.97 rewrote workspace package versions in the lockfile before the local snapshot was committed; the resulting source digest is therefore not claimed to reproduce the R2.4 receipt's `f4940796d2d2b9db56db35a96f3c7f90d3763043622cc6c3f4d1d225a03f93a9` digest. No live request used either build.
- No API key or native credential contents were read, copied, exported, printed, or semantically inspected. The broker and tests use only synthetic local fixtures. The local integration test's placeholder proxy-header marker is synthetic and never reached an upstream.

## Foundation hard stop

At #249 exact head `e6a36ee79b6427cbce528c2e97c67630f39d01f7`, build and repository-path preflight passed; Foundation validation failed in run `37357660234`, job `111924352519`:

- `nonfunction-claim-closure:integrated` failed with `NONFUNCTION_CLAIM_OUTPUT_DRIFT` for the generated source-discovery, closure-summary, discovery-coverage, and claim-adjudication index outputs.
- `discovery:every-repository-path-accounted` reported `listed=7016 tracked=7026`.

The authoritative `adjudicate_nonfunction_claims.py` generator iterates every tracked repository path and reads file contents for paths admitted by the knowledge-corpus auto-discovery policy. No narrower authorized input boundary is available for this stage. Running that generator could read Lane A / AB-19 material, so it was not run. No generated output, classification manifest, claim status, adjudication, claim source, claim ceiling, or validation rule was changed. This new R2.5 package adds runtime-evidence paths, so repository-path accounting and exact-head Foundation CI remain unresolved.

## Counts and terminal boundary

- Native-auth runtime requests: `0`; canary calls: `0`; R4 units: `0/18`; retries/replacements/reorders: `0`; evaluator runs: `0`; Task230: `false`.
- Trusted pre-send capture: none. Runtime auth route and host discovery: not attempted. No exact-host network allowlist was opened for forwarding; `api.openai.com:443` is only the fixed R1 endpoint reference and a local fixture-test authority.
- Independent read-only review before a live scientific request: pending. Exact-head CI for this successor: pending at receipt creation; no live work is admitted unless required CI is green.
- Unresolved assumptions: the actual Codex app-server process tree has not been launched under this profile; actual native-auth endpoint/refresh hosts have not been discovered; host-level broker forwarding to the real endpoint has not been attempted; and Rust 1.97 build provenance differs from the pinned-toolchain R2.4 digest.
- An accidental broad `git status` path-metadata listing from a fresh no-checkout Formal clone is documented in the private lane audit. Its truncated output prevents determining whether protected path names appeared; no content blobs were read by that command. The listing was not reopened.

**Terminal marker:** `TASK229_R4_RUNTIME_ADMISSION_BLOCKED_BY_EGRESS_SCOPE_LIMIT`
