# Lane B Task229 R4 runtime admission receipt

**Marker:** `TASK229_R4_RUNTIME_ADMISSION_BLOCKED_BY_EGRESS_SCOPE_LIMIT`

**Execution status:** `LIVE_CANARY_NOT_ADMITTED`

**Decision:** Stop before any scientific canary request. Runtime-only repairs are recorded for review; the host-scoped egress and process-cleanup gate is not satisfied.

## Authority and frozen starting state

- Stage controller: `Arvin-liu/1111`, branch `relay/goal-mode/IGNITION-20261005-stage-01`, commit `a1037f481af80287be9af011325ac1b8a4697ad4`.
- Frozen R1 runtime/canary specification: `Arvin-liu/when-systems-catch-fire@ef819228adf52bd162ba834095fb2489b348cb8e:ignition/evaluation/ignition-229-r4-runtime-prereg-r1/`.
- Starting Formal Draft PR #248: exact head `4fdb590ab315b385b544a97f386fabd4c4d24717`, base commit `ef819228adf52bd162ba834095fb2489b348cb8e`.
- Starting 1111 R2.2 receipt: commit `3eea13b6a3d40b5eeaec4ef7b117c6fafbc9b1ef`; its pinned receipt checksums were verified at preflight. No new 1111 receipt was created.
- Upstream Codex source: tag `rust-v0.159.2`, tag object `8b9fa496bbf2c47aebd62e85a080b9a522a455b5`, peeled commit `ff6aec96948b70d94983af2641a6b67c94faeff5`.

## Runtime-only repair lineage and hashes

- Preserved initial runtime patch: `07f11700db081da904e011c03dd6d4221a770a55`.
- R2.4 admission/capture/parser/cap repair: `e61e1ad5e3d73519e5b0c9a3c867e72e899b69da`.
- Build-bound source identity repair: `21bb399c7944499c08e01c78c6a606fbc47b8cca` on branch `lane-b/r2-4-admission-guards`.
- Upstream source archive SHA-256 at `21bb399`: `f7ed5d02d4073259c9d648c4cfcdff59f9d7ca67efc5175d7e4e00778ac68d79`.
- Runtime's compiled selected-source SHA-256: `f4940796d2d2b9db56db35a96f3c7f90d3763043622cc6c3f4d1d225a03f93a9`.
- Offline-built `codex` executable SHA-256: `f191d968bf168d27cd39ad46966da151339092e13faae4e25cabc95dde7e55e5`.

The runtime-only patch is included in this review package as `upstream-runtime-repair.patch`, based on the exact upstream tag commit and ending at `21bb399`. It modifies Codex request/response runtime machinery and build identity only. No frozen R4 scientific prompt, route, digest, expected outcome, 18-unit composition/order, retry rule, evaluator, or claim ceiling was edited.

## Review findings and offline disposition

The independent review found five defects. This repair addresses four and leaves the admission blocker open:

1. Unit mode could run before a successful canary. **Addressed in runtime code:** unit mode now requires a passing canary receipt tied to the current compiled source commit/hash and run metadata.
2. Process/egress isolation and cleanup were unproven. **Unresolved:** the permitted local sandbox cannot express the required host-scoped endpoint rule; descendant cleanup was not proven.
3. A pre-send run/source/input-hash record was missing. **Addressed in runtime code:** `pre-send.json` is written before transport with run, source, input, request, model/effort, empty-tools, and retry-count fields.
4. Duplicate JSON keys were accepted. **Addressed in runtime code:** response parsing rejects duplicate object keys recursively and trailing bytes.
5. The response byte cap exceeded the frozen value by one byte. **Addressed in runtime code:** the transport bound is exactly 1,048,576 bytes.

Capture paths and files are also constrained to canonical, private, runtime-owned, newly created objects without following the final-component symlink. These code changes are static/offline candidates only; they have not been admitted for a live run.

## Egress-profile probe evidence

The only egress tests were local macOS `sandbox-exec` profile-parse probes using the literal `/usr/bin/true` helper. The helper did not make a network request. Accepted profiles may have launched that helper; no Codex runtime, native-auth model client, or scientific process was launched.

| Profile | Result | Exact parser result | SHA-256 |
|---|---|---|---|
| `sandbox-profile-api-host-probe.sb` | Rejected | exit 65: `host must be * or localhost in network address` for `(remote ip "api.openai.com:443")` | `f052ed2ce7b76df8a02e9ec3f3591baf25ec171ff4723bc41ae3338192af15c9` |
| `sandbox-profile-probe.sb` | Rejected | exit 65: same host restriction for `(remote ip "1.1.1.1:443")` | `b0662dbb2ef5d9185b3859ac6bbffb3022d0a634ff5e1ea66bda7320d003d9e6` |
| `sandbox-profile-remote-tcp-probe.sb` | Rejected | exit 65: same host restriction for `(remote tcp "api.openai.com:443")` | `5d21a5d4d6d055ea2c460093071375cac35fd0ad2e92b1874e4171fbe5ba0826` |
| `sandbox-profile-param-probe.sb` | Rejected | exit 65: same host restriction for `(remote tcp (param "task229HostPort"))` | `f57144d18a1d4fbbd3ccaa082ed108d3ac1a42afcab6ff6328d1496acfa10f15` |
| `sandbox-profile-localhost-probe.sb` | Accepted | localhost-only destination; does not cover the frozen native-auth endpoint | `e58c6916083aab6e20adbafe645a42ecd6ca6b7f7cb3eca9b6375c93894b4461` |
| `sandbox-profile-wildcard-port-probe.sb` | Accepted | `(remote tcp "*:443")`; permits arbitrary-host HTTPS and was rejected as too broad, never used to run Codex | `ffb9eef12779bc19c379405b4dad7d6adbbf5fc411118cafe648627037d21f4b` |

The exact profile files are included under `profiles/`. The API hostname, numeric destination, protocol-specific host, and parameterized host rules all failed the same host restriction. A wildcard port rule is too broad. No alternate provider route, credential path, privileged firewall, or widened permission was used. The local `sandbox-exec` manual marks the interface deprecated.

## Call, process, capture, and run counts

- Native-auth Codex/model request process: `0`.
- Live provider/model calls: `0`; canary attempted: `0`.
- Local profile probes: parser-only. On accepted profiles, only literal `/usr/bin/true` helper processes could launch; no helper attempted networking.
- Codex runtime descendants or cleanup test: `0`; descendant cleanup remains unproven.
- Pre-send capture: none, because no live request was made. No response or scientific input capture exists.
- R4 units: `0/18`; evaluator: `0`; Task230: `false`.
- Ready/merge: `0`; new 1111 receipt: none; starting R2.2 receipt unchanged.
- Credentials: no credentials or credential-file contents were read, exported, copied, or substituted; no API key was used.
- Lane A / AB-16 scientific bodies, fixtures, hidden outcomes, and result artifacts: not accessed.

## Validation and remaining admission condition

- `RUSTUP_TOOLCHAIN=stable cargo build --offline --bin codex` completed for `21bb399`; binary SHA-256 is recorded above.
- `git diff --check` passed for the upstream runtime patch and Formal receipt changes.
- The earlier targeted offline Rust test attempt stopped before compilation because `assert_matches v1.5.0` is not cached. No dependency fetch or provider call was attempted.
- No scientific canary, R4 unit, or evaluator was run.
- Initial Draft PR #249 checks at exact head `0fb9cea984daa2d0d3ea5981d8b98cc43048b028`:

  | Workflow/job | Run | Conclusion at observation |
  |---|---:|---|
  | `architecture-pages / build` | `37356133949` | `SUCCESS` |
  | `architecture-pages / deploy` | `37356133949` | `SKIPPED` |
  | `repository-path-accounting-preflight / preflight` | `37356134051` | `FAILURE` — 10 new R2.4 paths were missing from the classification manifest |
  | `foundation-validation / validate` | `37356133963` | `IN_PROGRESS` at the last observation; its job output was not inspected |

  The failed preflight inspected path metadata only. The 10 paths were added as `EVALUATION_EVIDENCE`; the exact local `validate_repository_path_classification.py --check` then passed all 10 checks, and `git diff --check` passed. The next commit records this append-only correction; its exact-head CI is pending.
- Independent read-only review of the successor package remains pending.

Admission remains blocked until an authorized process-scoped control proves both (a) exact host-scoped egress for the actual native-auth model-facing request while denying other egress and (b) bounded descendant cleanup and capture. If local policy cannot establish those properties without credential access or permission widening, this hard stop remains terminal for the current execution.
