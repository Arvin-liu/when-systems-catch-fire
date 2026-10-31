# Handoff Artifact Byte Checker

`collaboration.verify_handoff_artifact_files` is an optional, read-only local
checker for a typed Federation result receipt. It opens the receipt's artifact
references under a caller-selected workspace root inside this checkout's
`ignition/` directory and compares bounded file bytes with each declared
SHA-256 digest.

It complements `collaboration.preflight_receiver_handoff`: that preflight binds
a serialized handoff bundle to its receipt and checks caller-declared receiver
preconditions, while this tool reads local artifact bytes. A matching digest
does not authenticate the receipt or its author, prove where the file came
from, establish that an action occurred, or authorize a takeover.

The existing `knowledge.assemble_context_packet` also checks file digests, but
it assembles UTF-8 line excerpts for task obligations and emits selected source
text. This checker has a narrower artifact-receipt contract: it can verify
binary files, returns digest statuses without file contents, and reads only
under the caller-selected `ignition/` workspace. The synthetic comparison
found complementary scopes; neither tool replaces the other's useful tasks.

## Invocation

The root is a separate CLI argument, not an untrusted field inside the receipt.
Relative roots resolve from the repository root; the resolved root must remain
under `ignition/`. Artifact references must be relative POSIX paths under that
root. Absolute paths, traversal, URI references, symlink components, non-regular
files, and unsupported platforms fail closed.

```sh
python3 -B ignition/tools/toolbox_verify_handoff_artifact_files.py \
  --stdin \
  --workspace-root ignition/tests/fixtures/toolbox-handoff-artifact-byte-check/workspace \
  < ignition/tests/fixtures/toolbox-handoff-artifact-byte-check/valid-input-r0.json
```

The JSON input contains exactly `schema_version` and a canonical
`FederatedResultReceipt`. The result reports a per-artifact status and expected
and observed digests; it never returns file contents. `execution_authorized`
is always false. The self-digest is unkeyed, so receipt authenticity remains
unestablished.

## Bounds and fallback

- Standard-library Python; POSIX descriptor operations with `O_NOFOLLOW`,
  `O_DIRECTORY`, and `dir_fd` support are required.
- Input is capped at 262,144 bytes, artifact count at 64, one file at 8 MiB,
  and total bytes read at 32 MiB.
- Each file must be regular. File identity/size/time metadata is checked before
  and after the bounded read; a detected concurrent change is reported.
- The tool makes no writes, network requests, billing calls, secret reads, or
  external actions. CPU, memory, and latency cost beyond the fixed read limits
  has not been calibrated.
- `ALL_DIGESTS_MATCH` means only that the bytes read during this invocation
  match the unkeyed digests in the supplied receipt. Other outcomes require
  reconciliation or a separately authorized review; do not treat them as a
  receiver preflight pass.

If the local root or a referenced artifact is unavailable, report the typed
status and use the existing handoff process only after independent provenance,
workspace, capability, and authorization checks. Do not infer success from a
caller assertion or a receipt's self-digest.
